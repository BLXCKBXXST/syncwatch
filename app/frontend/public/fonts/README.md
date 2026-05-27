# Шрифты альтернативной светлой темы

В папке лежат 4 файла `.woff2` — variable-сборка `@fontsource-variable`
(один файл на subset, все веса 100–900 внутри):

| Файл                              | Шрифт          | Subset    |
| --------------------------------- | -------------- | --------- |
| `inter-latin.woff2`               | Inter          | latin     |
| `inter-cyrillic.woff2`            | Inter          | cyrillic  |
| `jetbrains-mono-latin.woff2`      | JetBrains Mono | latin     |
| `jetbrains-mono-cyrillic.woff2`   | JetBrains Mono | cyrillic  |

Источник:
- `https://cdn.jsdelivr.net/npm/@fontsource-variable/inter@5.2.5/files/inter-<subset>-wght-normal.woff2`
- `https://cdn.jsdelivr.net/npm/@fontsource-variable/jetbrains-mono@5.2.5/files/jetbrains-mono-<subset>-wght-normal.woff2`

Подключение — через `@font-face` с `unicode-range` в [`src/styles/sonar-theme.css`](../../src/styles/sonar-theme.css). Файлы активируются только под `:root[data-theme='sonar']`.
