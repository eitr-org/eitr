from pathlib import Path
import unittest
import os
import shutil
import subprocess
import tempfile
import re
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "distro/lib"))
from layout import Layout


class QmlRegistryTests(unittest.TestCase):
    def test_directory_registry_includes_all_named_components(self):
        root = Path(__file__).parents[1]
        registry = (root / 'qmldir').read_text()
        registered = {line.split()[-1] for line in registry.splitlines() if line.strip()}
        components = {file.relative_to(root).as_posix() for file in root.rglob('*.qml') if file.stem[0].isupper() and 'tests' not in file.parts}
        self.assertEqual(registered, components)
        self.assertIn('singleton DesktopFonts 1.0 services/DesktopFonts.qml', registry)


    def test_exports_keep_singleton_identity_and_ship_as_code(self):
        root = Path(__file__).parents[1]
        layout = Layout(REPO)
        for line in (root / "qmldir").read_text().splitlines():
            fields = line.split()
            source = root / fields[-1]
            with self.subTest(component=source.name):
                self.assertEqual(fields[0] == "singleton", "pragma Singleton" in source.read_text())
                rule = layout.classify(source.relative_to(REPO).as_posix())
                self.assertEqual(rule["class"], "C")
                self.assertTrue(rule["runtime"])
                if source.parent != root:
                    self.assertIn('import ".."', source.read_text())

    def test_relative_helpers_and_assets_resolve_from_component_folder(self):
        root = Path(__file__).parents[1]
        for line in (root / "qmldir").read_text().splitlines():
            source = root / line.split()[-1]
            urls = re.findall(r'import "([^"]+\.js)"|Qt\.resolvedUrl\("([^"+]+)"\)|icon\.source: "([^"]+)"', source.read_text())
            for alternatives in urls:
                relative = next(value for value in alternatives if value)
                with self.subTest(component=source.name, url=relative):
                    self.assertTrue((source.parent / relative).exists())




    def test_exported_payload_stages_every_registry_target(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            exported = Path(temporary) / "export"
            staged = Path(temporary) / "stage"
            for relative in ("distro/layout-manifest.json", "distro/legacy-layout.json",
                             "quickshell/desktop-bar/qmldir"):
                destination = exported / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO / relative, destination)
            targets = [line.split()[-1] for line in (root / "qmldir").read_text().splitlines()]
            for target in targets:
                destination = exported / "quickshell/desktop-bar" / target
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / target, destination)
            Layout(exported).stage(staged)
            for target in targets:
                self.assertEqual((root / target).read_bytes(),
                                 (staged / "quickshell/desktop-bar" / target).read_bytes())

    @unittest.skipUnless(shutil.which("quickshell"), "Quickshell required")
    def test_root_export_and_nested_component_share_one_singleton(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fixture = folder / "shell.qml"
            fixture.write_text('''import QtQuick
import Quickshell
import "BAR" as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 320; implicitHeight: 100
        Bar.PanelHeading {
            id: heading
            text: "Registry"; foreground: "white"; accent: "cyan"
        }
        Timer {
            interval: 200; running: true
            onTriggered: {
                Bar.DesktopFonts.family = "Monospace";
                Qt.callLater(function() {
                    const title = heading.children[1].children[0];
                    if (title.font.family !== Bar.DesktopFonts.family) {
                        console.error("SINGLETON_IDENTITY_FAILED"); Qt.exit(1); return;
                    }
                    heading.grabToImage(function(result) {
                        if (!result.saveToFile("CAPTURE")) { Qt.exit(1); return; }
                        console.log("GROUPED_REGISTRY_OK"); Qt.quit();
                    });
                });
            }
        }
    }
}
'''.replace("BAR", root.as_uri()).replace("CAPTURE", str(folder / "heading.png")))
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                               QML_IMPORT_PATH=str(root.parent), XDG_RUNTIME_DIR=temporary,
                               DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent",
                               HYPRLAND_INSTANCE_SIGNATURE="", EITR_CODE_ROOT=temporary)
            for kind in ("CONFIG", "CACHE", "STATE", "DATA"):
                environment[f"XDG_{kind}_HOME"] = str(folder / kind.lower())
            result = subprocess.run(["quickshell", "-p", str(fixture)], env=environment,
                                    text=True, capture_output=True, timeout=10)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("GROUPED_REGISTRY_OK", output)
            self.assertTrue((folder / "heading.png").is_file())


if __name__ == '__main__':
    unittest.main()
