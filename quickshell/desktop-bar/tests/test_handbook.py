import importlib.util
import json
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
        for name in ("system", "system-connectivity", "system-devices", "system-information", "system-maintenance", "security"):
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

    def test_runtime_reader_is_read_only_and_offline(self):
        source = (ROOT / "quickshell/desktop-bar/panels/Handbook.qml").read_text()
        self.assertIn("readOnly: true", source)
        self.assertIn("FamilyWindow {", source)
        self.assertIn("LibraryWindow {", (ROOT / "quickshell/desktop-bar/settings/FamilyWindow.qml").read_text())
        shared = (ROOT / "quickshell/desktop-bar/components/LibraryWindow.qml").read_text()
        self.assertIn("FloatingWindow {", shared)
        self.assertIn("onClosed:", shared)
        self.assertIn('stateName: "handbook"', source)
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

    def test_toggle_script_does_not_need_a_positional_argument(self):
        source = (ROOT / "quickshell/desktop-bar/scripts/handbook.sh").read_text()
        source = source.replace("sleep 0.2", "true").replace("exec eitr-shell", "printf '%s\\n'")
        result = subprocess.run(["bash", "-c", source], text=True, capture_output=True, check=True)
        self.assertTrue(result.stdout.rstrip().endswith("toggle"))


if __name__ == "__main__":
    unittest.main()
