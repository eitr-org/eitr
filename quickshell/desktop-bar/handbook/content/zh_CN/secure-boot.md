# 使用 sbctl 配置安全启动

Eitr 记录了安全启动的相关文档，但**绝不会自动为您录入密钥或对文件进行签名**。此处的任何错误都可能导致机器拒绝引导或无法显示画面，因此请在一台您能够正常进入固件设置界面的电脑上，在备好磁盘密码短语和[恢复指南](RECOVERY.md)的情况下，手动按步骤操作。本指南中的任何内容尚未在 Eitr 测试硬件上进行实际验证。

## 开始之前

- 仅限 UEFI 引导。请注意如何进入固件设置（通常是 F2、Del 或 F12）并设置固件管理员密码，否则任何人都可以再次关闭安全启动。
- 如果录入了 TPM 磁盘解锁，请备好密码短语：录入密钥会更改 TPM PCR 7，因此下次启动时会要求输入一次密码短语。之后请重新录入 TPM 解锁（安全 → TPM 磁盘解锁：先移除，再录入）。
- 在固件设置中，将安全启动置于**设置模式 (Setup Mode)**（通常称为“清除密钥”或“重置为设置模式”）。请勿删除无法恢复的密钥；大多数固件都提供“恢复出厂密钥”选项。

## sbctl 工作流

```sh
sudo pacman -S --needed sbctl
sbctl status                      # 必须报告 "Setup Mode: Enabled"
sudo sbctl create-keys            # 私钥保存在 /var/lib/sbctl（仅限 root 访问）
sudo sbctl enroll-keys -m         # -m 保留微软的密钥；详见下文风险
sudo sbctl verify                 # 列出 EFI 文件及其签名状态
sudo sbctl sign -s <file>         # 对 verify 列出的每个未签名文件执行一次
```

`sign -s` 会将文件保存在 sbctl 的数据库中；sbctl 的 pacman 钩子会在内核和引导加载程序更新后自动为保存的文件重新签名。每次更改后请运行 `sudo sbctl verify`，然后在固件中启用安全启动并重启。请在线下私密备份 `/var/lib/sbctl`：它包含签名私钥。切勿将其复制到本代码仓库中。

## 风险说明

- **Option ROM 与厂商密钥。** 显卡、NVMe 驱动器和网卡通常运行由微软 UEFI CA 签名的固件 (Option ROM)。如果仅录入您自己的密钥而不带 `-m`，固件可能会拒绝加载它们：导致无显示、无引导磁盘，在某些笔记本上甚至无法进入固件设置。除非您确信硬件不包含此类固件，否则请务必保留 `-m`。`sbctl enroll-keys --tpm-eventlog` 亦可添加本次引导所使用的 Option ROM 哈希值，但它们会在硬件变动或固件更新后发生改变。
- **未签名文件。** 引导路径中的每个 EFI 二进制文件都必须使用您的密钥进行签名。遗漏任何一个文件都会导致无法引导；可在固件中禁用安全启动以进行恢复。
- **双系统引导。** 只有保留 `-m` 时 Windows 才能继续正常引导。

## 引导加载程序与快照条目

- **GRUB：** 使用以下命令重新安装：
  `sudo grub-install --target=x86_64-efi --efi-directory=<esp> --bootloader-id=GRUB --modules="tpm" --disable-shim-lock`，
  然后为新的 `grubx64.efi` 和 `/boot` 中的内核签名。在此配置下，GRUB 不会校验内核签名，因此 grub-btrfs 快照条目可以继续正常引导，但保护范围涵盖的是 GRUB 二进制文件本身而非每个内核。当 GRUB 更新更改镜像后，请重新运行 `grub-install` 和 `sbctl sign`。
- **Limine：** 为 Limine EFI 二进制文件签名（`sbctl sign -s <esp>/EFI/limine/BOOTX64.EFI` 或其安装位置）。Limine 使用哈希值而非签名来保护其配置和内核。如果您将配置哈希录入到二进制文件中 (`limine enroll-config`)，对 `limine.conf` 的每次更改（包括来自 limine-snapper-sync 的每个新快照条目）都必须重新录入并重新签名。在启用安全启动之前，请确认您的 `limine-mkinitcpio-hook` 设置能够自动完成此操作（安装后它会调用 sbctl），否则下次快照同步会导致引导程序拒绝其菜单。
- **systemd-boot：** 为 `systemd-bootx64.efi` 及其加载的内核或统一内核映像 (UKI) 签名。它不支持快照引导条目。
- 较旧内核的快照条目仍必须通过您引导程序的校验。启用安全启动后，请先尝试引导一次快照条目以确认其能正常工作，以备不时之需。

## 撤销与还原

1. 进入固件设置并禁用安全启动，或选择“恢复出厂密钥”以恢复到硬件厂商的原始密钥集。在安全启动关闭的情况下，已安装的系统仍能继续正常引导。
2. 可选使用 `sudo sbctl remove-file <file>` 从 sbctl 数据库中移除已保存的文件；文件本身的现有签名并无危害。
3. 如果在安全启动开启期间录入了 TPM 解锁，PCR 7 会再次发生改变：输入一次密码短语并重新录入即可。

参考资料：[sbctl](https://github.com/Foxboron/sbctl)、[Arch Wiki: 安全启动](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot)。
