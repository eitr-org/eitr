# Development tools

Main > Development groups **AI**, **Cloud**, **Git Accounts**, **Monitoring**, **LazyVim** and
**VS Code**. Project selectors open the chosen directory in the editor; theme
integration updates supported open editors, including LazyVim sessions.

**Git Accounts** configures a default GitHub/GitLab identity, per-folder
overrides, SSH keys and separate provider CLI logins. Every rule change needs a
preview confirmation; it never rewrites project remotes or changes global CLI
accounts. See [Git Accounts](handbook:git-accounts).

## Optional toolchains

Install > Development Languages and JavaScript Tools install the tools you
choose. Java, Flutter and database clients are not required just to run EITR's
bar, launcher or themes. Install > Databases offers optional database tools.
Install > Developer Apps offers Bruno, Cursor, GitHub Desktop, Insomnia, JetBrains
Toolbox, Meld, Postman, VS Code and Zed; Install > Productivity offers
1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack and Thunderbird.
AUR entries download and build on your machine; some licenses do not allow
EITR to ship them.

Languages also offers **mise (many runtimes)** as an optional Arch package. Enable it manually with `eval "$(mise activate zsh)"` in `~/.zshrc`; it can conflict with nvm/uv for the same runtime. Existing per-language managers remain unchanged.

## Web apps

Install > Web Apps > Create Web App asks for a name and an address and adds a
launcher that opens the site in its own window. The site's icon is downloaded
when you create it, only over HTTP(S). Malformed manifests or unavailable icons
fall back to page icons or a generic browser icon. Do not put login credentials
in the address. Launchers and icons use your XDG data directory, including a
custom `XDG_DATA_HOME`; removal through either menu uses that same location.
Web apps need Chrome, Chromium, Edge, Brave or Vivaldi (Install > Browsers);
streaming sites with DRM, such as Netflix, need Chrome. Remove one with Delete
in Install > Web Apps or in the Apps menu.

With several browser profiles, creating a web app asks which profile it opens in; to change it, remove and add the app again.

Install > Browsers also offers Brave (AUR). Install > Productivity offers Basecamp and Notion as optional web apps. These recipes contain only a name and URL; the site icon is downloaded on your machine when you install. Nothing is preinstalled.

## AI assistants

Assistants open in your home folder. **SUPER + A** also trusts that folder where safely supported and passes Handbook guidance through supported extra instruction options; Development > AI opens an assistant as its own command would. CLI limitations are listed in distro/ASSISTANT-STARTUP.md. Read-only quick chat includes an Eitr primer and relevant localized Handbook excerpts; it says when the Handbook does not cover a question.

Each cloud assistant has an Accounts submenu under Development > AI. Default uses the existing configuration and login without moving files. Add Account… asks for a label, shows a review, then opens the CLI’s own sign-in with a private browser window where supported (unknown browsers use their normal opener). Enter confirms; Esc cancels. Select an account to switch future interactive sessions, Ask the AI and read-only helpers manually; running sessions keep their account. Delete removes an added account and its local configuration after confirmation; Default cannot be removed. Removing the selected account returns to Default and never logs another account out. Antigravity offers only Default because its CLI has no supported config-folder override. Ratatoskr has one local account. Account labels and selection stay on this PC in `eitr/ai-accounts.json` (0600); separate folders live under `$XDG_DATA_HOME/eitr/ai-accounts/` (0700). AI Usage groups readable accounts by assistant and hides unreadable or unsupported usage. Sections start closed at login and keep their open or closed state for the session.

Development > AI offers a menu for each installed assistant: Antigravity CLI, Claude Code, Codex, Gemini CLI, GitHub Copilot CLI, Grok Build, OpenCode and Pi. Install them from Install > AI CLIs; with none installed, Development > AI links there.

Opening a LazyVim or VS Code project first asks for a
folder under `~/Development`: pick folders to go deeper, Open to use the one
you are in, and Back to go up a level or, at the top, return to the menu.

Antigravity CLI, Claude Code, Codex, Gemini CLI, GitHub Copilot CLI, Grok Build, OpenCode and Pi can also be started by command. If a tool is missing, Eitr explains it and offers the same installation as Install > AI CLIs. Enter confirms installation; Esc cancels. Without an interactive terminal, the command exits with installation instructions. Installed binaries take precedence over these launchers. Sign in through each tool’s own workflow; no assistant binaries or credentials are bundled.

Development > Default Assistant selects one installed assistant for this computer. **SUPER + A** opens it in a terminal; without a default, it opens the chooser. The SUPER + A assistant opens with full access by default: it can change files and run commands without asking. Assistants opened from Development > AI keep their normal permission prompts. Choose **System > Security > Assistant Access > Ask before changes** to restore normal permission prompts. The preference is stored only on this PC in `eitr/ai.json`. Organization restrictions force permission prompts. Sudo still requires your password. Headless collaboration and voice reminders remain read-only.

