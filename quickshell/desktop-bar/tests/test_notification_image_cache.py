import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]


class NotificationImageCacheTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
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
        source = (ROOT / "quickshell/desktop-bar/notifications/NotificationService.qml").read_text()
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

    def test_large_image_burst_respects_byte_budget(self):
        # Exercise the production QML retain/evict code with real decoded fixtures.
        bar = ROOT / "quickshell/desktop-bar"
        source = (bar / "notifications/NotificationService.qml").read_text()
        retention = source[source.index("    Component {\n        id: retainedImageComponent"):source.index("    onPopupIdsChanged:")]
        receipt = re.search(r"        onNotification: function\(notification\) \{.*?\n        \}", source, re.S).group()
        receipt = receipt.replace("onNotification: function", "function receiveNotification", 1)
        scheduling = re.search(r"    function scheduleExpiry\(\) \{.*?\n    \}", source, re.S).group()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            # Uncompressed PPM keeps this fixture independent of image libraries.
            image = target / "large.ppm"
            image.write_bytes(b"P6\n2048 1536\n255\n" + bytes([40, 100, 160]) * (2048 * 1536))
            fixture = target / "tst_budget.qml"
            fixture.write_text("""import QtQuick
import QtTest
import """ + '"' + (bar / "NotificationLogic.js").as_uri() + '" as Logic\n' + """
TestCase {
    id: service
    name: "NotificationImageBudget"
    when: windowShown
    property var retainedImages: ({})
    property var imageOrder: []
    property var popupIds: []
    property bool centerOpen: false
    property bool doNotDisturb: false
    property int retainedImageBudget: 3 * 160 * 120 * 4
    property int retainedImageBytes: 0
    property var all: []
    property var tracked: []
    property var timestamps: ({})
    property var popupDeadlines: ({})
    property var pausedPopupIds: []
    Timer { id: expiry }
""" + retention + scheduling + receipt + """
    function test_deadlines() {
        var now = Date.now();
        all = [{id: 1, appName: "Chat"}, {id: 2, appName: "Reminders", expireTimeout: 1000}];
        popupIds = [1];
        popupDeadlines = {1: now + 5000};
        timestamps = {2: now};
        scheduleExpiry();
        verify(expiry.running);
        verify(expiry.interval > 0 && expiry.interval <= 1000);
        all = [all[0]];
        scheduleExpiry();
        verify(expiry.interval > 1000 && expiry.interval <= 5000);
        pausedPopupIds = [1];
        scheduleExpiry();
        verify(!expiry.running);
        all = [];
        pausedPopupIds = [];
    }
    function test_burst() {
        for (var index = 1; index <= 150; index++) {
            popupIds = [index];
            var notice = {id: index, appName: "Screenshot Test", image: Qt.resolvedUrl("large.ppm?" + index)};
            tracked = tracked.concat([notice]);
            receiveNotification(notice);
            verify(retainedImageBytes <= retainedImageBudget);
            compare(retainedImages[index].status, Image.Ready);
            verify(retainedImages[index].sourceSize.width <= 160);
            verify(retainedImages[index].sourceSize.height <= 120);
        }
        verify(!retainedImages[1]);
        verify(!!retainedImages[150]);
        // Open-center cards and popups survive pressure, then trim on hiding.
        centerOpen = true;
        for (var extra = 151; extra <= 155; extra++) {
            retainImage({id: extra, image: Qt.resolvedUrl("large.ppm?" + extra)});
            trimImages();
        }
        verify(!!retainedImages[150]);
        verify(!!retainedImages[155]);
        verify(retainedImageBytes > retainedImageBudget);
        centerOpen = false;
        popupIds = [150, 155];
        tracked = [{id: 150, appName: "First"}, {id: 155, appName: "Second"}];
        trimImages();
        verify(retainedImageBytes <= retainedImageBudget);
        verify(!!retainedImages[150]);
        verify(!!retainedImages[155]);
        retainImage({id: 155, image: Qt.resolvedUrl("large.ppm?replacement")});
        trimImages();
        compare(imageOrder.filter(value => value === 155).length, 1);
        imageOrder.slice().forEach(id => releaseImage(id));
        compare(retainedImageBytes, 0);
    }
}
""")
            result = subprocess.run(["/usr/lib/qt6/bin/qmltestrunner", "-input", str(fixture)],
                                    env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                                    text=True, capture_output=True, timeout=30)
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
