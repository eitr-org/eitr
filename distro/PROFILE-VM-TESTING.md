# Organization profiles: maintainer VM verification

These commands have not been run for this change. Run only against throwaway VM
work directories with the candidate ISO containing the working-tree changes.
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

Remaining visual/manual guest checks: profile-only wizard Review (boot with the
stick and without firmware answers); unattended summary/countdown; cancellation
of `eitr profile apply` with a mistyped phrase; all four translated summaries;
Remote Access absent from both bar orientations, menus and search; assistants
switch and update-channel control hidden; group menus hidden; direct tools still
refused. Check defaults at next login and signed HTTPS repository setup. Add a
setup script writing a guest-only marker, apply twice and confirm it ran once;
check failed/interrupted script attempts remain recorded. Check both the
installed-machine and installer paths. No hardware behavior is established by
these VM checks.
