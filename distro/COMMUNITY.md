# Community index

The Store reads `index.json` from `eitr-org/eitr-store` (schema 2) only on demand; it also
accepts schema 1. The index holds pointers, never packages: each entry names the author's
Git repository and folder, and the Store downloads from there only when someone installs it.
Community is a separate badge. Official status follows repository address only:
`eitr-org/eitr-themes` for themes and `eitr-org/eitr-plugins` for plugins.
An entry's maintainer, license, or community membership cannot grant official trust.
What may be listed (fan content included) is in [STORE.md](STORE.md), Community content.

A theme entry is a strict JSON object in the index's `themes` array:

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

IDs use lowercase letters, digits and single hyphens (at most 64 characters) and are unique
within their kind. Repository URLs must be HTTPS or SSH Git addresses; local paths and
credential-bearing HTTPS URLs are rejected. Folder is a relative path without hidden
components, traversal or backslashes. Maintainer is nonempty text up to 128 characters.
License is one SPDX license ID (not an expression) or `LicenseRef-` plus a short name.
Descriptions are nonempty and at most 72 characters. Unknown and duplicate keys are rejected.
Plugins additionally require `commit`, a full 40-character Git SHA. Themes follow the
repository's current HEAD and must pass Eitr's data-only validator. Wallpaper packs use the
same fields in `wallpapers`.

`removed` is an array of `{ "kind": "themes", "id": "example", "reason": "Why it was
removed" }` objects; kind is `themes`, `plugins` or `wallpapers`. Removed IDs cannot remain
in that kind's active list. Reasons are at most 256 characters.

`eitr-store` validates the index in CI with `validate.py`, which runs this repository's
`distro/lib/eitr_community.py` (vendored there). One invalid entry makes desktops refuse the
whole index, so a new field or license form ships to stable before the index uses it.
`eitr_community.verify` fetches only selected package trees through sparse Git object reads,
pins plugins to their reviewed commit, rejects links/submodules and oversized trees, and runs
the existing theme/plugin validators without executing their code. Reviewers must still assess
plugin code; structural validation is not a security approval.

`distro/lib/spdx-license-ids.json` is the SPDX identifier set shipped by Python
packaging's SPDX data, kept locally so catalog validation needs no extra package.

The desktop catalog reads plugin manifest metadata, including optional pictures
and videos, from the entry's pinned commit. Browsing never downloads media blobs.
Selected media uses the same bounded artwork loader as official plugins. Native
install and update reviews stage that exact commit; a newer upstream HEAD is
never substituted for the community pin. See [PLUGINS.md](PLUGINS.md).
