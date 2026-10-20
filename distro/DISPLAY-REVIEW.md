# Display review

Scope: `walker/`, `elephant/`, `quickshell/desktop-bar/scripts/` and `distro/`.
Line numbers identify launch/render call sites, not private runtime output. Tests,
package names, generated legacy-layout hashes, comments and incidental “less” words
are excluded. Shared launchers are included alongside their consumers. Review uses
source inspection only; no cloud CLI, live settings, package install or desktop UI
was exercised. “Current” records the pre-change view; “Changed” describes this patch.

Use Walker for choices that drive another operation; use existing native panels
for equivalent desktop status/settings. Use fzf for searching long logs/events and
text; use the existing cloud pager for passive reports. Keep terminals for vendor
login, typed forms, privileged confirmation and readable task failures.

| Place (source lines) | Current view | Proposed view | Reason |
| --- | --- | --- | --- |
| `walker/bin/menu-path/kitty` (15, 25) | Shared terminal launcher/presenter | Keep | Shared task banner, floating window behavior and failure retention are intentional. |
| `walker/scripts/actions/about.sh` (18) | Persistent informational terminal | Keep; open: native About presentation | Output stays readable; replacing its layout is a design decision, not a picker correction. |
| `walker/scripts/actions/assistant-collaboration.py` (41) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `walker/scripts/actions/development/git-accounts.py` (440, 441) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `walker/scripts/actions/development/open-project.sh` (45) | Interactive terminal/editor or fzf file search | Keep | Terminal/editor is the requested application; fzf searches long file content rather than settings. |
| `walker/scripts/actions/install/software.py` (46, 47, 48, 213, 369, 408, 439, 453, 461) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `walker/scripts/actions/share/localsend-share.sh` (17) | Terminal launch or output helper | Keep; open: inspect native parity before migration | No demonstrated equivalent native panel; preserve current interaction pending targeted review. |
| `walker/scripts/actions/system/crash-help.py` (83, 84) | Held assistant terminal | Keep | Diagnostic explanation remains readable after the assistant exits. |
| `walker/scripts/actions/system/dotfiles.sh` (9) | Terminal launch or output helper | Keep; open: inspect native parity before migration | No demonstrated equivalent native panel; preserve current interaction pending targeted review. |
| `walker/scripts/actions/system/update-channel.py` (16) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `walker/scripts/menus/ai-tools.sh` (71, 74, 79, 82, 87, 90, 95, 98, 101, 104, 108) | Terminal launch or output helper | Keep; open: inspect native parity before migration | No demonstrated equivalent native panel; preserve current interaction pending targeted review. |
| `walker/scripts/menus/cloud/aws/cloudfront.sh` (34, 41, 48, 61, 69) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/cloudwatch.sh` (117, 134, 139, 144, 149, 156, 160) | fzf logs/events and shared terminal/pager helpers | Keep searchable text; open: non-log resource viewers | Search, preview and copying suit long text. Shared helpers retain error handling and readable fallback. |
| `walker/scripts/menus/cloud/aws/cognito.sh` (35, 42, 46, 53, 60, 68, 75) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/docdb.sh` (35, 42, 46, 53, 60, 73, 81) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/ec2.sh` (22, 29, 33, 40, 44, 51, 55, 62, 66, 73) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/ecr.sh` (45, 52, 65, 74, 83, 93) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/ecs.sh` (97, 121, 150, 180, 204, 256, 266, 280, 297, 300, 303, 306, 309, 312, 315, 318) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/grafana.sh` (34, 41, 59) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/iam.sh` (37, 47, 54, 58, 65, 69, 76, 80, 87, 94, 102) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/lambda.sh` (74, 80, 87, 94, 100, 106, 111) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/lightsail.sh` (21, 28, 32, 39, 43, 50, 54, 61) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/menu.sh` (23, 33, 72, 82) | Walker choices; CLI output/login terminal; some fzf text | Keep; open: resource status → native panel or Walker after schema review | Provider-specific output and authentication require context; native cloud panels do not exist. |
| `walker/scripts/menus/cloud/aws/rds.sh` (69, 76, 81, 88, 96, 112, 133, 143) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/route53.sh` (34, 41, 48, 56, 63) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/s3.sh` (45, 52, 60, 77, 90, 99) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/aws/terminal-helpers.sh` (17, 31, 32, 35, 50) | fzf logs/events and shared terminal/pager helpers | Keep searchable text; open: non-log resource viewers | Search, preview and copying suit long text. Shared helpers retain error handling and readable fallback. |
| `walker/scripts/menus/cloud/aws/vpc.sh` (36, 43, 50, 58, 65, 73, 80, 88, 95, 103) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/acr.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/aks.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/app-service.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/compute.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/functions.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/logs.sh` (17, 25) | fzf logs/events and shared terminal/pager helpers | Keep searchable text; open: non-log resource viewers | Search, preview and copying suit long text. Shared helpers retain error handling and readable fallback. |
| `walker/scripts/menus/cloud/azure/menu.sh` (15, 25, 34, 38, 63, 70, 79, 87, 91) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/resource-groups.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/sql.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/storage.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/azure/vnet.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/common.sh` (97, 135, 182, 184) | Walker choices; CLI output/login terminal; some fzf text | Keep; open: resource status → native panel or Walker after schema review | Provider-specific output and authentication require context; native cloud panels do not exist. |
| `walker/scripts/menus/cloud/gcp/artifact-registry.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/gcp/cloud-run.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/gcp/compute.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/gcp/functions.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/gcp/gke.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/gcp/iam.sh` (11, 18) | Walker choices; CLI output/login terminal; some fzf text | Keep; open: resource status → native panel or Walker after schema review | Provider-specific output and authentication require context; native cloud panels do not exist. |
| `walker/scripts/menus/cloud/gcp/logs.sh` (17, 25) | fzf logs/events and shared terminal/pager helpers | Keep searchable text; open: non-log resource viewers | Search, preview and copying suit long text. Shared helpers retain error handling and readable fallback. |
| `walker/scripts/menus/cloud/gcp/menu.sh` (15, 25, 34, 38, 63, 70, 79, 87, 91) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/gcp/sql.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/gcp/storage.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/gcp/vpc.sh` (11, 18) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/cloud/providers.py` (66, 70, 71, 77, 122, 123) | New Walker account and tool lists; held CLI help/login terminal | Changed: confirmed local deletion and read-only views in the existing pager | Selection belongs in Walker; login, deletion confirmation and vendor help use a terminal. Resource commands are limited to the reviewer-verified list. |
| `walker/scripts/menus/cloud/terminal-helpers.sh` (56, 57, 59, 60, 71, 74, 81, 90, 107, 113, 118, 121, 124, 133) | fzf resource reports; Walker choices; terminals | Changed: resource reports → existing pager; keep Walker choices and log search | These fzf pipelines only printed a highlighted row; no action consumed the selection. Reports need readable output. |
| `walker/scripts/menus/shortcuts.sh` (124, 127, 166, 169) | Interactive terminal/editor or fzf file search | Keep | Terminal/editor is the requested application; fzf searches long file content rather than settings. |
| `walker/scripts/themes/generate.sh` (10) | Terminal launch or output helper | Keep; open: inspect native parity before migration | No demonstrated equivalent native panel; preserve current interaction pending targeted review. |
| `walker/scripts/themes/kitty.sh` (6, 59, 65) | Terminal launch or output helper | Keep; open: inspect native parity before migration | No demonstrated equivalent native panel; preserve current interaction pending targeted review. |
| `elephant/aws-profile-entries.lua` (8, 11) | Terminal launch or output helper | Keep; open: inspect native parity before migration | No demonstrated equivalent native panel; preserve current interaction pending targeted review. |
| `elephant/cloud-context-entries.lua` (4, 11) | Terminal launch or output helper | Keep; open: inspect native parity before migration | No demonstrated equivalent native panel; preserve current interaction pending targeted review. |
| `elephant/menu-rows/battery-limit.json` (7, 15, 23, 31, 39) | Walker rows opening task terminals with --hold | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/factory-reset.json` (13, 27, 40) | Walker rows opening task terminals with --hold | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/fido2.json` (7, 15) | Walker rows opening task terminals | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/fingerprint.json` (7, 15) | Walker rows opening task terminals | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/network-backend.json` (7, 15, 23) | Walker rows opening task terminals | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/power.json` (35) | Walker rows opening task terminals | Keep task/read-output terminal | Installation, maintenance, sharing and diagnostic output needs prompts or time to read; these rows already use Walker for choice. |
| `elephant/menu-rows/remote-away.json` (7, 15, 23, 31, 39, 47, 55) | Walker rows opening task terminals | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/remote-share.json` (7, 15, 23, 31, 39, 47, 55, 63, 71) | Walker rows opening task terminals | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/security.json` (38, 46, 54) | Walker rows opening task terminals with --hold | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/share.json` (21, 33) | Walker rows opening task terminals | Keep task/read-output terminal | Installation, maintenance, sharing and diagnostic output needs prompts or time to read; these rows already use Walker for choice. |
| `elephant/menu-rows/shortcuts.json` (98, 106, 138) | Walker rows opening task terminals | Keep task/read-output terminal | Installation, maintenance, sharing and diagnostic output needs prompts or time to read; these rows already use Walker for choice. |
| `elephant/menu-rows/snapshots.json` (13, 21, 37, 45, 53, 82) | Walker rows opening task terminals with --hold | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/style.json` (69) | Walker rows opening task terminals | Keep task/read-output terminal | Installation, maintenance, sharing and diagnostic output needs prompts or time to read; these rows already use Walker for choice. |
| `elephant/menu-rows/system-information.json` (52) | Walker rows opening task terminals with --hold | Keep task/read-output terminal | Installation, maintenance, sharing and diagnostic output needs prompts or time to read; these rows already use Walker for choice. |
| `elephant/menu-rows/system-maintenance.json` (38) | Walker rows opening task terminals with --hold | Keep task/read-output terminal | Installation, maintenance, sharing and diagnostic output needs prompts or time to read; these rows already use Walker for choice. |
| `elephant/menu-rows/terminal.json` (5) | Walker terminal preferences | Keep Walker settings | Kitty is named as the terminal application; this row is a preference, not a report. |
| `elephant/menu-rows/tpm-unlock.json` (7, 15, 23) | Walker rows opening task terminals with --hold | Keep setup/confirmation terminal; open: status rows → existing panel where equivalent | Privileged operations and recovery output need readable errors. Native status parity and hardware need separate verification. |
| `elephant/menu-rows/update-advanced.json` (7, 15, 23) | Walker rows opening task terminals | Keep task/read-output terminal | Installation, maintenance, sharing and diagnostic output needs prompts or time to read; these rows already use Walker for choice. |
| `elephant/menu-rows/update.json` (26) | Walker rows opening task terminals | Keep task/read-output terminal | Installation, maintenance, sharing and diagnostic output needs prompts or time to read; these rows already use Walker for choice. |
| `elephant/menus/git-accounts.lua` (5, 13) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `elephant/menus/monitoring.lua` (14, 21) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `elephant/menus/projects-nvim.lua` (12) | Walker project choice opens terminal editor | Keep | The terminal hosts the requested editor, rather than an output picker. |
| `elephant/menus/update-channel.lua` (15, 26, 29) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `elephant/menus/webapps.lua` (6, 18) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `quickshell/desktop-bar/scripts/updates-notify.sh` (18) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |
| `distro/lib/eitr_assistants.py` (87) | Walker choices with task/form terminal | Keep | The list selects the task; terminal handles installation, typed values, authentication or diagnostics. |

