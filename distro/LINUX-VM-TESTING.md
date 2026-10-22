# Linux VM testing

This is a temporary testing guide, not a release certification. Remove it once
the installation and release tests have a permanent home.

## Isolated test machine

Install the host tools:

```sh
sudo pacman -Syu --needed qemu-desktop virt-manager libvirt edk2-ovmf dnsmasq
sudo systemctl enable --now libvirtd.service
```

Use Virt Manager with a user session when system libvirt access is unavailable:

```sh
virt-manager --connect qemu:///session
```

Create an x86_64 KVM guest with UEFI, 4 CPUs, 8 GiB RAM, an 80 GiB QCOW2 disk,
VirtIO graphics and NAT networking. Attach a checksum-verified Arch ISO. Never
attach the host's physical disks or share its configuration/account folders.
Install minimal Arch with a Btrfs root (`@`) and home (`@home`), an EFI partition,
a normal user and sudo. Follow [the installation recipe](README.md#install-on-a-new-machine).
Preserve a powered-off disk and UEFI-variable baseline before running Eitr.

The current local test domain is `eitr-test` on `qemu:///session`. Its artifacts
and private test credentials remain outside this repository. Use
`virsh -c qemu:///session start eitr-test` to start it. Closing its QEMU display
can terminate the guest; shut down from inside the guest instead.

### Graphics troubleshooting

Plain VirtIO 2D can boot Hyprland, but is insufficient for the tested Hyprpaper
buffer allocation. Use VirtIO 3D for desktop tests. On this NVIDIA host, the SPICE
viewer remained black even when guest screenshots showed a working desktop.
An SDL OpenGL display worked with VM-scoped QEMU environment settings
`__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json` and
`GBM_BACKEND=nvidia-drm`. These are host-specific test settings, not Eitr defaults.
The SDL test domain does not use SPICE channels or host audio.

For a fixed guest resolution, use a guest-only `~/.config/hypr/local.lua`:

```lua
hl.monitor({ output = "Virtual-1", mode = "1920x1080@60", position = "auto", scale = 1 })
```

Verify the actual output name/modes first with `hyprctl monitors -j`.

## Offline ISO installation test

Build the ISO as described in [the build instructions](README.md#build-installer-iso)
on the builder VM, copy it to the host and compare its SHA-256. Install into a
new domain and disk, never an existing test VM, defined **without any network
interface** so the run proves the offline payload:

```sh
qemu-img create -f qcow2 eitr-offline.qcow2 80G
virsh -c qemu:///session define eitr-offline.xml   # q35, OVMF, VirtIO 3D, no <interface>
virsh -c qemu:///session start eitr-offline
```

With an `egl-headless` plus VNC display, `virsh screenshot` fails once the 3D
scanout is active; capture with `gvnccapture 127.0.0.1:<display>` instead. After
the installer powers off, eject the ISO (`virsh change-media <domain> sda
--eject --config`) before starting the domain again.

## Automated VM tests

`distro/vm-tests/eitr-vm-test` runs the same tests without a person at the
keyboard. It starts plain QEMU (no libvirt domain), keeps the disk, firmware
variables, generated SSH key, random password, serial logs and screenshots in
the work directory it is given, and never touches an existing VM:

```sh
RUN=~/eitr-runs/$(date +%F-%H%M)
distro/vm-tests/eitr-vm-test install --iso eitr-*.iso --work "$RUN"   # no network device
distro/vm-tests/eitr-vm-test verify --work "$RUN"                     # host-only network
distro/vm-tests/eitr-vm-test update --work "$RUN"                     # System Update online
distro/vm-tests/eitr-vm-test reset --work "$RUN" --mode keep-files    # or everything
distro/vm-tests/eitr-vm-test boot-guard --work "$RUN"                 # after an update
```

- **install** passes the answers through QEMU's firmware config: the ISO's
  login sees them and runs `eitr-guided-install --answers` instead of the
  wizard (erase install on `/dev/vda`, user `tester`, the run's SSH key). The
  installer logs to the serial port and powers off when done. With
  `--encrypted` it installs on LUKS2 with a random passphrase saved as
  `passphrase` in the run folder; every later boot and restart types it at
  the unlock prompt through QEMU's monitor.
- **verify** boots the disk with a network that reaches only the host and
  checks over SSH: a running system with no failed units, SDDM up, the Eitr
  packages, the install log, online-only package sources and the Hyprland
  session. It saves `login.png` from the VM's screen.
- **update** runs Walker's System Update script with pacman's default answers,
  then verifies. When packages were upgraded it requires a pre/post snapshot
  pair; on an image that is already current it requires that no upgrade
  snapshot was taken. To exercise a real upgrade, install the previous ISO (or
  publish a newer `eitr-desktop` than the ISO's payload) first.
- **reset** adds a file, a hidden setting, a system file, an account and a new
  password, answers Walker's Factory Reset warnings (first with a mistyped
  phrase, which must change nothing), waits for the restart, checks what the
  mode keeps and removes, and verifies. Both modes can run one after the other
  on the same disk: the restore point stays.

- **boot-guard** (on a disk that went through `update`) runs a second update,
  then masks the login screen so starts fail. It checks that two failed starts
  are counted, that the third restores the update's before snapshot and restarts
  by itself, and that the restored system is healthy, disarmed, rid of the failed
  copy and ready to tell the next login.

CI cannot run these (no KVM on GitHub's runners); run them before tagging a
release.

The harness boots with plain VirtIO 2D graphics, where Hyprpaper crashes and the
desktop shows no wallpaper. To check a wallpaper, boot the disk with
`-device virtio-vga-gl -display egl-headless -vnc 127.0.0.1:77` instead (with the
NVIDIA settings from Graphics troubleshooting) and capture with
`gvnccapture 127.0.0.1:77 out.png`. Type at the login screen and consoles with
QMP `send-key`; `input-send-event` clicks where Hyprland's
`hl.dsp.cursor.move({ x = X, y = Y })` dispatcher put the pointer.

To test a real upgrade without publishing, rebuild `eitr-desktop` with a higher
`pkgrel`, sign it and a repository database with a throwaway GPG key, serve them
on the host's loopback (QEMU's user network reaches it as `10.0.2.2`), and in the
guest `pacman-key --add` and `--lsign-key` that key and add the repository above
`[core]` in `pacman.conf`. Then run `update`. Stop the server and throw the disk
away afterwards.

## Verification record

October 15, 2026, with `eitr-vm-test` (4 CPUs, 8 GiB, 80 GiB VirtIO disk):

- ISO from `9a2923b`: offline install in 100 s. Verification found
  `systemd-networkd-wait-online` failing after its two-minute timeout on a
  wired-only machine; fixed in `cbd763e`. System Update then upgraded
  `eitr-desktop` from the ISO's build to the published `cbd763e` build, with a
  pre/post snapshot pair, and the next boot passed every check.
- The 0.3.0 ISO: offline install in 100 s; all checks passed on first boot.
  Keep My Files and then Erase Everything on the same disk: a mistyped phrase
  changed nothing, each mode kept and removed what it promises, the password
  changed after installation still worked, the previous system was deleted and
  no unit failed. The login screen showed the Clockwork Tape design.
- Releases 0.3.0 to 0.6.3 (their commits are in the pre-squash history kept
  offline). 0.3.0 to 0.4.0 and 0.4.0 to 0.5.0 upgraded through System Update from
  a fresh install of the previous ISO; the 0.4.0 and 0.5.0 ISOs each installed
  offline in about 100 s, 0.6.0 in about 140 s, and 0.6.1 to 0.6.3 in 127 to
  135 s; each passed verification, both factory resets and a System Update.

October 13, 2026: Eitr-built offline ISOs (UEFI, 4 CPUs, 8 GiB, 80 GiB VirtIO
disk, no network device):

- The ISO boots the Eitr splash and the wizard; the review screen, typed disk
  confirmation and one progress screen work without network access.
- An unencrypted installation ran unattended after the wizard: archinstall, the
  desktop and hardware packages, user seeding, theme generation, login design,
  snapshots, splash and online sources, in about three minutes on this host.
- A LUKS2 installation shows the Eitr splash passphrase prompt with masked
  input, unlocks, and continues with the progress splash. After the installer
  powers off and the ISO is removed, the next boot reaches the login.
- First boot reaches the Clockwork Tape SDDM login with the Hyprland UWSM session
  preselected; login starts Hyprland with the bar, Afterglow wallpaper, Welcome
  panel, Walker apps and Kitty with Zsh/Powerlevel10k. No system or user units
  failed. pacman uses the online mirrors and no payload repository remains.

Later the same day, with the ISO that adds install types and factory reset:

- The wizard's boxes render with square corners on the live console font.
- Unencrypted erase install on an empty 80 GiB disk: 129 s from the typed
  confirmation to the finish screen (base 49 s, desktop 71 s, user setup 7 s,
  boot menu 2 s, restore point 0.5 s). The finish screen shows the total and
  `/var/log/eitr-install.log` keeps the step times.
- Install alongside, LUKS2, on a 120 GiB GPT disk shaped like Windows after
  shrinking C: (100 MiB ESP with a stand-in `bootmgfw.efi`, MSR, 40 GiB NTFS,
  recovery partition, 79 GiB free): 188 s (base 108 s with LUKS). The ESP,
  NTFS and recovery partitions kept identical SHA-256 hashes through the
  install and two resets. Limine lists Eitr and Windows; the Windows entry
  chainloads the loader on the Windows ESP. Eitr's firmware entry boots first.
- Factory reset from Walker on both systems: Keep My Files kept home folder
  files, moved hidden settings into "Settings before reset <date>", removed a
  later account (its home folder stayed), a system file and Snapper's
  snapshots; Erase Everything returned the home folders and accounts to the
  first login. The current password was kept, the finish service deleted
  the previous system and disabled itself, and no system or user unit failed.
  Declining the first warning or mistyping the phrase changed nothing.

October 21, 2026, with the rebuilt 0.6.4 ISO and `install --encrypted` (LUKS2
erase install, passphrase typed through QEMU's monitor at every start): verify
and System Update passed; the boot guard counted two failed starts and its
third start restored the update's before snapshot, brought the login back,
told the next login and deleted the failed system; Keep My Files and Erase
Everything each passed all checks and came back through the unlock prompt.

October 22, 2026, organization profiles (`distro/PROFILE-VM-TESTING.md`) with an
ISO built from the commit under test: an offline install from a stick labelled
EITRANSWERS removed Steam, the remote-access and gaming apps, installed a
checksummed package from the stick and wrote root-owned policies; a profile
removing Hyprland was refused before the disk changed; `eitr profile apply` brought
an installed machine to the same state; an online install queued Zoom from Flathub
and the first-boot timer installed it; System Update (nothing to upgrade) kept
the profile. The runs found and fixed: stick packages refused by a wrong pacman
option, the 12-character FAT label, and Flatpak extra data failing in the chroot.

Later on October 22, the remaining profile checks, with an ISO built from
`fe9ae8a` and then from the fix below. An unattended install from a stick holding
both answers and a profile applied it. A real System Update upgraded pipewire,
hyprutils and a locally served `eitr-desktop` build (pre/post snapshot pair);
the excluded apps stayed absent, and an `eitr-desktop` that newly depended on
`tailscale` stopped the upgrade at pacman's IgnorePkg question instead of
installing it. With the policies on, the bar (top and left) had no Tailscale or
Streaming icons, the Control Center no channel Change button, and Walker's menus
and search no Remote Access, update-channel or "Let assistants work together"
rows; removing `policies.json` brought them back. `eitr profile apply`: a mistyped
phrase changed nothing; Norse, the profile wallpaper and Firefox were in place
after the next login; the extra repository installed a package signed by its key
over HTTPS; the setup script ran once in three applies, and a failing one kept
its marker and was not rerun. The wizard Review and the countdown (Ctrl+C
cancelled it) were shown in all five languages by running the installer with
`LANG` on tty2. Fixed: the Review and countdown mixed English lines into
translated screens, the summary promised first-start Flathub installs for every
profile and printed `False`, and a skipped unfinished setup script said nothing.
Still open: the live console font lacks ã, õ, Á and Ó.

Earlier record:


The October 12, 2026 run installed Eitr on minimal Arch; it did **not** boot an
Eitr-built installer ISO or exercise guided disk partitioning.

Verified:

- Official and AUR manifests install, including Yay, Walker and Elephant.
- The desktop package builds, seeds missing defaults, and enables the intended services.
- Installer preflight accepts the completed installation without overwriting it.
- SDDM password login starts the Hyprland UWSM session.
- Elephant and Walker's background service start at login.
- Wallpaper rendering, Jade/Daylight application and theme style generation.
- Apps and global search launch Kitty; uninstall is shown only inside Apps.
- Control Center and calendar rendering; unavailable VM radios are disabled.
- A notification stays above the Idle panel and dismisses without locking.
- System Update creates paired pre/post snapshots and a boot archive. The test
  had no available upgrades; GRUB generated snapshot entries.
- The full repository check suite passes.

Still required before release:

- Guided ISO installation on real AMD, Intel and NVIDIA hardware and USB media;
  the offline VM runs above used VirtIO graphics only.
- Recovery boot and rollback on real hardware, including a failed update.
- Custom SDDM designs, lock/unlock, capture, and optional runtime installers.
- Real WiFi/Bluetooth, battery/power profiles, fingerprint/FIDO2, TPM/LUKS,
  Secure Boot, native GPU performance, and gaming/account workflows.

The official GeForce NOW Flatpak installed, but its requested Freedesktop 24.08
runtime reported end-of-life. Installation success does not certify that upstream
runtime's security status or cloud-gaming compatibility.
