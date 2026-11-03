# Website fonts for the catalog

Cinzel 500 and 700 and Cormorant Garamond 500 come from the website's
`@fontsource/cinzel` and `@fontsource/cormorant-garamond` packages. Their Latin
and Latin Extended WOFF subsets are decoded and merged into TTF with fontTools.
The original OFL-1.1 notices accompany the fonts; these are third-party assets,
not EITR artwork. FontLoader loads them only for the catalog, with the system's
Noto Sans Runic and fixed JetBrains Mono for runes and body text.

Regenerate with fontTools installed, from the repository root:

```sh
python3 quickshell/desktop-bar/assets/fonts/export.py website/node_modules/@fontsource
```

The package stages the TTFs and OFL texts with the catalog assets and installs
copies of the licenses under `/usr/share/licenses/eitr-desktop/`.
