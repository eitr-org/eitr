# 终端与编辑器

**SUPER + Enter** 打开您选择的终端（默认为 Kitty）。**SUPER + Ctrl + Enter** 打开/附加到主 tmux 会话。**SUPER + P** 模糊查找文件；**SUPER + Ctrl + P** 搜索文件内容。“学习 > Cmux 命令”、“Tmux 命令”和“LazyVim 命令”是可搜索的参考列表；选择命令会将其复制，而不是直接执行。

Kitty 在光标跳跃至少两个单元格时显示简短的光标轨迹，例如按 Enter、Home/End 以及在单词之间移动。它在光标静止 3 毫秒后开始，并在 0.05–0.15 秒内淡出。如需自定义，请在 `~/.config/kitty/local.conf` 中设置 `cursor_trail`、`cursor_trail_decay` 或 `cursor_trail_start_threshold`；`cursor_trail 0` 可禁用它。个人选项会覆盖随附的默认设置，并在主题更改后依然有效。

### 光标烈焰 (Cursor Fire)

在**设置 > 外观 > 终端**中开启“光标烈焰”，体验 Kitty 的炽烈光标轨迹。它默认关闭。关闭它会恢复常规光标轨迹和个人着色器选择。

该效果需要 Kitty 0.49+ 和 `shader-slang`，已包含在 Eitr 的桌面依赖项中。启用前会先验证内置着色器，然后再保存或重新加载 Kitty。机器本地偏好设置为 `~/.config/eitr/terminal.json`；辅助工具会写入 `kitty/cursor-fire.conf`，该文件由 Kitty 的用户加载器最后引入。启用期间，它会选择烈焰着色器并将移动阈值降至一个单元格。字体、主题和个人配置文件保持不变。

## 选择终端

使用“设置 > 外观 > 终端”选择 Kitty 或 Ghostty。“Walker > 设置 > 桌面 > 外观 > 终端”是另一种途径。`~/.config/eitr/terminal.json` 中的机器本地 `terminal` 字段控制 Super+Enter、tmux、用户终端会话、AI/项目终端以及 Walker 的在终端中打开操作。如果 Ghostty 缺失，选择它会打开常规的官方软件包安装流程：按 Enter 安装，按 Esc 取消。在安装成功前，Kitty 保持选定状态。如果稍后移除了 Ghostty，启动会后备回退到 Kitty。Ghostty 是可选的，不包含在 ISO 安装镜像中。

主题切换会使用主题的 16 种 ANSI 颜色、背景、前景、选区和文本光标颜色重新生成 `~/.config/ghostty/eitr.conf`。字体更改会重新生成所选字体系列；默认大小为 10 磅。Ghostty 运行相同的 zsh 和提示符，默认采用 75% 不透明度和零普通窗口内边距。Hyprland 提供模糊效果和相同的常规窗口装饰/规则。`eitr/cursor.json` 中的指针系列、大小和“自动”/“浅色”/“深色”选项继续应用于 GTK 和合成器；它们与终端的文本光标是独立的。

Ghostty 通过 Eitr 启动器加载生成的文件。请将个人设置（如 `font-size = 12` 或 `cursor-style = bar`）放在 `~/.config/ghostty/local.conf` 中，该文件最后加载且在主题更改时予以保留。正在运行的 Ghostty 会话在主题/字体更改后会接收到其支持的重新加载信号。某些选项仅适用于新窗口。Kitty 的光标轨迹和“光标烈焰”是 Kitty 独有的；Ghostty 没有对等的内置炽烈效果设置。

Eitr 的任务、菜单、状态和设置终端始终使用 Kitty，包括 `eitr-menu-terminal`、`eitr-plugins` 和 `fif-terminal`：它们的 `--class`、`--hold`、`--title` 选项和浮动窗口规则依然专属于 Kitty。在选择 Ghostty 时它们不会发生改变。

## 终端外观与共享模糊

