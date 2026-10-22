# Organization profiles

Use the official ISO unchanged. On a FAT32 stick labelled `EITR-ANSWERS`, put
`eitr-profile.json` beside or instead of `eitr-answers.json`. With only a profile,
the normal wizard includes its changes in Review. With both files, the installer
lists the disk operation and every profile change before its 15-second countdown;
Ctrl+C cancels before disk changes. Keep the stick connected until power-off.

A complete example (replace all example digests with the actual lowercase SHA-256
from `sha256sum`; copy these files onto the stick):

```json
{
  "version": 1,
  "name": "Example office",
  "remove": ["steam", "moonlight-qt", "eitr-sunshine", "tailscale"],
  "add": {
    "recipes": ["productivity/libreoffice"],
    "packages": ["chromium"],
    "flathub": ["us.zoom.Zoom"],
    "files": [{"file": "packages/office-tools-1-1-any.pkg.tar.zst", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
  },
  "defaults": {
    "theme": "norse",
    "wallpaper": {"file": "office.png", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
    "browser": "chromium",
    "update_channel": "stable",
    "repository": {
      "name": "office",
      "server": "https://packages.example.org/$arch",
      "key": {"file": "office-key.asc", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
    }
  },
  "setup": {"file": "setup.sh", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
  "policies": {"remote_access": false, "assistants_together": false, "update_channel": "stable", "gaming": false}
}
```

Only `version` and `name` are required. Unknown and duplicate JSON keys are errors.
Remove optional sections you do not need. Paths are relative to the stick, with
no symlinks, parent traversal (`..`) or absolute paths. All referenced files must exist
and match their checksum before the installer changes any disk. Wallpaper files
must decode as PNG, JPEG or WebP. The repository key must contain exactly one
OpenPGP public key; the HTTPS server cannot contain credentials. Its key is added
and locally trusted in pacman's keyring; only use an organization key you trust.
Package archives and setup scripts are trusted administrator code, not sandboxed.

`remove` accepts only the reviewed `distro/removable-apps.json` allowlist. The
entry-by-entry review is in `distro/PROFILE-PACKAGE-REVIEW.md`. Protected or unknown
packages refuse the whole profile. pacman checks dependencies; removal never
uses recursive removal or dependency overrides. Group policies exclude every
allowlisted package in that group: `gaming`, `media`, `development`, `sharing`,
and `remote_access`. `true` permits a feature; `false` disables it. The `update_channel`
policy accepts only `"stable"`. Omitted policies are unrestricted.

Recipes use `group/name` from `distro/software.json`. Only prebuilt pacman and
Flatpak recipes are accepted. AUR and interactive managed/webapp recipes are
refused; provide reviewed prebuilt package files instead. Repository packages,
recipes and Flathub additions require internet. Stick packages install offline
when their dependencies are already on the ISO or also supplied on the stick.
Package names must be available in pacman's current sync databases when checked;
refresh them through the normal update workflow before checking online additions.
No AUR builds run during installation. Online pacman additions use a full upgrade,
never a partial upgrade. Extra repositories are configured for future updates;
packages available only there should be supplied as stick files for installation.

Browser defaults support Firefox and Chromium. Chromium must also be added.
Theme and wallpaper defaults are saved for the selected desktop user's next login;
profile application does not restart their desktop. The extra repository and
update channel are system-wide. `setup` runs as root with the staged stick directory
as its working directory, after the profile is recorded. A SHA-256 marker records
its attempt before starting, so a failed or interrupted script is not rerun
silently. Change the script (and its digest) to authorize another attempt. Script
output and failures remain visible; a failed installation does not roll back
completed package transactions.

On an installed machine:

```sh
eitr profile check /run/media/alex/EITR-ANSWERS
eitr profile apply /run/media/alex/EITR-ANSWERS
```

`check` reads files and package metadata and uses temporary validation directories;
it changes no system configuration. `apply` uses the explicit root-owned
`eitr-system profile-apply` action, privately stages and rechecks the stick, shows
the same summary, then requires typing `APPLY PROFILE`. Cancellation changes
nothing. It removes installed excluded packages through pacman, installs additions,
saves defaults, writes root-owned `/etc/eitr/policies.json` (0644, root:root), and
records `/etc/eitr/profile.json`. Applying another profile replaces the recorded
choices; it does not automatically reinstall previously removed apps or reset
omitted preferences. The setup marker remains across profile replacements.

The recorded exclusions filter manual installer manifests. An `IgnorePkg` include
in pacman's options also prevents System Update from pulling excluded packages
back as dependencies; such a dependency conflict must stop the upgrade. Seeding
user settings installs no applications. Policies hide Elephant menu/search rows,
Remote Access bar entries, the assistants-together switch and channel controls;
Eitr's tools also refuse these actions directly. Existing sessions may need their
next menu/panel refresh to reflect a newly applied policy.

**This is not a lockdown against a user with root.** Root can edit the policy or
run other tools. Real lockdown also means not granting root. Policies govern Eitr
workflows, not arbitrary third-party software or fleet management.

VM verification is pending. See `distro/PROFILE-VM-TESTING.md` for exact commands.