Theme changes update only the light/dark theme setting in existing, readable Claude Code, Gemini CLI and Grok Build settings. Other settings and formatting stay intact. Missing, broken or uninstalled clients are skipped; assistants without a supported light/dark setting follow their terminal’s colors.

Installed SDK versions and installer sources are maintained in distro manifests.
Follow the actual picker rather than assuming a handbook example is a promise
about the newest upstream version. Toolchain installation may need downloads.

### OpenCode, Pi and the Eitr skill

Install > AI CLIs also offers **OpenCode** (`opencode`, official Arch package) and **Pi** (`pi`, npm package `@mariozechner/pi-coding-agent`). Both have Development > AI menus, first-use command launchers and Default Assistant choices for SUPER + A. OpenCode uses `--auto` for full access. Its Accounts menu offers only Default: its config-directory override does not isolate credentials. Pi supports separate accounts through `PI_CODING_AGENT_DIR` and receives the Handbook guidance through `--append-system-prompt`. Pi has no built-in permission prompts; Eitr refuses its interactive launch in Ask before changes mode or under organization restrictions. Neither is a read-only collaboration helper.

The packaged **Eitr** skill teaches safe desktop changes and points to this offline Handbook. `eitr-config seed` copies the same source to `~/.claude/skills/eitr/SKILL.md` for Claude Code and `~/.agents/skills/eitr/SKILL.md` for Codex, Gemini CLI and OpenCode when skill discovery is enabled. `eitr-config update` refreshes unedited copies, keeps user-created or edited copies, and writes changed defaults to `.eitr-new` for review. Existing installations receive missing skills at login. Per-CLI startup instructions remain active; no sign-in is performed.

### Ratatoskr (local, experimental)

Development > Default Assistant always offers **Ratatoskr (local, experimental)**, which needs no account or subscription. The first time, a terminal explains the one-time downloads before anything changes: the Arch package `ollama` (about 15 MB) and the language model `qwen3:4b` (about 2.5 GB, Apache-2.0 licence). One confirmation (Enter confirms; Esc cancels) installs the package, creates the user service `eitr-ollama.service`, downloads the model with visible progress and makes it the default. If a step fails, its output stays on screen and the previous default is kept.

Everything stays on this PC: the service listens only on `127.0.0.1:11434`, starts when needed and keeps its models in `~/.local/share/eitr/ollama`. It is noticeably less reliable than the cloud assistants, especially with unusual phrasing, and slower on the processor. Voice reminders check its answers like any other assistant's, so a wrong answer changes nothing. **SUPER + A** opens a chat with the model; `/bye` closes it. It is never a helper for assistants working together and has no AI Usage entry.

Select **Ratatoskr** in the same menu and press **Delete**. Removal asks once, then deletes the service and the models, resets the default if it was local and uninstalls `ollama` if setup installed it. Ollama's own key and chat history in `~/.ollama` are kept.

## Monitoring

Development > Monitoring keeps your dashboards one search away. **Add Dashboard**
asks for the service (Grafana, Datadog, Sentry, New Relic, Prometheus or Other),
a name and its address, and the dashboard then opens in your browser from the
menu. They are saved only on this computer, in `~/.config/eitr/monitoring.json`;
Delete removes one. Never put passwords or tokens in an address.

**Monitoring Tools** installs command-line tools: Prometheus's `promtool` and the
Sentry CLI. Amazon Managed Grafana workspaces are under Cloud > AWS > your
account > Grafana, with the other AWS tools.

## Accounts and cloud workflows

AI usage requires an installed/configured client; sign in through its normal
workflow. Account quotas and enterprise/API billing may differ from supported
personal-account panels. No credentials are bundled in EITR.

Cloud menus use your local provider accounts/profiles. AWS profiles come from
the local AWS configuration or configured EITR cloud profile mapping. Google
Cloud lists named gcloud configurations with their account and project. A
configuration without a project asks you to choose one when opening resource
tools, so Login remains accessible before project discovery. Azure lists enabled
subscriptions with their tenant IDs. Select a context before choosing a tool:
Google Cloud and Azure tools are searched inside their context menu, not from
global search. Opening a Google context clears unrelated inherited project
overrides; configurations without a project ask you to select one for resource
tools. Terminal returns retain the context, and the project you picked
for a configuration without one, without switching global CLI defaults. Login, Check Auth and
Refresh live inside each detected context. Google Login targets its configured
account; Azure Login targets its tenant and restores the previous default
subscription after authentication. Azure Refresh updates its subscription cache
and displays the selected subscription.

