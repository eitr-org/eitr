# 开发工具

“主菜单 > 开发”汇集了 **AI**、**云**、**Git 账户**、**监控**、**LazyVim** 和 **VS Code**。项目选择器在编辑器中打开所选目录；主题集成会更新受支持的已打开编辑器，包括 LazyVim 会话。

**Git 账户**配置默认的 GitHub/GitLab 身份、按文件夹的替代设置、SSH 密钥和独立的提供商 CLI 登录。每项规则更改都需要预览确认；它绝不会重写项目远程仓库或更改全局 CLI 账户。请参阅 [Git 账户](handbook:git-accounts)。

## 可选工具链

“安装 > 开发语言”和“JavaScript 工具”用于安装您选择的工具。仅运行 EITR 的桌面栏、启动器或主题并不需要 Java、Flutter 和数据库客户端。“安装 > 数据库”提供可选的数据库工具。“安装 > 开发者应用”提供 Bruno、Cursor、GitHub Desktop、Insomnia、JetBrains Toolbox、Meld、Postman、VS Code 和 Zed；“安装 > 办公效率”提供 1Password、Bitwarden、Discord、LibreOffice、Obsidian、Slack 和 Thunderbird。AUR 条目在您的机器上下载并构建；某些许可证不允许 EITR 直接分发它们。

“开发语言”还提供 **mise (多运行时管理器)** 作为可选 Arch 软件包。在 `~/.zshrc` 中添加 `eval "$(mise activate zsh)"` 以手动启用它；针对同一运行时它可能与 nvm/uv 产生冲突。现有的按语言管理器保持不变。

## 网页应用

“安装 > 网页应用 > 创建网页应用”会提示输入名称和地址，并添加一个在其独立窗口中打开该网站的启动器。创建时仅通过 HTTP(S) 下载网站图标。格式错误的清单或不可用的图标会后备回退到页面图标或通用浏览器图标。

切勿在地址中包含登录凭据。启动器和图标使用您的 XDG 数据目录（包括自定义的 `XDG_DATA_HOME`）；通过任意菜单进行移除均使用相同的存储位置。网页应用需要 Chrome、Chromium、Edge、Brave 或 Vivaldi（安装 > 浏览器）；包含 DRM 的流媒体网站（如 Netflix）需要 Chrome。在“安装 > 网页应用”或“应用”菜单中按 Delete 即可移除。

当存在多个浏览器配置文件时，创建网页应用会询问在哪个配置文件中打开；如需更改，请移除该应用并重新添加。

“安装 > 浏览器”还提供 Brave (AUR)。“安装 > 办公效率”提供 Basecamp 和 Notion 作为可选的网页应用。这些方案仅包含名称和 URL；网站图标在您安装时于本机下载。未预装任何内容。

## AI 助手

打开“设置 > AI 助手”以选择您的默认助手、管理账户和“助手权限”，或在同意后允许助手协同工作。“开发 > AI”保留会话启动器。

**SUPER + A** 在您的主文件夹中打开助手，在安全受支持的场合信任该文件夹，并通过受支持的额外指令选项传递手册指南。“开发 > AI”会询问文件夹（从主文件夹开始），并在该位置像其自身命令一样打开助手。CLI 限制列在 distro/ASSISTANT-STARTUP.md 中。只读快速问答包含 Eitr 入门指南和相关的本地化手册摘录；在手册未涵盖相关问题时会明确指出。

