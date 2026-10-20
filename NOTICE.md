# Third-party notices

EITR's own code and configuration are GPL-3.0-or-later ([LICENSE](LICENSE)).
Its wallpapers, lockscreen backgrounds and screenshots are CC BY 4.0
([artwork licensing](distro/ARTWORK-LICENSING.md)). This file lists everything
else that EITR's repository, packages or ISO contain, with its source and
license. `distro/tests/test_notice.py` fails when a license file or bundled
package is missing from it.

## Inside this repository

| Component | Where | From | License |
|---|---|---|---|
| Lockscreen layouts Girl, Material, Nothing and Theme Wallpaper, and their SDDM login versions | `quickshell/lockscreen/` | [qylock](https://github.com/Darkkal44/qylock) by Darkkal44, revision `f6561e2` | GPL-3.0, [`quickshell/lockscreen/LICENSE`](quickshell/lockscreen/LICENSE) |
| Clockwork lockscreen | `quickshell/lockscreen/` | EITR's own code; its Tape and Neo Orbital ideas come from qylock's Clockwork designs | GPL-3.0-or-later |
| Neovim configuration | `nvim/` | [LazyVim starter](https://github.com/LazyVim/starter) | Apache-2.0, [`nvim/LICENSE`](nvim/LICENSE) |
| Emoji list and keywords | `quickshell/emoji-picker/emojis.json` | Unicode [emoji-test.txt](https://unicode.org/Public/emoji/latest/emoji-test.txt) and [CLDR](https://cldr.unicode.org) annotations, © Unicode, Inc., built by `build-emojis.py` | Unicode-3.0, [`quickshell/emoji-picker/LICENSE.unicode`](quickshell/emoji-picker/LICENSE.unicode) |
| Website music and sound effects | `website/public/audio/` | Alexander Nakarada, NaturesTemper, TRP, Darsycho | CC BY 4.0 and CC0, [`website/public/audio/CREDITS.md`](website/public/audio/CREDITS.md) |

Colour palettes named after their projects (Catppuccin, Gruvbox, Kanagawa, Nord,
One Dark Pro, Rosé Pine) follow those projects' published colours; all of them
are MIT licensed. Themes name the Neovim colorscheme plugins and VS Code themes
they use (`themes/integrations.json`); those download from their authors when
installed and keep their own licenses.

## Packages EITR builds and redistributes

EITR's package repository and ISO include these packages, built from the AUR or
packaged by EITR. Their licenses travel inside each package under
`/usr/share/licenses/`.

| Package | Upstream | License |
|---|---|---|
| walker | https://github.com/abenz1267/walker | GPL-3.0 |
| elephant-bin, elephant-desktopapplications-bin, elephant-menus-bin, elephant-providerlist-bin, elephant-websearch-bin | https://github.com/abenz1267/elephant | GPL-3.0 |
| yay | https://github.com/Jguer/yay | GPL-3.0-or-later |
| bibata-cursor-theme | https://github.com/ful1e5/Bibata_Cursor | GPL-3.0-or-later |
| yaru-icon-theme | https://github.com/ubuntu/yaru | GPL-3.0 and CC BY-SA 4.0 |
| obs-cmd | https://github.com/grigio/obs-cmd | MIT |
| kvantum-theme-catppuccin-git | https://github.com/catppuccin/Kvantum | MIT |
| eitr-cmux-tui-bin | https://cmux.com/tui | GPL-3.0-or-later |

The ISO also contains official Arch Linux packages, unmodified. Each keeps its
own license under `/usr/share/licenses/`.

## Source code

For every GPL-licensed program in EITR's packages or ISO you can get the
corresponding source:

- **Official Arch Linux packages:** build recipes at
  https://gitlab.archlinux.org/archlinux/packaging/packages and source archives
  at https://sources.archlinux.org/, by package name and the version shown by
  `pacman -Q`.
- **Packages listed above:** their upstream repositories at the listed version,
  and the build recipes in the AUR (https://aur.archlinux.org/packages/NAME) or in
  `distro/pkg/` here.
- **EITR itself:** this repository, tagged per release.

If any of these is unavailable, write to contact@eitr.info and you will get the
complete corresponding source for the version you received, for at least three
years after that release.
