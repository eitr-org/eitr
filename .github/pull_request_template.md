## What changes

<!-- What a user notices, in a sentence or two. Link the issue it fixes, if any. -->

## Why

<!-- The problem it solves or the idea behind it. -->

## How it was tested

<!-- Tests alone are not enough for anything you can see or use: say what you ran
     and on what (real hardware or a VM, which GPU/monitor if it matters). -->

- [ ] `bash tools/check.sh` passes
- [ ] Tried on a running Eitr desktop (or a VM installed from the Eitr ISO)

## Screenshots or a short clip

<!-- Required when the change touches the bar, panels, menus, themes, the lockscreen,
     the installer or anything else on screen. Leave out private windows, names and
     network details. Write "No visible change" otherwise. -->

## Checklist

- [ ] The Handbook, README or menu text that describes this is updated, and
      `python3 tools/handbook-build.py --check` passes
- [ ] New interface text goes through `Eitr.I18n.tr`/`tr()` and `python3 tools/i18n-build.py --check` passes
- [ ] No secrets, personal paths, logs from your machine or generated files that do not belong in the repository
- [ ] The code is my own work or properly credited, and can be published under GPL-3.0