“Walker > 设置 > 桌面 > 外观 > 终端”和“设置 > 外观 > 终端”将不透明度、内边距和模糊预设应用于 Kitty 和 Ghostty。不透明度提供“实心”(100%)、“轻微”(90%)、“中等”(80%)、“默认”(75%) 和“强烈”(70%)。内边距提供“无”、“小”(4 磅) 和“舒适”(8 磅)。默认设置保持 75% 不透明度、无内边距并开启模糊。实用工具终端保留其纯色背景和任务内边距。

关闭模糊会禁用常规 Kitty 和 Ghostty 窗口的合成器模糊；这不会使它们变成实心不透明。模糊强度在整个桌面共享：“柔和”（大小 2，单次处理）、“中等”（大小 3，双次处理，默认）和“强烈”（大小 5，三次处理）。相同的选项出现在 Walker 的“桌面栏”和设置 (SUPER + ,) 的“桌面栏”中，位于外观旁边。

Hyprland 0.57 具有全局模糊强度，因此这会影响所有已在使用模糊的表面，包括面板、通知、概览以及其他启用模糊的应用程序。选择模糊强度不会启用终端模糊。较强的模糊需要消耗更多的 GPU 算力。“主题颜色”保持其现有的实心外观。

终端选项保存在 `eitr/terminal.json` 中；共享的 `blur-strength` 保存在 `quickshell/desktop-bar/bar-settings.json`（版本 1）中。生成的 `kitty/appearance.conf`、`ghostty/eitr.conf` 和 `hypr/appearance.lua` 通过这些偏好设置在重新生成后依然有效。合成器在 `hypr/local.lua` 之前加载生成的外观，因此个人合成器规则优先。`kitty/local.conf` 和 `ghostty/local.conf` 中的终端设置会覆盖预设。主题切换和软件包更新会重新生成设置。Kitty 接收 SIGUSR1，受支持的 Ghostty 会话接收 SIGUSR2；无法重新加载的选项将应用于新窗口。

## eitr 命令

`eitr` 将 Eitr 的工具汇集在一个命令中；单独运行它可查看列表。它运行与菜单相同的脚本，因此两者的行为始终保持一致。

```
eitr update                  # 系统更新：快照、软件包、AUR、Flatpak
eitr update aur              # 仅更新 AUR 软件包，不创建快照
eitr theme list              # 已安装的主题，当前主题标有 *
eitr theme set "Eitr" # 切换主题
eitr firewall on             # 同样支持：off、status
eitr snapshots               # 恢复快照
eitr snapshots changes       # 每次更新更改的内容
eitr reset keep-files        # 恢复出厂设置，经过通常的两次警告后执行
eitr report                  # 准备问题报告
eitr handbook troubleshooting
eitr version
eitr about
eitr matrix                  # 符文雨；按任意键停止
```

`eitr about` 打开“关于 Eitr”，或者如果已打开则聚焦其窗口。

`eitr config` 和 `eitr git` 将其参数传递给 `eitr-config` 和 `eitr-git`。每个命令都有 `--help`。

## 您自己的钩子 (Hooks)

钩子是您编写的小脚本，Eitr 在特定时刻运行它，这样您就可以在不更改 Eitr 本身的情况下扩展其功能。在 `~/.config/eitr/hooks/` 中放置以该时刻命名的可执行文件：

| 文件 | 运行契机 | 接收参数 |
| --- | --- | --- |
| `post-update` | 在系统更新或 pacman/AUR 更新后 | `system`、`pacman`、`yay` 或 `full` |
| `theme-set` | 在切换主题后 | 主题的文件夹名称 |
| `battery-low` | 每次电量降至 15% 时触发一次 | 电量百分比 |
| `post-boot` | 每次开机后的首次登录时 | 无参数 |

例如，要在主题更改时重新为 Spotify 配色（使用 Spicetify），请创建 `~/.config/eitr/hooks/theme-set`：

```
#!/usr/bin/env bash
spicetify config color_scheme "$1" && spicetify apply
```

然后使用 `chmod +x ~/.config/eitr/hooks/theme-set` 使其可执行。每个钩子最多执行 60 秒；其输出和任何故障记录在 `~/.local/state/eitr/hooks.log` 中，失败的钩子绝不会中止更新或主题切换。`eitr hook list` 显示存在哪些钩子，而 `eitr hook run theme-set eitr` 可测试运行某个钩子。更新绝不会触碰此文件夹。

