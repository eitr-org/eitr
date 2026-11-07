import importlib.util
import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import re
import tempfile
import tomllib
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
spec = importlib.util.spec_from_file_location("welcome_state", ROOT / "scripts/welcome-state.py")
welcome_state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(welcome_state)


def run(*args):
    output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(io.StringIO()):
        code = welcome_state.main(list(args))
    return code, json.loads(output.getvalue()) if code == 0 else None


class WelcomeStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        patcher = patch.dict(os.environ, {"XDG_STATE_HOME": self.directory.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.state = Path(self.directory.name) / "eitr"

    def mark_installed(self):
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "installed-paths").write_text(".config/quickshell\n")

    def test_state_lives_under_xdg_state_home(self):
        self.assertEqual(welcome_state.state_dir(), self.state)
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "", "XDG_CACHE_HOME": "", "XDG_STATE_HOME": "", "XDG_DATA_HOME": ""}), patch.object(Path, "home", return_value=Path("/h")):
            self.assertEqual(welcome_state.state_dir(), Path("/h/.local/state/eitr"))

    def test_existing_desktop_without_installer_record_is_not_interrupted(self):
        self.assertEqual(run("status"), (0, {"show": False, "dismissed": False, "pending": False}))
        self.assertFalse(self.state.exists(), "status must not create state")

    def test_first_run_after_install_shows(self):
        self.mark_installed()
        self.assertTrue(run("status")[1]["show"])

    def test_dismiss_prevents_showing_again(self):
        self.mark_installed()
        self.assertFalse(run("dismiss")[1]["show"])
        self.assertTrue((self.state / "welcome-dismissed").exists())
        self.assertFalse(run("status")[1]["show"])

    def test_remind_shows_next_login_even_without_installer_record(self):
        self.assertTrue(run("remind")[1]["show"])
        self.assertTrue(run("status")[1]["pending"])
        self.assertEqual(run("dismiss")[1], {"show": False, "dismissed": True, "pending": False})
        self.assertFalse((self.state / "welcome-pending").exists())

    def test_remind_clears_an_earlier_dismissal(self):
        self.mark_installed()
        run("dismiss")
        self.assertEqual(run("remind")[1], {"show": True, "dismissed": False, "pending": True})

    def test_unknown_command_is_rejected(self):
        self.assertEqual(run("reset")[0], 2)
        self.assertEqual(run()[0], 2)


class HandbookWelcomeTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "panels/Handbook.qml").read_text()
        self.welcome = "\n".join(path.read_text() for path in sorted((ROOT / "welcome").glob("*.qml")))

    def test_welcome_uses_shared_components_and_text_roles(self):
        for name in ("PanelButton {", "PanelSwitch {", "ControlCard {", "ControlRow {", "PanelStyle.captionSize",
                     "SettingsPalette.line", "SettingsInk.gold", "SiteStyle.carved", "BarPreview {", "PalettePreview {",
                     "WallpaperArt {", "DesktopStyle.motionDuration("):
            self.assertIn(name, self.welcome)
        self.assertIn("FamilyPageHeader {", self.source)
        self.assertIn("WelcomePage {", self.source)
        for source in (self.source, self.welcome):
            self.assertNotIn("SiteButton", source)
            self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", source), "colors must use the shared Settings palette")
            self.assertNotIn("execDetached", source)
            self.assertNotIn("Process {", source)
            for pattern in ("/home/", "/Users/", "erick", "~/"):
                self.assertNotIn(pattern, source)
        for name in ("WelcomePage", "WelcomeHero", "WelcomeTour", "WelcomeTourArt", "WelcomeSetupCards", "WelcomeMore"):
            self.assertIn(f"{name} welcome/{name}.qml", (ROOT / "qmldir").read_text())

    def test_tour_advances_on_its_own_pauses_on_hover_and_follows_the_keyboard(self):
        tour = (ROOT / "welcome/WelcomeTour.qml").read_text()
        self.assertIn("interval: 6000; repeat: true", tour)
        self.assertIn("running: tour.active && tour.visible && !hover.hovered", tour)
        self.assertIn("HoverHandler { id: hover }", tour)
        self.assertIn('book.welcomeVisible && !event.modifiers && (event.key === Qt.Key_Left || event.key === Qt.Key_Right)', self.source)
        self.assertIn("artSource: wallpaper.source", self.source)
        self.assertIn("CurrentWallpaper { id: wallpaper; live: book.opened }", self.source)

    def test_setup_cards_open_existing_settings_pages(self):
        chapters = json.loads((ROOT / "handbook/chapters.json").read_text())
        setup = chapters[0]["welcome"]["setup"]
        self.assertEqual([card["id"] for card in setup], ["wifi", "appearance", "keyboard", "picture", "displays"])
        self.assertTrue(all(card["icon"] for card in setup), "every setup card needs its glyph")
        index = (ROOT / "settings/SettingsIndex.js").read_text()
        pages = json.JSONDecoder().raw_decode(index.split("\nvar pages = ", 1)[1])[0]
        page_ids = {page["id"] for page in pages}
        for card in setup:
            page, _, tab = card["route"].partition("/")
            self.assertIn(page, page_ids, card["route"])
            if tab:
                tabs = re.search(r"^    " + page + r": \[(.*)\],?$", index, re.MULTILINE)
                self.assertIn('{id: "' + tab + '"', tabs.group(1), card["route"])
        session = (ROOT / "services/WelcomeSession.qml").read_text()
        self.assertIn("onSetupRequested: function(route) { host.showSettings(route); }", session)
        self.assertIn("function showSettings(page) { settingsWindow.show(page); }", (ROOT / "shell.qml").read_text())
        self.assertIn("onSetupRequested: route => book.openStep(route)", self.source)
        self.assertIn("function openStep(route) { setupRequested(route); }", self.source)

    def test_welcome_is_the_first_chapter_and_opens_once_per_session(self):
        chapters = json.loads((ROOT / "handbook/chapters.json").read_text())
        first = chapters[0]["id"] if isinstance(chapters, list) else chapters["chapters"][0]["id"]
        self.assertEqual(first, "getting-started")
        self.assertIn('welcomeChapter: "getting-started"', self.source)
        shell = (ROOT / "shell.qml").read_text() + (ROOT / "services/WelcomeSession.qml").read_text()
        self.assertIn('reloadableId: "handbookWelcomeSession"', shell)
        self.assertIn('command: session.welcomeCommand("status")', shell)
        self.assertIn("if (state.show) handbook.showWelcome(state.pending);", shell)
        self.assertIn('if (welcomeShown && !showAtLogin) welcomeChoice("dismiss");', self.source)

    def test_only_its_own_controls_close_the_handbook(self):
        closers = [line.strip() for line in self.source.splitlines() if "opened = false" in line]
        expected = ("function close()", "Key_Escape", "onCloseRequested:")
        self.assertEqual(len(closers), len(expected), closers)
        for line, marker in zip(closers, expected):
            self.assertIn(marker, line)
        self.assertIn('closeName: Eitr.I18n.tr("Close handbook")', self.source)
        sidebar = (ROOT / "settings/FamilySidebar.qml").read_text()
        self.assertEqual(sidebar.count("sidebar.closeRequested()"), 1, "only the header's close button asks to close")
        self.assertIn("Accessible.name: sidebar.closeName", sidebar)

    def test_the_old_welcome_panel_is_gone(self):
        self.assertFalse((ROOT / "WelcomeMenu.qml").exists())
        self.assertNotIn("WelcomeMenu", (ROOT / "qmldir").read_text())
        self.assertNotIn("welcomeMenu", (ROOT / "shell.qml").read_text())

    def test_learn_offers_the_handbook_whose_first_chapter_is_the_welcome(self):
        # Learn lists the Handbook itself, not its chapters; the welcome is reopened inside it.
        learn = {"entries": json.loads((REPO / "elephant/menu-rows/learn.json").read_text())}
        texts = [entry["text"] for entry in learn["entries"]]
        self.assertIn("EITR Handbook", texts)
        self.assertNotIn("Welcome", texts)
        self.assertFalse(any("handbook.sh open" in entry.get("actions", {}).get("open", "") for entry in learn["entries"]))
        self.assertIn("**Learn > EITR Handbook**", (REPO / "quickshell/desktop-bar/handbook/content/getting-started.md").read_text())


if __name__ == "__main__":
    unittest.main()
