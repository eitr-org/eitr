# 恢复出厂设置

使用 Eitr ISO 安装的计算机可以通过“Walker → 设置 → 系统 → 维护 → 恢复出厂设置”返回其首次登录的状态。此重置是在本地进行的：它恢复保存在同一磁盘上的只读副本。它不是备份，也不属于安全擦除；磁盘损坏将同时丢失计算机及其还原点。

## 还原点

引导式安装程序的最后一步会运行 `eitr-factory-reset capture`，它将完成的安装保存在顶层 Btrfs 子卷 `@eitr-factory` 下：

| 路径 | 内容 |
|---|---|
| `root` | `@` 的只读快照（系统、账户、设置） |
| `home` | `@home` 的只读快照（初始预置的用户文件夹） |
| `boot.tar` | EFI 分区的文件：Limine、其菜单、内核以及 initramfs |
| `manifest.json` | 创建时间、文件系统和 EFI 分区 UUID、账户、`boot.tar` SHA-256 |

随后 `@eitr-factory` 本身被设置为只读。它位于 `@` 旁边，而不是在 `@/.snapshots` 中，因此 Snapper 绝不会列出或清理它，且 Walker 不提供删除它的方法。Root 仍可将其删除，格式化或磁盘故障也会将其销毁。它的快照与正在运行的系统共享数据，因此起初占用的空间很少，随着更新替换原始文件而逐渐增长。

`capture` 拒绝替换现有的还原点。未使用 ISO 进行的安装没有还原点，“恢复出厂设置”会报告此情况。

## 两种重置方式

**抹掉所有内容**将计算机恢复到首次登录状态：此后安装的应用程序、更改的设置、后来添加的账户以及主目录中的所有文件都将被清除。

**保留我的文件**恢复系统、应用程序和设置，并保留主目录文件夹。对于还原点中的每个账户，其当前的隐藏项（`~/.config`、`~/.local`、`~/.ssh`、浏览器配置文件等）会移动到该主目录中名为 `Settings before reset <date time>` 的可见文件夹中，然后将还原点的隐藏项复制回来。主目录中的任何文件都不会被删除。安装后添加的账户会随系统一同移除，但它们的主目录仍保留在 `/home` 下。

两种重置方式都会保留磁盘加密密码（绝不会触碰 LUKS 标头）以及还原点中同样存在的每个账户的当前密码。TPM 解锁槽位仍保留在 LUKS 标头中，但在重新设置 TPM 解锁之前，恢复后的 initramfs 会要求输入密码。日志（`@log`）和软件包缓存（`@pkg`）均予保留。

## 确认

Walker 的操作在终端中显示两次独立的警告：

1. 所选重置将删除和保留的内容。仅输入 `y` 或 `yes` 才会继续；按 Enter 取消。
2. 正在重置哪台计算机、它将立即重启以及未保存的工作将会丢失。必须准确输入 `RESET MY COMPUTER`。

root 拥有的辅助工具（`/usr/lib/eitr/eitr-factory-reset`）会再次检查输入的短语，并在更改任何内容之前进行验证：

- `/` 是子卷 `@`，`/home` 是同一个 Btrfs 文件系统上的 `@home`，且 `/boot` 是 FAT EFI 分区。
- 还原点及其快照仍为只读，其清单中记录了此文件系统和 EFI 分区，且 `boot.tar` 与其 SHA-256 匹配。
- Secure Boot 已关闭：恢复的引导文件未用登记的密钥签名。
- 没有更早的重置仍在等待处理中。

`sudo /usr/lib/eitr/eitr-factory-reset status`（Walker → 重置状态）运行相同的检查并且不更改任何内容。

## 重置的运行机制

正在运行的 root 和 home 绝不会被写入。在一个新的顶层子卷 `@eitr-reset-previous` 下，该辅助工具执行：

1. 为还原点的 root 创建可写快照，在其中重新创建 Snapper 的 `.snapshots` 子卷，复制进当前密码并在其中启用 `eitr-factory-reset-finish.service`。
2. 创建新的 home：还原点 home 的可写快照（抹掉所有内容），或当前 `@home` 的快照并将设置移到一旁，如上文所述（保留我的文件）。
3. 将当前 EFI 分区文件归档至 `boot.tar`，并解包还原点的归档以供复制。

在此之前的任何故障都会删除 `@eitr-reset-previous` 并使计算机保持不变。辅助工具随后将恢复的引导文件复制到 EFI 分区上（发生故障时它会恢复刚刚创建的归档），在 `@eitr-reset-previous` 内部将 `@` 和 `@home` 重命名为 `old@` 和 `old@home`，将准备好的子卷重命名为 `@` 和 `@home`，然后重启。如果重命名失败，则恢复先前的名称和引导文件。

在下一次引导时，`eitr-factory-reset-finish.service` 确认正在运行的 root 是恢复后的 root，删除 `@eitr-reset-previous`（包括旧系统的 Snapper 快照）并禁用其自身。

## 恢复中断的重置

在少数几个重命名操作期间发生断电可能会导致 `@` 或 `@home` 缺失。引导 Eitr ISO，按 Escape 退出向导，如果磁盘已加密则解锁磁盘（`cryptsetup open /dev/<partition> root`），然后检查：

```sh
mount -o subvolid=5 /dev/mapper/root /mnt   # 或 Btrfs 分区本身
btrfs subvolume list /mnt
cat /mnt/@eitr-reset-previous/manifest.json
```

- `@` 和 `@home` 均存在且 `@eitr-reset-previous/new-root` 已消失：交换已完成。重启计算机；完成服务会进行清理。
- `@` 或 `@home` 缺失：将匹配的 `@eitr-reset-previous/old@` 或 `old@home` 重命名还原（`mv /mnt/@eitr-reset-previous/old@ /mnt/@`），然后将 `@eitr-reset-previous/boot.tar` 解包到 EFI 分区以匹配旧系统，并重启计算机。

仅在系统正确启动后，才使用 `btrfs subvolume delete --recursive` 删除 `@eitr-reset-previous`；在此之前它保存着先前的系统。

## 验证

在没有网络的 UEFI 虚拟机中进行了测试（参见 [LINUX-VM-TESTING.md](LINUX-VM-TESTING.md)）：在未加密抹掉安装上进行了两种重置，并在与 Windows 磁盘共存的 LUKS2 安装上进行了两种重置，每次重置后均成功引导、登录并由完成服务完成清理。尚未测试：真实硬件、交换过程中的断电以及通过在线系统更新保留还原点（虚拟机没有网络）。
