# Fonts

Subset Latin faces converted from the Fontsource packages to plain TTF so Pillow
can load them.

| File | Family | Weight | Licence |
|---|---|---|---|
| Montserrat-Black.ttf | Montserrat | 900 | SIL Open Font Licence 1.1 |
| Montserrat-ExtraBold.ttf | Montserrat | 800 | SIL OFL 1.1 |
| Montserrat-Bold.ttf | Montserrat | 700 | SIL OFL 1.1 |
| Inter-Medium/SemiBold/Bold.ttf | Inter | 500/600/700 | SIL OFL 1.1 |
| JetBrainsMono-Medium/Bold.ttf | JetBrains Mono | 500/700 | SIL OFL 1.1 |

Converted with `fontTools` (`flavor = None` on the woff2 files from
`@fontsource/montserrat@5`, `@fontsource/inter@5`, `@fontsource/jetbrains-mono@5`).
The OFL requires that these files keep their licence; they are not modified
outlines, only re-containerised.
