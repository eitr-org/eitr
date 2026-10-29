# EITR package repository

Installed systems receive EITR updates from a signed pacman repository, `[eitr]`,
hosted on Cloudflare R2 (bucket `eitr-downloads`, folder `repo/`) and served at
`download.eitr.info`:

```ini
[eitr]
SigLevel = Required
Server = https://download.eitr.info/repo
```

It holds `eitr-desktop`, the reviewed local packages (`distro/pkg`) and prebuilt
AUR packages from the offline payload, so users do not compile AUR packages.
Packages whose licenses forbid redistribution (`distro/redistribution.json`:
VS Code, 1Password, Chrome, Postman, Slack) are left out; users build those from
the AUR on their own machine. R2's free tier covers 10 GB of storage with no
charge for downloads; the bucket also holds the one public ISO, so together they
stay under that (packages are under 1 GB, twice that while a previous publish is
kept). Package files are cached at the edge for a year (their names carry the
version); the databases are never cached, so a new publish is visible at once.

## Signing key (once, by the owner)

Create a dedicated key on a trusted machine and keep the private key offline,
with a revocation certificate and a backup:

```sh
gpg --quick-gen-key "EITR Package Signing <batista.erick@outlook.com>" ed25519 sign 3y
gpg --list-keys --with-colons "EITR Package Signing" | awk -F: '/^fpr/{print $10; exit}' > distro/keys/eitr.fingerprint
gpg --armor --export "$(cat distro/keys/eitr.fingerprint)" > distro/keys/eitr.asc
gpg --output eitr-revocation.asc --gen-revoke "$(cat distro/keys/eitr.fingerprint)"
```

Commit only `eitr.asc` and `eitr.fingerprint`. Once they exist, the payload
builds `eitr-keyring` (`distro/pkg/eitr-keyring`), which installs the key for
pacman, and the guided installer adds the `[eitr]` section to new systems. Before
the key expires, extend it (`gpg --quick-set-expire`), re-export `eitr.asc` and
publish a new `eitr-keyring`. If the key is lost or compromised, publish a
keyring that revokes it and a new key, signed packages with the new key, and
announce it.

## Publishing

Day to day, after pushing a change, one command rebuilds `eitr-desktop` from
HEAD and publishes it (a developer tool in this repository; the package does not
ship it):

```sh
distro/repo/release-desktop.py            # or --dry-run DIRECTORY to only sign locally
```

It refuses uncommitted or unpushed work, rebuilds `eitr-artwork` only when
HEAD's artwork version is not published yet, reuses the other published packages
after verifying their signatures (cached in `~/.cache/eitr/release-packages`),
uploads only packages whose content changed, asks once for the signing key
passphrase, and checks that the published database lists the new version.
Repository package filenames must be plain package basenames. Reuse requires
GPG to succeed and report the exact configured signing fingerprint; malformed
repository archives are refused.
The release tool also verifies the database signature before reading its package
list or confirming a publication.
Uploads go through the `eitr-r2` AWS CLI profile with R2's endpoint on every
command; the endpoint comes from `EITR_R2_ENDPOINT`, else `npx wrangler whoami`
in `website/`. Packages go up before the database that lists them, and the
previous publish's packages stay until the next publish, so a machine that read
the old database a moment earlier still finds its files.

### Update channels

Machines on the **testing** channel list a second signed repository,
`[eitr-testing]` (folder `repo-testing/`), before `[eitr]`, so they install new
Eitr builds first. It holds only Eitr's own new packages; everything else still
comes from `[eitr]` and Arch. A build goes to testing, the owner (and anyone else
on testing) lives with it, then it is promoted unchanged:

```sh
distro/repo/release-desktop.py --channel testing   # build HEAD, publish to testing only
distro/repo/release-desktop.py --promote           # testing's packages to stable, not rebuilt
```

A plain stable release also publishes its `eitr-desktop` build to testing, so the
testing repository always exists and is never behind stable. The artwork is not
copied there: testing machines take the identical `eitr-artwork` from `[eitr]`.

Users switch with System > Maintenance > Update > Update Channel or
`eitr channel testing|stable`; `eitr-system channel-set` adds or removes the
marked `[eitr-testing]` block in `/etc/pacman.conf`, and refuses to add it while
the testing repository cannot be downloaded.

New AUR package versions come from a full payload build instead:

```sh
distro/payload/build-payload.py --work /abs/payload-work --output /abs/payload
EITR_R2_ENDPOINT=https://<account>.r2.cloudflarestorage.com \
  distro/repo/publish.py --payload /abs/payload --key "$(cat distro/keys/eitr.fingerprint)"
```

`publish.py --dry-run DIRECTORY` signs into a local directory without uploading. It
signs every package and the database, uploads packages before the database that
refers to them, and removes files neither the new nor the previous database
lists. Package file names drop the epoch's `:`, which URLs would need escaped
(`1:0.3.0…` becomes `1.0.3.0…`), renamed before `repo-add`.

## Existing installations

Install `eitr-keyring` once, then add the section above to `/etc/pacman.conf`
after the Arch repositories. System Update then upgrades EITR with the rest of
the system.

## Verification

Tested by signing a payload with a throwaway key into a local directory and
pointing pacman at it with `SigLevel = Required`: the database and packages
verified, a tampered package was refused, and the personal-only packages were
absent. The first release (0.3.0 Ymir, 20 packages) was published on 2026-10-14;
its database and packages verify against `distro/keys/eitr.asc`.
