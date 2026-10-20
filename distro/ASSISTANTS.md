# Assistant bridge: implementation and review

The AI menu switch registers a stdio MCP server named `assistants` for connected supported clients. It is off until explicitly confirmed. The server implements newline
JSON-RPC 2.0 `initialize`, `ping`, `tools/list` and `tools/call`; notifications
receive no response. Each tool has exactly one required string, `question`.
Tool errors use MCP text content with `isError`; protocol errors use JSON-RPC
errors. Stdout is reserved for the protocol.

## Local CLI evidence

Only help and installed documentation were inspected. No real assistant was
prompted, no account status command was run, and no settings were registered.
The command lines below are constructed by `eitr_collaboration.command`.
`BINARY` is the real executable returned by `eitr_assistants.executable`, never
a first-use launcher. Every helper inherits the server's current working
directory and gets `EITR_ASSISTANTS_DEPTH=1`. A server with that variable set
lists no tools and refuses calls. The timeout is 180 seconds; timeout cleanup
kills the helper process group, including descendants.

### Claude

```
BINARY -p --safe-mode --tools Read,Glob,Grep --permission-mode plan --permission-prompts none --strict-mcp-config --mcp-config '{"mcpServers":{}}' --no-session-persistence --output-format text -- QUESTION
```

`claude --help` describes `-p` as printing the response and exiting; `--tools`
selects the available built-in tools. The explicit Read/Glob/Grep set excludes
editing, shell execution, delegation and plan-exit tools. `--permission-mode`
lists `plan`. `--permission-prompts none` denies actions that would prompt.
`--safe-mode` disables customizations including hooks, plugins and MCP;
`--strict-mcp-config` ignores other MCP configurations. Session persistence is
disabled. Text output is the final response. `claude mcp --help` documents stdio
registration and JSON server configuration. Eitr uses user `mcpServers` in
`~/.claude.json`; a custom `CLAUDE_CONFIG_DIR` uses its `.claude.json`.

### Codex

```
BINARY exec --ignore-user-config --ignore-rules --sandbox read-only -c 'approval_policy="never"' --ephemeral --skip-git-repo-check --json -
```

The question is passed on stdin, so leading option characters cannot change
flags. `codex exec --help` describes stdin prompts, `read-only`, ephemeral
sessions, ignoring user config and rules, and JSONL output. `codex --help`
describes the sandbox as the execution policy and `never` as returning execution
failures rather than asking for escalation. This does not grant approvals or
bypass the sandbox. The server returns only the last completed `agent_message`
text, excluding reasoning and tool output. `codex mcp --help` documents external
MCP management; user configuration is `~/.codex/config.toml` (or `CODEX_HOME`),
with a `mcp_servers.assistants` table.

### Gemini CLI

```
BINARY --prompt=QUESTION --approval-mode plan --allowed-mcp-server-names eitr-no-mcp-7b7478c7-67be-4dcb-9666-7bd9c36a54ed --extensions none --output-format text
```

The equals form keeps leading `--` in the question as text. Installed help
labels plan mode read-only and prompt mode headless. The MCP array requires
one argument, and the installed implementation treats an empty allowlist as
unrestricted. Eitr therefore restricts it to a reserved, deliberately nonexistent
server name instead of omitting the restriction. Never configure that name.
`--extensions none` disables extensions; no yolo or automatic approval is used.
Plan mode is a documented policy, not an independently verified OS sandbox;
upstream describes dedicated plan-file writes. No real-account test was run.

Offline detection accepts non-empty `GEMINI_API_KEY` or `GOOGLE_API_KEY`, or
`security.auth.selectedType` equal to `gemini-api-key` or `vertex-ai` in
`~/.gemini/settings.json`. Personal Google OAuth does not qualify. These are
availability hints, not credential validation; no auth command is run.

Installed `gemini mcp add --help` documents `-s user`, `-e KEY=value` and stdio
command arguments; `gemini mcp remove --help` documents user scope. Registration
therefore uses Gemini's own add/remove commands, without `--trust`, and reads
only its user `mcpServers` entry for exact-match ownership checks. It never
replaces an existing `assistants` entry or removes an edited one.

Sources: [headless mode](https://geminicli.com/docs/cli/headless/),
[MCP servers](https://geminicli.com/docs/tools/mcp-server/), installed CLI help
and bundled CLI argument/extension handling. Eitr has not yet tested Gemini
with a paid key or company account; report problems with Report a Problem.

### Other helpers

- Copilot: not installed; no installed help/docs could be verified. TODO's
  documented approach requires restricting allowed read tools and denying
  writes/shell. No unverified command or MCP registration is shipped.
- Grok: omitted as designed; read-only and MCP support lack confirmed official
  documentation.

## Settings and approval boundaries

Registration adds only command, arguments and caller identity. It adds no
allowed-tools lists, approval exemptions or automatic approval mode. Tool
annotations conservatively describe the subscription hand-off as having side
effects, even though file operations are read-only. The calling assistant's
normal tool approval remains the approval boundary; users must not enable
server/tool auto-approval. Actual approval prompts require step 3 verification.

Offline sign-in hints read only the supported OAuth credential fields. No
credential is copied to Eitr state. Other clients’ API-key-only and keyring-only sign-ins are
conservatively excluded; Gemini uses the explicit rules above. Expired credentials can appear signed in; failure is
returned without exposing CLI stderr or refreshing credentials ourselves.

Registration goes through each tool's own command (`claude mcp add -s user`,
`codex mcp add`, `copilot mcp add`, `grok mcp add -s user`, `gemini mcp add -s user`), never a direct edit of their settings: Claude Code rewrites
`~/.claude.json` while it runs. An existing `assistants` server is never
replaced. A private state file records which tools Eitr registered and the
exact entry, with no settings or tokens. Disable removes only a still-matching managed entry and retains conflicts for
retry. Menu mutations are serialized with a machine-local advisory lock.

The package stages the helper and library via `layout-manifest.json`; recipes
live at `/usr/share/eitr/software.json`. The entrypoint finds `lib` in the
installed tree as well as `distro/lib` in a checkout, including isolated Python
runs with no `PYTHONPATH`. Tests exercise that packaged layout and recipe lookup.

Verified with real accounts (Claude Code 2.1.304, Codex 0.163.0, Copilot CLI
1.0.100, Grok 1.0.62): every helper answered from the caller's folder, none
could create a file or run a shell command, a helper saw no tools of its own,
and each tool's own `mcp add/remove` registered and removed exactly Eitr's
entry, keeping other servers. Copilot runs headless with `--allow-all-tools`
but denies `shell`, `write`, `url` and the assistants server, which always win.
Grok runs in plan mode inside its kernel-enforced `read-only` sandbox, which
still allows writes to `~/.grok` and temporary folders. Grok's `mcp add`
replaces an existing server of the same name, so Eitr checks first. Gemini ships from documentation, with a real-account test still open.
Antigravity (`agy`) is never a helper: headless runs deny even reads, and its
only unlocks bypass permissions or change global settings. Re-check when it
supports per-run permissions or a read-only headless mode.
