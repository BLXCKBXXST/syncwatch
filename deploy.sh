#!/usr/bin/env bash
# deploy.sh — install/uninstall the platform on your own server behind a Caddy
# reverse proxy.
#
# Usage (run ON the server):
#   ./deploy.sh --install     # deploy the app
#   ./deploy.sh --uninstall   # tear it down
#
# Assumes a Caddy stack already exists at /opt/stack/docker-compose.yml.
# Both modes are idempotent and safe to re-run.
set -euo pipefail

STACK_DIR="/opt/stack"
COMPOSE_FILE="${STACK_DIR}/docker-compose.yml"
CADDY_FILE="${STACK_DIR}/caddy/Caddyfile"
APP_DIR="${STACK_DIR}/blxckhub"
ENV_FILE="${APP_DIR}/.env"
USER_NAME="$(id -un)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<EOF
Usage: $(basename "$0") --install | --uninstall

  --install     Install: sync sources into ${APP_DIR}, add the
                blxckhub-db/redis/backend/frontend services to the shared
                docker-compose.yml, append the subdomain to Caddyfile, and
                bring the stack up.

  --uninstall   Uninstall: stop and remove the containers, drop the services
                from docker-compose.yml and the subdomain block from Caddyfile,
                delete ${APP_DIR}.

Both modes are idempotent and safe to re-run.
EOF
}

prompt_default() {
    local msg="$1" def="$2" var="$3" ans
    read -r -p "${msg} [${def}]: " ans || true
    printf -v "${var}" '%s' "${ans:-$def}"
}

require_caddy_stack() {
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        echo "ОШИБКА: ${COMPOSE_FILE} не найден. Сначала разверните Caddy-стек." >&2
        exit 1
    fi
    if [[ ! -f "${CADDY_FILE}" ]]; then
        echo "ОШИБКА: ${CADDY_FILE} не найден. Сначала разверните Caddy-стек." >&2
        exit 1
    fi
}

reload_caddy() {
    echo "==> Перезагружаю Caddy..."
    if ( cd "${STACK_DIR}" && docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null ); then
        echo "    Caddy перечитал конфиг без рестарта."
    else
        echo "    caddy reload не сработал — перезапускаю контейнер."
        ( cd "${STACK_DIR}" && docker compose restart caddy )
    fi
}

# Случайная строка из шестнадцатеричных символов (безопасна для URL и .env).
gen_secret() {
    openssl rand -hex 32
}

action_install() {
    require_caddy_stack

    prompt_default "Public domain" "example.com" DOMAIN

    echo "==> Бэкаплю docker-compose.yml и Caddyfile..."
    local stamp; stamp="$(date +%Y%m%d-%H%M%S)"
    cp -a "${COMPOSE_FILE}" "${COMPOSE_FILE}.bak.${stamp}"
    cp -a "${CADDY_FILE}"   "${CADDY_FILE}.bak.${stamp}"

    echo "==> Создаю каталоги ${APP_DIR}..."
    sudo -A mkdir -p "${APP_DIR}/data/pg" "${APP_DIR}/data/media" "${APP_DIR}/data/static"
    sudo -A chown -R "${USER_NAME}:${USER_NAME}" "${APP_DIR}"

    echo "==> Синхронизирую исходники: ${SCRIPT_DIR}/app -> ${APP_DIR}/app..."
    rsync -a --delete \
        --exclude='.git' --exclude='node_modules' --exclude='.venv' \
        --exclude='__pycache__' --exclude='*.pyc' --exclude='db.sqlite3' \
        --exclude='media' --exclude='staticfiles' --exclude='dist' --exclude='.env' \
        "${SCRIPT_DIR}/app/" "${APP_DIR}/app/"

    if [[ ! -f "${ENV_FILE}" ]]; then
        echo "==> Генерирую ${ENV_FILE}..."
        local db_pass; db_pass="$(gen_secret)"
        cat >"${ENV_FILE}" <<EOF
DJANGO_SECRET_KEY=$(gen_secret)
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=${DOMAIN}
DATABASE_URL=postgres://blxckhub:${db_pass}@blxckhub-db:5432/blxckhub
POSTGRES_DB=blxckhub
POSTGRES_USER=blxckhub
POSTGRES_PASSWORD=${db_pass}
REDIS_URL=redis://blxckhub-redis:6379/0
CORS_ALLOWED_ORIGINS=https://${DOMAIN}
CSRF_TRUSTED_ORIGINS=https://${DOMAIN}
EOF
    else
        echo "==> ${ENV_FILE} уже существует — оставляю без изменений."
    fi

    if grep -qE '^[[:space:]]+blxckhub-backend:[[:space:]]*$' "${COMPOSE_FILE}"; then
        echo "==> Services already present in ${COMPOSE_FILE} — skipping."
    else
        echo "==> Adding services to ${COMPOSE_FILE}..."
        cat >>"${COMPOSE_FILE}" <<'EOF'

  blxckhub-db:
    image: postgres:16-alpine
    container_name: blxckhub-db
    restart: unless-stopped
    env_file: ./blxckhub/.env
    volumes:
      - ./blxckhub/data/pg:/var/lib/postgresql/data

  blxckhub-redis:
    image: redis:7-alpine
    container_name: blxckhub-redis
    restart: unless-stopped

  blxckhub-backend:
    build: ./blxckhub/app/backend
    container_name: blxckhub-backend
    restart: unless-stopped
    env_file: ./blxckhub/.env
    depends_on:
      - blxckhub-db
      - blxckhub-redis
    volumes:
      - ./blxckhub/data/media:/app/media
      - ./blxckhub/data/static:/app/staticfiles

  blxckhub-frontend:
    build: ./blxckhub/app/frontend
    container_name: blxckhub-frontend
    restart: unless-stopped
    depends_on:
      - blxckhub-backend
    volumes:
      - ./blxckhub/data/media:/srv/media:ro
      - ./blxckhub/data/static:/srv/static:ro
EOF
    fi

    if grep -qF "${DOMAIN} {" "${CADDY_FILE}"; then
        echo "==> Блок ${DOMAIN} уже есть в ${CADDY_FILE} — пропускаю."
    else
        echo "==> Дописываю блок ${DOMAIN} в ${CADDY_FILE}..."
        cat >>"${CADDY_FILE}" <<EOF

${DOMAIN} {
    encode gzip
    reverse_proxy blxckhub-frontend:80
}
EOF
    fi

    echo "==> docker compose config (валидация)..."
    ( cd "${STACK_DIR}" && docker compose config >/dev/null )

    echo "==> docker compose up -d --build (сборка может занять пару минут)..."
    ( cd "${STACK_DIR}" && docker compose up -d --build \
        blxckhub-db blxckhub-redis blxckhub-backend blxckhub-frontend )

    reload_caddy

    cat <<EOF

================================================================================
Deployment complete.

Public URL:
  https://${DOMAIN}  -> blxckhub-frontend (nginx) -> blxckhub-backend (daphne)

Next steps:
  1. Make sure DNS A/CNAME for ${DOMAIN} points at this server's public IP.
  2. Open https://${DOMAIN} — on the first request Caddy spends ~30 seconds
     issuing a TLS certificate from Let's Encrypt.
  3. Sign in with a username and password; there is also a "sign in as guest"
     button. Guest accounts are auto-deleted after 24 hours of inactivity.
  4. Logs: docker logs -f blxckhub-backend | blxckhub-frontend | caddy

To tear down later:
  ./deploy.sh --uninstall
================================================================================
EOF
}

