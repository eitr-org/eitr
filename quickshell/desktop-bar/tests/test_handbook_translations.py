import importlib.util
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
BOOK = ROOT / "quickshell/desktop-bar/handbook"
spec = importlib.util.spec_from_file_location("localized_handbook", ROOT / "tools/handbook-build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def code_blocks(text):
    result = []
    current = None
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if current is None:
                current = [line]
            else:
                result.append("\n".join(current + [line]))
                current = None
        elif current is not None:
            current.append(line)
    return result


def inline_commands(text):
    for block in code_blocks(text):
        text = text.replace(block, "")
    return {re.sub(r"\s+", " ", command.strip())
            for command in re.findall(r"`([^`]+)`", text)}


class LocalizedHandbookTests(unittest.TestCase):
    def test_every_locale_bundle_matches_its_sources(self):
        for locale in builder.languages(ROOT):
            path = BOOK / "catalog.json" if locale == "en" else BOOK / "catalogs" / (locale + ".json")
            with self.subTest(locale=locale):
                self.assertEqual(path.read_text(), builder.build(locale))

    def test_missing_chapter_falls_back_without_losing_other_translations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "book"
            book.mkdir()
            (root / "english.md").write_text("# Original English\n")
            (book / "chapters.json").write_text(json.dumps([{"id": "example", "title": "Example", "source": "english.md"}]))
            (root / "i18n").mkdir()
            (root / "i18n/languages.json").write_text(json.dumps({"languages": {"en": {}, "fr": {}}}))
            for locale in ("en", "fr"):
                folder = root / "i18n/catalogs" / locale
                folder.mkdir(parents=True)
                (folder / "handbook.json").write_text(json.dumps({"Example": "Exemple" if locale == "fr" else "Example"}))
            with patch.object(builder, "ROOT", root), patch.object(builder, "BOOK", book):
                chapter = json.loads(builder.build("fr"))["chapters"][0]
                self.assertEqual(chapter["sourceLocale"], "en")
                self.assertEqual(chapter["title"], "Exemple")
                self.assertIn("Original English", chapter["markdown"])
                localized = book / "content/fr/example.md"
                localized.parent.mkdir(parents=True)
                localized.write_text("# Traduction française\n")
                chapter = json.loads(builder.build("fr"))["chapters"][0]
                self.assertEqual(chapter["sourceLocale"], "fr")
                self.assertIn("Traduction française", chapter["markdown"])

    def test_translated_chapters_keep_commands_and_link_targets(self):
        definitions = json.loads((BOOK / "chapters.json").read_text())
        for locale in ("pt_BR", "es", "de", "fr"):
            for chapter in definitions:
                if "source" not in chapter:
                    continue
                translated = BOOK / "content" / locale / (chapter["id"] + ".md")
                if not translated.is_file():
                    continue
                original = (ROOT / chapter["source"]).read_text()
                with self.subTest(locale=locale, chapter=chapter["id"]):
                    self.assertEqual(code_blocks(translated.read_text()), code_blocks(original))
                    self.assertEqual(re.findall(r"\]\(([^)]+)\)", translated.read_text()),
                                     re.findall(r"\]\(([^)]+)\)", original))

    def test_chapters_keep_sections_inline_commands_and_product_names(self):
        definitions = json.loads((BOOK / "chapters.json").read_text())
        for chapter in definitions:
            if "source" not in chapter:
                continue
            source = (ROOT / chapter["source"]).read_text()
            commands = inline_commands(source)
            headings = re.findall(r"^(#{1,6}) ", source, re.MULTILINE)
            for locale in ("pt_BR", "es", "de", "fr"):
                path = BOOK / "content" / locale / (chapter["id"] + ".md")
                with self.subTest(locale=locale, chapter=chapter["id"]):
                    self.assertTrue(path.is_file(), "Every maintained chapter needs a full translation")
                    translated = path.read_text()
                    self.assertEqual(inline_commands(translated), commands)
                    self.assertEqual(re.findall(r"^(#{1,6}) ", translated, re.MULTILINE), headings)
                    for product in ("WiFi", "Bluetooth", "OBS", "LIVE", "VS Code", "Steam", "GeForce NOW", "RetroArch"):
                        if product in source:
                            self.assertIn(product, translated)

    def test_new_feature_details_are_not_lost_from_translations(self):
        details = {
            "capture": ("Videos/Records", "Hybrid MP4", "LIVE"),
            "devices": ("~/.config/hypr/local.lua", "hyprctl reload", "US International", "15"),
            "development": ("monitoring.json", "Amazon Managed Grafana", "promtool", "Ctrl+R"),
            "desktop-bar": ("SUPER + ,", "10", "ᚾ"),
        }
        for locale in ("pt_BR", "es", "de", "fr"):
            for chapter, markers in details.items():
                text = (BOOK / "content" / locale / (chapter + ".md")).read_text()
                with self.subTest(locale=locale, chapter=chapter):
                    for marker in markers:
                        self.assertIn(marker, text)

    def test_recovery_guides_preserve_every_command_and_path_occurrence(self):
        sources = {"recovery": "distro/RECOVERY.md",
                   "factory-reset": "distro/FACTORY-RESET.md",
                   "secure-boot": "distro/SECURE-BOOT.md",
                   "network-backends": "distro/NETWORKING.md"}

        def tokens(text):
            for block in code_blocks(text):
                text = text.replace(block, "")
            return Counter(re.sub(r"\s+", " ", token.strip())
                           for token in re.findall(r"`([^`]+)`", text))

        for chapter, source in sources.items():
            original = (ROOT / source).read_text()
            for locale in ("pt_BR", "es", "de", "fr"):
                translated = (BOOK / "content" / locale / (chapter + ".md")).read_text()
                with self.subTest(locale=locale, chapter=chapter):
                    self.assertEqual(tokens(translated), tokens(original))
                    self.assertEqual(re.findall(r"^\s*(\d+)\. ", translated, re.MULTILINE),
                                     re.findall(r"^\s*(\d+)\. ", original, re.MULTILINE))

    def test_keyboard_binding_labels_keep_their_key_identifiers(self):
        english = json.loads((ROOT / "i18n/catalogs/en/menus.json").read_text())
        bindings = [key for key in english if re.fullmatch(r"SUPER(?: \+ \S+)+", key)]
        for locale in ("pt_BR", "es", "de", "fr"):
            catalog = json.loads((ROOT / "i18n/catalogs" / locale / "menus.json").read_text())
            for binding in bindings:
                with self.subTest(locale=locale, binding=binding):
                    self.assertEqual(catalog[binding], binding)

    def test_update_notification_buttons_match_documentation(self):
        for locale in ("pt_BR", "es", "de", "fr"):
            helpers = json.loads((ROOT / "i18n/catalogs" / locale / "helpers.json").read_text())
            chapter = (BOOK / "content" / locale / "maintenance.md").read_text()
            for key in ("Restart now", "Log out now", "Later"):
                with self.subTest(locale=locale, button=key):
                    self.assertIn("**" + helpers[key] + "**", chapter)

    def test_named_interface_controls_match_their_catalog(self):
        # English catalogs identify controls; prose emphasis and key bindings do
        # not become interface names merely because Markdown makes them bold.
        definitions = json.loads((BOOK / "chapters.json").read_text())
        bold = re.compile(r"\*\*([^*]+)\*\*")
        panel_chapters = {"devices", "control-center", "desktop-bar", "getting-started", "language"}
        for locale in ("pt_BR", "es", "de", "fr"):
            catalogs = {layer: json.loads((ROOT / "i18n/catalogs" / locale / (layer + ".json")).read_text())
                        for layer in ("qml", "menus")}
            for chapter in definitions:
                if "source" not in chapter:
                    continue
                source = bold.findall((ROOT / chapter["source"]).read_text())
                translated = bold.findall((BOOK / "content" / locale / (chapter["id"] + ".md")).read_text())
                with self.subTest(locale=locale, chapter=chapter["id"]):
                    self.assertEqual(len(translated), len(source), "Keep emphasized controls aligned with English")
                    primary = "qml" if chapter["id"] in panel_chapters else "menus"
                    secondary = "menus" if primary == "qml" else "qml"
                    catalog = {**catalogs[secondary], **catalogs[primary]}
                    for original, localized in zip(source, translated):
                        original_parts = re.sub(r"\s+", " ", original).split(" > ")
                        localized_parts = re.sub(r"\s+", " ", localized).split(" > ")
                        if not any(part.removesuffix(":") in catalog for part in original_parts):
                            continue
                        self.assertEqual(len(localized_parts), len(original_parts), original)
                        for key, label in zip(original_parts, localized_parts):
                            key = key.removesuffix(":")
                            key = {"Show Icons": "Show icons"}.get(key, key)
                            if key in catalog:
                                self.assertEqual(label.removesuffix(":").strip(), catalog[key],
                                                 f"{original}: use the {primary} interface label for {key!r}")

    def test_source_changes_are_detected_even_after_catalog_regeneration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "book"
            folder = book / "content/fr"
            folder.mkdir(parents=True)
            source = root / "english.md"
            source.write_text("# Original\nFull chapter.\n")
            (book / "chapters.json").write_text(json.dumps([
                {"id": "example", "title": "Example", "source": "english.md"}]))
            (folder / "example.md").write_text("# Traduction\nChapitre complet.\n")
            with patch.object(builder, "ROOT", root), patch.object(builder, "BOOK", book):
                self.assertEqual(builder.translation_source_problems("fr"), ["fr/example"])
                (folder / "source-hashes.json").write_text(json.dumps({
                    "example": hashlib.sha256(source.read_bytes()).hexdigest()}))
                self.assertEqual(builder.translation_source_problems("fr"), [])
                source.write_text("# Original\nFull chapter with an added safety warning.\n")
                (book / "catalogs").mkdir()
                (book / "catalogs/fr.json").write_text("regenerating a catalog cannot approve a translation")
                self.assertEqual(builder.translation_source_problems("fr"), ["fr/example"])
                (folder / "example.md").unlink()
                self.assertEqual(builder.translation_source_problems("fr"), [], "English fallback has no stale translation")

    def test_every_existing_translation_records_its_english_revision(self):
        for locale in ("pt_BR", "es", "de", "fr"):
            with self.subTest(locale=locale):
                self.assertEqual(builder.translation_source_problems(locale), [])

    def test_generated_shortcut_tables_translate_actions_and_preserve_bindings(self):
        original = builder.shortcuts()
        bindings = re.findall(r"\| \*\*((?:SUPER|Ctrl|Alt|Shift)[^*]+)\*\*", original)
        for locale in ("pt_BR", "es", "de", "fr"):
            translated = builder.localized_shortcuts(locale)
            with self.subTest(locale=locale):
                self.assertNotEqual(translated, original)
                self.assertEqual(re.findall(r"\| \*\*((?:SUPER|Ctrl|Alt|Shift)[^*]+)\*\*", translated), bindings)
                self.assertEqual(translated.count("| :--- | :--- |"), original.count("| :--- | :--- |"))

    def test_editorial_regressions_keep_keys_and_german_address_consistent(self):
        for locale in ('pt_BR', 'es', 'de', 'fr'):
            capture = (BOOK / 'content' / locale / 'capture.md').read_text()
            self.assertIn('**Print:**', capture)
        for path in (BOOK / 'content/de').glob('*.md'):
            text = path.read_text()
            for mixed in ('melde sich', 'Melde sich', 'Verbinde sich', 'du das TPM registrieren',
                          'du es bestätigt haben', 'du die Firmware-Einstellungen öffnen'):
                self.assertNotIn(mixed, text, str(path))
