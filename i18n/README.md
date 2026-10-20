# Eitr translation infrastructure

English is the source and fallback. Only languages listed in `languages.json`
are offered as supported. Locale precedence is `LC_ALL`, `LC_MESSAGES`, `LANG`;
empty values are skipped. `C`, `POSIX`, invalid and unsupported locales use
English. Regional catalogs fall back to the base language, then English.
Changing the system locale takes effect when a new desktop session starts.
The Language picker uses the shared `eitr_language.py` helper to save a user-session
LC_MESSAGES preference in
`~/.config/environment.d/90-eitr-language.conf`; System default removes it.
No machine locale configuration is bundled.

## Runtime owners

- QML: `Eitr.I18n.tr("English text", [argument])`, with `%1` placeholders.
  `quickshell/Eitr/Locale.js` owns QML locale selection and fallback. The
  `Eitr.I18n` singleton uses the generated `Catalogs.js` snapshot of the JSON
  tables. The singleton reads the Quickshell process environment directly.
  SDDM packaging removes that dependency and uses Qt’s system locale.
- Menus: `elephant/i18n.lua` selects the generated table from the environment without
  launching subprocesses, preserves English and translated search keywords,
  and sorts translated folders
  before actions using accent-insensitive sort keys. Callers explicitly preserve Main's and Apps' ordering.
- Python: `distro/lib/eitr_i18n.py` owns locale lookup and the `eitr` gettext
  domain. Metadata and locale selections are cached. Direct entrypoints use
  the one `eitr_bootstrap.py` owner, exposed by source-tree links; session
  launchers provide its installed library through PYTHONPATH. Use `tr("Hello {name}", name=name)` and `ntr` for count messages.
  The builder exports `eitr.po` and `eitr.mo` under `i18n/locales/<locale>/LC_MESSAGES/`
  from the canonical helper JSON. GNU `msgfmt` is a build dependency; Python’s
  standard gettext reader is the runtime dependency. `mark()` records display
  labels whose English value remains an internal key until the rendering step.
- Shell: source `distro/lib/i18n.sh` (installed as `lib/i18n.sh`), then use
  `eitr_gettext` or `eitr_ngettext`. These delegate to the same Python owner;
  translated text is never evaluated as shell code.
- Handbook: localized chapter files belong under `handbook/content/<locale>/`
  with English fallback per chapter. Chapter IDs and links remain stable.

## Catalog workflow

Run `python3 tools/i18n-build.py` after marking new messages. It updates the
English tables and `i18n/sources.json`, which records each source location.
`--check` reports stale catalogs, every missing message and changed placeholders.
It checks only registered messages: integrating each UI/helper layer is a
separate migration, and unmarked strings are not claimed to be translated.

Translate values only, retaining English keys, placeholders, package/command
names, paths and glyphs. Keep typed destructive confirmation tokens untranslated
unless the prompt and the matching check are deliberately changed together and
tested. Never translate protocol strings, action identifiers or JSON keys.

The installed Quickshell 0.3.2 exposes no QML translator-loading API. An isolated
offscreen probe found `Quickshell.loadTranslation` undefined and `qsTr` still
returning source text. The shared-table approach is used for all QML; no `.qm`
loader, Qt plugin or per-component locale helper is introduced.

Validate with `bash tools/check.sh`, and check translated layouts only with
offscreen QML renders, never live desktop screenshots.

Helper translations are reviewed before use. Unreviewed drafts use English
instead of generated prose. `pending-helpers.json` lists every English-valued
helper entry by locale, including shared technical names. It is generated and
checked with the catalogs. Usage lines, argparse help, developer diagnostics,
and payload/repository build tooling stay outside the helper catalogs.

Handbook source freshness is tracked separately from generated catalogs in each
locale’s `source-hashes.json`. Each chapter records the SHA-256 of its English
source revision. `handbook-build.py --check` reports changed or unrecorded
sources, even after someone rebuilds the catalogs. After translating the entire
changed chapter, update only its hash to the reviewed English source’s SHA-256.
Rebuilding never acknowledges source changes automatically. Initial hashes
record the English revision present when each existing translation was committed;
they track revision drift, not translation quality or completeness.

The helper quality pass translates the user-facing English fallbacks. Remaining
English-valued entries include shared technical names (such as Cursor and AWS
SSO), display-only identifier templates, and developer validation diagnostics
(for example unsupported action identifiers, template sizes and malformed
package IDs). These intentionally remain English; the fallback report continues
to list them rather than treating identical text as a completed translation.

Handbook interface labels are checked against the QML and Walker catalogs.
Bold controls and menu paths keep their English source order; panel chapters
prefer QML labels and menu chapters prefer Walker labels when the same English
word has different translations. Key bindings and prose emphasis are identified
from the English source rather than treated as translated interface labels.
This check covers catalogued controls; it does not certify unregistered dynamic
labels or replace a paragraph-by-paragraph editorial review.

Recovery editorial checks preserve every inline command/path occurrence and
numbered step in the recovery, factory-reset, Secure Boot and network-backend
guides. The commands themselves remain English. Shortcut labels retain literal
key identifiers, including Space and Print. Human-facing update notification
buttons and problem-report choices are translated without changing their action
IDs or translating diagnostic report contents.

Dynamic QML and Lua display messages accept named `{field}` placeholders as
well as existing Qt positional placeholders. Interpolation is a single pass: a
value containing another placeholder is literal data. Mark choice titles and
descriptions at their owner; never mark their option IDs. Python-generated menu
keys use `from eitr_i18n import mark as menu_mark` to register them in the menu
catalog without translating the JSON consumed by Lua. Lua formats display fields;
JSON IDs and the values passed back to Python stay unchanged.

Shell prompts keep typed confirmation tokens in English (`yes`, `[y/N]`,
`RESET MY COMPUTER`, and the TPM tokens). Translated questions explicitly retain
those tokens. `eitr_gettext 'Message {name}' "name=$value"` formats named values
as data through the shared Python owner, without evaluating translated shell.
