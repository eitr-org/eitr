# Eitr 恢复快照

快照是恢复点，**不是脱机备份**。损坏的磁盘可能会同时销毁系统及其快照。请保留独立的外部备份。

Eitr 目前支持在 Btrfs 根分区上运行 Snapper，且 `/usr`、`/etc` 和 `/var/lib/pacman` 位于同一个根子卷中。`/home` 可以独立存在：它不受根快照覆盖。不受支持的布局在升级前会自动安全终止。`install.sh` 不会格式化磁盘或重新排布现有的子卷；仅有 ISO 的 `eitr-guided-install` 会在您确认后抹掉磁盘并创建此布局（请参阅 README 的“引导式安装”部分）。

## 更新前准备

安装程序会启用 `/etc/eitr/system-update-policy.conf`。在“设置 → 更新 → 系统更新”升级官方和 AUR 软件包之前，它会：

1. 验证受支持的布局和 Snapper 根配置。
2. 仅当 `/boot` 和 `/efi` 为独立挂载点时对其进行归档（位于 Btrfs 根内部的 `/boot` 目录已包含在根快照中）。归档文件存储在 `/var/lib/eitr/boot-backups/<快照编号>/` 下，仅供 root 访问。
3. 创建升级前的根快照。
4. 如果引导备份或快照创建失败，则中止升级。

当升级完成、失败或被拒绝时，该工作流会创建相应的升级后快照；其描述记录了结果（“after package upgrade”、“after failed package upgrade”）。如果在此之前工作流被终止，下一次“系统更新”首先会使用“after interrupted package upgrade”升级后快照来关闭遗留的升级前快照。无论哪种情况，失败的升级都会保留其升级前快照和引导归档。
对 Flatpak、SDKMAN/NVM 运行时以及独立 home 子卷上文件的更新不受这些快照的保护。终端命令 `eitr update pacman|aur|full` 以及直接执行的 pacman/yay 命令特意设计为不自动创建快照。如果手动安装了较旧的 Eitr 快照 hook，必须将其移除以采用此策略。

新的 Snapper 配置通过清理计时器保留最多 10 个普通编号快照和 5 个重要编号快照。现有的策略予以保留。每次“系统更新”时引导归档会修剪至最新的 10 个，以匹配默认的快照限制；如果 Snapper 先移除了快照，归档可能会比其快照保留更久，因此在还原之前请检查快照是否存在。磁盘已满会阻止更新，而不是跳过保护机制。

## 引导守护 (Boot Guard)

在采用 Eitr 引导式安装布局的机器上，成功的“系统更新”后，引导守护会保持该更新的“更新前”快照处于就绪状态 (`/var/lib/eitr/boot-guard.json`)。`eitr-boot-guard.service` 在引导早期计算每次启动，并且一旦登录屏幕持续显示 45 秒，`eitr-boot-guard-healthy.service` 便将此次启动计为健康，从而解除守护武装。

当更新后连续两次启动均未达到该状态时，第三次启动将自动还原，采用经过验证的出厂重置步骤：

1. 将快照的引导文件（`/var/lib/eitr/boot-backups/<编号>/boot.tar`）复制到 EFI 分区，在保留今天的引导文件以备放回之后进行。
2. 失败的根子卷被重命名为 `@eitr-guard-failed`，快照的可写副本变为 `@`，Snapper 的 `.snapshots` 存储移动到其中。
3. 计算机重启进入还原后的系统。如果任何步骤失败，子卷和引导文件将按原样恢复，不执行任何重启。

还原后的系统在到达登录屏幕后会删除 `@eitr-guard-failed`，并在下次登录时显示通知。主目录文件夹不受影响。当内核本身无法启动时，守护程序无法提供帮助；此时请从引导菜单引导更新的快照（见下文）。其他磁盘布局绝不会装备引导守护。

## 身份验证更改

“安全 → 启用指纹/FIDO2”在编辑 `/etc/pam.d/hyprlock`、`sddm` 和 `sudo` 之前，会将它们备份在 `/var/lib/eitr/pam-backups/<时间戳>/` 下，并在任何写入失败时还原这三者。指纹会添加到这三者中，因此“仅密码”也适用于锁屏；pam_fprintd 可能会将密码提示延迟长达 10 秒。要从正常的 root shell 或 TTY 返回到先前的策略：