The search also matched Kitty configuration generation, cursor shader probes,
layout manifests and default-package metadata. These do not display results and
are excluded: `style/fonts.py`, `style/terminal-effects.py`, `display-settings.py`,
`distro/bin/eitr-config`, `distro/defaults/kitty/kitty.conf`,
`distro/layout-manifest.json`, `distro/lib/{adoption,generated,layout}.py` and
`distro/user-defaults.json`.

The changes replace 60 passive report pipelines in 33 cloud scripts. Other
occurrences in those files (resource selectors, logs and detailed reports) keep
their existing behavior.

## Open decisions and offline gaps

- Cloud status has no existing native panel. Do not invent one or parse unknown
  output simply to remove a terminal. AWS/GCP/Azure authentication and complex
  event/object viewers retain their existing view pending interaction review.
- Snapshot, security, battery and remote-access status may benefit from native
  panels only after parity and hardware review. Their setup/confirmation terminals
  remain necessary. About remains a readable terminal pending a design decision.
- All seven providers now have concrete sign-in actions. The six additional
  providers use the reviewer-verified vendor commands recorded in the Handbook.
  DigitalOcean and Hetzner list contexts, Oracle lists private configuration
  profiles, and IBM displays its target. Context/profile selection stays local
  and commands pass `--context` / `--profile` (Oracle also uses
  `--auth security_token`); Vercel uses `--scope` after explicit team selection.
  Vercel/Netlify native switching and IBM targeting run only inside the selected
  private workspace. No global default is changed merely to navigate.