AWS accounts must have a matching `[default]` or `[profile NAME]` section in the AWS config file (`~/.aws/config`, or `AWS_CONFIG_FILE` when set). Profiles found only in the credentials file are excluded, as are config profiles that set `endpoint_url` (even an empty value), including nested service settings and referenced `[services NAME]` groups, because they may target S3-compatible services such as Cloudflare R2. `EITR_AWS_PROFILES` can label or restrict eligible profiles, but cannot include excluded ones. EITR does not edit either AWS file.

Each provider menu offers **Add AWS Account**, **Add GCP Account** or
**Add Azure Account**, so you can set up as many accounts as you need, for
example a company's Development and Production. It asks for a name first, then
runs the provider CLI's own setup under that name: an AWS profile through AWS SSO
(IAM Identity Center) or access keys, a separate gcloud configuration with its
sign-in and project, or an Azure sign-in whose subscriptions you name. A missing
`gcloud` or `az` is offered for installation first. **Ctrl+R** renames an account.
Names live in `~/.config/eitr/cloud-contexts.json` (keyed by AWS profile, gcloud
configuration or subscription ID); EITR does not infer environments or store
credentials there, and Add never switches a global CLI default. Grafana
and cloud operations need their corresponding accounts and permissions. Some
actions are read-only; others can modify remote resources—review the requested
operation and account before confirming.

Keep tokens, `.env` secrets and credentials outside shared dotfiles and
screenshots. Shell configuration loads supported managers without installers
rewriting your profiles. Learn retains dedicated LazyVim, tmux and cmux references.

## Assistants working together

Development > AI > Let assistants work together is off by default. Enable it
to connect installed Claude Code, Codex, Copilot, Grok and Gemini CLI clients
that appear signed in. Each hand-off uses the helper's subscription or API
billing and counts toward its limits. Other clients' API-key-only and
keyring-only sign-ins are not detected.

Gemini is detected only with a non-empty `GEMINI_API_KEY` or `GOOGLE_API_KEY`,
or `security.auth.selectedType` set to `gemini-api-key` or `vertex-ai` in
`~/.gemini/settings.json`. Personal Google sign-in does not count: Google no
longer serves it. Gemini runs headlessly in plan mode, with MCP servers and
extensions excluded. Eitr has tested it with a free API key: a read-only question
and a question passed through the bridge both answered. Plan mode is documented as read-only; Eitr has not independently
verified its file, shell or plan-file behavior.

Ask your assistant to consult the other one for a review, explanation or
suggestion. Approve each hand-off through the calling assistant’s normal tool
prompt; Eitr never pre-approves these tools. Do not enable automatic tool
approval for the assistants server. Helpers only read; edits stay with your
main assistant. A helper cannot ask another helper. A notification identifies
who asked whom, and each request has a three-minute timeout. The helper reads
the caller’s current working directory; its question and context may be sent
to that assistant’s provider.

The switch registers one `assistants` MCP server through each assistant's own
command (`claude mcp add`, `codex mcp add`, `copilot mcp add` and
`grok mcp add`, `gemini mcp add -s user`), so each assistant writes its own settings. An existing server with the same name is left unchanged
and reported. Changes
are recorded only on this computer in `~/.local/state/eitr/assistants.json`
(or `XDG_STATE_HOME`). Turning the switch off removes exactly Eitr’s entries;
if an entry was edited afterwards, Eitr keeps it and reports the conflict.
Restart existing assistant sessions after changing the switch. Real-account
hand-offs still await separate end-to-end verification.

Antigravity CLI (`agy`) is available for personal Google accounts through Install > AI CLIs and the first-use launcher. It is never bundled. It installs through Google's official installer, which verifies its download, and you sign in with your Google account. It is not yet offered as an assistants-together helper. An already installed `agy` can be launched normally. Gemini CLI requires a Gemini API key or a Google Cloud/company account. Antigravity is not a collaboration helper: headless mode denies even reads. Its only unlocks bypass permissions or change global rules. Eitr will reconsider it when per-run permissions or a read-only headless mode are available.

### Additional providers

Development > Cloud also lists Cloudflare (`wrangler`), DigitalOcean (`doctl`), Hetzner Cloud (`hcloud`), Oracle Cloud (`oci`), Vercel, Netlify and IBM Cloud (`ibmcloud`). Add an account using a lowercase name with digits or dashes. These accounts are private workspaces under `~/.config/eitr/cloud-accounts/<provider>/<name>`; existing provider configurations are never imported. The chosen provider and workspace remain visible in the tool picker and terminal. Return from a terminal to the same workspace; Shift+Backspace returns to the account list. Selecting a workspace never switches a global CLI default.