```sh
sudo ls /var/lib/eitr/pam-backups
sudo /usr/lib/eitr/eitr-system auth-restore <时间戳>
# 如果没有 eitr-desktop 软件包，辅助工具为 /usr/local/lib/eitr/eitr-system。
```

## TPM 磁盘解锁

“安全 → TPM 磁盘解锁”可以为 LUKS2 根分区添加 TPM2 密钥槽位，以便在开机引导时无需输入密码即可解锁磁盘。安装程序不会运行此处的任何内容。root 辅助工具（`luks-tpm-check`、`luks-recovery-key`、`luks-tpm-enroll`、`luks-tpm-remove`）会在以下情况下拒绝执行：设备不是 LUKS2、`systemd-cryptenroll --tpm2-device=list` 未列出 TPM2 设备，或密码/恢复槽位尚不存在。它仅**添加**槽位；密码依然保留。

- **恢复密钥优先。** Walker 流程提供 `systemd-cryptenroll --recovery-key`；密钥仅在终端中输出一次，绝不存储。请在脱机状态下抄写下来。它在常规密码提示符下均有效。
- **PCR 选择。** Eitr 绑定到 PCR 7（Secure Boot 状态和密钥）。固件更新很少更改它，而 Secure Boot 密钥更改会更改它。仅当使用您自己的密钥启用 Secure Boot 时，PCR 7 才能提供实质性保护（参见 [SECURE-BOOT.md](SECURE-BOOT.md)）；否则任何人都可以在修改内核命令行后引导此计算机并获取已解锁的磁盘。如需更强保护，请手动使用 PIN 登记：
  `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 --tpm2-with-pin=yes <设备>`。
- **Initramfs。** busybox `encrypt` hook 无法使用 TPM2 令牌，因此在配置它时会拒绝登记。在 `HOOKS` 中切换到 `systemd` 和 `sd-encrypt`（在内核命令行中使用 `rd.luks.name=<LUKS-UUID>=root` 替换 `cryptdevice=`，或配置 `/etc/crypttab.initramfs`）是一项关键的引导更改，Eitr 将其留给您自行决定。进行更改、运行 `sudo mkinitcpio -P`、更新引导条目，并在登记 TPM **之前**确认一次密码引导能够正常工作。

如果 TPM 停止解锁（固件或 Secure Boot 更改、TPM 重置），密码提示将像以前一样显示。输入密码，然后移除并重新登记。要完全回滚，请使用“移除 TPM 解锁”，或在任何正常工作的 shell 中运行：

```sh
sudo systemd-cryptenroll /dev/<luks-分区>            # 列出槽位
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/<luks-分区>
```

## 恢复出厂设置

使用 Eitr ISO 安装的计算机还在 Snapper 外部保留了首次登录的只读还原点。“Walker → 设置 → 系统 → 维护 → 恢复出厂设置”可返回该状态，支持保留或不保留主目录文件；参见 [FACTORY-RESET.md](FACTORY-RESET.md)。

## 检查恢复点

使用“Walker → 设置 → 系统 → 维护 → 快照”，或运行以下只读检查：

```sh
sudo snapper -c root list
findmnt -o TARGET,SOURCE,FSTYPE / /boot /efi
sudo du -sh /var/lib/eitr/boot-backups
```

如果桌面发生故障但系统仍能引导，请切换到文本控制台或使用您自己配置的 SSH 连接。如果无法引导，请使用 Arch 官方安装程序 ISO 并挂载系统的 Btrfs 文件系统。在进行任何更改之前，请确认正确的磁盘、加密映射、根子卷、快照编号和 EFI 挂载点。切勿盲目从另一台机器复制命令。

## 主目录快照

默认关闭。**Walker > 设置 > 系统 > 维护 > 快照 > 主目录快照**可开启此功能（会先提示确认，关闭它们会将其删除）。Snapper 的 `home` 配置随后每小时保留一个 `/home` 快照（持续一天），每天保留一个快照（持续一周），当可用空间低于 20% 时删除最早的快照。

缓存、`~/Downloads`、虚拟机磁盘文件夹（`~/.local/share/libvirt/images`、GNOME Boxes、`~/VirtualBox VMs`）和 Steam 库被排除在外：在下次启动时、任何人登录之前，`eitr-home-exclusions.service` 会将它们转变为嵌套的 Btrfs 子卷，主目录快照不包含这些子卷。它们的文件予以保留（通过 reflink，因此移动不占用额外空间）。恢复出厂设置的“保留我的文件”会将这些子卷带入恢复后的主目录中：隐藏的子卷进入“Settings before reset”文件夹，缓存被丢弃。如果某个子卷无法移动，先前的 home 将保留供检查而不是删除。