- `doctl` and `hcloud` are Arch extra packages. Oracle and IBM official HTTPS
  installer URLs are in `distro/installers.json`, invoked through
  `download_run` / `installer_url` (Oracle: `--accept-all-defaults`); downloads
  and redirects require HTTPS. Vercel and Netlify use the existing NVM/npm
  recipe (`vercel`, `netlify-cli`). Installer and command facts were supplied
  from the reviewer's official-documentation verification, not guessed offline.
- Still untested: live installs/sign-ins, remote identity/project verification,
  and remote resource verification with real accounts. Read-only resource views
  and confirmed private-account deletion are implemented for the seven new providers.
  Tests use mocks and temporary directories;
  no owner cloud configuration or account was accessed. The source display
  review is accepted; native presentation improvements above remain future work.
- Private workspaces isolate HOME, XDG paths, cwd and inherited provider variables.
  They deliberately do not discover or import existing owner accounts. Workspace
  labels do not prove remote identity; browser consoles have their own sessions.

## Verification

- `bash tools/check.sh`: all seven stages passed (existing skips retained), plus Node, syntax, ShellCheck, Qt 6 QML lint,
  whitespace and structured-data checks.
- `python3 tools/i18n-build.py --check`: passed for all five languages.
- `python3 quickshell/desktop-bar/scripts/handbook-build.py --check`: passed.
- New untracked provider Python/JSON files were also parsed explicitly, since
  the syntax/data stages discover tracked files. Provider tests run through the
  normal Walker test discovery, with mocks and temporary account directories.
