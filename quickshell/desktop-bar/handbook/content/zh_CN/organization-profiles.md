# 组织配置文件

请使用未经修改的官方 ISO。在卷标为 `EITRANSWERS` 的 FAT32 U 盘中，将 `eitr-profile.json` 放置在 `eitr-answers.json` 旁边或直接替换它。如果只有配置文件，常规向导会在“检查确认”中包含其更改。如果两个文件都存在，安装程序会在其 15 秒倒计时之前列出磁盘操作和每项配置文件更改；在磁盘更改前按 Ctrl+C 可取消操作。在关机前请保持 U 盘连接。

完整示例（将所有示例摘要替换为来自 `sha256sum` 的实际小写 SHA-256；将这些文件复制到 U 盘中）：

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
    "theme": "eitr",
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

仅 `version` 和 `name` 是必需的。未知和重复的 JSON 键均属于错误。请删除不需要的可选部分。路径均相对于 U 盘，不包含符号链接、父目录遍历（`..`）或绝对路径。在安装程序更改任何磁盘之前，所有引用的文件必须存在且与其校验和匹配。壁纸文件必须能够解码为 PNG、JPEG 或 WebP。软件仓库密钥必须包含恰好一个 OpenPGP 公钥；HTTPS 服务器不能包含凭据。其密钥会添加并本地信任在 pacman 的密钥环中；请仅使用您信任的组织密钥。软件包归档和设置脚本是受信任的管理员代码，不放在沙盒中运行。

`remove` 仅接受经过审核的 `distro/removable-apps.json` 允许列表。逐项审核记录在 `distro/PROFILE-PACKAGE-REVIEW.md` 中。受保护或未知的软件包会使整个配置文件被拒绝。pacman 会检查依赖项；移除绝不会使用递归移除或依赖项替代。组策略会排除该组中列入允许列表的所有软件包：`gaming`、`media`、`development`、`sharing` 和 `remote_access`。`true` 允许某项功能；`false` 禁用它。`update_channel` 策略仅接受 `"stable"`。省略的策略不受限制。

`plugins` 接受 `false`（隐藏插件菜单并拒绝添加、更新和启动插件），或 `{"allow": ["https://git.example.org/team/tools.git", "git@github.com:team/plugin.git"]}`（仅允许这些仓库）。允许列表条目为 HTTPS 或 SSH URL，不区分协议、用户、端口、`.git` 后缀、尾随斜杠和字母大小写；来自 `~/.ssh/config` 的 SSH 主机别名必须按原样列出。在已安装的计算机上应用此类策略会停止并禁用不再允许的插件的服务，同时保留其文件。

方案使用 `distro/software.json` 中的 `group/name`。仅接受预构建的 pacman 和 Flatpak 方案。AUR 和交互式托管/网页应用方案会被拒绝；请提供经过审核的预构建软件包文件作为替代。软件仓库包、方案和 Flathub 增项需要互联网连接。当其依赖项已包含在 ISO 中或在 U 盘中一同提供时，U 盘软件包可以离线安装。软件包名称在检查时必须在 pacman 当前的同步数据库中可用；在检查在线增项之前，请通过常规更新工作流刷新它们。安装期间不运行任何 AUR 构建。在线 pacman 增项使用完整升级，绝不使用部分升级。额外仓库会针对未来的更新进行配置；仅在这些仓库中可用的软件包应作为 U 盘文件提供以供安装。

在安装期间，Flathub 应用和 Flatpak 方案会排队加入桌面用户队列，并在首次连网启动时安装。失败的安装会在下次引导时重试。在已安装的计算机上应用配置文件会直接安装它们。

浏览器默认设置支持 Firefox 和 Chromium。Chromium 也必须添加到增项中。主题和壁纸默认设置会保存用于所选桌面用户的下一次登录；应用配置文件不会重启其桌面。额外仓库和更新通道是全系统生效的。在记录配置文件之后，`setup` 以 root 身份运行，并将暂存的 U 盘目录作为其工作目录。在启动前，SHA-256 标记会记录其尝试，因此失败或中断的脚本不会静默重新运行。更改脚本（及其摘要）以授权另一次尝试。脚本输出和失败保持可见；失败的安装不会回滚已完成的软件包事务。

在已安装的计算机上：

```sh
eitr profile check /run/media/alex/EITRANSWERS
eitr profile apply /run/media/alex/EITRANSWERS
```

`check` 读取文件和软件包元数据并使用临时验证目录；它不更改任何系统配置。`apply` 使用显式的 root 所属 `eitr-system profile-apply` 操作，以私有方式暂存并重新检查 U 盘，显示相同的摘要，然后需要输入 `APPLY PROFILE`。取消操作不会更改任何内容。它通过 pacman 移除已安装的排除包，安装新增包，保存默认设置，写入 root 所属的 `/etc/eitr/policies.json`（0644，root:root），并记录 `/etc/eitr/profile.json`。应用另一个配置文件会替换所记录的选择；它不会自动重新安装先前移除的应用或重置省略的偏好设置。设置标记在配置文件替换后依然保留。

记录的排除项会过滤手动安装程序清单。pacman 选项中的 `IgnorePkg` include 也会防止系统更新将排除的软件包作为依赖项重新拉入；此类依赖项冲突必须中止升级。预置用户设置不会安装任何应用程序。策略会隐藏 Elephant 菜单/搜索行、远程访问栏条目、助手协同开关和更新通道控制；Eitr 的工具也会直接拒绝这些操作。现有会话可能需要其下一次菜单/面板刷新才能反映新应用的策略。

**这并不是防范拥有 root 权限用户的锁死机制。** root 用户可以编辑策略或运行其他工具。真正的锁死也意味着不授予 root 权限。策略管理的是 Eitr 工作流，而不是任意第三方软件或设备机群管理。

有网络和无网络的安装、被拒绝的配置文件、将配置文件应用于已安装的计算机、升级、隐藏控件以及每种语言的安装程序屏幕均在虚拟机中通过验证（`distro/PROFILE-VM-TESTING.md`）。
