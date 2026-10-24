# Interactive assistant startup

Eitr interactive launchers start in the user's home, after selecting the account
environment. Ratatoskr and headless read-only calls retain their own behavior.
No user instruction files are written. Trusting home also trusts its descendants
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