转换和创建缺失的排除文件夹以主目录所有者的身份运行，包括该账户的附加组。拒绝符号链接的主目录以及位于其他文件系统上的路径；作为符号链接或位于符号链接文件夹下方（例如位于另一个磁盘上的 Downloads）的排除文件夹保持原样，绝不跟进。失败的转换会使设置保持挂起状态，并留下任何 `名称.eitr-subvolume` 或 `名称.eitr-old` 文件夹以供检查；原始文件保留在 `名称` 或 `名称.eitr-old` 中。在移除残留并重试之前请先检查这些文件夹。不尝试进行特权自动清理：作为所有者删除非空 Btrfs 子卷通常需要 `user_subvol_rm_allowed`。

**快照 > 恢复文件或文件夹**（或 `eitr restore 路径`）列出包含该路径的快照，并将所选版本以 `名称 (restored 日期)` 复制到当前文件身旁，或者在被删除时还原到原位。绝不会覆盖任何现有文件。

## 每次更新更改的内容

在回滚之前，请检查您将要撤销的内容。**Walker > 设置 > 系统 > 维护 > 快照 > 每次更新更改的内容**（或 `eitr snapshots changes`）列出每次更新的前后对比对，附带升级、降级、安装和移除的软件包数量。`eitr snapshots changes <更新前编号>` 列出单次更新中的每个软件包及其新旧版本。它比较两个快照内部保存的软件包数据库；尚未生成更新后快照的更新将与正在运行的系统进行比较。

## 引导更早的快照

使用 GRUB 或 Limine，引导菜单可以列出只读的 Snapper 快照，因此无需引导介质即可检查并回滚损坏的更新。安装程序仅在您输入 `yes` 后才提供此选项；在现有安装上请运行 `bash distro/bootloader/setup.sh`（`--check` 仅报告状态）。通过“Walker → 设置 → 系统 → 维护 → 快照 → 可引导快照状态”或 `sudo /usr/lib/eitr/eitr-system snapshots-boot-status` 检查结果。

| 引导加载程序 | 集成方式 | 软件包 (`distro/bootloader/`) |
|---|---|---|
| GRUB | 每当 Snapper 添加或移除快照时，`grub-btrfsd.service` 重建“Arch Linux snapshots”子菜单 | `grub-btrfs`, `inotify-tools` (官方) |
| Limine | `limine-snapper-sync.service` 向 `limine.conf` 添加快照条目 | `limine-snapper-sync`, `limine-mkinitcpio-hook` (AUR) |
| systemd-boot | **不支持。** 它仅从 EFI/XBOOTLDR 分区加载内核，无法打开 Btrfs 快照 | 使用下方的引导介质流程 |

检测程序读取 `/boot`、`/efi` 和 `/boot/efi` 下的 GRUB、Limine 和 systemd-boot 文件。如果配置了多个加载程序（例如 GRUB 旁边残留的 systemd-boot 文件），安装程序会拒绝执行而不是进行猜测；请移除过时文件或手动配置条目。安装程序首先将当前的 `grub.cfg`/`limine.conf` 复制到 `/var/lib/eitr/boot-config-backups/<时间戳>/`，并为下次引导启用服务：

- **GRUB：** 安装程序运行一次 `grub-mkconfig -o /boot/grub/grub.cfg`。如果 `/boot` 是独立分区，快照条目会引导*当前*内核；在内核更新后，还需还原匹配的引导归档（见下文）。
- **Limine：** `limine-snapper-sync` 管理由 `limine-entry-tool`（来自 `limine-mkinitcpio-hook`）创建的条目，并在 EFI 分区上保留每个快照内核的副本，因此该分区需要足够的空间（上游建议 4 GiB）。检查 `/etc/default/limine`（`SNAPPER_CONFIG_NAME="root"`，如果未检测到则指定 `ESP_PATH`），运行 `sudo limine-update`，检查菜单，然后运行 `sudo systemctl start limine-snapper-sync.service`。Eitr 不会代您运行 `limine-update`，因为它会重写引导菜单。

要撤销更改，请禁用服务并复制回备份，例如：
`sudo systemctl disable grub-btrfsd.service` 以及
`sudo cp /var/lib/eitr/boot-config-backups/<时间戳>/grub.cfg /boot/grub/grub.cfg`。