- User systemd bus access was denied by the sandbox; the full gate ran directly.
  No installs, account commands, real cloud configuration access, commits or
  desktop service changes were performed.

## Changed files

The full preserved working tree contains these changed/new files, including the
accepted display changes from the previous pass and generated catalogs. No
commit or staging operation was performed.

- `TODO.md`
- `distro/DISPLAY-REVIEW.md`
- `distro/installers.json`
- `distro/layout-manifest.json`
- `distro/software.json`
- `elephant/menu-rows/cloud.json`
- `elephant/menus/cloudflare-contexts.lua`
- `elephant/menus/digitalocean-contexts.lua`
- `elephant/menus/hetzner-contexts.lua`
- `elephant/menus/ibm-contexts.lua`
- `elephant/menus/netlify-contexts.lua`
- `elephant/menus/oracle-contexts.lua`
- `elephant/menus/vercel-contexts.lua`
- `i18n/catalogs/de/helpers.json`
- `i18n/catalogs/de/menus.json`
- `i18n/catalogs/de/menus.lua`
- `i18n/catalogs/en/helpers.json`
- `i18n/catalogs/en/menus.json`
- `i18n/catalogs/en/menus.lua`
- `i18n/catalogs/es/helpers.json`
- `i18n/catalogs/es/menus.json`
- `i18n/catalogs/es/menus.lua`
- `i18n/catalogs/fr/helpers.json`
- `i18n/catalogs/fr/menus.json`
- `i18n/catalogs/fr/menus.lua`
- `i18n/catalogs/pt_BR/helpers.json`
- `i18n/catalogs/pt_BR/menus.json`
- `i18n/catalogs/pt_BR/menus.lua`
- `i18n/locales/de/LC_MESSAGES/eitr.mo`
- `i18n/locales/de/LC_MESSAGES/eitr.po`
- `i18n/locales/en/LC_MESSAGES/eitr.mo`
- `i18n/locales/en/LC_MESSAGES/eitr.po`
- `i18n/locales/es/LC_MESSAGES/eitr.mo`
- `i18n/locales/es/LC_MESSAGES/eitr.po`
- `i18n/locales/fr/LC_MESSAGES/eitr.mo`
- `i18n/locales/fr/LC_MESSAGES/eitr.po`
- `i18n/locales/pt_BR/LC_MESSAGES/eitr.mo`
- `i18n/locales/pt_BR/LC_MESSAGES/eitr.po`
- `i18n/pending-helpers.json`
- `i18n/sources.json`
- `quickshell/desktop-bar/handbook/catalog.json`
- `quickshell/desktop-bar/handbook/catalogs/de.json`
- `quickshell/desktop-bar/handbook/catalogs/es.json`
- `quickshell/desktop-bar/handbook/catalogs/fr.json`
- `quickshell/desktop-bar/handbook/catalogs/pt_BR.json`
- `quickshell/desktop-bar/handbook/content/de/development.md`
- `quickshell/desktop-bar/handbook/content/de/source-hashes.json`
- `quickshell/desktop-bar/handbook/content/development.md`
- `quickshell/desktop-bar/handbook/content/es/development.md`
- `quickshell/desktop-bar/handbook/content/es/source-hashes.json`
- `quickshell/desktop-bar/handbook/content/fr/development.md`
- `quickshell/desktop-bar/handbook/content/fr/source-hashes.json`
- `quickshell/desktop-bar/handbook/content/pt_BR/development.md`
- `quickshell/desktop-bar/handbook/content/pt_BR/source-hashes.json`
- `walker/scripts/actions/install/development.sh`
- `walker/scripts/actions/install/software.py`
- `walker/scripts/menus/cloud/aws/cloudfront.sh`
- `walker/scripts/menus/cloud/aws/cognito.sh`
- `walker/scripts/menus/cloud/aws/docdb.sh`
- `walker/scripts/menus/cloud/aws/ec2.sh`
- `walker/scripts/menus/cloud/aws/ecr.sh`
- `walker/scripts/menus/cloud/aws/ecs.sh`
- `walker/scripts/menus/cloud/aws/grafana.sh`
- `walker/scripts/menus/cloud/aws/iam.sh`
- `walker/scripts/menus/cloud/aws/lambda.sh`
- `walker/scripts/menus/cloud/aws/lightsail.sh`
- `walker/scripts/menus/cloud/aws/rds.sh`
- `walker/scripts/menus/cloud/aws/route53.sh`
- `walker/scripts/menus/cloud/aws/s3.sh`
- `walker/scripts/menus/cloud/aws/vpc.sh`
- `walker/scripts/menus/cloud/azure/acr.sh`
- `walker/scripts/menus/cloud/azure/aks.sh`
- `walker/scripts/menus/cloud/azure/app-service.sh`
- `walker/scripts/menus/cloud/azure/compute.sh`
- `walker/scripts/menus/cloud/azure/functions.sh`
- `walker/scripts/menus/cloud/azure/menu.sh`
- `walker/scripts/menus/cloud/azure/resource-groups.sh`
- `walker/scripts/menus/cloud/azure/sql.sh`
- `walker/scripts/menus/cloud/azure/storage.sh`
- `walker/scripts/menus/cloud/azure/vnet.sh`
- `walker/scripts/menus/cloud/gcp/artifact-registry.sh`
- `walker/scripts/menus/cloud/gcp/cloud-run.sh`
- `walker/scripts/menus/cloud/gcp/compute.sh`
- `walker/scripts/menus/cloud/gcp/functions.sh`
- `walker/scripts/menus/cloud/gcp/gke.sh`
- `walker/scripts/menus/cloud/gcp/menu.sh`
- `walker/scripts/menus/cloud/gcp/sql.sh`
- `walker/scripts/menus/cloud/gcp/storage.sh`
- `walker/scripts/menus/cloud/gcp/vpc.sh`
- `walker/scripts/menus/cloud/providers.json`
- `walker/scripts/menus/cloud/providers.py`
- `walker/tests/test_extra_cloud_providers.py`
- `walker/tests/test_software.py`
- `walker/tests/test_update_workflow.py`
- `walker/themes/current/item_menus-cloudflare-contexts.xml`
- `walker/themes/current/item_menus-digitalocean-contexts.xml`
- `walker/themes/current/item_menus-hetzner-contexts.xml`
- `walker/themes/current/item_menus-ibm-contexts.xml`
- `walker/themes/current/item_menus-netlify-contexts.xml`
- `walker/themes/current/item_menus-oracle-contexts.xml`
- `walker/themes/current/item_menus-vercel-contexts.xml`

