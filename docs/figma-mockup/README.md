# Figma-каркасы

HTML-каркасы экранов Syncwatch для импорта в Figma через плагин
[html.to.design](https://www.figma.com/community/plugin/1159123024924461424).
Каждый файл — самостоятельная страница с inline-стилями и SVG-иконками,
без внешних зависимостей кроме шрифтов с Google Fonts.

## Темы

### `default/` — тёмная (8 экранов × desktop/mobile)

Полный набор экранов в дефолтной тёмной теме с индигово-фиолетовым акцентом:
`home`, `login`, `register`, `watch`, `room`, `upload`, `profile`, `notfound`.

- `default/desktop/` — ширина 1440 px.
- `default/mobile/` — ширина 390 px.

### `sonar/` — светлая deep-blue (4 ключевых экрана × desktop/mobile)

Компактный набор в теме Sonar (белый фон, deep-blue акцент, концентрические
кольца на auth-фоне): `home`, `watch`, `room`, `auth` (вход + регистрация
на одном экране).

- `sonar/desktop/` — ширина 1440 px.
- `sonar/mobile/` — ширина 360 px.

## Импорт в Figma

1. В Figma запустить плагин **html.to.design** (Plugins → Import).
2. Вкладка **Code** — скопировать содержимое любого `.html` и вставить.
   Либо вкладка **URL** — указать raw-ссылку из GitHub
   (`https://raw.githubusercontent.com/BLXCKBXXST/syncwatch/main/docs/figma-mockup/...`).
3. Плагин создаёт фрейм с правильной шириной и осмысленными именами слоёв.
4. После импорта можно объединять парные desktop/mobile фреймы в страницы по экранам.
