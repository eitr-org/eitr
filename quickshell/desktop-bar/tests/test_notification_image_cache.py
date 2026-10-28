import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]


class NotificationImageCacheTests(unittest.TestCase):
    def test_notification_card_actions_in_popup_and_history(self):
        bar = ROOT / 'quickshell/desktop-bar'
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / 'shell.qml'
            source = (bar / 'tests/tst_notification_card.qml').read_text()
            source = source.replace('import ".."', 'import Quickshell\nimport "' + bar.as_uri() + '"')
            source = source.replace('when: windowShown', 'when: true')
            source = source.replace('TestCase {', 'ShellRoot { FloatingWindow { visible: true; implicitWidth: 440; implicitHeight: 420\nTestCase {', 1) + '\n}}\n'
            fixture.write_text(source)
            result = subprocess.run(['quickshell', '-p', str(fixture)],
                env=dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                    QML_IMPORT_PATH=str(bar.parent), EITR_CODE_ROOT=str(ROOT),
                    XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                    XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                    DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE=''),
                text=True, capture_output=True, timeout=20)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn('REMINDER_ACTIONS_OK_true', output)
            self.assertIn('REMINDER_ACTIONS_OK_false', output)
            self.assertNotIn('FAIL!', output)

    def test_bulk_dismiss_publishes_one_history_update(self):
        source = (ROOT / "quickshell/desktop-bar/NotificationService.qml").read_text()
        state = source[source.index("    readonly property var tracked:"):source.index("    readonly property var history:")]
        state = state.replace("readonly property var tracked: server.trackedNotifications.values", "property var tracked: []")
        clear = re.search(r"    function clear\(\) \{.*?\n    \}", source, re.S).group()
        fixture = """import QtQuick
import QtTest
TestCase {
    id: service
    name: "NotificationBulkDismiss"
    when: windowShown
    property var popupIds: []
""" + state + clear + """
    SignalSpy { id: changes; target: service; signalName: "allChanged" }
    function test_clear_coalesces_cards() {
        var notices = [];
        for (var index = 0; index < 43; index++) {
            notices.push({id: index, dismiss: function() { service.tracked = service.tracked.slice(1); }});
        }
        tracked = notices;
        tryVerify(function() { return service.all.length === 43; });
        changes.clear();
        service.clear();
        compare(tracked.length, 0);
        compare(changes.count, 0);
        tryVerify(function() { return service.all.length === 0; });
        compare(changes.count, 1);
    }
}
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tst_bulk.qml"
            path.write_text(fixture)
            result = subprocess.run(["/usr/lib/qt6/bin/qmltestrunner", "-input", str(path)],
                                    env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                                    text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_thumbnail_remains_available_after_sender_deletes_file(self):
        with tempfile.TemporaryDirectory(prefix="eitr-notification-test-") as directory:
            target = Path(directory)
            fixture = target / "tst_notification_image_cache.qml"
            shutil.copyfile(Path(__file__).with_name(fixture.name), fixture)
            thumbnail = target / "thumbnail.png"
            shutil.copyfile(ROOT / "branding/png/eitr-logo-green-64.png", thumbnail)
            process = subprocess.Popen(
                ["/usr/lib/qt6/bin/qmltestrunner", "-input", str(fixture)],
                env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            output = []
            try:
                for line in process.stdout:
                    output.append(line)
                    if "THUMBNAIL_LOADED" in line:
                        thumbnail.unlink()
                self.assertEqual(process.wait(timeout=10), 0, "".join(output))
                self.assertFalse(thumbnail.exists(), "Sender cleanup was not exercised")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                process.stdout.close()
