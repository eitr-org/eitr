# Alongside Windows VM test

Tests installing Eitr beside Windows 11, as on a PC where Windows was shrunk first.

1. Download Windows 11 Enterprise (LTSC) Evaluation, 64-bit en-US, from Microsoft's
   Evaluation Center. It needs no product key; an expired evaluation still boots, which is
   all this test needs.
2. Build the Windows disk once (6-40 minutes, unattended, no network):

   ```sh
   distro/vm-tests/windows/make-base --iso WINDOWS.iso --output vm-windows/base
   ```

   `autounattend.xml` puts Windows on 40 GB of a 100 GB disk, skips the TPM and Secure
   Boot checks, turns hibernation (Fast Startup) off and shuts down after the first sign-in.
   The output holds `disk.qcow2` and `vars.fd` (firmware with Windows Boot Manager first).
3. Install over a throwaway copy of it, then verify as usual:

   ```sh
   distro/vm-tests/eitr-vm-test install --iso eitr.iso --work runs/alongside \
       --base vm-windows/base --layout alongside
   distro/vm-tests/eitr-vm-test verify --work runs/alongside
   ```

4. Check by hand that Windows' partitions kept their start, size and IDs
   (`qemu-img dd` the first MiB of both disks and compare `sfdisk --dump`), and that
   Windows starts from Eitr's boot menu. Windows has no virtio disk driver, so boot it with
   the disk on SATA (`-device ahci,id=sata` and `-device ide-hd,drive=disk,bus=sata.0`,
   as `make-base` does).
