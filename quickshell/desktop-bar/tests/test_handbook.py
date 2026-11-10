import importlib.util
import json
import re
import sys
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
BOOK = ROOT / "quickshell/desktop-bar/handbook"
spec = importlib.util.spec_from_file_location("handbook_build", ROOT / "tools/handbook-build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class HandbookTests(unittest.TestCase):
    def test_bundle_matches_current_sources(self):
        self.assertEqual((BOOK / "catalog.json").read_text(), builder.build())

    def test_all_system_group_actions_are_documented(self):
        sys.path.insert(0, str(ROOT / "walker/tests"))
        import menu_data
        text = "\n".join(chapter["markdown"] for chapter in json.loads(builder.build())["chapters"]).casefold()
        for name in ("system", "system-connectivity", "system-devices", "input", "remote-access", "apps-keys", "system-maintenance", "security", "users"):
            menu = menu_data.load(name)
            for entry in menu["entries"]:
                self.assertIn(entry["text"].casefold(), text)

    def test_shortcuts_come_from_the_existing_picker(self):
        text = builder.shortcuts()
        self.assertIn("SUPER + F1", text)
        self.assertIn("SUPER + Ctrl + V", text)
        self.assertIn("SUPER + Tab", text)
        self.assertIn("Toggle floating and pin", text)
        self.assertIn("## Keyboard", text)
        self.assertIn("## Mouse", text)
        self.assertIn("Bar: double right-click", text)
        self.assertIn("Workspace: right-click", text)
        self.assertIn("| Shortcut | Action |", text)
        self.assertIn("| Gesture | Action |", text)

    def test_handbook_pages_show_a_scroll_bar_you_can_grab(self):
        bar = (ROOT / "quickshell/desktop-bar/components/PanelScrollBar.qml").read_text()
        self.assertIn("policy: needed ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff", bar)
        self.assertIn("width: 10", bar)
        # Only the Handbook's reading area uses it; Settings and the sidebars keep their light bars.
        self.assertIn("ScrollBar.vertical: PanelScrollBar {", (ROOT / "quickshell/desktop-bar/panels/Handbook.qml").read_text())
        self.assertNotIn("PanelScrollBar", (ROOT / "quickshell/desktop-bar/settings/FamilySidebar.qml").read_text())

    def test_runtime_reader_is_read_only_and_offline(self):
        source = (ROOT / "quickshell/desktop-bar/panels/Handbook.qml").read_text()
        self.assertIn("readOnly: true", source)
        self.assertIn("FamilyWindow {", source)
        self.assertIn("LibraryWindow {", (ROOT / "quickshell/desktop-bar/settings/FamilyWindow.qml").read_text())
        shared = (ROOT / "quickshell/desktop-bar/components/LibraryWindow.qml").read_text()
        self.assertIn("FloatingWindow {", shared)
        self.assertIn("onClosed:", shared)
        self.assertNotIn('stateName', source)
        self.assertNotIn("execDetached", source)
        self.assertNotIn("Process {", source)
        self.assertNotIn("XMLHttpRequest", source)
        self.assertIn("FamilySidebar {", source)
        sidebar = (ROOT / "quickshell/desktop-bar/settings/FamilySidebar.qml").read_text()
        self.assertIn("EitrLogo {", sidebar)
        # The header logo matches the height of the EITR title and subtitle lines.
        self.assertIn("iconSize: 66", sidebar)
        self.assertIn("Model.articleBlocks(book.chapter)", source)
        self.assertIn("Model.sidebarEntries(book.chapters, book.filtered", source)
        self.assertIn("enabled: book.opened", source)

    def test_every_chapter_has_a_contiguous_group(self):
        chapters = json.loads((BOOK / "chapters.json").read_text())
        groups = [chapter["group"] for chapter in chapters]
        self.assertTrue(all(groups))
        seen = []
        for group in groups:
            if not seen or seen[-1] != group:
                self.assertNotIn(group, seen, "chapters of one group stay together")
                seen.append(group)
        for locale in ("de", "es", "fr", "pt_BR"):
            translated = json.loads((BOOK / "catalogs" / (locale + ".json")).read_text())["chapters"]
            self.assertEqual([chapter["id"] for chapter in translated], [chapter["id"] for chapter in chapters])
            self.assertTrue(all(chapter["group"] for chapter in translated))

    def test_rendering_blocks_preserve_code_entities_and_tables(self):
        html = '<h1>Title</h1>\n<p>Text &amp; more</p>\n<pre><code>&lt;esp&gt;</code></pre><table><tr><td>Key</td></tr></table>'
        pieces = builder.blocks(html)
        self.assertEqual(len(pieces), 4)
        self.assertIn("&lt;esp&gt;", pieces[2])
        self.assertEqual(pieces[3], '<table><tr><td>Key</td></tr></table>')

    def test_code_inside_list_items_renders_as_code(self):
        text = "1. Run this:\n\n   ```sh\n   sudo mount /dev/x /mnt\n   ```\n\n   Then reboot.\n"
        html = builder.markdown.markdown(builder.unnest_fences(text), extensions=["fenced_code"])
        self.assertIn('<pre><code class="language-sh">sudo mount /dev/x /mnt\n</code></pre>', html)
        for chapter in json.loads(builder.build())["chapters"]:
            self.assertFalse(any("```" in block or "<p><code>sh\n" in block for block in chapter["blocks"]), chapter["id"])

    def test_welcome_layout_comes_from_each_translated_chapter(self):
        definition = json.loads((BOOK / "chapters.json").read_text())[0]["welcome"]
        for locale in ("en", "de", "es", "fr", "pt_BR"):
            with self.subTest(locale=locale):
                chapter = json.loads(builder.build(locale))["chapters"][0]
                welcome = chapter["welcome"]
                self.assertTrue(welcome["title"] and welcome["lead"])
                self.assertEqual([step["id"] for step in welcome["tour"]["items"]], definition["tour"])
                self.assertEqual([card["route"] for card in welcome["setup"]["items"]],
                                 [card["route"] for card in definition["setup"]])
                for item in welcome["tour"]["items"] + welcome["setup"]["items"]:
                    self.assertTrue(item["title"] and item["text"], item)
                # The website reads every block; the reader replaces the hidden ones with its own layout.
                hidden = [chapter["blocks"][index] for index in welcome["hidden"]]
                self.assertTrue(hidden[0].startswith("<h1>") and hidden[1].startswith("<p>"))
                self.assertEqual(sum(block.startswith("<ul>") for block in hidden), 2)
                self.assertTrue(any(block.startswith("<h2>") for index, block in enumerate(chapter["blocks"])
                                    if index not in welcome["hidden"]), "further reading stays in the chapter")

    def test_welcome_markers_are_validated(self):
        definition = {"tour": ["one", "two"]}
        good = "# Hi\n\nLead.\n\n<!-- eitr-welcome:tour -->\n## Tour\n\n- **One**: First.\n- **Two**: Second.\n<!-- /eitr-welcome:tour -->\n"
        def parse(text):
            return builder.welcome(definition, builder.parse_blocks(builder.markdown.markdown(text)))
        self.assertEqual([item["title"] for item in parse(good)["tour"]["items"]], ["One", "Two"])
        for broken in (good.replace("- **Two**: Second.\n", ""), good.replace("<!-- /eitr-welcome:tour -->", ""),
                       good.replace("**Two**: Second.", "Two, second."), good.replace("# Hi\n\nLead.\n\n", "")):
            with self.assertRaises(ValueError):
                parse(broken)

    def test_figure_markers_become_captioned_figure_blocks(self):
        def parse(text):
            return builder.parse_blocks(builder.markdown.markdown(text)).blocks
        blocks = parse("# Hi\n\n<!-- eitr-figure: bar-anatomy -->\n\nThe **bar**.\n\nAfter.\n")
        self.assertEqual(blocks[1], '<figure data-figure="bar-anatomy"><figcaption>The <strong>bar</strong>.</figcaption></figure>')
        self.assertEqual(blocks[2], "<p>After.</p>")
        for broken in ("<!-- eitr-figure: unknown -->\n\nCaption.\n", "<!-- eitr-figure: launcher -->\n",
                       "<!-- eitr-figure: launcher -->\n\n## Heading\n",
                       "<!-- eitr-figure: launcher -->\n<!-- eitr-figure: launcher -->\n\nCaption.\n"):
            with self.assertRaises(ValueError):
                parse(broken)

    def test_every_figure_is_drawn_placed_and_kept_by_translations(self):
        figures = ROOT / "quickshell/desktop-bar/figures"
        qmldir = (ROOT / "quickshell/desktop-bar/qmldir").read_text()
        for name in builder.FIGURES:
            filename = "".join(word.capitalize() for word in name.split("-")) + "Figure.qml"
            self.assertTrue((figures / filename).is_file(), filename)
            self.assertIn(f"{filename[:-4]} figures/{filename}", qmldir)
            source = (figures / filename).read_text()
            for forbidden in ("Process {", "execDetached", "XMLHttpRequest", "FileView", "Timer {"):
                self.assertNotIn(forbidden, source, filename)
        english = {chapter["id"]: builder.figures(chapter["blocks"]) for chapter in json.loads(builder.build())["chapters"]}
        self.assertEqual(sorted(name for names in english.values() for name in names), sorted(builder.FIGURES))
        for locale in ("de", "es", "fr", "pt_BR"):
            for chapter in json.loads(builder.build(locale))["chapters"]:
                self.assertEqual(builder.figures(chapter["blocks"]), english[chapter["id"]], f"{locale}/{chapter['id']}")

    def test_launcher_figure_shows_the_settings_menu_rows(self):
        source = (ROOT / "quickshell/desktop-bar/figures/LauncherFigure.qml").read_text()
        drawn = re.findall(r'\{text: Eitr\.I18n\.tr\("([^"]+)"\), icon: "\\u\{([0-9A-F]+)\}"(?:, description: Eitr\.I18n\.tr\("([^"]+)"\))?\}', source)
        rows = json.loads((ROOT / "elephant/menu-rows/settings.json").read_text())
        self.assertEqual([(text, int(code, 16), description or ">") for text, code, description in drawn],
                         [(row["text"], ord(row["icon"]), row["subtext"]) for row in rows])

    def test_toggle_script_does_not_need_a_positional_argument(self):
        source = (ROOT / "quickshell/desktop-bar/scripts/handbook.sh").read_text()
        source = source.replace("sleep 0.2", "true").replace("exec eitr-shell", "printf '%s\\n'")
        result = subprocess.run(["bash", "-c", source], text=True, capture_output=True, check=True)
        self.assertTrue(result.stdout.rstrip().endswith("toggle"))


if __name__ == "__main__":
    unittest.main()
