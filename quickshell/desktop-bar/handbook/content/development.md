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

Development > AI offers Default Assistant and a menu for each installed assistant: Claude Code, Codex, Gemini CLI, Grok Build and GitHub Copilot CLI. Install them from Install > AI CLIs; with none installed, Development > AI links there.

Starting a session, or opening a LazyVim or VS Code project, first asks for a
folder under `~/Development`: pick folders to go deeper, Open to use the one
you are in, and Back to go up a level or, at the top, return to the menu.

Claude Code, Codex, Gemini CLI, Grok Build and GitHub Copilot CLI (`copilot`) can also be started by command. If a tool is missing, Eitr explains it and offers the same installation as Install > AI CLIs. Type `yes` to install; Enter cancels. Without an interactive terminal, the command exits with installation instructions. Installed binaries take precedence over these launchers. Sign in through each tool’s own workflow; no assistant binaries or credentials are bundled.

Development > AI > Default Assistant selects one installed assistant for this computer. **SUPER + Alt + A** opens it in a terminal; without a default, it opens the chooser. Eitr uses each assistant’s normal permission prompts.

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
to connect installed Claude Code, Codex, Copilot and Grok clients that appear
signed in. The
confirmation names the assistants and explains that each hand-off uses the
helper’s subscription and counts toward its limits. API-key-only and
keyring-only sign-ins are not detected. Gemini is not offered: Google no
longer serves Gemini CLI for personal accounts.

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
`grok mcp add`), so each assistant writes its own settings. An existing server with the same name is left unchanged
and reported. Changes
are recorded only on this computer in `~/.local/state/eitr/assistants.json`
(or `XDG_STATE_HOME`). Turning the switch off removes exactly Eitr’s entries;
if an entry was edited afterwards, Eitr keeps it and reports the conflict.
Restart existing assistant sessions after changing the switch. Real-account
hand-offs still await separate end-to-end verification.
