# Git accounts

Open **Development > Git Accounts**. GitHub and GitLab accounts can be used
simultaneously, including several accounts on the same provider or enterprise
hostname. GitHub CLI (`gh`) and GitLab CLI (`glab`) ship in new installations.
Existing ISO images must be rebuilt to include changes.

Each account is a row showing where Git uses it: **Default**, the names of its
folders, or **Not used yet**. Press Enter on an account to open its actions;
Shift+Backspace returns to the list.

## First setup

1. **Add Account** opens the shared step-by-step form for provider, account name, commit author name and email, hostname, an optional existing private SSH key, default identity and folder rule. Every answer appears in Review; revisit any step before applying. Esc or Ctrl+C cancels without saving.
2. **Import Existing Setup** reads identities configured by hand instead: the
   default `user.name`/`user.email` and per-folder `includeIf "gitdir:…"` rules in
   `~/.gitconfig` or `~/.config/git/config`, including the SSH alias and key an
   included file routes through (`url.<alias>.insteadOf`). It lists what it found
   and creates matching accounts and rules after confirmation. Your files stay
   unchanged; wildcard folder patterns are listed as skipped.

## Default and folders

The **default** account applies in every folder without its own account. A
**folder** account applies only to repositories inside that folder. The most
specific folder wins; repository-local settings and Git command-line or
environment overrides still take precedence. EITR preserves existing global
configuration and comments, adding a marked include at the end of
`~/.gitconfig`, and confirmed rules override identities from external includes.

Account actions in Walker, each confirmed before saving and reported in a
notification: **Make Default** or **Stop Using as Default**, **Add Folder**
(pick `~/Development` or a folder inside it, or **Other folder…** to type a
path) and **Remove Folder**. Git matches the actual `.git` directory, so linked
worktrees and submodules can follow a parent repository's account.

## SSH keys

Commit identity does not grant repository access. **Show Public Key** prints the
account's public key, copies it to the clipboard and names the provider page to
add it to (GitHub: Settings > SSH keys). **Set Existing SSH Key** picks a key
from `~/.ssh`; **Create SSH Key** makes an Ed25519 key with a passphrase and then
shows its public key. **Test Connection** reports the provider's greeting, such
as "Hi username!", in a notification. Never share a private key.

Keys apply only to their provider SSH hostname. The launcher resolves existing
SSH aliases without connecting, then uses only the selected key, ignoring other
SSH configuration for that connection. Proxy connections are refused; retain a
repository-local `core.sshCommand` for advanced setups. Known-host verification
stays enabled. Accounts without a configured key use normal SSH, not another
account's key. HTTPS credentials and credential helpers are unchanged.

## Provider CLIs

**Log In to CLI** signs into a separate config directory for each account; it
does not switch the ordinary global `gh` or `glab` account. Inherited
provider-token variables are removed for that process. Its confirmation explains
that tokens are stored in private, unencrypted CLI profile files, avoiding
keyring entries shared between accounts on the same host.
Never share `~/.config/eitr/git-accounts/cli`; it is not included in EITR backups.

From a repository, use the account-aware CLI:

```sh
eitr-git cli auth status
eitr-git cli repo view
```

The selected default/folder account chooses `gh` or `glab`. Ordinary CLI commands
keep their existing global behavior. SSH-key registration does not authenticate
CLI API operations. No Bitbucket CLI is bundled.

## Removal and recovery

**Edit Name and Email** changes identity fields; **Remove Account** removes an
account and its rules after confirmation. Removing a folder rule falls back to a
broader rule or the default; clearing the default restores existing Git settings
outside remaining rules. Projects, keys and CLI credentials are never deleted,
and removing a rule does not revoke provider access.

Versioned settings live in `~/.config/eitr/git-accounts.json`. Every apply backs
up the global Git file, active include and settings under
`~/.local/state/eitr/git-account-backups/<id>` with private permissions.
`manifest.json` identifies original paths, backup filenames and modes. Keys and
CLI tokens are never copied. For manual recovery, review that manifest and keep
any edits made since the backup before restoring files. Edited or malformed
EITR include blocks are refused instead of silently replaced.

References: [Git conditional includes](https://git-scm.com/docs/git-config),
[GitHub CLI profiles](https://cli.github.com/manual/gh_help_environment),
[GitLab CLI profiles](https://docs.gitlab.com/cli/configuration/).
