# Eitr Store

The Store is a dedicated Quickshell window and application launcher entry.
`eitr-shell desktop-bar ipc call -- store show [kind] [tab]` opens it; omitted
arguments keep the selected view. The launcher supplies empty strings for omitted
arguments to the typed Quickshell handler. Raw Quickshell callers pass both strings. Tabs are `installed` and `discover`.
The `catalog` IPC target remains an alias for existing shortcuts and callers.
Machine-local catalog caches and review paths retain their names.

`distro/store-kinds.json` is the single kind registry. It owns the ID, translated
label, rune, icon, Installed/Discover descriptions, sources, backend ID and
capabilities: use on click, removal, updates and administrator authentication.
`python3 tools/store-kinds.py` projects it to `StoreKinds.js`; `--check` checks
synchronization. Translation extraction reads the same registry.

Every kind has Installed and Discover. Discover merges its registered official
and community sources, with provenance badges and All/Official/Community filters.
Search spans loaded kinds in the selected Installed or Discover view. Theme tone
filtering remains available. Plugin install and update always use the existing
prepare/confirm permission review; lockscreen changes use the existing signed
package helper and administrator password. Official labels are presentation,
never permission grants or substitutes for backend source verification.

The Store reads schema 2 at
`https://raw.githubusercontent.com/eitr-org/eitr-store/HEAD/index.json`.
It also accepts schema 1. Only a 404 falls back to the former community index
while the new repository is unpublished. Cached names remain stable. A malformed
new index is refused; it does not fall back to older metadata.

## Wallpaper packs

A pack contains `eitr-wallpapers.json` with `id`, `name`, `description`, and
`images` (unique flat filenames), plus exactly those images. JPEG, PNG and WebP
are accepted after full decoding, with the own-picture decoder's dimensions
and the theme package's aggregate byte and file limits. No symlinks, executable
blobs, subdirectories, scripts or unlisted files are accepted.

Verified images are installed with `store-<pack-id>-` prefixes directly in the
person's own wallpapers directory. The picker and carousel discover them using
their existing code. Separate private ownership records track only those files;
removing a pack leaves unrelated pictures alone. A pack used by a saved wallpaper selection cannot be removed until another image is chosen. Installed shows shipped theme
wallpapers, personal images and pack management cards. Clicking an image uses
the existing wallpaper apply helper; clicking a pack uses its first image.

## Adding a kind (screensavers are not implemented)

1. Add a registry entry with the fields above; choose only supported sources and
   declare its capabilities truthfully.
2. Add its backend function to `distro/lib/eitr_store_backends.py` and `BACKENDS`
   under the registry's backend ID. The small operation interface returns
   `{'items': [...]}` for `installed` and `index`, `{'result': ...}` for `install`,
   `remove`, `update`, `apply`, and `{'image': ...}` for `preview`. Unsupported
   operations must fail explicitly. Reviewable executable content additionally
   uses `prepare`, `confirm`, `discard`, `detail`, `artwork` and source inspection.
3. Validate its requests and content before any mutation, preserve bounded reads,
   deadlines and atomic installation, and test it in a temporary home without
   network. Extend the Store index schema only when the kind uses community data.
4. Regenerate the registry projection, translations and Handbook, classify new
   runtime files, and render both palettes. The sidebar, provenance filter and
   grid need no new page. Kind-specific detail controls belong in small components.