[herdr](https://herdr.dev) 是一款用于并排运行 AI 编程 Agent 的终端，随 Eitr 一同提供：在首次登录时（以及现有桌面的下次登录时），Eitr 在后台运行 herdr 的官方安装程序，该程序会验证下载并将 `herdr` 放置在 `~/.local/bin` 中。在没有网络连接时，它会在以后的登录中重试。一旦安装完成便不会重复安装，因此将其移除后会保持移除状态。使用 `herdr update` 更新它。“Walker > 学习 > Herdr 命令”列出其按键和命令，“Walker > 开发 > Agent 工作区”在终端中打开 herdr 或 cmux。

每个云端助手在“开发 > AI”下都有一个“账户”子菜单。“默认”使用现有配置和登录信息，无需移动文件。“添加账户…”提示输入标签，显示审核内容，然后在受支持的情况下通过隐私浏览器窗口打开 CLI 自身的登录界面（未知的浏览器使用其常规打开方式）。按 Enter 确认；按 Esc 取消。

选择一个账户可以手动切换未来的交互式会话、“咨询 AI”和只读辅助工具；正在运行的会话保留其原有账户。经确认后，“删除”会移除添加的账户及其本地配置；“默认”无法移除。移除当前选定的账户会返回到“默认”，且绝不会将另一个账户注销。Antigravity 仅提供“默认”，因为其 CLI 不支持配置文件目录覆盖。

Ratatoskr 拥有一个本地账户。账户标签和选择保存在本机的 `eitr/ai-accounts.json` (0600) 中；独立的文件夹位于 `$XDG_DATA_HOME/eitr/ai-accounts/` (0700) 下。“AI 使用量”按助手将可读账户分组，并隐藏不可读或不受支持的用量数据。各分段在登录时初始处于关闭状态，并在会话期间保留其打开或关闭状态。

“开发 > AI”为每个已安装的助手提供菜单：Antigravity CLI、Claude Code、Codex、Gemini CLI、GitHub Copilot CLI、Grok Build、OpenCode 和 Pi。可从“安装 > AI CLI”安装它们；如果未安装任何助手，“开发 > AI”会链接到此处。

会话菜单将**新建**排在首位，随后按字母顺序排列其他操作。Claude Code 和 GitHub Copilot CLI 提供**新建命名会话**、**继续上次**、**恢复选择器**以及按名称或 ID 恢复（Claude 将其标记为**按名称恢复**）。Codex 提供**继续上次**、**恢复选择器**和**按名称或 ID 恢复**。Gemini CLI 提供**继续上次**、Walker **恢复选择器**和**按编号恢复**；最后一个选项会在终端中显示编号会话列表，然后再提示输入编号。

Grok Build 提供**继续上次**、Walker **恢复选择器**和**按 ID 或标题恢复**。OpenCode 通过其会话 ID 选项提供**继续上次**、Walker **恢复选择器**、**按 ID 恢复**和**新建命名会话**：新名称创建会话，现有 ID 则恢复会话。Antigravity CLI 提供**继续上次**和**按 ID 恢复**，不支持会话列表或命名选项。

Pi 仅保留**新建**，因为会话选项无法从现有的软件包文档中得到确认。Walker 选择器在可用时显示会话标题和日期；空列表显示提示信息。空的名称/ID 提示会取消操作。“账户”子菜单依然可用。

打开 LazyVim 或 VS Code 项目首先会提示选择文件夹，从您的主文件夹开始（隐藏文件夹被排除）：选择文件夹以深入子目录，选择“打开”以使用当前所在的文件夹，选择“返回”以上升一级，或者在顶层返回菜单。键入可在当前所在文件夹下方深度达六层的目录中搜索所有文件夹，跳过 `node_modules`、`target`、`build`、`dist`、`venv` 和 `__pycache__`，完全同名的文件夹优先列出，浅层文件夹排在深层文件夹之前；AI 菜单的文件夹步骤采用相同的机制。

Antigravity CLI、Claude Code、Codex、Gemini CLI、GitHub Copilot CLI、Grok Build、OpenCode 和 Pi 也可以通过命令启动。如果缺少某个工具，Eitr 会进行解释并提供与“安装 > AI CLI”相同的安装流程。按 Enter 确认安装；按 Esc 取消。在非交互式终端中，命令退出并输出安装说明。已安装的二进制文件优先于这些启动器。请通过每个工具自身的工作流登录；未捆绑任何助手二进制文件或凭据。

“开发 > AI > 默认助手”为此计算机选择一个已安装的助手。**SUPER + A** 在终端中打开它；如果没有默认助手，则打开选择器。SUPER + A 打开的助手默认拥有完整访问权限：它可以更改文件并运行命令而无需询问。从“开发 > AI”打开的助手保留其常规权限提示。

选择**设置 > AI 助手 > 助手权限 > 更改前询问**以恢复常规权限提示。该首选项仅存储在本机的 `eitr/ai.json` 中。组织限制会强制执行权限提示。Sudo 仍然需要输入密码。无外壳协作和语音提醒保持只读模式。

主题更改仅更新现有、可读的 Claude Code、Gemini CLI 和 Grok Build 设置中的浅色/深色主题设置。其他设置和格式保持不变。缺少、损坏或未安装的客户端会被跳过；没有受支持浅色/深色设置的助手遵循其终端的颜色。

已安装的 SDK 版本和安装程序来源在发行版清单中进行维护。请以实际选择器为准，不要假设手册中的示例是对最新上游版本的保证。工具链安装可能需要下载。

### OpenCode、Pi 与 Eitr 技能

“安装 > AI CLI”还提供 **OpenCode**（`opencode`，Arch 官方软件包）和 **Pi**（`pi`，npm 软件包 `@mariozechner/pi-coding-agent`）。两者都拥有“开发 > AI”菜单、首次使用命令启动器以及 SUPER + A 的默认助手选项。OpenCode 使用 `--auto` 获取完全访问权限。其“账户”菜单仅提供“默认”：其配置目录覆盖无法隔离凭据。Pi 通过 `PI_CODING_AGENT_DIR` 支持独立账户，并通过 `--append-system-prompt` 接收手册指南。Pi 没有内置权限提示；在“更改前询问”模式下或在组织限制下，Eitr 会拒绝其交互式启动。两者都不是只读协作辅助工具。

打包的 **Eitr** 技能指导如何安全地进行桌面更改并指向本离线手册。当启用技能发现时，`eitr-config seed` 将相同源复制到 Claude Code 的 `~/.claude/skills/eitr/SKILL.md` 以及 Codex、Gemini CLI 和 OpenCode 的 `~/.agents/skills/eitr/SKILL.md`。`eitr-config update` 刷新未编辑的副本，保留用户创建或编辑的副本，并将更改的默认值写入 `.eitr-new` 以供审核。现有安装在登录时接收缺失的技能。每个 CLI 的启动指令保持活动状态；不执行登录操作。

### Ratatoskr（本地，实验性）

“开发 > AI > 默认助手”始终提供 **Ratatoskr（本地，实验性）**，它不需要账户或订阅。首次使用时，终端会在更改任何内容之前说明一次性下载内容：Arch 软件包 `ollama`（约 15 MB）和语言模型 `qwen3:4b`（约 2.5 GB，Apache-2.0 许可证）。一次确认（按 Enter 确认；按 Esc 取消）将安装软件包、创建用户服务 `eitr-ollama.service`、下载模型（附带可见进度）并将其设为默认。如果某一步骤失败，其输出保留在屏幕上并保留先前的默认设置。

一切内容均保留在本机上：服务仅监听 `127.0.0.1:11434`，在需要时启动，并将其模型保存在 `~/.local/share/eitr/ollama` 中。它明显不如云端助手稳定，尤其是在遇到不寻常的措辞时，并且在处理器上运行较慢。语音提醒像对待其他任何助手一样检查其回答，因此错误的回答不会更改任何内容。**SUPER + A** 打开与模型的聊天；输入 `/bye` 可关闭。它绝不作为助手协同工作的辅助工具，也没有“AI 使用量”条目。

在同一菜单中选择 **Ratatoskr** 并按 **Delete**。移除会提示确认一次，然后删除服务和模型，重置默认设置（如果原先是本地），并卸载 `ollama`（如果是安装程序安装的）。Ollama 自身在 `~/.ollama` 中的密钥和聊天记录予以保留。

## 监控

“开发 > 监控”让您的仪表盘触手可及。**添加仪表盘**提示输入服务（Grafana、Datadog、Sentry、New Relic、Prometheus 或“其他”）、名称及其地址，随后仪表盘可直接从菜单在浏览器中打开。它们仅保存在本机计算机的 `~/.config/eitr/monitoring.json` 中；按 Delete 可移除一个。切勿在地址中包含密码或令牌。

**监控工具**安装命令行工具：Prometheus 的 `promtool` 和 Sentry CLI。Amazon Managed Grafana 工作区位于“云 > AWS > 您的账户 > Grafana”下，与其他 AWS 工具并列。

## 账户与云工作流

AI 使用量需要已安装/配置的客户端；请通过其常规工作流登录。账户配额和企业/API 计费可能与受支持的个人账户面板有所不同。EITR 中未捆绑任何凭据。

云菜单使用您本地的提供商账户/配置文件。AWS 配置文件来自本地 AWS 配置或已配置的 EITR 云配置文件映射。Google Cloud 列出已命名的 gcloud 配置及其账户和项目。没有项目的配置在打开资源工具时会提示您选择一个，因此在项目发现之前登录功能依然可用。

Azure 列出启用的订阅及其租户 ID。在选择工具之前请先选择上下文：Google Cloud 和 Azure 工具在其上下文菜单内部搜索，而不是从全局搜索中搜索。打开 Google 上下文会清除无关的继承项目覆盖；没有项目的配置会要求您为资源工具选择一个项目。

终端返回会保留上下文以及您为无项目配置选择的项目，而无需切换全局 CLI 默认设置。“登录”、“检查认证”和“刷新”位于每个检测到的上下文内部。Google 登录针对其配置的账户；Azure 登录针对其租户，并在身份验证后恢复先前的默认订阅。Azure 刷新更新其订阅缓存并显示选定的订阅。

AWS 账户必须在 AWS 配置文件（`~/.aws/config`，或设置了 `AWS_CONFIG_FILE` 时）中具有匹配的 `[default]` 或 `[profile NAME]` 节。仅在凭据文件中找到的配置文件将被排除，设置了 `endpoint_url`（即使是空值）的配置配置文件（包括嵌套的服务设置和引用的 `[services NAME]` 组）也会被排除，因为它们可能以与 S3 兼容的服务（如 Cloudflare R2）为目标。`EITR_AWS_PROFILES` 可以为符合条件的配置文件添加标签或进行限制，但无法包含已排除的配置文件。EITR 不会编辑任何一个 AWS 文件。

每个提供商菜单均提供**添加 AWS 账户**、**添加 GCP 账户**或**添加 Azure 账户**，因此您可以根据需要设置多个账户，例如公司的开发和生产环境。它首先要求输入名称，然后以该名称运行提供商 CLI 自身的安装程序：通过 AWS SSO (IAM Identity Center) 或访问密钥配置 AWS 配置文件、带有登录和项目的独立 gcloud 配置，或者由您命名其订阅的 Azure 登录。

缺失的 `gcloud` 或 `az` 会优先提示安装。按 **Ctrl+R** 可重命名账户。名称保存在 `~/.config/eitr/cloud-contexts.json` 中（以 AWS 配置文件、gcloud 配置或订阅 ID 为键）；EITR 不会推断环境或在其中存储凭据，“添加”也绝不会切换全局 CLI 默认设置。Grafana 和云操作需要其对应的账户和权限。

某些操作是只读的；其他操作可以修改远程资源——在确认之前请仔细审核请求的操作和账户。

请将令牌、`.env` 密钥和凭据保留在共享的 dotfiles 和屏幕截图之外。Shell 配置加载受支持的管理器，而无需安装程序重写您的配置文件。“学习”保留专用的 LazyVim、tmux 和 cmux 参考。

## 助手协同工作

“开发 > AI > 允许助手协同工作”默认关闭。启用它可连接已安装且看似已登录的 Claude Code、Codex、Copilot、Grok 和 Gemini CLI 客户端。每次交接均使用辅助工具的订阅或 API 计费，并计入其限额。其他客户端仅使用 API 密钥和仅使用密钥环的登录无法被检测到。

仅当存在非空的 `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`，或者在 `~/.gemini/settings.json` 中将 `security.auth.selectedType` 设置为 `gemini-api-key` 或 `vertex-ai` 时，才能检测到 Gemini。个人 Google 登录不计入：Google 不再支持此服务。Gemini 在方案模式下无头运行，排除了 MCP 服务器和扩展。Eitr 已使用免费 API 密钥对其进行了测试：只读问题以及通过桥接传递的问题均得到了回答。方案模式文档记录为只读；Eitr 尚未独立验证其文件、shell 或方案文件行为。

让您的助手咨询另一个助手以进行审核、解释或提出建议。通过发起调用的助手的常规工具提示批准每次交接；Eitr 绝不预先批准这些工具。切勿为助手服务器启用自动工具批准。辅助工具仅执行读取；编辑操作仍由您的主助手完成。辅助工具无法咨询另一个辅助工具。通知会指明谁向谁发起了咨询，且每次请求有三分钟的超时时间。辅助工具读取调用方的当前工作目录；其问题和上下文可能会发送给该助手的提供商。

该开关通过每个助手自有的命令（`claude mcp add`、`codex mcp add`、`copilot mcp add`、`grok mcp add`、`gemini mcp add -s user`）注册一个 `assistants` MCP 服务器，因此每个助手都会写入其自有的设置。具有相同名称的现有服务器保持不变并予以报告。更改仅记录在本机的 `~/.local/state/eitr/assistants.json`（或 `XDG_STATE_HOME`）中。关闭该开关会精确移除 Eitr 的条目；如果某个条目在此后被编辑过，Eitr 会保留它并报告冲突。

更改开关后请重启现有的助手会话。真实账户的交接仍有待单独的端到端验证。

Antigravity CLI (`agy`) 可通过“安装 > AI CLI”和首次使用启动器供个人 Google 账户使用。它绝不捆绑随附。它通过 Google 官方安装程序进行安装（安装程序会验证下载），并且您使用 Google 账户登录。它尚未作为助手协同工作的辅助工具提供。已安装的 `agy` 可以正常启动。

Gemini CLI 需要 Gemini API 密钥或 Google Cloud/企业账户。Antigravity 不是协作辅助工具：无外壳模式甚至拒绝读取操作。其唯一的解锁方式是绕过权限或更改全局规则。当按运行提供权限控制或只读无外壳模式可用时，Eitr 将重新考虑它。

### 其他提供商

“开发 > 云”还列出 Cloudflare (`wrangler`)、DigitalOcean (`doctl`)、Hetzner Cloud (`hcloud`)、Oracle Cloud (`oci`)、Vercel、Netlify 和 IBM Cloud (`ibmcloud`)。使用包含数字或短横线的小写名称添加账户。这些账户是位于 `~/.config/eitr/cloud-accounts/<provider>/<name>` 下的专用工作区；绝不会导入现有的提供商配置。选定的提供商和工作区在工具选择器和终端中保持可见。从终端返回到同一个工作区；按 Shift+Backspace 返回到账户列表。选择工作区绝不会切换全局 CLI 默认设置。

缺失的 `wrangler`、`doctl` 和 `hcloud` 可从 Arch 官方仓库提供（`doctl` 和 `hcloud` 在 extra 仓库中）。Oracle Cloud 和 IBM Cloud 使用来自 `distro/installers.json` 的官方 HTTPS shell 安装程序；Oracle 传递 `--accept-all-defaults`。Vercel (`vercel`) 和 Netlify (`netlify-cli`，命令为 `netlify`) 使用现有的 NVM/npm 安装方案。安装需要确认。登录和账户操作仅在选定的私有工作区内运行。

DigitalOcean 和 Hetzner 列出原生上下文；Oracle 列出该工作区 `~/.oci/config` 中的配置文件。选择其上下文/配置文件会保存本地选择并使用针对单条命令的参数标志，而不会更改全局默认设置。Vercel 和 Netlify 提供其原生切换操作；随后输入选定的团队/账户标签。Vercel 还会在登录前提示输入作用域，并在后续命令中传递 `--scope TEAM`。

IBM 提供 SSO 和 API 密钥登录，显示 `ibmcloud target`，并以明确的账户和区域为目标。返回菜单时，选定的上下文/配置文件/作用域/账户以及保存的区域保持可见。这些标签属于本地选择，并非经验证的远程身份。不继承现有的凭据和提供商覆盖项。浏览器控制台使用各自独立的会话；在操作前请仔细核对账户。

这七个私有工作区提供商使用中立的资源和操作图标，并附带简短说明。账户按字母顺序排在最前，随后是“添加账户”；工具按其翻译后的名称按字母顺序排序。选择器显示选定的账户、上下文和保存的区域，且每个只读报告都会在其输出上方重复该上下文。报告保留共享的 AWS 分页器；不引入额外的资源命令或日志搜索。

| 提供商 | 登录命令 | 列出 / 切换 / 命令上下文 |
| --- | --- | --- |
| Cloudflare | `wrangler login` | — |
| DigitalOcean | `doctl auth init --context NAME` | `doctl auth list`; `doctl auth switch --context NAME`; `--context NAME` |
| Hetzner Cloud | `hcloud context create NAME` | `hcloud context list`; `hcloud context use NAME`; `--context NAME` |
| Oracle Cloud | `oci session authenticate --profile-name NAME --region REGION` | `~/.oci/config`; `--profile NAME --auth security_token` |
| Vercel | `vercel login` | `vercel switch`; `--scope TEAM` |
| Netlify | `netlify login` | `netlify switch` |
| IBM Cloud | `ibmcloud login --sso`; `ibmcloud login --apikey` | `ibmcloud target`; `ibmcloud target -c ACCOUNT -r REGION` |

云导航使用真实的 Elephant 菜单。Shift+Backspace 返回上级菜单：服务或资源选择返回到包含它的菜单，账户菜单返回到提供商的账户列表，该列表返回到“云”。选定的账户和上下文保持可见。Eitr 将此导航选择保存在 `~/.config/eitr/cloud-navigation.json` 中；提供商 CLI 默认设置保持不变。报告保留其分页器，日志搜索保留 fzf，设置流程保留其经过审核的终端表单。自由文本搜索提示依然在 Walker 中接受文本输入；它们不是导航列表。

在账户行上按 Delete 键或在其菜单内部选择**删除账户**即可删除账户。确认提示会指明提供商和账户：它会在本机计算机上移除该提供商针对该账户的登录信息，而不会影响远程账户。取消操作不会更改任何内容。仅移除选定的 Eitr 私有账户文件夹；拒绝符号链接、位于其提供商根目录外部的路径以及正在运行 Eitr 操作的账户。AWS、Azure 和 Google Cloud 没有新的删除操作。确认窗口在 Walker 内部打开，带有“取消”和“确认”；不打开终端。

只读报告使用选定的私有账户环境和现有的云分页器。Cloudflare：账户、R2 存储桶、D1 数据库、KV 命名空间、Pages 项目、队列。DigitalOcean：Droplet、应用、数据库、Kubernetes、卷、域名、负载均衡器、余额。Hetzner：服务器、卷、网络、防火墙、负载均衡器、主 IP、快照。Oracle：区间、实例、存储桶、VCN。Vercel：项目、部署、域名。

Netlify：状态、网站。IBM：账户、目标、资源组、服务实例。DigitalOcean 和 Hetzner 始终传递所选上下文；Oracle 传递所选配置文件和安全令牌身份验证，仅从该账户的私有配置文件中读取租户信息。存储桶列表首先读取其命名空间。Vercel 传递所选的团队作用域。错误保持易读，且绝不会触发使用另一个账户重试。

日志搜索保留现有的 fzf 查看器。使用真实账户进行的实时检查仍处于挂起状态。

云账户、Git 账户（“添加”和“编辑”）、监控仪表盘和网页应用的设置表单在左侧列出步骤，在右侧列出当前回答。使用方向键或 Tab 键选择步骤，按 Enter 进行回答。“检查确认”在应用任何更改前列出每项回答；按向左箭头或方向键可返回某个步骤，使用 PgUp/PgDn 可滚动长篇审核内容。

按 Esc 或 Ctrl+C 取消且不保存。提供商登录在审核后开始；失败或中断的登录会丢弃新账户。Google Cloud 在登录前会提示输入可选的项目 ID；Azure 在登录前会提示输入可选的订阅标签，否则保留每个订阅的现有名称。Vercel 在登录前提示输入其作用域。

## Docker

Docker、docker-compose 和 Lazydocker 已预装，但 Docker 服务默认关闭。使用 `sudo systemctl enable --now docker.service` 启用它。

如果 `docker ps` 报告权限不足，请使用 `sudo usermod -aG docker $USER` 将您的用户添加到 docker 组。成为 docker 组成员等同于获取 root 权限。注销并重新登录，或在一个终端中使用 `newgrp docker`。使用 `id -nG` 检查您的所属组。
