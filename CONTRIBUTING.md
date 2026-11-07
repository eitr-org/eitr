# Contributing to Eitr

Thank you for helping. Eitr is a small project with one maintainer, so focused
contributions that are easy to review land fastest.

## Before you start

- **Bugs:** open an issue with the [problem report](https://github.com/eitr-org/eitr/issues/new?template=problem.md)
  and attach the report from Settings > System > Information > Report a Problem.
- **Security problems:** do not open an issue; see [SECURITY.md](SECURITY.md).
- **Bigger changes or new features:** open an issue first to agree on the idea and
  where it belongs, before writing a lot of code.
- **Themes and plugins:** they live outside this repository. Official ones are in
  `eitr-org/eitr-themes` and `eitr-org/eitr-plugins`; community ones are listed in
  `eitr-org/eitr-community` (see [distro/THEMES.md](distro/THEMES.md) and
  [distro/COMMUNITY.md](distro/COMMUNITY.md)).

## Where things are

| What | Where |
|---|---|
| The bar, panels, Control Center, lockscreen and other desktop surfaces (Quickshell/QML) | `quickshell/` |
| Menus (Walker and its Elephant providers) | `walker/`, `elephant/` |
| Hyprland configuration (Lua) | `hypr/` |
| Installer, packages, system helpers, updates and recovery | `distro/` |
| The EITR Handbook (built into the desktop) | `quickshell/desktop-bar/handbook/` |
| Translations | `i18n/` |
| Website | `website/` |

[AGENTS.md](AGENTS.md) describes the design rules and conventions in detail; it is
written for coding assistants but is the best map for people too.

## Trying a change

On an Eitr desktop, run the bar from your checkout without installing anything:

```sh
eitr-shell desktop-bar kill
eitr-shell --repo "$PWD" desktop-bar --daemonize
```

Logging out and back in returns to the installed bar. Installer, update and
recovery changes are tested in a virtual machine installed from the Eitr ISO; see
[distro/LINUX-VM-TESTING.md](distro/LINUX-VM-TESTING.md).

## Checks

Run every repository check (CI runs the same script):

```sh
bash tools/check.sh
```

`bash tools/check.sh --list` shows the stages, so you can run one while iterating.
The script clears your desktop's XDG folders first, so tests never write into your
real home; prefer it over running test files directly.

## What a good pull request has

- **One focused change**, with a clear title in the style of the history:
  `Area: what changed, in plain words` (for example
  `Media: the cover fills the panel`).
- **Proof it works:** say what you tried and on what. For anything on screen (bar,
  panels, menus, themes, lockscreen, installer), add screenshots or a short clip,
  without private windows, names or network details. Passing tests alone are not
  enough for visible changes.
- **Docs in step:** update the Handbook chapter, README section or menu text that
  describes the change, then run `python3 tools/handbook-build.py` and its `--check`.
- **Translatable text:** wrap new interface text in `Eitr.I18n.tr()` (QML) or `tr()`
  (Python) and run `python3 tools/i18n-build.py` and its `--check`. You do not need
  to translate it yourself.
- **Reuse before you write:** look for an existing component, control or helper and
  extend it rather than adding a second one that does the same thing.
- **Small files:** keep a file to one page, panel, component or helper, ideally under
  400 lines. If a file really needs to be larger, list it in
  `tools/file-size-baseline.json` with its size and a one-line reason;
  `bash tools/check.sh` checks this.
- **Both light and dark themes** keep working, and nothing assumes a particular user
  name, monitor, GPU, locale or disk layout.
- **No secrets** (tokens, keys, passwords, clipboard contents), logs from your
  machine, caches or build output.

## Code and licence

Write your own code. Take ideas from anywhere, but do not paste code from other
projects unless its licence allows it and you credit it in the pull request.
Contributions are published under the [GPL-3.0](LICENSE), like the rest of Eitr.

Be kind and patient in issues and reviews; everyone here is volunteering their time.