action_uninstall() {
    require_caddy_stack

    prompt_default "Domain to remove" "example.com" DOMAIN

    echo "==> Бэкаплю docker-compose.yml и Caddyfile..."
    local stamp; stamp="$(date +%Y%m%d-%H%M%S)"
    cp -a "${COMPOSE_FILE}" "${COMPOSE_FILE}.bak.${stamp}"
    cp -a "${CADDY_FILE}"   "${CADDY_FILE}.bak.${stamp}"

    echo "==> Stopping and removing containers..."
    for svc in blxckhub-frontend blxckhub-backend blxckhub-redis blxckhub-db; do
        if ( cd "${STACK_DIR}" && docker compose ps --services 2>/dev/null | grep -qx "${svc}" ); then
            ( cd "${STACK_DIR}" && docker compose stop "${svc}" && docker compose rm -f "${svc}" )
        fi
    done

    if grep -qE '^[[:space:]]+blxckhub-db:[[:space:]]*$' "${COMPOSE_FILE}"; then
        echo "==> Removing services from ${COMPOSE_FILE}..."
        # Удаляем блок от строки "  blxckhub-db:" до следующего НЕ-blxckhub
        # сервиса (две ведущих пробела + слово) либо до конца файла.
        awk '
            BEGIN { skip = 0 }
            /^[[:space:]]+blxckhub-db:[[:space:]]*$/ { skip = 1; next }
            skip && /^[[:space:]]{2}[A-Za-z0-9_-]+:[[:space:]]*$/ && $0 !~ /blxckhub-/ { skip = 0 }
            skip && /^[A-Za-z]/ { skip = 0 }
            skip == 0 { print }
        ' "${COMPOSE_FILE}" > "${COMPOSE_FILE}.tmp"
        mv "${COMPOSE_FILE}.tmp" "${COMPOSE_FILE}"
    else
        echo "==> Services are absent from ${COMPOSE_FILE} — skipping."
    fi

    if grep -qF "${DOMAIN} {" "${CADDY_FILE}"; then
        echo "==> Удаляю блок ${DOMAIN} из ${CADDY_FILE}..."
        awk -v dom="${DOMAIN}" '
            BEGIN { skip = 0 }
            $0 ~ "^"dom" \\{$" { skip = 1; next }
            skip && /^\}[[:space:]]*$/ { skip = 0; next }
            skip == 0 { print }
        ' "${CADDY_FILE}" > "${CADDY_FILE}.tmp"
        mv "${CADDY_FILE}.tmp" "${CADDY_FILE}"
    else
        echo "==> Блок ${DOMAIN} отсутствует в ${CADDY_FILE} — пропускаю."
    fi

    if [[ -d "${APP_DIR}" ]]; then
        echo "==> Удаляю каталог ${APP_DIR}..."
        sudo -A rm -rf "${APP_DIR}"
    fi

    echo "==> docker compose config (валидация)..."
    ( cd "${STACK_DIR}" && docker compose config >/dev/null )

    reload_caddy

    cat <<EOF

================================================================================
Uninstalled: containers stopped, services and Caddy block removed,
${APP_DIR} deleted. Timestamped backups of compose and Caddyfile
remain alongside — restore manually if needed.
================================================================================
EOF
}

case "${1:-}" in
    --install)   action_install ;;
    --uninstall) action_uninstall ;;
    -h|--help|"") usage; [[ -z "${1:-}" ]] && exit 1 || exit 0 ;;
    *) echo "Неизвестный ключ: $1" >&2; usage; exit 1 ;;
esac