## Private account deletion and resource reports

The seven new providers expose Delete on account rows and Delete Account inside
an account. Confirmation names the provider and account and explains that only
its sign-in on this computer is removed, leaving the remote account unaffected.
Cancellation changes nothing. Deletion is limited to that private account folder;
symlinks, paths outside the provider root, the current working folder and accounts
locked by a running Eitr action are refused. AWS, Azure and Google Cloud are unchanged.

All requested read-only views run with the existing private HOME/XDG environment
and cwd. DigitalOcean/Hetzner use explicit contexts, Oracle uses an explicit
profile with security-token authentication and its own profile's tenancy, and
Vercel uses a selected team scope. Oracle buckets first resolve the namespace;
a failed lookup never proceeds to listing. Reports and command errors use the
existing cloud pager without credential fallback. Existing log/fzf views remain.
Live checks with real accounts are the remaining provider work.

Validation for this follow-up uses mocked CLI execution and temporary accounts,
including cancellation, symlink and active-action refusal, replaced-directory
refusal, explicit context flags, Oracle tenancy/namespace scoping, Vercel without
a selected team, and readable command failures without credential retries.
The full repository gate and both catalog build/check pairs pass.

## Shared terminal setup wizard

The terminal setup forms now reuse `distro/lib/eitr_wizard.py`, extracted from
`distro/archinstall/installer-ui.py`. The installer retains its original
`collect()` sequence, Norse palette, renderer, filtering, validation, back/cancel
rules, default Cancel selection and final typed disk confirmation. Setup forms
add independent step navigation and a Review screen: arrows/Tab select a step,
Enter edits it, Left/Tab returns from editing, and Esc/Ctrl+C cancels. Text,
masked secrets, validated defaults, optional text and filterable choices share
one renderer. Review masks secrets, shows every answer (PgUp/PgDn scrolls), and
allows returning to any step before applying. Required unanswered steps and
invalid drafts cannot be applied.

