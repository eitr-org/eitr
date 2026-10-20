# Before Publishing

See [PUBLISHING.md](PUBLISHING.md): split the personal overlay from the distro.

# Display Layout

Deferred until a second physical monitor is connected for testing:

- Verify arrangements (side, alignment, following a changed target) and
  persistent primary selection with both monitors connected.
- Verify OBS full-screen capture follows the selected primary display. Its
  Wayland portal permission currently keeps the previously selected monitor;
  do not silently claim this follows the bar's primary setting.

Already in the Display panel: primary selection (machine-local
`hypr/primary-display`), and each monitor's mode, scale, arrangement beside
another (aligned, remembered, overlaps refused) and mirroring, with a 15-second
revert unless kept, plus Edit layout by hand.

# Later

- **AI multi-account:** several accounts per assistant, with manual switching only;
  no automatic account switching.
- **Eitr plugins:** installable Git repositories with a manifest and a clear trust
  warning before running their code. The cooler-display tool would be the first plugin.
- **Personal overlay split:** move the owner's own `HOME_FILES/.zshrc` and
  `owner/cooler-display` to a private repository once the owner creates it.
