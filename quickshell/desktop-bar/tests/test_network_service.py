"""Exercise the production owner with fake helpers and offscreen QML consumers."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class NetworkServiceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "Quickshell unavailable")
    def test_shared_readers_actions_and_screen_destruction(self):
        bar = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="eitr-network-test-") as directory:
            root = Path(directory)
            for name in ("services/NetworkService.qml", "NetworkStatus.js", "services/DesktopData.qml", "DesktopDataProtocol.js"):
                (root / Path(name).name).write_text((bar / name).read_text().replace('import ".."\n', '').replace('"../', '"'))
            (root / "qmldir").write_text("singleton DesktopData DesktopData.qml\nNetworkService NetworkService.qml\n")
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("bar-data.py", "bar_data_topics.py", "capture-domain.py", "power-domain.py"):
                shutil.copy(bar / "scripts" / name, scripts / name)
            (scripts / "wifi-popup.py").write_text(
                'import json, os, sys, time\nfrom pathlib import Path\n'
                'def read_state(action, interface):\n'
                '    with Path(os.environ["NETWORK_TEST_LOG"]).open("a") as output: output.write(action + "\\n")\n'
                '    time.sleep(0.15)\n'
                '    fixtures = json.loads(Path(__file__).with_name("network.json").read_text())\n'
                '    return fixtures["latency"] if action == "probe" else fixtures["connected"]\n'
                'if __name__ == "__main__":\n'
                '    read_state(sys.argv[1], "")\n'
                '    assert json.loads(sys.stdin.readline())["password"] == "fixture-secret"\n'
                '    print(json.dumps({"ok": True}))\n')
            shutil.copy(bar / "tests/fixtures/network.json", scripts / "network.json")
            for name in ("network-reader.py", "network.json"):
                shutil.copy(bar / "tests/fixtures" / name, root / Path(name).name)
            shutil.copy(bar / "tests/fixtures/network-service.qml", root / "shell.qml")
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen",
                               QML_IMPORT_PATH=str(bar.parent),
                               DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent",
                               NETWORK_TEST_LOG=str(root / "launches"), XDG_RUNTIME_DIR=str(runtime))
            for kind in ("CONFIG", "CACHE", "STATE", "DATA"):
                environment[f"XDG_{kind}_HOME"] = str(root / kind.lower())
            for name in ("WAYLAND_DISPLAY", "DISPLAY", "QS_CONFIG_PATH", "QS_CONFIG_NAME"):
                environment.pop(name, None)
            result = subprocess.run(["quickshell", "--no-color", "-p", str(root / "shell.qml")],
                                    env=environment, capture_output=True, text=True, timeout=15)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("NETWORK PASS", output)
            self.assertNotIn("NETWORK FAIL", output)
            self.assertNotIn("ReferenceError", output)
            self.assertNotIn("TypeError", output)
            launches = (root / "launches").read_text().splitlines()
            self.assertEqual(launches.count("connect"), 1)
            self.assertNotIn("power", launches)
            self.assertEqual(launches.count("qr"), 1)
            self.assertEqual(launches.count("status"), 2, launches)
            self.assertEqual(launches.count("probe"), 1, launches)


if __name__ == "__main__":
    unittest.main()


class SubscriptionLifetimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "Quickshell unavailable")
    def test_plugin_loader_updates_owner_and_pending_query_destruction(self):
        bar = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="eitr-lifetimes-") as directory:
            root = Path(directory)
            for name in ("plugins/PluginComponent.qml", "services/UpdatesStatus.qml", "components/SpectrumConsumer.qml",
                         "PanelStyle.js", "Spectrum.js", "DesktopDataProtocol.js"):
                (root / Path(name).name).write_text((bar / name).read_text().replace('import ".."\n', '').replace('"../', '"'))
            (root / "WeatherWidget.qml").write_text('import QtQuick\nItem { property var host; property bool autoRefresh; property bool compact; property string temperature; signal clicked() }')
            # The Eitr controls offered to plugins, as inert stand-ins.
            for control in ("ChoiceDropdown", "PanelButton", "PanelTextField", "PanelSwitch"):
                (root / (control + ".qml")).write_text('import QtQuick\nItem { property color foreground; property color background; property color gold; property color accent; property string text }')
            (root / "DesktopData.qml").write_text('''pragma Singleton
import QtQuick
import "DesktopDataProtocol.js" as Protocol
QtObject {
    id: data
    property var topics: ({})
    property var wire: ({})
    property var client: Protocol.createClient(send, function() {})
    function send(frame) {
        if (frame.op === "subscribe") {
            if (wire[frame.token]) throw new Error("duplicate subscribe");
            wire[frame.token] = frame.topic;
        }
        if (frame.op === "unsubscribe") {
            if (!wire[frame.token]) throw new Error("duplicate unsubscribe");
            delete wire[frame.token];
        }
    }
    function observe(topic, owner) { return client.observe(topic, owner); }
    function releaseOwner(owner) { client.releaseOwner(owner); }
    function refresh(topic) { client.refresh(topic); }
    function count() { return Object.keys(client.tokens).length; }
    function hello(epoch) { client.receive(JSON.stringify({v: 1, op: "hello", epoch: epoch})); }
    function restart(epoch) { client.died(); wire = {}; hello(epoch); hello(epoch); }
}
''')
            stubs = {
                "DesktopFonts": 'property string family: "sans-serif"',
                "DesktopStyle": 'function radius(value) { return value; }',
                "PluginRegistry": 'property var palette: ({})\nfunction registerSource(entry) {}\nfunction recordError(plugin, source, line, error) {}',
                "SpectrumProvider": '''property var consumers: []
property bool audioActive: false
property var levels: []
property var config: ({smoothing: false})
function acquire(owner) { consumers = consumers.concat([owner]); }
function release(owner) { consumers = consumers.filter(existing => existing !== owner); }
function update() {}''',
            }
            registry = ['singleton DesktopData DesktopData.qml', 'PluginComponent PluginComponent.qml',
                        'UpdatesStatus UpdatesStatus.qml', 'SpectrumConsumer SpectrumConsumer.qml', 'BarTooltip BarTooltip.qml', 'WeatherWidget WeatherWidget.qml',
                        'ChoiceDropdown ChoiceDropdown.qml', 'PanelButton PanelButton.qml', 'PanelTextField PanelTextField.qml', 'PanelSwitch PanelSwitch.qml']
            for name, body in stubs.items():
                (root / (name + '.qml')).write_text('pragma Singleton\nimport QtQuick\nQtObject {\n' + body + '\n}\n')
                registry.append(f'singleton {name} {name}.qml')
            (root / 'qmldir').write_text('\n'.join(registry) + '\n')
            (root / 'BarTooltip.qml').write_text('''import QtQuick
QtObject { property var target; property bool hovered; property string text; property color foreground; property color background }
''')
            (root / 'Fixture.qml').write_text('''import QtQuick
Item {
    id: plugin
    required property var api
    Component.onCompleted: {
        DesktopData.observe("hardware.details", plugin);
        DesktopData.client.queryWeather("search", {query: "fixture"}, plugin, function(error, data) {
            if (error !== "broker-unavailable") throw new Error("late reply");
        });
    }
    Component.onDestruction: DesktopData.releaseOwner(plugin)
}
''')
            (root / 'shell.qml').write_text('''import QtQuick
import Quickshell
ShellRoot {
    id: harness
    property int phase: 0
    property int cycles: 0
    property int ticks: 0
    property var host: null
    property var updates: null
    function check(ok, message) { if (!ok) { console.error("LIFETIME FAIL", message); Qt.exit(1); } }
    Component { id: updateComponent; UpdatesStatus {} }
    Component {
        id: pluginComponent
        PluginComponent {
            width: 200; height: 60
            foreground: "white"; background: "black"; accent: "red"
            entry: ({plugin: "fixture", id: "fixture", title: "Fixture", qml: "Fixture.qml",
                source: Qt.resolvedUrl("Fixture.qml"), kind: "barItems", capabilities: ["audio-spectrum"]})
        }
    }
    Component.onCompleted: DesktopData.hello("initial")
    Timer {
        interval: 20; running: true; repeat: true
        onTriggered: {
            harness.check(++harness.ticks < 400, "deadline phase " + harness.phase);
            if (harness.phase === 0) {
                harness.check(DesktopData.count() === 0, "baseline");
                harness.updates = updateComponent.createObject(harness);
                harness.host = pluginComponent.createObject(harness);
                harness.phase = 1;
            } else if (harness.phase === 1) {
                if (DesktopData.client.count("hardware.details") !== 1) return;
                harness.check(DesktopData.count() === 2, "loaded observers");
                harness.check(SpectrumProvider.consumers.length === 1, "plugin spectrum acquired");
                DesktopData.restart("restart-" + harness.cycles);
                harness.check(Object.keys(DesktopData.wire).length === 2, "live observers replay once");
                harness.host.active = false;
                harness.updates.destroy();
                harness.phase = 2;
            } else if (harness.phase === 2) {
                harness.check(DesktopData.count() === 0, "unload releases tokens");
                harness.check(SpectrumProvider.consumers.length === 0, "spectrum released");
                harness.host.active = true;
                harness.phase = 3;
            } else if (harness.phase === 3) {
                if (DesktopData.count() !== 1) return;
                harness.host.destroy();
                harness.phase = 4;
            } else if (harness.phase === 4) {
                harness.check(DesktopData.count() === 0, "screen removal releases tokens");
                harness.check(SpectrumProvider.consumers.length === 0, "screen removal releases spectrum");
                // Unload before the asynchronous Loader completes.
                harness.host = pluginComponent.createObject(harness);
                harness.host.destroy();
                harness.phase = 5;
            } else {
                harness.check(DesktopData.count() === 0, "pending load destruction baseline");
                DesktopData.restart("empty-" + harness.cycles);
                harness.check(Object.keys(DesktopData.wire).length === 0, "removed owners never replay");
                if (++harness.cycles === 20) { console.log("LIFETIME PASS"); Qt.quit(); }
                harness.phase = 0;
            }
        }
    }
}
''')
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QUICK_BACKEND="software",
                               QML_IMPORT_PATH=str(bar.parent), DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent",
                               HYPRLAND_INSTANCE_SIGNATURE="", XDG_RUNTIME_DIR=str(root))
            for kind in ("CONFIG", "CACHE", "STATE", "DATA"):
                environment[f"XDG_{kind}_HOME"] = str(root / kind.lower())
            for name in ("WAYLAND_DISPLAY", "DISPLAY", "QS_CONFIG_PATH", "QS_CONFIG_NAME"):
                environment.pop(name, None)
            result = subprocess.run(["quickshell", "--no-color", "-p", str(root / "shell.qml")],
                                    env=environment, capture_output=True, text=True, timeout=12)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("LIFETIME PASS", output)
            for error in ("LIFETIME FAIL", "ReferenceError", "TypeError", "Error:"):
                self.assertNotIn(error, output)