Converted flows:

- AWS Add Account: name, profile ID, SSO/access-key method.
- Google Cloud Add Account: name, configuration ID, optional project ID.
- Azure Add Account: tenant and optional subscription label; blank retains each
  subscription's name. Subscription discovery follows vendor sign-in.
- Cloudflare, DigitalOcean, Hetzner Cloud, Oracle Cloud, Vercel, Netlify and IBM
  Cloud Add Account: private workspace name; Oracle also collects region and
  Vercel scope before sign-in.
- IBM Cloud target selection: account and region reviewed together.
- Git Accounts Add Account: provider, label, author, email, hostname, optional
  existing SSH key, default choice and optional folder rule.
- Git Accounts Edit: label, author and email.
- Development > Monitoring > Add Dashboard: service, name and URL.
- Install > Web Apps > Create Web App: name, URL and optional icon URL.

AWS, Google Cloud and Azure vendor writes are staged in private temporary
configuration paths after review and published only after successful sign-in.
Failure or interruption discards staging and restores environment variables.
AWS uses a temporary HOME for SSO cache writes. Existing files are checked for
concurrent changes before publishing; symlinked configuration trees are refused.
The seven private-workspace providers create no folder until review succeeds;
failed/interrupted sign-in removes the new workspace and newly created parent
folders. Vendor-controlled browser/token prompts still run after review.
Missing CLI installation is offered after review.

Inventory: searched Walker scripts for `input(`, `read -r -p`, `read -rp`, all
shell `read` statements, `getpass`, and Terminal `ask`/`choose`/`confirm` helpers.
The following remain as they are:

- Cloud rename and native context/profile selection: one local answer each.
- Git folder assignment: one path plus its existing save confirmation; Git
  import, account changes and CLI login retain their single confirmation.
- SSH key generation: `ssh-keygen` owns the passphrase prompts.
- Factory reset, TPM/Secure Boot/security actions, battery limit, remote access,
  network backend/reboot, firewall, home snapshots, update/cleanup and assistant
  collaboration: independent yes/no or typed safety confirmations.
- Report Problem: a repeated action menu for an already generated report,
  rather than a multi-question setup form.
- Task failure/close pauses, cloud pagers and About: acknowledgement only.
- Cloud resource pickers and fzf search: browsing existing resources, not setup.
- Theme scripts' `read` statements: parsing generated data, not user questions.

Packaging: the existing runtime `distro/lib/**` layout rule already installs the
shared module under `/usr/share/eitr/lib`; an explicit rule names its owner.
The ISO exports the repository, including `distro/lib`, and archinstall's existing
`eitr_bootstrap.py` symlink resolves there. No extra payload copy, PKGBUILD change
or ISO build change is necessary.

Verification uses mocked screens, key sequences, subprocesses and temporary
homes with `walker/tests/home_isolation.py`. Existing installer tests remain
unchanged; additional tests assert the original step order, validators, review
contents, Cancel/Continue selection and typed disk confirmation, plus setup
navigation, filtering, defaults, validation, secret masking and cancellation.
Provider tests cover staged publication and rollback on failure/interruption,
and cancellation/failed sign-in for all seven private workspace providers.
No cloud/account CLI, account configuration, terminal launcher or desktop was
used for live verification. Handbook chapters and helper catalogs cover English,
Brazilian Portuguese, Spanish, German and French.

Files changed for the shared-wizard conversion (including generated catalogs):

