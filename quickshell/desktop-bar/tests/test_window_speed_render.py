"""Offscreen render and interaction verification for ControlCenterWindowInfo and ControlCenterSpeedTest."""
from pathlib import Path
import tempfile
import unittest

from layout_render import capture_path, copy_runtime, render, render_environment


def write_mock_desktop_data(folder: Path) -> None:
    (folder / "services/DesktopData.qml").write_text(
        """pragma Singleton
import QtQuick
QtObject {
    property var topics: ({})
    property var calls: []
    property var cancelled: []
    property int seq: 0
    function observe(topic, owner, interval) { return topic; }
    function release(token) {}
    function releaseOwner(owner) {}
    function refresh(topic) {}
    function queryWindow(name, args, owner, callback) {
        seq += 1;
        calls = calls.concat([{topic: "window", name: name, args: args}]);
        const win = {
            address: "0x55a1b2",
            title: "neovim — ~/eitr",
            "class": "kitty",
            initialClass: "kitty",
            pid: 4242,
            process: "kitty",
            workspace: {id: name === "move" ? args.workspace : 2, name: String(name === "move" ? args.workspace : 2)},
            at: [48, 64],
            size: [1120, 760],
            floating: name === "float",
            pinned: name === "pin",
            fullscreen: 0
        };
        const workspaces = [
            {id: 1, name: "1"},
            {id: 2, name: "2"},
            {id: 3, name: "3"},
            {id: 4, name: "4"}
        ];
        if (callback) callback("", name === "close" ? {window: null, workspaces: workspaces, closed: true} : {window: win, workspaces: workspaces});
        return "win-" + seq;
    }
    function querySpeed(name, args, owner, callback) {
        seq += 1;
        calls = calls.concat([{topic: "speed", name: name, args: args}]);
        if (name === "disk") {
            if (callback) callback("", {kind: "disk", writeMBps: 1420.5, readMBps: 2890.3, bytes: 268435456, durationMs: 412});
        } else if (name === "network") {
            if (callback) callback("", {kind: "network", latencyMs: 12.4, downloadMbps: 412.8, uploadMbps: 185.2, service: "speed.cloudflare.com"});
        }
        return "spd-" + seq;
    }
    function cancelQuery(id) {
        cancelled = cancelled.concat([id]);
    }
}
"""
    )


class WindowSpeedRenderTests(unittest.TestCase):
    def test_window_info_and_speed_test_render_and_interactions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtime"
            runtime.mkdir()
            copy_runtime(runtime)
            write_mock_desktop_data(runtime)

            win_dark = capture_path("WINDOW_SPEED", root, "window-info-dark.png")
            win_light = capture_path("WINDOW_SPEED", root, "window-info-light.png")
            spd_dark = capture_path("WINDOW_SPEED", root, "speed-test-dark.png")
            spd_light = capture_path("WINDOW_SPEED", root, "speed-test-light.png")

            harness = runtime / "test_window_speed_harness.qml"
            harness.write_text(
                f"""import "."
import QtQuick
import QtQuick.Window
import Quickshell

ShellRoot {{
    id: root
    property var centerMock: ({{lastActiveWindowAddress: "0x55a1b2"}})
    Window {{
        id: winDarkWin
        visible: true
        width: 460
        height: 460
        color: "#1b1f27"
        Rectangle {{ anchors.fill: parent; color: "#1b1f27" }}
        ControlCenterWindowInfo {{
            id: winDark
            x: 16; y: 16; width: 428
            centerRef: root.centerMock
            shown: true
            foreground: "#e6edf3"
            background: "#1b1f27"
            accent: "#7aa2f7"
        }}
    }}
    Window {{
        id: winLightWin
        visible: true
        width: 460
        height: 460
        color: "#f4f6f9"
        ControlCenterWindowInfo {{
            id: winLight
            x: 16; y: 16; width: 428
            centerRef: root.centerMock
            shown: true
            foreground: "#1c2128"
            background: "#f4f6f9"
            accent: "#2563eb"
        }}
    }}
    Window {{
        id: spdDarkWin
        visible: true
        width: 460
        height: 440
        color: "#1b1f27"
        Rectangle {{ anchors.fill: parent; color: "#1b1f27" }}
        ControlCenterSpeedTest {{
            id: spdDark
            x: 16; y: 16; width: 428
            centerRef: root.centerMock
            foreground: "#e6edf3"
            background: "#1b1f27"
            accent: "#7aa2f7"
        }}
    }}
    Window {{
        id: spdLightWin
        visible: true
        width: 460
        height: 440
        color: "#f4f6f9"
        ControlCenterSpeedTest {{
            id: spdLight
            x: 16; y: 16; width: 428
            centerRef: root.centerMock
            foreground: "#1c2128"
            background: "#f4f6f9"
            accent: "#2563eb"
        }}
    }}
    Timer {{
        interval: 250
        running: true
        onTriggered: {{
            spdDark.runDisk();
            spdDark.runNetwork();
            spdLight.runDisk();
            spdLight.runNetwork();
            winDark.act("float", {{}});
            if (!winDark.windowData || !winDark.windowData.floating) {{
                console.error("Expected floating=true after float action");
                Qt.exit(2);
                return;
            }}
            winDark.act("pin", {{}});
            if (!winDark.windowData || !winDark.windowData.pinned) {{
                console.error("Expected pinned=true after pin action");
                Qt.exit(3);
                return;
            }}
            winDark.act("move", {{workspace: 3}});
            if (!winDark.windowData || winDark.windowData.workspace.id !== 3) {{
                console.error("Expected workspace=3 after move action");
                Qt.exit(4);
                return;
            }}
            winDark.act("float", {{}});
            captureTimer.start();
        }}
    }}
    Timer {{
        id: captureTimer
        interval: 150
        onTriggered: {{
            winDarkWin.contentItem.grabToImage(function(res1) {{
                res1.saveToFile("{win_dark}");
                winLightWin.contentItem.grabToImage(function(res2) {{
                    res2.saveToFile("{win_light}");
                    spdDarkWin.contentItem.grabToImage(function(res3) {{
                        res3.saveToFile("{spd_dark}");
                        spdLightWin.contentItem.grabToImage(function(res4) {{
                            res4.saveToFile("{spd_light}");
                            Qt.quit();
                        }});
                    }});
                }});
            }});
        }}
    }}
}}
"""
            )
            code, output = render(harness, render_environment(root, (600, 600)), 15)
            self.assertEqual(code, 0, output)
            for path in (win_dark, win_light, spd_dark, spd_light):
                self.assertTrue(path.is_file() and path.stat().st_size > 1000, f"Missing capture: {path}")


if __name__ == "__main__":
    unittest.main()