### 只读快照

Snapper 快照是只读的。按原样引导的快照无法写入 `/var`，因此 SDDM 和其他服务可能会启动失败；如果图形登录未启动，请在文本控制台 (Ctrl+Alt+F3) 上登录。initramfs overlay 可使引导的快照在 RAM 中可写（更改在重启时消失）。Eitr 不会编辑 `HOOKS`；请自行添加，然后重新生成，请注意只有在此之后创建的快照才包含该 hook：

- GRUB：在 `/etc/mkinitcpio.conf` 的 `HOOKS=(...)` 中追加 `grub-btrfs-overlayfs`，然后运行 `sudo mkinitcpio -P`。
- Limine：在 `filesystems` 之后添加 `btrfs-overlayfs`（如果使用 systemd hook 则添加 `sd-btrfs-overlayfs`），然后运行 `sudo limine-update`。

### 永久回滚

1. 在引导菜单的快照列表中选择最新的“after package upgrade 前”快照，并确认系统在该快照下工作正常。
2. **Limine：** 运行 `sudo limine-snapper-restore` 并选择快照。它使用配置的 `RESTORE_METHOD` 进行还原，并为被替换的系统添加备份条目，因此还原操作本身也可以从引导菜单中恢复。
3. **GRUB：** `snapper rollback` 仅在通过 Btrfs 默认子卷挂载根分区时才有效。Arch 布局通常引导 `rootflags=subvol=@`（检查 `findmnt -no OPTIONS /` 和 `/etc/fstab`），因此 rollback 不会生效。在检查顶层文件系统的子卷列表后，从引导介质替换根子卷。以下示例**仅**适用于 Eitr 的引导式安装布局（其中 Snapper 创建了嵌套的 `@/.snapshots` 子卷）；其他布局需要其自身的实际路径：

   ```sh
   sudo mount -o subvolid=5 /dev/<根分区或映射设备> /mnt
   sudo mv /mnt/@ /mnt/@.broken
   sudo btrfs subvolume snapshot /mnt/@.broken/.snapshots/<编号>/snapshot /mnt/@
   # Btrfs 快照不包含嵌套子卷。将原始 Snapper 存储保留在还原后的根分区中，而不是随 @.broken 一同删除。
   sudo rmdir /mnt/@/.snapshots
   sudo mv /mnt/@.broken/.snapshots /mnt/@/.snapshots
   ```

   如果任何命令失败，请停止并检查；切勿删除保留的根分区。确认快照存储存在于还原后的根分区下，并在继续之前检查其 fstab。如果 `/boot` 是独立的，请还原匹配的 `/var/lib/eitr/boot-backups/<编号>/` 归档，重启进入常规条目，运行 `sudo grub-mkconfig -o /boot/grub/grub.cfg`，仅在还原后的系统验证无误后，再使用 `sudo btrfs subvolume delete` 删除 `@.broken`。

## 从引导介质安全还原

1. 备份所需的任何较新文件。挂载 Btrfs 顶层文件系统并检查其子卷列表；定位所选快照的 `snapshot` 子卷。路径取决于 `.snapshots` 的挂载位置。
2. 通过重命名来保留发生故障的根子卷。在原始根子卷路径下创建所选恢复快照的**可写 Btrfs 快照**，匹配已安装引导加载程序的 rootflags 和 fstab。
3. 挂载还原后的根分区及其真实的 boot/EFI 分区。如果内核/initramfs/引导加载程序文件发生了更改，还原匹配的引导归档。归档必须与所选的根快照相匹配；绝不能将较新的内核与较旧的模块混合使用。
4. 检查 fstab 和引导加载程序配置，然后根据该机器的需要通过 `arch-chroot` 重新生成 initramfs 或修复引导条目。仅在根文件和引导文件达成一致后才重启计算机。

这是兼顾布局的手动恢复流程，**不是经过验证的一键式回滚实现**。对于任意 Arch 子卷/引导加载程序布局，单独使用 Snapper 的 `rollback` 命令是不够的。上述 GRUB 和 Limine 快照条目在声称自动恢复之前，仍需要在真实硬件上进行验证。

参考资料：[grub-btrfs](https://github.com/Antynea/grub-btrfs)、[limine-snapper-sync](https://gitlab.com/Zesko/limine-snapper-sync)、[Snapper 恢复概念](https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-snapper.html)、[Arch 安装指南](https://wiki.archlinux.org/title/Installation_guide)。