- `distro/DISPLAY-REVIEW.md`
- `distro/archinstall/installer-ui.py`
- `distro/layout-manifest.json`
- `distro/lib/eitr_wizard.py`
- `i18n/catalogs/de/helpers.json`
- `i18n/catalogs/en/helpers.json`
- `i18n/catalogs/es/helpers.json`
- `i18n/catalogs/fr/helpers.json`
- `i18n/catalogs/pt_BR/helpers.json`
- `i18n/locales/de/LC_MESSAGES/eitr.mo`
- `i18n/locales/de/LC_MESSAGES/eitr.po`
- `i18n/locales/en/LC_MESSAGES/eitr.mo`
- `i18n/locales/en/LC_MESSAGES/eitr.po`
- `i18n/locales/es/LC_MESSAGES/eitr.mo`
- `i18n/locales/es/LC_MESSAGES/eitr.po`
- `i18n/locales/fr/LC_MESSAGES/eitr.mo`
- `i18n/locales/fr/LC_MESSAGES/eitr.po`
- `i18n/locales/pt_BR/LC_MESSAGES/eitr.mo`
- `i18n/locales/pt_BR/LC_MESSAGES/eitr.po`
- `i18n/pending-helpers.json`
- `i18n/sources.json`
- `quickshell/desktop-bar/handbook/catalog.json`
- `quickshell/desktop-bar/handbook/catalogs/de.json`
- `quickshell/desktop-bar/handbook/catalogs/es.json`
- `quickshell/desktop-bar/handbook/catalogs/fr.json`
- `quickshell/desktop-bar/handbook/catalogs/pt_BR.json`
- `quickshell/desktop-bar/handbook/content/de/development.md`
- `quickshell/desktop-bar/handbook/content/de/git-accounts.md`
- `quickshell/desktop-bar/handbook/content/de/source-hashes.json`
- `quickshell/desktop-bar/handbook/content/development.md`
- `quickshell/desktop-bar/handbook/content/es/development.md`
- `quickshell/desktop-bar/handbook/content/es/git-accounts.md`
- `quickshell/desktop-bar/handbook/content/es/source-hashes.json`
- `quickshell/desktop-bar/handbook/content/fr/development.md`
- `quickshell/desktop-bar/handbook/content/fr/git-accounts.md`
- `quickshell/desktop-bar/handbook/content/fr/source-hashes.json`
- `quickshell/desktop-bar/handbook/content/git-accounts.md`
- `quickshell/desktop-bar/handbook/content/pt_BR/development.md`
- `quickshell/desktop-bar/handbook/content/pt_BR/git-accounts.md`
- `quickshell/desktop-bar/handbook/content/pt_BR/source-hashes.json`
- `walker/scripts/actions/development/git-accounts.py`
- `walker/scripts/actions/development/monitoring.py`
- `walker/scripts/actions/install/webapps.py`
- `walker/scripts/menus/cloud/accounts.py`
- `walker/scripts/menus/cloud/providers.py`
- `walker/tests/test_cloud_accounts.py`
- `walker/tests/test_extra_cloud_providers.py`
- `walker/tests/test_git_accounts.py`
- `walker/tests/test_setup_wizard.py`

Final results for this conversion:

- `bash tools/check.sh`: all seven stages passed; 1,097 Python tests across
  eight suites, with the existing skips retained, plus the Node checks.
- `python3 tools/i18n-build.py` and `--check`: passed.
- `python3 quickshell/desktop-bar/scripts/handbook-build.py` and `--check`: passed.
- Both new Python files were parsed explicitly; `git diff --check` passed.
- No commit, staging or push was performed.

## AWS reference comparison for the seven private-workspace providers

AWS was traced from its Elephant profile entries and shared row layout through
`aws/menu.sh`, every resource script and both shared terminal-helper layers.
The comparison below covers the existing commands only. Account entries remain
above Add Account, ordered by name; tool rows sort by translated label before
icons are prepended. These providers have no additional resource subfolders to
sort. AWS's legacy service-specific menu order is not copied over the repository's
folder-first, alphabetical convention.

| Provider | Structure against AWS | Icons against AWS | Description examples |
| --- | --- | --- | --- |
| AWS reference | Profile list → services → existing resource views; profile in picker and terminal header | Resource-specific glyphs; plus for Add Account | Short resource titles and terminal headers, such as EC2 instances and S3 buckets |
| Cloudflare | Private account list → six reports plus existing account actions | AWS bucket-list folder, neutral database, account, project and queue glyphs | Object storage buckets; SQL databases; Key-value namespaces |
| DigitalOcean | Private account list → eight reports plus existing list/switch/sign-in actions | AWS EC2, volume, DNS and cluster motifs; neutral database and balance | Compute instances; Managed databases; Account balance |
| Hetzner Cloud | Private account list → seven reports plus existing context actions | AWS EC2, VPC, security, disk and IP glyphs | Virtual networks; Network firewalls; Server snapshots |
| Oracle Cloud | Private account list → four reports plus existing profile actions | AWS EC2, bucket-list, VPC and group glyphs | Resource compartments; Compute instances; Object storage buckets |
| Vercel | Private account list → three reports plus existing team actions | AWS deployment, DNS and folder glyphs | Application deployments; DNS domains; Application projects |
| Netlify | Private account list → two reports plus existing account actions | AWS status and globe glyphs | Sign-in and site status; Websites |
| IBM Cloud | Private account list → four reports plus existing SSO/API-key/target actions | AWS account, group, instance and key glyphs; neutral target | Account details; Account and region; Provisioned services |