Missing `wrangler`, `doctl` and `hcloud` are offered from Arch's official repositories (`doctl` and `hcloud` in extra). Oracle Cloud and IBM Cloud use their official HTTPS shell installers from `distro/installers.json`; Oracle passes `--accept-all-defaults`. Vercel (`vercel`) and Netlify (`netlify-cli`, command `netlify`) use the existing NVM/npm installation recipe. Installation requires confirmation. Sign-in and account actions run only inside the selected private workspace. DigitalOcean and Hetzner list native contexts; Oracle lists profiles from that workspace's `~/.oci/config`. Selecting their context/profile saves a local selection and uses per-command flags, without changing a global default. Vercel and Netlify expose their native switch action; enter the selected team/account label afterward. Vercel also asks for a scope before login and passes `--scope TEAM` on subsequent commands. IBM provides SSO and API-key sign-in, displays `ibmcloud target`, and targets an explicit account and region. The selected context/profile/scope/account and saved region remain visible when returning to the menu. These labels are local selections, not verified remote identities. Existing credentials and provider overrides are not inherited. Browser consoles use their own sessions; check the account before acting.

The seven private-workspace providers use neutral resource and action icons with short descriptions. Accounts appear first in alphabetical order, followed by Add Account; tools are sorted alphabetically by their translated names. The picker shows the selected account, context and saved region, and each read-only report repeats that context above its output. Reports retain the shared AWS pager; no additional resource commands or log searches are introduced.

| Provider | Sign in | List / switch / command context |
| --- | --- | --- |
| Cloudflare | `wrangler login` | — |
| DigitalOcean | `doctl auth init --context NAME` | `doctl auth list`; `doctl auth switch --context NAME`; `--context NAME` |
| Hetzner Cloud | `hcloud context create NAME` | `hcloud context list`; `hcloud context use NAME`; `--context NAME` |
| Oracle Cloud | `oci session authenticate --profile-name NAME --region REGION` | `~/.oci/config`; `--profile NAME --auth security_token` |
| Vercel | `vercel login` | `vercel switch`; `--scope TEAM` |
| Netlify | `netlify login` | `netlify switch` |
| IBM Cloud | `ibmcloud login --sso`; `ibmcloud login --apikey` | `ibmcloud target`; `ibmcloud target -c ACCOUNT -r REGION` |

Cloud navigation uses real Elephant menus. Shift+Backspace goes to the previous menu: a service or resource choice returns to its containing menu, the account menu returns to the provider’s account list, and that list returns to Cloud. The selected account and context remain visible. Eitr stores this navigation selection in `~/.config/eitr/cloud-navigation.json`; provider CLI defaults stay unchanged. Reports keep their pager, log searches keep fzf, and setup keeps its reviewed terminal forms. Free-text search prompts still accept text in Walker; they are not navigation lists.

Delete an account with the Delete key on its account row or **Delete Account** inside its menu. The confirmation names the provider and account: it removes that provider’s sign-in for that account on this computer, without affecting the remote account. Cancellation changes nothing. Only the selected Eitr private account folder is removed; symbolic links, paths outside its provider root and accounts with a running Eitr action are refused. AWS, Azure and Google Cloud have no new deletion action. The confirmation opens inside Walker with Cancel and Confirm; no terminal opens.

Read-only reports use the selected private account environment and the existing cloud pager. Cloudflare: Account, R2 Buckets, D1 Databases, KV Namespaces, Pages Projects, Queues. DigitalOcean: Droplets, Apps, Databases, Kubernetes, Volumes, Domains, Load Balancers, Balance. Hetzner: Servers, Volumes, Networks, Firewalls, Load Balancers, Primary IPs, Snapshots. Oracle: Compartments, Instances, Buckets, VCNs. Vercel: Projects, Deployments, Domains. Netlify: Status, Sites. IBM: Account, Target, Resource Groups, Service Instances. DigitalOcean and Hetzner always pass the chosen context; Oracle passes the chosen profile and security-token authentication, reading the tenancy only from that account’s private profile. Bucket listing first reads its namespace. Vercel passes the selected team scope. Errors remain readable and never trigger a retry with another account. Log searches retain the existing fzf viewer. Live checks with real accounts remain pending.

Setup forms for cloud accounts, Git Accounts (Add and Edit), monitoring dashboards and web apps list their steps on the left and the current answer on the right. Use arrows or Tab to select a step and Enter to answer it. Review lists every answer before applying anything; return to a step with Left or the arrows, and use PgUp/PgDn to scroll long reviews. Esc or Ctrl+C cancels without saving. Vendor sign-in starts after review; failed or interrupted sign-in discards the new account. Google Cloud asks for an optional project ID before sign-in; Azure asks for an optional subscription label before sign-in and otherwise keeps each subscription’s existing name. Vercel asks for its scope before sign-in.

## Docker

Docker, docker-compose and Lazydocker are installed, but the Docker service is off by default. Enable it with `sudo systemctl enable --now docker.service`.

If `docker ps` reports permission denied, add your user with `sudo usermod -aG docker $USER`. Membership in the docker group is root-equivalent. Log out and back in, or use `newgrp docker` in one terminal. Check your groups with `id -nG`.
