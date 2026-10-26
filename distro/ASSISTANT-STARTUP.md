# Interactive assistant startup

Eitr interactive launchers start in the user's home, after selecting the account
environment. Ratatoskr and headless read-only calls retain their own behavior.
Startup does not write per-CLI instruction files. The packaged Eitr skill is
seeded separately as described below. Trusting home also trusts its descendants
according to the CLI's own trust rules. Existing trust entries remain intact.
JSON trust updates preserve unrelated bytes, use atomic replacement and retain
permissions; an existing original is backed up once as `.eitr-backup`. Malformed,
ambiguous, symlinked or unreadable settings are skipped, leaving the native prompt.

Verified 2026-10-23 against installed `--help`, installed package code where
noted, and the vendor references below. No sign-in or assistant session was run.

| CLI | Home trust | Extra instructions | Verification |
| --- | --- | --- | --- |
| Claude | `projects[home].hasTrustDialogAccepted` in `~/.claude.json`, or `$CLAUDE_CONFIG_DIR/.claude.json` | `--append-system-prompt` | Installed binary trust key/path resolver and help; [settings](https://code.claude.com/docs/en/settings) |
| Codex | Invocation-only `-c 'projects."HOME".trust_level="trusted"'` | `-c developer_instructions=…` | Installed help; [configuration](https://developers.openai.com/codex/config-reference/) |
| Gemini | Invocation-only `--skip-trust` | Skipped: no additive system instruction option verified | Installed help; [system override](https://geminicli.com/docs/cli/system-prompt/) replaces core instructions, so is deliberately unused |
| Grok | Skipped: installed help has no trust flag; storage not safely verified | `--rules` | Installed help; [permissions](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/22-permissions-and-safety.md); upstream describes `--trust` for headless, absent from installed help |
| Copilot | Append home to selected `$COPILOT_HOME/config.json` `trustedFolders` (default `~/.copilot`) | Skipped: no extra/system text option verified | Installed help; [trusted directories](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/configure-copilot-cli); `--trust-folder` is prompt-mode only |
| agy | Skipped: trust storage format/location not safely verified together | Skipped: no extra/system option verified | Installed help and [reference](https://www.agy.dev/docs/cli/reference/); no config override supported |

The read-only Control Center quick chat includes an Eitr primer and up to four
keyword-ranked Handbook sections, at most 7168 UTF-8 bytes combined. It searches
the latest two user questions, uses the user's locale with per-chapter English
fallback, and labels excerpts and system facts as data. It sends no additional
machine information beyond the existing allowlisted summary.

## OpenCode, Pi and the Eitr skill

Verified from vendor documentation and tagged source without running either CLI:

- **OpenCode**: official Arch Extra package `opencode` (upstream moved from
  sst to anomalyco), preferred over npm `opencode-ai`. The
  [Arch package record](https://archlinux.org/packages/extra/x86_64/opencode/)
  identifies the upstream; [CLI docs](https://opencode.ai/docs/cli/) list `--auto`
  for auto-approval of permissions not explicitly denied. Eitr adds it only for
  interactive full access. No home-trust storage or additive prompt flag is
  verified, so startup adds neither. Native AGENTS.md/CLAUDE.md rules and skills
  remain available. `OPENCODE_CONFIG_DIR` exists but does not isolate credentials:
  `auth.json` remains under the shared data directory. Accounts therefore offers
  only Default; Eitr never changes global XDG roots to simulate isolation.
- **Pi**: `@mariozechner/pi-coding-agent`, command `pi`, installed through NVM/npm.
  No cached local metadata or repository documentation was found. The
  [v0.61.0 package manifest](https://github.com/badlogic/pi-mono/blob/v0.61.0/packages/coding-agent/package.json)
  verifies both names; the matching
  [README](https://github.com/badlogic/pi-mono/blob/v0.61.0/packages/coding-agent/README.md)
  verifies `--append-system-prompt` and `PI_CODING_AGENT_DIR` (default
  `~/.pi/agent`, including auth). Eitr appends its normal Handbook guidance and
  supports separate accounts. Sign in with `/login` inside Pi. No home-trust
  write is verified. Pi reads AGENTS.md/CLAUDE.md and native skills. Pi has no
  built-in permission prompts and needs no full-access flag. Eitr refuses its
  interactive launch in Ask before changes mode or under organization restrictions;
  selecting that mode cannot make Pi ask for approval. It is not a read-only
  collaboration backend. New upstream releases use a different npm scope; this
  recipe intentionally retains the requested Mario Zechner package.

`distro/assistant/skills/eitr/SKILL.md` ships as package-owned data under
`/usr/share/eitr/distro/assistant/skills/eitr/`. `eitr-config seed` installs a
managed copy at `~/.claude/skills/eitr/SKILL.md`. Claude Code and OpenCode discover
that location ([OpenCode skill docs](https://opencode.ai/docs/skills/)); OpenCode's
external/Claude skill discovery must remain enabled. `eitr-config update` refreshes
an unedited copy, preserves user edits or an existing user-created skill, and puts
changed upstream content in `.eitr-new` for review. The login migration seeds
missing skills on existing installations without overwriting anything. This does
not replace per-CLI startup instructions or change any login. Separate Claude
config directories can have their own skill discovery settings; no account folder
is overwritten. Pi receives the Handbook primer through its additive prompt flag.