## cmux TUI

在 Kitty 中运行 `cmux`，或运行 `cmux --session work` 进入指定会话。cmux TUI 是与 tmux 并行的可选工作流，而不是 Kitty 或其现有快捷键的替代品。全新 EITR 安装在 `/usr/bin/cmux` 中包含固定版本的官方二进制文件；现有的每用户安装可能会在 PATH 中优先加载。使用 `command -v cmux` 查看选中了哪一个。已包含 `less` 用于阅读终端输出和文本文件。

默认前缀键是 **Ctrl-b**：松开它，然后按下一个键。

| 快捷键 | 操作 |
| --- | --- |
| Ctrl-b ? | 显示当前快捷键 |
| Ctrl-b W | 创建工作区 |
| Ctrl-b c | 创建屏幕 |
| Ctrl-b % / Ctrl-b " | 向右 / 向下拆分 |
| Ctrl-b t | 新建终端标签页 |
| Ctrl-b h/j/k/l | 聚焦左/下/上/右 |
| Ctrl-b s | 显示/隐藏侧边栏 |
| Ctrl-b d | 在本地退出或从服务器断开连接 |

如需会话在没有界面时继续运行，请运行 `cmux --headless --session work`，然后使用 `cmux attach --session work` 进行附加连接。浏览器标签页需要 Chrome/Chromium。关闭标签页、窗格或工作区可能会影响正在运行的任务；在使用这些操作前请仔细检查。“学习 > Cmux 命令”包含会话命令、导航、鼠标控件和关闭快捷键。默认值可能会更改或被覆盖；**Ctrl-b ?** 是实时参考。

## 任务终端

菜单打开的终端，以及更新和问题报告通知的终端，均居中浮动在窗口上方并使用主题的纯色背景。AI 助手会话和 LazyVim 项目（开发菜单）作为常规平铺窗口打开（类似于您自己打开的终端），带有半透明背景。常规终端是交互式的且不带品牌横幅。

安装程序/更新/设置终端显示带主题样式的符文风 EITR 横幅；成功的任务通常会自动关闭，而失败的任务保持打开直到被关闭。信息类报告可能会特意保持打开状态。重启 Elephant 不会关闭已启动的应用程序：从菜单、快捷键绑定和桌面栏按钮打开的应用程序和终端在 uwsm 会话中使用独立的应用程序作用域。

在没有 uwsm 的情况下，它们直接启动。对于桌面辅助工具和后备启动，Elephant 保持仅进程级别的停止策略。

按 **Esc** 关闭处于等待状态的任务、账户、报告和“关于”终端。Enter 仍用于作答和确认，包括确认恢复密钥和关闭安装程序电源。

## Shell 历史记录

`history` 列出近期命令。在 zsh 中，使用以下命令检查实际的历史记录路径：

```sh
printf '%s\n' "$HISTFILE"
```

要在 Neovim 中打开它：

```sh
nvim "$HISTFILE"
```

历史记录可能包含令牌或凭据；切勿将其复制到错误报告中。在手动编辑它之前请先关闭其他 shell，因为正在运行的 shell 可能会将其内存中的历史记录写回。扩展的 zsh 历史记录可能包含时间戳元数据和多行命令；请移除整个相关条目，而不是任意片段。如果需要撤销，请私下备份该文件。

## 编辑器外观

主题更改会更新生成的 VS Code 和 LazyVim 首选项。受支持的实时 LazyVim 会话无需重新打开即可刷新。用户覆盖项/插件可以选择其自己的颜色；如果编辑器未跟随桌面外观，请验证其配置。默认字体集成仅在应用程序支持的场合应用。

## 个人资料头像

`eitr picture`（或 `eitr picture show`）以 JSON 格式显示当前的头像状态。`eitr picture set 文件` 保存最大的居中正方形；`eitr picture remove` 移除头像。使用“设置 > 用户”调整裁剪。
