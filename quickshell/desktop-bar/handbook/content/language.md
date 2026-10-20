# Language

Eitr follows the system's message locale. **Control Center > System > Language**
shows the language Eitr uses for that locale and opens a language picker;
**Walker > System > Language** lists the same choices with the current one
checked. Choose a language or **System default**,
then sign out and back in. Eitr never signs you out automatically.

Eitr checks **LC_ALL**, then **LC_MESSAGES**, then **LANG**. Empty variables are
ignored. `LC_MESSAGES` changes messages without changing your date, number or
currency formats; `LC_ALL` overrides all locale categories and is normally left
unset. `C`, `POSIX` and unsupported languages use English. A missing translated
message falls back to English; a missing Handbook chapter falls back as a whole.

## Change the system language

The picker writes only `~/.config/environment.d/90-eitr-language.conf`. It sets
`LC_MESSAGES` and clears `LC_ALL` for the next user session, preserving your
date and number formats. **System default** removes that preference. It never
edits `/etc/locale.conf` or generates locales. If necessary, use your system locale configuration. On Arch Linux, enable the locale you want
in `/etc/locale.gen` and regenerate installed locales with `sudo locale-gen`.
Then set the language in `/etc/locale.conf`, for example:

```text
LANG=pt_BR.UTF-8
```

The first translation targets are `pt_BR.UTF-8` (Brazilian Portuguese),
`es_ES.UTF-8` (Spanish), `de_DE.UTF-8` (German) and `fr_FR.UTF-8` (French).
Regional variants can fall back to the base language. Check `locale` in a
terminal for overrides, and `locale -a` for installed locales. Sign out and back
in to apply the language to the desktop, menus and newly opened terminals.
The picker changes your next session; already running applications keep their language.

## Contribute a translation

English text is the source. Catalogs live in `i18n/catalogs/<locale>/`; edit the
translated values, keeping the English keys. Python and shell messages use the
single `eitr` gettext domain. Keep placeholders such as `%1` and `{name}`, glyphs,
package names, commands and file paths unchanged. Typed destructive-action
confirmation words must match the words the confirmation check accepts.

Handbook chapters go in
`quickshell/desktop-bar/handbook/content/<locale>/<chapter-id>.md`. Keep
`handbook:` links, code blocks and commands intact. Keyboard and mouse tables
are generated from the canonical shortcut sources; translate their messages in
the Handbook catalog rather than maintaining a second list of bindings.

Run `python3 tools/i18n-build.py --check`, rebuild the Handbook with
`python3 quickshell/desktop-bar/scripts/handbook-build.py`, then run its `--check`
and `bash tools/check.sh`. Catalog checks list missing messages and changed
placeholders. Check long translations in offscreen previews before submitting.

After translating a changed chapter in full, update its entry in `source-hashes.json` with the SHA-256 of the English source. The build check flags changed or unrecorded English sources; rebuilding catalogs alone never acknowledges a source change.
