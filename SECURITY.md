# Security

## Reporting a vulnerability

Please report security problems privately, not in a public issue:

- Email **reports@eitr.info** with "Security" in the subject.

Include what is affected (a file, menu, package or the website), how to reproduce it,
and what an attacker could do with it. Leave out real passwords, tokens and keys,
including ones you found: describe them instead. Reports in English or Portuguese are
both fine.

Eitr is maintained by one developer, so replies are not instant. You can expect an
acknowledgement within a week. Please give a reasonable time for a fix before
publishing details; we will agree on a date together and credit you in the release
notes unless you prefer otherwise.

## What is in scope

- The Eitr desktop (`eitr-desktop`): the bar, menus, helpers, privileged
  `eitr-system` actions, updates, snapshots and recovery.
- The installer and the ISO.
- The package repository at download.eitr.info and how updates are signed and verified.
- The plugin and theme catalogs, including how plugins are reviewed and blocked.
- The website eitr.info.

Upstream software (Arch Linux packages, Hyprland, Quickshell, browsers and other
applications) should be reported to its own project; tell us too if Eitr's
configuration makes it worse.

A plugin that steals data or damages systems is reported with the
[plugin report form](https://github.com/eitr-org/eitr/issues/new?template=malicious-plugin.yml),
so it can be added to the blocklist quickly.

## Supported versions

Security fixes go to the latest release on the stable update channel (and the
testing channel). Older releases are fixed by updating: run System Update.