All seven use neutral Material Design Nerd Font glyphs, including their Cloud
parent rows. AWS's existing database glyph is from the Devicons range, so the
new database rows use Material Design's database glyph to meet the neutral-MD
requirement. Bucket reports reuse S3's **List buckets** glyph, rather than its
service-level icon. Instance, network, volume, IP, domain, deployment, account,
sign-in and Add Account glyphs reuse their matching AWS motifs.

Every action has an icon and a short description. Account list rows carry the
account glyph; Add Account carries its own plus glyph through the five-column
Python-to-Elephant transport. Delete retains its independent action and local-only
confirmation. The selected workspace/context/region remains in the picker prompt
and is repeated above report output. English, pt_BR, es, de and fr cover the
presentation and Handbook changes.

Reports continue through the same `cloud_report` bat/less/fallback pager as AWS.
Vendor stderr and nonzero exit status remain readable, with no retries under a
different account; Oracle namespace failure still stops bucket listing. Existing
AWS object/log fzf searches are unchanged. No new fzf views or provider commands
were added. Cancellation and terminal return retain the selected private account.
Validation uses synthetic accounts and mocked vendor execution, including actual
Lua parsing of synthetic account rows; no cloud CLI or real cloud configuration
is used.

### Verified icon mapping

Each codepoint below was checked using `fc-list ':charset=<hex>' family` and
matched the exact `JetBrainsMono Nerd Font` family. All are Material Design
symbols, with no company logos.

| Row | Glyph | Codepoint |
| --- | --- | --- |
| Account | 󰀄 | U+F0004 |
| R2 Buckets | 󰉋 | U+F024B |
| D1 Databases | 󰆼 | U+F01BC |
| KV Namespaces | 󰆼 | U+F01BC |
| Pages Projects | 󰉋 | U+F024B |
| Queues | 󰉹 | U+F0279 |
| Droplets | 󰍹 | U+F0379 |
| Apps | 󰘦 | U+F0626 |
| Databases | 󰆼 | U+F01BC |
| Kubernetes | 󰌗 | U+F0317 |
| Volumes | 󰋊 | U+F02CA |
| Domains | 󰖟 | U+F059F |
| Load Balancers | 󰑓 | U+F0453 |
| Balance | 󰄔 | U+F0114 |
| Servers | 󰍹 | U+F0379 |
| Networks | 󰩠 | U+F0A60 |
| Firewalls | 󰒋 | U+F048B |
| Primary IPs | 󰓦 | U+F04E6 |
| Snapshots | 󰋊 | U+F02CA |
| Compartments | 󰘦 | U+F0626 |
| Instances | 󰍹 | U+F0379 |
| Buckets | 󰉋 | U+F024B |
| VCNs | 󰩠 | U+F0A60 |
| Projects | 󰉋 | U+F024B |
| Deployments | 󰐱 | U+F0431 |
| Status | 󰅟 | U+F015F |
| Sites | 󰖟 | U+F059F |
| Target | 󰓾 | U+F04FE |
| Resource Groups | 󰘦 | U+F0626 |
| Service Instances | 󰍹 | U+F0379 |
| Account list rows / List Accounts | 󰀄 | U+F0004 |
| Add Account | 󰐕 | U+F0415 |
| Sign In | 󰒋 | U+F048B |
| Switch Account | 󰑓 | U+F0453 |
| Delete Account | 󰆴 | U+F01B4 |
| CLI Help | 󰋖 | U+F02D6 |
| Open Console | 󰖟 | U+F059F |
| Sign In with API Key | 󰌆 | U+F0306 |
| Seven provider parent rows | 󰅟 | U+F015F |

Validation for this AWS-parity pass: `bash tools/check.sh` passed all seven
stages (1,112 Python tests, existing skips retained, plus Node, syntax,
ShellCheck, Qt 6 QML lint, whitespace and structured data). Both i18n and
Handbook build/check pairs passed. All 21 final glyph codepoints matched
JetBrainsMono Nerd Font. No live account checks or commits were performed.
