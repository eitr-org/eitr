from pathlib import Path
import unittest


BAR = Path(__file__).resolve().parents[1]


class RealmEffectsTests(unittest.TestCase):
    def test_shell_hosts_the_effects_and_their_ipc(self):
        source = (BAR / "wallpaper/RealmEffects.qml").read_text()
        self.assertIn('target: "realm"', source)
        self.assertIn("function lightning(monitor: string, geometry: string): void", source)
        self.assertIn("function ragnarok(): void", source)
        self.assertIn("RealmEffects {", (BAR / "shell.qml").read_text())
        self.assertIn("RealmEffects wallpaper/RealmEffects.qml", (BAR / "qmldir").read_text())

    def test_lightning_never_takes_input(self):
        source = (BAR / "wallpaper/RealmEffects.qml").read_text()
        storm = source[source.index("id: storm"):source.index("id: fenrir")]
        self.assertIn("mask: Region {}", storm)
        self.assertIn("WlrKeyboardFocus.None", storm)

    def test_ragnarok_ends_with_the_bite_and_can_be_dismissed(self):
        source = (BAR / "wallpaper/RealmEffects.qml").read_text()
        self.assertIn("Keys.onEscapePressed: fenrir.dismiss()", source)
        self.assertIn("onClicked: fenrir.dismiss()", source)
        self.assertNotIn("takes shape", source)
        self.assertTrue((BAR / "assets/ragnarok/fenrir-bite.png").is_file())


if __name__ == "__main__":
    unittest.main()
