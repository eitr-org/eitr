# Community index

The catalog reads `index.json` from `eitr-org/eitr-community` only on demand.
Community is a separate badge. Official status follows repository address only:
`eitr-org/eitr-themes` for themes and `eitr-org/eitr-plugins` for plugins.
An entry's maintainer, license, or community membership cannot grant official trust.

Each `themes/<id>.json` or `plugins/<id>.json` is a strict JSON object:

```json
{
  "id": "example",
  "repository": "https://github.com/example/themes",
  "folder": "themes/example",
  "maintainer": "example",
  "license": "MIT",
  "description": "A short description"
}
```

The id must match its filename and use lowercase letters, digits and single
hyphens (at most 64 characters). Repository URLs must be HTTPS or SSH Git addresses;
local paths and credential-bearing HTTPS URLs are rejected. Folder is a relative
path without hidden components, traversal or backslashes. Maintainer is nonempty
text up to 128 characters. License is one SPDX license ID, not an expression.
Descriptions are nonempty and at most 72 characters. Unknown and duplicate keys
are rejected. Plugins additionally require `commit`, a full 40-character Git SHA.
Themes follow the repository's current HEAD and must pass Eitr's data-only validator.

`removed.json` is an array of `{ "kind": "themes", "id": "example", "reason":
"Why it was removed" }` objects; kind is `themes` or `plugins`. Removed IDs cannot
remain in that kind's active list. Reasons are at most 256 characters.

Run `python3 /path/to/eitr/tools/community-index.py .` to generate the deterministic
index. Run with `--check --verify` in CI. Check rejects a stale index. Verify fetches
only selected package trees through sparse Git object reads, pins plugins to their
reviewed commit, rejects links/submodules and oversized trees, and runs the existing
theme/plugin validators without executing their code. Reviewers must still assess
plugin code; structural validation is not a security approval.

The generated object has `schemaVersion: 1`, sorted `themes` and `plugins` arrays,
and `removed`. Community themes use the catalog's selection/review flow; community
plugins are browse-only until the native plugin review is available.

`distro/lib/spdx-license-ids.json` is the SPDX identifier set shipped by Python
packaging's SPDX data, kept locally so catalog validation needs no extra package.
