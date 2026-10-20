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
Install > Developer Apps offers Bruno, GitHub Desktop, Insomnia, JetBrains
Toolbox, Meld, Postman, VS Code and Zed; Install > Productivity offers
1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack and Thunderbird.
AUR entries download and build on your machine; some licenses do not allow
EITR to ship them.

## Web apps

Install > Web Apps > Create Web App asks for a name and an address and adds a
launcher that opens the site in its own window. The site's icon is downloaded
when you create it, only over HTTP(S). Malformed manifests or unavailable icons
fall back to page icons or a generic browser icon. Do not put login credentials
in the address. Launchers and icons use your XDG data directory, including a
custom `XDG_DATA_HOME`; removal through either menu uses that same location.
Web apps need Chrome or Chromium (Install > Browsers);
streaming sites with DRM, such as Netflix, need Chrome. Remove one with Delete
in Install > Web Apps or in the Apps menu.

## AI assistants

Development > AI offers a menu for each installed assistant: Claude Code, Codex, Gemini CLI, Grok Build and GitHub Copilot CLI. Install them from Install > AI CLIs; with none installed, Development > AI links there.

Starting a session, or opening a LazyVim or VS Code project, first asks for a
folder under `~/Development`: pick folders to go deeper, Open to use the one
you are in, and Back to go up a level or, at the top, return to the menu.

Claude Code, Codex, Gemini CLI, Grok Build and GitHub Copilot CLI (`copilot`) can also be started by command. If a tool is missing, Eitr explains it and offers the same installation as Install > AI CLIs. Type `yes` to install; Enter cancels. Without an interactive terminal, the command exits with installation instructions. Installed binaries take precedence over these launchers. Sign in through each tool’s own workflow; no assistant binaries or credentials are bundled.

Development > Default Assistant selects one installed assistant for this computer. **SUPER + Alt + A** opens it in a terminal; without a default, it opens the chooser. Eitr uses each assistant’s normal permission prompts.

Theme changes update only the light/dark theme setting in existing, readable Claude Code, Gemini CLI and Grok Build settings. Other settings and formatting stay intact. Missing, broken or uninstalled clients are skipped; assistants without a supported light/dark setting follow their terminal’s colors.

Installed SDK versions and installer sources are maintained in distro manifests.
Follow the actual picker rather than assuming a handbook example is a promise
about the newest upstream version. Toolchain installation may need downloads.

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

Each provider menu starts with **Add AWS Account**, **Add GCP Account** or
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
extensions excluded. It is not yet tested by Eitr; report problems with
Report a Problem. A real-account test remains open for a paid key or company
account. Plan mode is documented as read-only; Eitr has not independently
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

Development > Cloud also lists Cloudflare (`wrangler`), DigitalOcean (`doctl`), Hetzner Cloud (`hcloud`), Oracle Cloud (`oci`), Vercel, Netlify and IBM Cloud (`ibmcloud`). Add an account using a lowercase name with digits or dashes. These accounts are private workspaces under `~/.config/eitr/cloud-accounts/<provider>/<name>`; existing provider configurations are never imported. The chosen provider and workspace remain visible in the tool picker and terminal. Return from a terminal to the same workspace; Escape returns to the account list. Selecting a workspace never switches a global CLI default.

Missing `wrangler`, `doctl` and `hcloud` are offered from Arch's official repositories (`doctl` and `hcloud` in extra). Oracle Cloud and IBM Cloud use their official HTTPS shell installers from `distro/installers.json`; Oracle passes `--accept-all-defaults`. Vercel (`vercel`) and Netlify (`netlify-cli`, command `netlify`) use the existing NVM/npm installation recipe. Installation requires confirmation. Sign-in and account actions run only inside the selected private workspace. DigitalOcean and Hetzner list native contexts; Oracle lists profiles from that workspace's `~/.oci/config`. Selecting their context/profile saves a local selection and uses per-command flags, without changing a global default. Vercel and Netlify expose their native switch action; enter the selected team/account label afterward. Vercel also asks for a scope after login and passes `--scope TEAM` on subsequent commands. IBM provides SSO and API-key sign-in, displays `ibmcloud target`, and targets an explicit account and region. The selected context/profile/scope/account and saved region remain visible when returning to the menu. These labels are local selections, not verified remote identities. Existing credentials and provider overrides are not inherited. Browser consoles use their own sessions; check the account before acting. Resource views and remote identity/project verification remain open; no live sign-in or installation was tested.

| Provider | Sign in | List / switch / command context |
| --- | --- | --- |
| Cloudflare | `wrangler login` | — |
| DigitalOcean | `doctl auth init --context NAME` | `doctl auth list`; `doctl auth switch --context NAME`; `--context NAME` |
| Hetzner Cloud | `hcloud context create NAME` | `hcloud context list`; `hcloud context use NAME`; `--context NAME` |
| Oracle Cloud | `oci session authenticate --profile-name NAME --region REGION` | `~/.oci/config`; `--profile NAME --auth security_token` |
| Vercel | `vercel login` | `vercel switch`; `--scope TEAM` |
| Netlify | `netlify login` | `netlify switch` |
| IBM Cloud | `ibmcloud login --sso`; `ibmcloud login --apikey` | `ibmcloud target`; `ibmcloud target -c ACCOUNT -r REGION` |

Cloud resource reports now use a pager for reading; they do not choose a resource or trigger an operation. Log and event searches keep fzf. Resource choices that control the next action remain Walker lists.
