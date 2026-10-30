# Temporary Apple Silicon VM testing guide

<!-- TEMPORARY: Remove this guide and its README links once the installation,
desktop, ISO, and hardware validation below is complete. Move any still-useful
supported installation instructions into distro/README.md before removal. -->

This is a temporary testing document, not a release installation guarantee.
Remove it once Eitr's installation and release testing is complete; preserve
supported instructions in the main installation guide first.

## What we are testing

Eitr currently targets **x86_64**, including its package lists and ISO recipe.
An M-series MacBook Pro (including M5) uses Apple Silicon. To test the current
project without an ARM port, use **x86_64 emulation**, not an ARM Linux VM.
UTM supports this, but it is slower than native ARM virtualization:
[UTM architecture support](https://mac.getutm.app/).

The first test uses the official Arch ISO, installs a minimal Arch system, then
runs Eitr's existing desktop installer. No custom graphical installer is required
for this test. The Eitr ISO from download.eitr.info has its own guided, offline
install and is tested on x86_64 Linux VMs (`LINUX-VM-TESTING.md`); this guide
covers installing onto an existing Arch system on a Mac.

## 1. Prepare the Mac and VM

1. Confirm the chip in macOS **About This Mac**. These instructions assume an
   M-series Mac, not an Intel Mac.
2. Install [UTM](https://mac.getutm.app/) and download the official **x86_64**
   ISO from [Arch Linux Downloads](https://archlinux.org/download/). Follow that
   page's verification instructions before using the image.
3. Create a VM using **Emulate**, Linux, and **x86_64** architecture. Attach the
   Arch ISO as the installation medium. Use UEFI boot.
4. Suggested starting allocation, not validated minimum requirements: 4 virtual
   CPUs, 8 GiB RAM if the Mac can spare it, and an 80 GiB virtual disk. Leave
   enough RAM and free disk space for macOS; AUR builds can be expensive.
5. Use shared/NAT networking and a virtual Ethernet adapter. Do not attach physical
   disks, pass through USB storage, or share personal/work folders for this test.
6. For the display, choose a VirtIO device labeled **GPU Supported** if available
   in the installed UTM version. Start with a modest resolution such as 1920×1080
   and Retina mode off. Device names/UI may vary by UTM version.

UTM's Linux VirGL/OpenGL acceleration is **experimental**; some applications can
crash or freeze. An emulated VM is useful for installation checks, but is not a
reliable benchmark for Hyprland blur, animations, screen capture, or gaming:
[UTM display settings](https://docs.getutm.app/settings-qemu/devices/display/).
If accelerated VirtIO graphics are unavailable, record that limitation rather
than assuming the desktop will work correctly with a basic VGA display.

## 2. Install a clean Arch guest

Boot the ISO and run `archinstall` inside the VM. Follow the current
[guided installer documentation](https://archinstall.archlinux.page/installing/guided.html);
menu wording can change between Arch ISO versions.

Choose a minimal installation, **not** a preconfigured Hyprland/GNOME/KDE desktop:

- Partition only the new VM's virtual disk. Check its size before accepting any
  erase/partition action. Never select a host or passed-through disk.
  Choose Btrfs root; `/usr`, `/etc` and `/var/lib/pacman` must remain within the
  root subvolume for Eitr's snapshot-protected upgrades.
- Create a normal user with a password and sudo access. Select your own locale,
  keyboard, timezone, and a UEFI-compatible bootloader.
- Include `git`, `sudo`, `base-devel`, and `python`. Eitr installs the desktop afterward.
- Enable the `multilib` repository, needed by the current Steam/lib32 defaults.
- Configure working virtual Ethernet using systemd-networkd and systemd-resolved.
  Do not enable NetworkManager: Eitr's preflight rejects it. Verify networking
  after booting the installed guest, not just in the live ISO.

Reboot into the installed system, eject the ISO, and log in as the normal user.
Save a powered-off copy/backup of this clean VM before Eitr setup so failures
can be reproduced from a fresh target.

## 3. Run Eitr's setup inside the guest

All commands in this section are for the **Arch VM**, not macOS or an existing
desktop. Read [the main installation guide](README.md) and package manifests.

```sh
uname -m
sudo -v
sudo pacman -Syu --needed git base-devel python
git clone https://github.com/eitr-org/eitr.git
cd eitr
git rev-parse HEAD
bash distro/install.sh --check
```

`uname -m` must report `x86_64`. Record the commit hash for your test report.
Preflight checks existing config paths, multilib availability, NetworkManager,
and detected graphics. It does not prove that every package or SDK can install.

If multilib is missing, edit `/etc/pacman.conf` with `sudo`: uncomment both
`[multilib]` and its `Include = /etc/pacman.d/mirrorlist` line, then run
`sudo pacman -Syu` and repeat preflight. If another check fails, stop and record
the message; do not delete existing configs or bypass the check.

Only after successful preflight:

```sh
bash distro/install.sh
```

Run this as the normal user, **not** `sudo bash`. The script uses sudo where
needed. Keep the VM online; official/AUR packages and SDKs are downloaded, not
bundled. Expect slow AUR builds under emulation. The current default package
set is substantial, including Steam and development tools.

Setup includes Yay, Lazygit/Lazydocker, Steam, GeForce NOW and snapshot protection.
Development runtimes and AI CLIs are optional Walker menu selections, not defaults.
Credentials are not copied. Report upstream download/package failures.

On failure, capture the first error and stage. Do not blindly rerun: finished steps are
skipped on a rerun, but copied configs can make preflight
reject a partially installed target. Keep the failed VM for diagnosis and use
the clean backup for a new attempt.

After success, review networking/DNS as described in the main guide, then reboot
the **guest**. SDDM should start; select Hyprland if necessary and log in. Apply a
theme from Walker once to generate application styles. No AI/app login is required
for the basic desktop test.

## 4. Test and record results

- [ ] Arch guest boots without the ISO; virtual Ethernet and DNS work.
- [ ] Preflight, package installs, AUR builds, and development setup finish.
- [ ] Reboot reaches SDDM; Hyprland login succeeds at a usable resolution.
- [ ] Quickshell, Walker, terminal, theme selection, and Settings > System > About work.
- [ ] Theme Color/Blur, light/dark themes, and all four bar edges render correctly.
- [ ] Panels open/close, resize, remain padded, and do not overlap incorrectly.
- [ ] Notifications appear above panels; dismissing one does not activate a
      control underneath. Use a harmless panel first, not a lock/power control.
- [ ] Workspaces 1–10 and Overview selection, previews, Escape, and outside-click
      dismissal work. Verify empty extra workspace markers disappear.
- [ ] Screenshot copy does not save; explicit Save does. Notification images work.
- [ ] `yay --version`, `lazygit --version` and `lazydocker --version` work.
- [ ] Optional Node/Java menu installs work; then a fresh terminal's `nvm current`,
      `node --version`, `sdk current java` and `java -version` confirm managers.
- [ ] System Update in the guest creates a root recovery snapshot and boot archives;
      recovery from live media is tested before calling rollback reliable.
- [ ] Another guest reboot preserves the setup.

For failures, record the repo commit, macOS/UTM versions, chip/RAM, VM architecture,
display device, resolution, installation stage, and exact error. Useful read-only
guest diagnostics include `hyprctl configerrors`, `hyprctl layers`,
`journalctl -b -p warning`, and `systemctl --failed`. Review logs/screenshots for
secrets or private content before sharing. Missing physical Wi-Fi/Bluetooth,
NVIDIA hardware, or successful gaming in this VM is not a desktop regression.

## What remains before a distro release

This Mac VM flow has **not yet been validated end to end**. Prefer testing first
on an x86_64 Linux VM to distinguish installer bugs from UTM/emulation limitations.
Still required:

- Reproducible fresh installation, reboot, login, and failure/recovery testing.
- Real AMD/Intel/NVIDIA graphics and networking checks; VM results cannot replace
  them. Native ARM support would be a separate package/installer compatibility task.
- Asset license review, security defaults, update strategy, and first-run review.

Once these testing milestones are complete, **remove this temporary document and
its links from both READMEs**, moving supported guidance into `distro/README.md`.
