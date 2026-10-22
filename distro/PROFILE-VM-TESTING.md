# Organization profiles: maintainer VM verification

Results are recorded in `distro/LINUX-VM-TESTING.md`. Run only against throwaway
VM work directories with a candidate ISO built from the commit under test.
Required host tools: existing QEMU/OVMF setup, dosfstools and mtools. Nothing here
requires mounting a filesystem or running the host commands as root. The harness
uses sudo only inside its throwaway guest.

Set the candidate ISO and a new scratch directory:

```sh
export EITR_PROFILE_ISO=/absolute/path/to/candidate.iso
export EITR_PROFILE_VM=/absolute/path/to/new-profile-tests
mkdir -p "$EITR_PROFILE_VM/offline-stick/packages" "$EITR_PROFILE_VM/online-stick" "$EITR_PROFILE_VM/refused-stick"
```

Copy a reviewed, compatible Arch package to
`$EITR_PROFILE_VM/offline-stick/packages/office-tools-1-1-any.pkg.tar.zst`.
It must have no dependencies beyond the ISO's installed set (or include every
extra dependency as another entry in add.files). It must not replace a desktop
component. Then generate the three profiles:

```sh
python3 - <<'PY'
import hashlib, json, os
from pathlib import Path
root = Path(os.environ['EITR_PROFILE_VM'])
package = root/'offline-stick/packages/office-tools-1-1-any.pkg.tar.zst'
profile = {'version': 1, 'name': 'Offline office',
           'remove': ['steam', 'moonlight-qt', 'eitr-sunshine', 'tailscale'],
           'add': {'files': [{'file': 'packages/' + package.name,
                              'sha256': hashlib.sha256(package.read_bytes()).hexdigest()}]},
           'policies': {'remote_access': False, 'assistants_together': False,
                        'update_channel': 'stable', 'gaming': False}}
(root/'offline-stick/eitr-profile.json').write_text(json.dumps(profile))
(root/'online-stick/eitr-profile.json').write_text(json.dumps({
    'version': 1, 'name': 'Online office', 'remove': ['steam'],
    'add': {'flathub': ['us.zoom.Zoom']}, 'policies': {'remote_access': False}}))
(root/'refused-stick/eitr-profile.json').write_text(json.dumps({
    'version': 1, 'name': 'Refused', 'remove': ['hyprland']}))
PY
python3 distro/vm-tests/eitr-vm-test stick --source "$EITR_PROFILE_VM/offline-stick" --output "$EITR_PROFILE_VM/offline.img"
python3 distro/vm-tests/eitr-vm-test stick --source "$EITR_PROFILE_VM/online-stick" --output "$EITR_PROFILE_VM/online.img"
python3 distro/vm-tests/eitr-vm-test stick --source "$EITR_PROFILE_VM/refused-stick" --output "$EITR_PROFILE_VM/refused.img"
python3 distro/vm-tests/eitr-vm-test install --iso "$EITR_PROFILE_ISO" --work "$EITR_PROFILE_VM/offline" --stick "$EITR_PROFILE_VM/offline.img"
python3 distro/vm-tests/eitr-vm-test verify --work "$EITR_PROFILE_VM/offline"
python3 distro/vm-tests/eitr-vm-test update --work "$EITR_PROFILE_VM/offline"
python3 distro/vm-tests/eitr-vm-test install --iso "$EITR_PROFILE_ISO" --work "$EITR_PROFILE_VM/online" --stick "$EITR_PROFILE_VM/online.img" --online
python3 distro/vm-tests/eitr-vm-test verify --work "$EITR_PROFILE_VM/online"
python3 distro/vm-tests/eitr-vm-test install --iso "$EITR_PROFILE_ISO" --work "$EITR_PROFILE_VM/refused" --stick "$EITR_PROFILE_VM/refused.img" --expect-refusal
python3 distro/vm-tests/eitr-vm-test install --iso "$EITR_PROFILE_ISO" --work "$EITR_PROFILE_VM/apply"
python3 distro/vm-tests/eitr-vm-test profile-apply --work "$EITR_PROFILE_VM/apply" --stick "$EITR_PROFILE_VM/offline.img"
python3 distro/vm-tests/eitr-vm-test verify --work "$EITR_PROFILE_VM/apply"
```

`install` defaults to no network device. `--online` adds a network device only
for that install. `--stick` attaches a read-only virtio raw image, copies the
expected profile with mtools, and leaves QEMU firmware answers on the first disk
(`/dev/vda`). `--expect-refusal` checks the serial error, stops the VM and compares
the target with an empty disk. It must not report a successful install.

`verify` and the verification after `update` assert the exact recorded profile,
root:root 0644 policies, excluded packages absent, requested Flathub apps present,
and direct Remote Access refusal plus menu-data filtering. Inspect the installed
stick package with `pacman -Q office-tools` in the guest as well. Test refusal
with an unknown package, missing file, wrong checksum, unknown recipe and unsafe
path by changing the refused profile and creating a new image/work directory for
each case. A dependency conflict must fail through pacman, never remove the
protected dependent or silently reinstall the excluded app.

Manual guest checks (passed on 2026-10-22; `distro/LINUX-VM-TESTING.md` has the
record and how to type, click and capture in the VM):

- Wizard and countdown: boot the ISO without firmware answers. A stick with only
  the profile opens the wizard on tty1; go through to Review. On tty2 (log in as
  root) run `LANG=de_DE.UTF-8 eitr-guided-install --profile /run/eitr-answers`
  for each language, and `--answers FILE --profile /run/eitr-answers` with a small
  answers file for the countdown; Ctrl+C cancels it. A stick with
  `eitr-answers.json` too installs unattended from tty1 after the countdown.
- Policies on screen: log in, open the right icon group, move the bar to the left
  (`eitr-shell desktop-bar ipc call bar update edge left`), open the Control
  Center's Updates and Walker's Connectivity, Update and AI menus, and search for
  remote, tailscale, moonlight, sharing, assistants, together and channel. Moving
  `policies.json` aside and restarting Elephant shows what the policies hid.
- `eitr profile apply` with defaults: a mistyped phrase first, then the real one
  three times; log in again and check theme, wallpaper and browser. For the
  repository, serve a signed database over HTTPS with a test CA the guest trusts
  (`trust anchor`), then `pacman -Sy` and install from it. A setup script that
  fails keeps its `started` marker and is not run again.
- A test repository whose `eitr-desktop` depends on an excluded app makes
  `eitr profile apply` refuse the profile (protected dependency); remove it first.

The host needs dosfstools and mtools for `stick`; without them, build the stick
images in the builder VM. No hardware behavior is established by these VM checks.
