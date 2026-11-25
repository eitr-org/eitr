"""Offscreen render and interaction verification for the Bar icon organizer and bar layouts."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from layout_render import BAR, capture_path, copy_runtime, render, render_environment

ROOT = Path(__file__).resolve().parents[3]


def _setup_mock_singletons(folder: Path, with_plugins: bool = True) -> None:
    (folder / "services/DesktopData.qml").write_text(
        """pragma Singleton
import QtQuick
QtObject {
    property var topics: ({
        "weather.default": {status: "ready", data: {temp: "21°C", text: "󰖐 21°C", location: "Lisbon", condition: "Clear", feels: "21°C", wind: "10 km/h", humidity: "55%", forecast: "Clear"}},
        "updates.status": {status: "ready", seq: 1, inFlight: false, data: {count: 0, repository: 0, aur: 0, downloadBytes: 0}},
        "power.battery": {status: "ready", data: {available: true, percent: 84, status: "Discharging", health: 98, hours: 6}},
        "power.profile": {status: "ready", data: {available: false, active: "", profiles: []}},
        "power.radios": {status: "ready", data: {available: false, enabled: false}},
        "ai.usage": {status: "ready", data: {providers: []}},
        "display.settings": {status: "ready", data: {monitors: [{name: "eDP-1", mode: "1920x1080@60", modes: ["1920x1080@60Hz"], scale: 1, transform: 0, position: "0x0"}]}},
        "network.details": {status: "ready", data: {backend: "iwd", devices: []}},
        "keyboard.layouts": {status: "ready", data: {current: "us", layouts: [{name: "us", variant: "", label: "English", code: "US"}, {name: "br", variant: "", label: "Portuguese", code: "BR"}], active: 0}},
        "obs.state": {status: "ready", data: {recording: false, paused: false, streaming: false}},
        "calendar.events": {status: "ready", data: {events: []}},
        "clock.timers": {status: "ready", data: {timers: []}},
        "remote.streaming": {status: "ready", data: {streaming: false, clients: []}}
    })
    property var client: QtObject {
        function detachAction(identifier) {}
        function setCapturePresence(present) {}
        function actPower(name, args, callback) { if (callback) callback("", {}); }
    }
    property var powerDomain: ({busy: false})
    property var captureDomain: ({busy: false})
    property var networkDomain: ({busy: false})
    function setCapturePresence(present) {}
    function observe(topic, owner, interval) { return topic; }
    function release(token) {}
    function releaseOwner(owner) {}
    function refresh(topic) {}
    function queryCatalog(name, args, owner, callback) { if (callback) callback("", {}); }
    function cancelQuery(token) {}
}
"""
    )
    (folder / "services/DisplayService.qml").write_text(
        """pragma Singleton
import QtQuick
QtObject {
    property var topology: ({primary: "eDP-1", windowGaps: [5, 5, 5, 5], screenGaps: [12, 12, 12, 12], monitors: [{name: "eDP-1", width: 1920, height: 1080, refreshRate: 60}]})
    function open(owner, interval) {}
    function close(owner) {}
    function pauseBrightness(owner) {}
    function resumeBrightness(owner) {}
    function pauseNightlight(owner) {}
    function resumeNightlight(owner) {}
    function refresh() {}
    function refreshBrightness() {}
}
"""
    )
    (folder / "services/PowerService.qml").write_text(
        """pragma Singleton
import QtQuick
QtObject {
    property var battery: ({available: true, percent: 84, status: "Discharging", health: 98, hours: 6})
    property var profile: ({available: false, active: "", profiles: []})
    property var radios: ({available: false, enabled: false})
    property bool busy: false
    function observe(owner, interval, radios) { return []; }
    function release(tokens) {}
    function refresh() {}
    function act(name, value, callback) {}
}
"""
    )
    (folder / "services/AudioDevices.qml").write_text(
        """pragma Singleton
import QtQuick
QtObject {
    property var sink: null
    property var source: null
    property real volume: 0.5
    property bool muted: false
    function refresh() {}
    function choices(kind) { return []; }
    function activeLabel(kind) { return ""; }
    function select(kind, name) {}
}
"""
    )
    (folder / "services/FocusMode.qml").write_text(
        """pragma Singleton
import QtQuick
QtObject { property bool enabled: false }
"""
    )
    (folder / "notifications/NotificationPopups.qml").write_text(
        """import QtQuick
Item {
    property var screen
    property bool shown: false
    property var service
    property color foreground
    property color background
    property color accent
    property string barEdge: "top"
    visible: false
}
"""
    )
    (folder / "overview/WorkspaceOverview.qml").write_text(
        """import QtQuick
Item {
    property var workspaceRows: []
    property var monitorName
    property bool ipcEnabled: false
    property var screen
    property color foreground
    property color background
    property color accent
    property bool opened: false
    visible: false
}
"""
    )
    (folder / "dock/EdgeDock.qml").write_text(
        """import QtQuick
Item {
    property var screen
    property string barEdge: "top"
    property var clients: []
    property bool dockEnabled: false
    property bool dockPreviews: true
    property color foreground
    property color background
    property color accent
    visible: false
}
"""
    )
    if with_plugins:
        (folder / "SampleWorldClock.qml").write_text(
            """import QtQuick
Item {
    required property var api
    implicitWidth: 68
    implicitHeight: 24
    Text { anchors.centerIn: parent; text: "LIS 14:05"; color: parent.api.foreground; font.family: parent.api.fontFamily; font.pixelSize: 12; font.bold: true }
}
"""
        )
        (folder / "SampleQuickNote.qml").write_text(
            """import QtQuick
Item {
    required property var api
    implicitWidth: 24
    implicitHeight: 24
    Text { anchors.centerIn: parent; text: parent.api.icon || "󰎞"; color: parent.api.foreground; font.family: parent.api.fontFamily; font.pixelSize: 15 }
}
"""
        )
        (folder / "SamplePluginPanel.qml").write_text(
            """import QtQuick
Item {
    required property var api
    implicitWidth: 320
    implicitHeight: 160
    Text { anchors.centerIn: parent; text: "Plugin panel"; color: parent.api.foreground; font.family: parent.api.fontFamily; font.pixelSize: 15 }
}
"""
        )
        weather_qml = (ROOT / "distro/plugins/bundled/weather/Weather.qml").as_uri()
        clock_qml = (folder / "SampleWorldClock.qml").as_uri()
        note_qml = (folder / "SampleQuickNote.qml").as_uri()
        panel_qml = (folder / "SamplePluginPanel.qml").as_uri()
        placed = [
            {"plugin": "ai-usage", "id": "usage", "kind": "barItems", "title": "AI Usage", "icon": "", "slot": "start", "panel": "limits", "bundled": True},
            {"plugin": "hardware", "id": "monitor", "kind": "barItems", "title": "Hardware", "icon": "󰍛", "slot": "start", "panel": "details", "bundled": True},
            {"plugin": "weather", "id": "weather", "kind": "barItems", "title": "Weather", "icon": "󰖐", "slot": "clockEnd", "panel": "forecast", "capabilities": ["weather"], "disabled": False, "qml": weather_qml, "source": weather_qml},
            {"plugin": "worldclock", "id": "clock", "kind": "barItems", "title": "World clock", "icon": "󰥔", "slot": "clock", "panel": "panel", "capabilities": [], "disabled": False, "qml": clock_qml, "source": clock_qml},
            {"plugin": "notes", "id": "quick", "kind": "barItems", "title": "Quick note", "icon": "󰎞", "slot": "status", "panel": "panel", "capabilities": [], "disabled": False, "qml": note_qml, "source": note_qml},
        ]
        entries = placed + [
            {"plugin": "worldclock", "id": "panel", "kind": "panels", "title": "World clock", "disabled": False, "qml": panel_qml, "source": panel_qml, "surface": "panel", "width": 320, "maxHeight": 200},
            {"plugin": "notes", "id": "panel", "kind": "panels", "title": "Quick note", "disabled": False, "qml": panel_qml, "source": panel_qml, "surface": "panel", "width": 320, "maxHeight": 200},
        ]
        (folder / "plugins/PluginRegistry.qml").write_text(
            f"""pragma Singleton
import QtQuick
QtObject {{
    signal reviewStarted()
    property string clockFormat: "24h"
    property var palette: ({{}})
    property var providers: []
    property var entries: {json.dumps(entries)}
    property var placedBarItems: {json.dumps(placed)}
    readonly property bool weatherEnabled: true
    readonly property bool aiUsageEnabled: true
    readonly property bool hardwareEnabled: true
    function barItemShown(plugin, itemId) {{ return true; }}
    function slotItems(slot) {{ return placedBarItems.filter(entry => (entry.slot || "status") === slot); }}
    function registerSource(entry) {{}}
    function unregisterSource(entry) {{}}
    function refresh() {{}}
    function startDiagnostics() {{}}
    function recordError(plugin, source, line, msg) {{}}
}}
"""
        )


def _save_optional_render(source_png: Path, name: str) -> None:
    target_dir = os.environ.get("EITR_ORGANIZER_RENDERS")
    if target_dir and source_png.is_file():
        out_dir = Path(target_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_png, out_dir / name)


def _adapt_bar_window(folder: Path) -> None:
    src = (BAR / "bar/BarWindow.qml").read_text()
    src = src.replace("import Quickshell.Wayland\n", "")
    src = src.replace("PanelWindow {\n    id: bar", "FloatingWindow {\n    id: bar\n    visible: true")
    src = src.replace("    screen: modelData\n", "    property var screen: modelData\n")
    src = src.replace("    exclusionMode: ExclusionMode.Normal\n", "")
    src = src.replace("    WlrLayershell.namespace: \"desktop-bar\"\n", "")
    src = '\n'.join(line for line in src.split('\n') if not line.startswith((
        '    WlrLayershell.layer:', '    WlrLayershell.keyboardFocus:')))
    src = src.replace("    mask: shown ? dockInput : hiddenInput\n", "")
    src = src.replace("    Region { id: hiddenInput }\n", "")
    src = src.replace("anchors {\n        top: !host.verticalBar || host.barEdge !== \"bottom\"\n        bottom: !host.verticalBar || host.barEdge !== \"top\"\n        left: host.verticalBar || host.barEdge !== \"right\"\n        right: host.verticalBar || host.barEdge !== \"left\"\n    }", "property var anchorsMock: ({})")
    # Remove the trailing anchors block inside PanelWindow lines 220-230 too if phrased differently
    lines = []
    skip_drag_window = False
    for line in src.splitlines():
        if "anchors { top: true; bottom: true; left: true; right: true }" in line:
            continue
        if "PanelWindow {" in line:
            skip_drag_window = True
            lines.append("    Item { visible: false")
            continue
        if skip_drag_window and ("WlrLayershell." in line or "exclusionMode:" in line or "mask: Region" in line or "screen: bar.screen" in line or "color: \"transparent\"" in line or "visible: host.dragCandidate" in line):
            continue
        if "exclusiveZone:" in line:
            continue
        if "anchors.top: host.barEdge === \"top\"" in line or "anchors.bottom: host.barEdge === \"bottom\"" in line or "anchors.left: host.barEdge === \"left\"" in line or "anchors.right: host.barEdge === \"right\"" in line:
            continue
        lines.append(line)
    # Remove any WlrLayer / ExclusionMode anchors block
    adapted = "\n".join(lines) + "\n"
    adapted = adapted.replace("""    anchors {
        top: host.barEdge === "top" || host.verticalBar
        bottom: host.barEdge === "bottom" || host.verticalBar
        left: host.barEdge === "top" || host.barEdge === "bottom" || host.barEdge === "left"
        right: host.barEdge === "top" || host.barEdge === "bottom" || host.barEdge === "right"
    }\n""", "")
    (folder / "bar/BarWindow.qml").write_text(adapted)


@unittest.skipUnless(shutil.which("quickshell"), "Quickshell required")
class BarIconOrganizerRenderTests(unittest.TestCase):
    def test_organizer_settings_drag_keyboard_and_reset_renders(self):
        palettes = [
            ("dark", "#e4e5ef", "#191b25"),
            ("light", "#202431", "#f5f3ee"),
            ("website", "#e4e5ef", "#161819"),
        ]
        with tempfile.TemporaryDirectory(prefix="eitr-icons-settings-") as directory:
            folder = Path(directory)
            copy_runtime(folder)
            _setup_mock_singletons(folder, with_plugins=True)
            for theme, fg, bg in palettes:
                out_default = capture_path("SETTINGS_ICONS", directory, f"settings-icons-{theme}.png")
                out_custom = capture_path("SETTINGS_ICONS", directory, f"settings-icons-{theme}-custom.png")
                interactive = "true" if theme == "dark" else "false"
                fixture = f"""import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {{
    id: root
    function find(item, name) {{
        if (!item) return null;
        if (item.objectName === name) return item;
        for (const child of item.children || []) {{
            const found = find(child, name);
            if (found) return found;
        }}
        return null;
    }}
    Bar.SettingsWindow {{
        id: window
        live: false
        foreground: {json.dumps(fg)}
        background: {json.dumps(bg)}
        accent: "#9a815c"
    }}
    Timer {{
        interval: 220; running: true; repeat: false
        onTriggered: {{
            Bar.SiteStyle.light = {json.dumps(theme == "light")};
            Bar.SettingsPalette.select({json.dumps("website" if theme == "website" else "theme")}, false);
            Bar.DesktopStyle.corners = "rounded";
            window.implicitWidth = 1280;
            window.implicitHeight = 960;
            window.show("bar/icons");
            stepTimer.restart();
        }}
    }}
    property int phase: 0
    property bool busy: false
    Timer {{
        id: stepTimer
        interval: 180; repeat: true
        onTriggered: {{
            if (busy) return;
            const content = root.find(window.contentItem, "settings-content");
            const iconsPage = root.find(content, "bar-icons-zone-left") ? root.find(content, "bar-icons-zone-left").page : null;
            if (!iconsPage) {{ console.error("Missing SettingsBarIconsPage"); Qt.exit(1); return; }}
            if (phase === 0) {{
                // Verify all 4 zone buckets and battery chip present
                for (const zoneName of ["left", "clockStart", "clockEnd", "right"]) {{
                    if (!root.find(content, "bar-icons-zone-" + zoneName)) {{ console.error("Missing zone " + zoneName); Qt.exit(1); return; }}
                }}
                for (const chipId of ["ai", "wifi", "weather:weather", "battery", "notifications", "notes:quick"]) {{
                    if (!root.find(content, "bar-icon-chip-" + chipId)) {{ console.error("Missing chip " + chipId); Qt.exit(1); return; }}
                }}
                busy = true;
                content.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(out_default))});
                    busy = false;
                    if ({interactive}) {{ phase = 1; }} else {{ console.log("ICONS_SETTINGS_OK"); Qt.quit(); }}
                }});
            }} else if (phase === 1) {{
                // Keyboard grab + move + Escape cancel test
                const preJson = iconsPage.effectiveOrderJson;
                iconsPage.toggleGrab("ai");
                iconsPage.moveGrabbed("ai", "right");
                iconsPage.moveGrabbed("ai", "right");
                if (iconsPage.resolved.zoneOf["ai"] !== "left") {{ console.error("Expected ai still in left before next step"); Qt.exit(1); return; }}
                iconsPage.cancelInteraction();
                if (iconsPage.grabbedId !== "" || iconsPage.effectiveOrderJson !== preJson) {{ console.error("Escape cancel failed"); Qt.exit(1); return; }}

                // Keyboard grab + move wifi up into clockEnd + drop
                iconsPage.toggleGrab("wifi");
                iconsPage.moveGrabbed("wifi", "up");
                iconsPage.toggleGrab("wifi");
                if (iconsPage.resolved.zoneOf["wifi"] !== "clockEnd") {{ console.error("Keyboard move failed: " + iconsPage.resolved.zoneOf["wifi"]); Qt.exit(1); return; }}

                // Pointer drag move updates into clockStart
                const updatesChip = root.find(content, "bar-icon-chip-updates");
                const targetZone = root.find(content, "bar-icons-zone-clockStart");
                const targetCenter = targetZone.mapToItem(updatesChip, targetZone.width / 2, targetZone.height / 2);
                iconsPage.beginDrag(iconsPage.resolved.byId["updates"], updatesChip, Qt.point(8, 8));
                iconsPage.updateDrag(updatesChip, targetCenter);
                iconsPage.finishDrag();
                if (iconsPage.resolved.zoneOf["updates"] !== "clockStart" || !iconsPage.isCustomized) {{ console.error("Drag reorder failed"); Qt.exit(1); return; }}
                phase = 2;
            }} else if (phase === 2) {{
                busy = true;
                content.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(out_custom))});
                    busy = false;
                    iconsPage.resetToDefault();
                    if (iconsPage.isCustomized || iconsPage.resolved.zoneOf["wifi"] !== "right" || iconsPage.resolved.zoneOf["updates"] !== "right") {{
                        console.error("Reset to default failed"); Qt.exit(1); return;
                    }}
                    console.log("ICONS_SETTINGS_OK");
                    Qt.quit();
                }});
            }}
        }}
    }}
}}
"""
                (folder / "fixture.qml").write_text(fixture)
                code, output = render(folder / "fixture.qml", render_environment(folder, (1280, 960)), 15)
                with self.subTest(theme=theme):
                    self.assertEqual(code, 0, output)
                    self.assertIn("ICONS_SETTINGS_OK", output)
                    self.assertTrue(out_default.is_file())
                    _save_optional_render(out_default, f"settings-icons-{theme}.png")
                    if theme == "dark":
                        self.assertTrue(out_custom.is_file())
                        _save_optional_render(out_custom, "settings-icons-dark-customized.png")
                    for err in ("ReferenceError", "TypeError", "Binding loop", "Cannot anchor", "Unable to assign", "Required property", "Error:"):
                        self.assertNotIn(err, output)

    def test_custom_icon_order_across_layouts_and_panels(self):
        with tempfile.TemporaryDirectory(prefix="eitr-icons-bar-") as directory:
            folder = Path(directory)
            copy_runtime(folder)
            _setup_mock_singletons(folder, with_plugins=True)
            _adapt_bar_window(folder)

            # Custom order that tests moving built-ins & plugins across EVERY zone
            custom_order = {
                "left": ["updates", "hardware", "idleLock"],
                "clockStart": ["wifi", "worldclock:clock"],
                "clockEnd": ["notes:quick"],
                "right": ["ai", "bluetooth", "display", "audio", "obs", "keyboard", "weather:weather", "battery", "notifications"],
            }
            captures = {
                key: capture_path("BAR_ORG", directory, f"{key}.png")
                for key in ("full-custom", "tabs-custom", "islands-custom", "dynamic-custom", "vertical-custom", "panel-wifi-center", "panel-weather-right")
            }

            fixture = f"""import QtQuick
import Quickshell
import "." as Bar
ShellRoot {{
    id: shell
    signal handbookOpened()
    property bool barVisible: true
    property string barAppearance: "solid"
    property string barLayout: "unified"
    property string barEdge: "top"
    property bool barPinned: true
    property bool barAutoHide: false
    property bool barDock: false
    property bool barDockPreviews: true
    property string barMediaStyle: "bars"
    property string barClock: "24h"
    property bool barMoments: false
    property bool barLyrics: false
    property string barScreens: "main"
    property string barIslandStyle: "floating"
    property string barSideStyle: "slopes"
    property bool attachedIslands: false
    property bool centeredLayout: barLayout === "centered"
    property bool islandsLayout: barLayout === "islands"
    property bool dynamicLayout: barLayout === "dynamic"
    property bool dropLayout: barLayout === "drop"
    property bool notchLayout: barLayout === "notch"
    property bool barCollapseIcons: true
    readonly property bool statusCollapsible: barCollapseIcons && !dynamicLayout && !dropLayout
    readonly property bool iconsOpen: !statusCollapsible || statusOpen
    property bool statusOpen: true
    property bool verticalBar: barEdge === "left" || barEdge === "right"
    property real barHeight: 40
    property int workspaceCount: 5
    property int workspaceItemSize: 24
    property int workspaceItemSpacing: 4
    property real tabStripThickness: 7
    property real tabBendRound: 6
    property bool settingsDirty: false
    property string dragCandidate: ""
    property bool barPointerHeld: false
    property string barIconOrderJson: {json.dumps(json.dumps(custom_order))}
    Binding {{ target: Bar.BarIconOrder; property: "savedOrderJson"; value: shell.barIconOrderJson }}

    property var windowGaps: [5, 5, 5, 5]
    property var screenGaps: [12, 12, 12, 12]
    property string workspaceStyle: "Square"
    property color fg: "#e4e5ef"
    property color bg: "#191b25"
    property color activeBg: "#9a815c"
    property color activeFg: "#191b25"
    property color workspaceMenuBg: "#1f2330"
    property color workspaceMenuFg: "#e4e5ef"
    property string wifiGlyph: "󰤨"
    property string focusNetworkGlyph: "󰤨"
    property bool idleLockEnabled: true
    property string idleLockGlyph: "󰌾"
    property string idleLockTooltip: "Idle Lock: On"
    property var updates: ({{checking: false, count: 2}})
    property string updatesIcon: "󰚰"
    property string updatesTooltip: "2 updates"
    property var battery: ({{available: true, percent: 84, status: "Discharging"}})
    property string batteryIcon: "󰁹"
    property bool dictating: false
    property bool transcribing: false
    property var dictationLevels: []
    property int remoteObservers: 0

    function barBackground() {{ return "#e61f2330"; }}
    function barSurface() {{ return barBackground(); }}
    readonly property color barFg: fg
    function mainScreen() {{ return screenObj; }}
    function isActiveBar(b) {{ return true; }}
    function registerBar(b) {{}}
    function unregisterBar(b) {{}}
    function updateBarSetting(k, v) {{}}
    function switchIdleLock() {{}}
    function checkUpdates() {{}}
    function openSystemUpdate() {{}}
    function setWorkspaceStyle(s) {{ workspaceStyle = s; }}
    function workspaceRows(s) {{ return [{{id: 1, number: 1}}, {{id: 2, number: 2}}, {{id: 3, number: 3}}, {{id: 4, number: 4}}, {{id: 5, number: 5}}]; }}
    function workspaceEntry(i, s) {{ return workspaceRows(s)[i] || {{id: i + 1, number: i + 1}}; }}
    function workspaceLabel(i, s) {{ return String(workspaceEntry(i, s).number); }}
    function workspaceApps(id) {{ return ""; }}
    function workspaceActive(i, s) {{ return i === 1; }}
    function focusWorkspace(n, s) {{}}
    function showSettings(p) {{}}
    function showClock(p) {{}}

    readonly property var screenObj: Quickshell.screens.length ? Quickshell.screens[0] : fallbackScreen
    QtObject {{ id: fallbackScreen; property string name: "eDP-1"; property real width: 1920; property real height: 1080 }}
    QtObject {{
        id: netSvc
        property bool busy: false
        property var details: ({{error: "", data: {{backend: "iwd", devices: []}}}})
        property var latency: ({{data: {{ping: 0}}}})
        function observe(o, t) {{ return ""; }}
        function release(t) {{}}
        function detach(o) {{}}
        function actionMessage(m) {{ return m; }}
    }}
    QtObject {{ id: notifSvc; signal toggleRequested(); property int count: 1; property var items: []; property var popups: []; property var notifications: []; property bool doNotDisturb: false; property bool centerOpen: false; property bool popupsOnAllDisplays: false; function toggleDnd() {{}} }}
    QtObject {{ id: remoteSvc; property bool allowed: false; property bool busy: false; property var streaming: ({{enabled: false, active: false}}); property var state: ({{streaming: false, enabled: false, error: ""}}); property var devices: []; function refresh() {{}} function detach(o) {{}} }}
    QtObject {{ id: dockSvc; property bool observing: false; property var clients: [] }}
    QtObject {{ id: idleProc; property bool running: false }}

    Bar.BarWindow {{
        id: bar
        modelData: screenObj
        host: shell
        networkServiceRef: netSvc
        notificationsRef: notifSvc
        remoteServiceRef: remoteSvc
        dockClientsRef: dockSvc
        idleLockProcessRef: idleProc
    }}

    property int step: 0
    function assertCenter(tag) {{
        const clock = shell.verticalBar ? bar.verticalCalendarIcon : bar.centerInfo;
        const pt = clock.mapToItem(bar.contentItem, clock.width / 2, clock.height / 2);
        const actual = shell.verticalBar ? pt.y : pt.x;
        const expected = (shell.verticalBar ? bar.height : bar.width) / 2;
        if (Math.abs(actual - expected) > 0.05) {{
            console.error(tag + " clock not centred: actual=" + actual + " expected=" + expected);
            Qt.exit(1);
            return false;
        }}
        return true;
    }}
    function checkXOrder(ids, tag) {{
        let prev = -1e9;
        for (const id of ids) {{
            const item = bar.iconItem(id);
            if (!item || !item.visible || item.width <= 0) {{
                console.error(tag + " missing horizontal icon " + id); Qt.exit(1); return false;
            }}
            const px = item.mapToItem(bar.contentItem, 0, 0).x;
            if (px <= prev) {{
                console.error(tag + " wrong x order at " + id + " (" + px + " <= " + prev + ")"); Qt.exit(1); return false;
            }}
            prev = px;
        }}
        return true;
    }}

    property bool busy: false
    Timer {{
        interval: 260; repeat: true; running: true
        onTriggered: {{
            if (busy) return;
            if (step === 0) {{
                Bar.DesktopStyle.corners = "rounded";
                if (!assertCenter("full")) return;
                if (!checkXOrder(["updates", "hardware", "idleLock", "wifi", "worldclock:clock"], "full-left-start")) return;
                if (!checkXOrder(["notes:quick", "ai", "obs", "weather:weather", "battery", "notifications"], "full-end-right")) return;
                // Check panel alignments match moved zones
                if (bar.wifiMenu.alignment !== "center" || bar.aiMenu.alignment !== "right" || bar.weatherMenu.alignment !== "right") {{
                    console.error("Wrong alignment: wifi=" + bar.wifiMenu.alignment + " ai=" + bar.aiMenu.alignment + " weather=" + bar.weatherMenu.alignment);
                    Qt.exit(1); return;
                }}
                busy = true;
                bar.stripItem.grabToImage(res => {{ res.saveToFile({json.dumps(str(captures["full-custom"]))}); busy = false; step = 1; }});
            }} else if (step === 1) {{
                // Open moved WiFi panel (clockStart -> centered)
                bar.showPanel(bar.wifiMenu);
                step = 2;
            }} else if (step === 2) {{
                if (bar.wifiMenu.alignment !== "center" || !bar.wifiMenu.visible) {{ console.error("WiFi panel not centered/open"); Qt.exit(1); return; }}
                busy = true;
                bar.wifiMenu.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["panel-wifi-center"]))});
                    bar.closePanels();
                    busy = false;
                    step = 3;
                }});
            }} else if (step === 3) {{
                // Open moved Weather panel (right -> right-aligned)
                bar.showPanel(bar.weatherMenu);
                step = 4;
            }} else if (step === 4) {{
                if (bar.weatherMenu.alignment !== "right" || !bar.weatherMenu.visible) {{ console.error("Weather panel not right-aligned/open"); Qt.exit(1); return; }}
                busy = true;
                bar.weatherMenu.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["panel-weather-right"]))});
                    bar.closePanels();
                    shell.barLayout = "notch";
                    busy = false;
                    step = 5;
                }});
            }} else if (step === 5) {{
                if (!assertCenter("tabs")) return;
                busy = true;
                bar.stripItem.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["tabs-custom"]))});
                    shell.barLayout = "islands";
                    busy = false;
                    step = 6;
                }});
            }} else if (step === 6) {{
                if (!assertCenter("islands")) return;
                const wifiPill = bar.islandSurfaces.pillFor(bar.wifiMenu.target);
                const weatherPill = bar.islandSurfaces.pillFor(bar.weatherMenu.morphAnchor);
                const aiPill = bar.islandSurfaces.pillFor(bar.aiMenu.target);
                if (!wifiPill || !weatherPill || !aiPill || weatherPill !== aiPill || wifiPill === weatherPill) {{
                    console.error("Wrong Islands pill mapping"); Qt.exit(1); return;
                }}
                busy = true;
                bar.stripItem.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["islands-custom"]))});
                    shell.barLayout = "dynamic";
                    busy = false;
                    step = 7;
                }});
            }} else if (step === 7) {{
                if (!assertCenter("dynamic")) return;
                const dyn = bar.dynamicSurfaces;
                if (dyn.islandFor(bar.wifiMenu) !== dyn.middleIsland || dyn.islandFor(bar.weatherMenu) !== dyn.trailingIsland || dyn.islandFor(bar.aiMenu) !== dyn.trailingIsland) {{
                    console.error("Wrong Dynamic island ownership"); Qt.exit(1); return;
                }}
                const leadIds = dyn.panelsOf(dyn.leadingIsland);
                if (leadIds.indexOf(bar.hardwareMenu) === -1) {{
                    console.error("Dynamic panelsOf missing hardwareMenu"); Qt.exit(1); return;
                }}
                busy = true;
                bar.stripItem.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["dynamic-custom"]))});
                    shell.barLayout = "unified";
                    shell.barEdge = "left";
                    busy = false;
                    step = 8;
                }});
            }} else if (step === 8) {{
                if (!assertCenter("vertical")) return;
                let prevY = -1e9;
                for (const id of ["updates", "hardware", "idleLock", "wifi", "ai", "weather:weather", "battery", "notifications"]) {{
                    const item = bar.iconItem(id);
                    if (!item || !item.visible || item.height <= 0) {{ console.error("Missing vertical icon " + id); Qt.exit(1); return; }}
                    const py = item.mapToItem(bar.contentItem, 0, 0).y;
                    if (py <= prevY) {{ console.error("Wrong vertical y order at " + id); Qt.exit(1); return; }}
                    prevY = py;
                }}
                busy = true;
                bar.stripItem.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["vertical-custom"]))});
                    busy = false;
                    shell.barIconOrderJson = "";
                    Qt.callLater(() => {{
                        if (bar.aiMenu.alignment !== "left" || bar.wifiMenu.alignment !== "right" || bar.weatherMenu.alignment !== "center") {{
                            console.error("Reset alignments failed"); Qt.exit(1); return;
                        }}
                        console.log("BAR_ORG_LAYOUTS_OK");
                        Qt.quit();
                    }});
                }});
            }}
        }}
    }}
}}
"""
            (folder / "fixture.qml").write_text(fixture)
            code, output = render(folder / "fixture.qml", render_environment(folder, (1920, 1080)), 25)
            self.assertEqual(code, 0, output)
            self.assertIn("BAR_ORG_LAYOUTS_OK", output)
            for key, path in captures.items():
                self.assertTrue(path.is_file(), f"Missing capture {key}: {output}")
                _save_optional_render(path, f"bar-{key}.png")
            for err in ("ReferenceError", "TypeError", "Binding loop", "Cannot anchor", "Unable to assign", "Required property", "Error:"):
                self.assertNotIn(err, output)

    def test_hardware_plugin_details_parts_and_hidden_bar_icon_renders(self):
        with tempfile.TemporaryDirectory(prefix="eitr-hardware-parts-") as directory:
            folder = Path(directory)
            copy_runtime(folder)
            _setup_mock_singletons(folder, with_plugins=True)
            _adapt_bar_window(folder)
            hw_icon = (ROOT / "distro/plugins/bundled/hardware/icon.svg").as_uri()
            hw_widget_qml = (ROOT / "distro/plugins/bundled/hardware/Hardware.qml").as_uri()
            hw_bar_qml = (ROOT / "distro/plugins/bundled/hardware/HardwareBar.qml").as_uri()
            hw_entries = [
                {"plugin": "hardware", "pluginName": "Hardware", "id": "hardware", "kind": "widgets", "title": "Hardware", "qml": "Hardware.qml", "source": hw_widget_qml, "minWidth": 260, "minHeight": 88, "defaultWidth": 480, "defaultHeight": 280, "surface": "panel", "bundled": True, "disabled": False, "capabilities": ["hardware"]},
                {"plugin": "hardware", "pluginName": "Hardware", "id": "monitor", "kind": "barItems", "title": "Hardware", "icon": "󰍛", "qml": "HardwareBar.qml", "source": hw_bar_qml, "slot": "start", "panel": "details", "bundled": True, "disabled": False, "capabilities": ["hardware"]},
                {"plugin": "hardware", "pluginName": "Hardware", "id": "details", "kind": "panels", "title": "Hardware", "qml": "HardwareBar.qml", "source": hw_bar_qml, "bundled": True, "disabled": False, "capabilities": ["hardware"]},
            ]
            hw_model = {
                "id": "hardware",
                "name": "Hardware",
                "author": "The Eitr project",
                "version": "1.0.0",
                "description": "Live CPU, GPU, RAM, storage and network usage on your desktop",
                "icon": hw_icon,
                "official": True,
                "builtin": True,
                "removable": True,
                "enabled": True,
                "updateCount": 0,
            }
            captures = {
                "details-dark": capture_path("HARDWARE_PARTS", directory, "plugin-details-parts-dark.png"),
                "details-light": capture_path("HARDWARE_PARTS", directory, "plugin-details-parts-light.png"),
                "bar-hidden": capture_path("HARDWARE_PARTS", directory, "bar-hardware-icon-hidden.png"),
            }
            (folder / "plugins/PluginRegistry.qml").write_text(
                f"""pragma Singleton
import QtQuick
QtObject {{
    signal reviewStarted()
    property string clockFormat: "24h"
    property var palette: ({{}})
    property var providers: []
    property var installed: [{json.dumps(hw_model)}]
    property var blocked: []
    property var errors: []
    property var tiles: []
    property var entries: {json.dumps(hw_entries)}
    property var widgetItems: entries.filter(entry => entry.kind === "widgets")
    property var barItems: entries.filter(entry => entry.kind === "barItems")
    property var placements: ({{
        version: 3,
        widgets: [{{plugin: "hardware", id: "hardware", instance: "12345678", monitor: "eDP-1", x: 24, y: 48, width: 480, height: 280, surface: "panel", aboveWindows: false}}],
        barItems: [{{plugin: "hardware", id: "monitor", slot: "start"}}, {{plugin: "ai-usage", id: "usage", slot: "start"}}]
    }})
    property var placedBarItems: [
        {{plugin: "ai-usage", id: "usage", kind: "barItems", title: "AI Usage", icon: "", slot: "start", panel: "limits", bundled: true}},
        {{plugin: "hardware", id: "monitor", kind: "barItems", title: "Hardware", icon: "󰍛", slot: "start", panel: "details", bundled: true}}
    ]
    property bool weatherEnabled: true
    property bool aiUsageEnabled: true
    property bool hardwareEnabled: true
    function barItemShown(plugin, itemId) {{
        return (placements.barItems || []).some(item => item.plugin === plugin && (!itemId || item.id === itemId));
    }}
    property var widgetMenus: ({{"12345678": [{{id: "compact", text: "Compact", checked: false, group: "Layout"}}, {{id: "detailed", text: "Detailed", checked: true, group: "Layout"}}]}})
    function slotItems(slot) {{ return placedBarItems.filter(entry => (entry.slot || "status") === slot); }}
    function editingCopy(copy) {{ return false; }}
    function rotation(copy) {{ return (copy && copy.rotation) || 0; }}
    function widgetSurface(entry) {{ return (entry && entry.geometry && entry.geometry.surface) || (entry && entry.surface) || "none"; }}
    function widgetKey(copy) {{ return (copy && copy.instance) || ""; }}
    function triggerMenu(copy, id) {{}}
    function toggleEditing(copy) {{}}
    function pluginErrors(id) {{ return []; }}
    function errorDetails(id) {{ return ""; }}
    function change(action, entry, extra) {{
        if (action === "unplace" && entry.kind === "barItems") {{
            placements = Object.assign({{}}, placements, {{barItems: placements.barItems.filter(item => !(item.plugin === entry.plugin && item.id === entry.id))}});
            placedBarItems = placedBarItems.filter(item => !(item.plugin === entry.plugin && item.id === entry.id));
            if (entry.plugin === "hardware") hardwareEnabled = false;
        }}
    }}
    function registerSource(entry) {{}}
    function unregisterSource(entry) {{}}
    function refresh() {{}}
    function startDiagnostics() {{}}
    function recordError(plugin, source, line, msg) {{}}
}}
"""
            )
            fixture = f"""import QtQuick
import Quickshell
import "." as Bar
ShellRoot {{
    id: shell
    signal handbookOpened()
    property bool barVisible: true
    property string barAppearance: "solid"
    property string barLayout: "unified"
    property string barEdge: "top"
    property bool barPinned: true
    property bool barAutoHide: false
    property bool barDock: false
    property bool barDockPreviews: true
    property string barMediaStyle: "bars"
    property string barClock: "24h"
    property bool barMoments: false
    property bool barLyrics: false
    property string barScreens: "main"
    property string barIslandStyle: "floating"
    property string barSideStyle: "slopes"
    property bool attachedIslands: false
    property bool centeredLayout: barLayout === "centered"
    property bool islandsLayout: barLayout === "islands"
    property bool dynamicLayout: barLayout === "dynamic"
    property bool dropLayout: barLayout === "drop"
    property bool notchLayout: barLayout === "notch"
    property bool barCollapseIcons: true
    readonly property bool statusCollapsible: barCollapseIcons && !dynamicLayout && !dropLayout
    readonly property bool iconsOpen: !statusCollapsible || statusOpen
    property bool statusOpen: true
    property bool verticalBar: barEdge === "left" || barEdge === "right"
    property real barHeight: 40
    property int workspaceCount: 5
    property int workspaceItemSize: 24
    property int workspaceItemSpacing: 4
    property real tabStripThickness: 7
    property real tabBendRound: 6
    property bool settingsDirty: false
    property string dragCandidate: ""
    property bool barPointerHeld: false
    property string barIconOrderJson: ""
    Binding {{ target: Bar.BarIconOrder; property: "savedOrderJson"; value: shell.barIconOrderJson }}

    property var windowGaps: [5, 5, 5, 5]
    property var screenGaps: [12, 12, 12, 12]
    property string workspaceStyle: "Square"
    property color fg: "#e4e5ef"
    property color bg: "#191b25"
    property color activeBg: "#9a815c"
    property color activeFg: "#191b25"
    property color workspaceMenuBg: "#1f2330"
    property color workspaceMenuFg: "#e4e5ef"
    property string wifiGlyph: "󰤨"
    property string focusNetworkGlyph: "󰤨"
    property bool idleLockEnabled: true
    property string idleLockGlyph: "󰌾"
    property string idleLockTooltip: "Idle Lock: On"
    property var updates: ({{checking: false, count: 2}})
    property string updatesIcon: "󰚰"
    property string updatesTooltip: "2 updates"
    property var battery: ({{available: true, percent: 84, status: "Discharging"}})
    property string batteryIcon: "󰁹"
    property bool dictating: false
    property bool transcribing: false
    property var dictationLevels: []
    property int remoteObservers: 0

    function barBackground() {{ return "#e61f2330"; }}
    function barSurface() {{ return barBackground(); }}
    readonly property color barFg: fg
    function mainScreen() {{ return screenObj; }}
    function isActiveBar(b) {{ return true; }}
    function registerBar(b) {{}}
    function unregisterBar(b) {{}}
    function updateBarSetting(k, v) {{}}
    function switchIdleLock() {{}}
    function checkUpdates() {{}}
    function openSystemUpdate() {{}}
    function setWorkspaceStyle(s) {{ workspaceStyle = s; }}
    function workspaceRows(s) {{ return [{{id: 1, number: 1}}, {{id: 2, number: 2}}, {{id: 3, number: 3}}, {{id: 4, number: 4}}, {{id: 5, number: 5}}]; }}
    function workspaceEntry(i, s) {{ return workspaceRows(s)[i] || {{id: i + 1, number: i + 1}}; }}
    function workspaceLabel(i, s) {{ return String(workspaceEntry(i, s).number); }}
    function workspaceApps(id) {{ return ""; }}
    function workspaceActive(i, s) {{ return i === 1; }}
    function focusWorkspace(n, s) {{}}
    function showSettings(p) {{}}
    function showClock(p) {{}}

    readonly property var screenObj: Quickshell.screens.length ? Quickshell.screens[0] : fallbackScreen
    QtObject {{ id: fallbackScreen; property string name: "eDP-1"; property real width: 1920; property real height: 1080 }}
    QtObject {{
        id: netSvc
        property bool busy: false
        property var details: ({{error: "", data: {{backend: "iwd", devices: []}}}})
        property var latency: ({{data: {{ping: 0}}}})
        function observe(o, t) {{ return ""; }}
        function release(t) {{}}
        function detach(o) {{}}
        function actionMessage(m) {{ return m; }}
    }}
    QtObject {{ id: notifSvc; signal toggleRequested(); property int count: 1; property var items: []; property var popups: []; property var notifications: []; property bool doNotDisturb: false; property bool centerOpen: false; property bool popupsOnAllDisplays: false; function toggleDnd() {{}} }}
    QtObject {{ id: remoteSvc; property bool allowed: false; property bool busy: false; property var streaming: ({{enabled: false, active: false}}); property var state: ({{streaming: false, enabled: false, error: ""}}); property var devices: []; function refresh() {{}} function detach(o) {{}} }}
    QtObject {{ id: dockSvc; property bool observing: false; property var clients: [] }}
    QtObject {{ id: idleProc; property bool running: false }}

    Bar.BarWindow {{
        id: bar
        modelData: screenObj
        host: shell
        networkServiceRef: netSvc
        notificationsRef: notifSvc
        remoteServiceRef: remoteSvc
        dockClientsRef: dockSvc
        idleLockProcessRef: idleProc
    }}

    FloatingWindow {{
        id: detailsWin
        visible: true
        implicitWidth: 460
        implicitHeight: Math.max(980, Math.ceil(detailsCard.height + 32))
        Rectangle {{
            id: detailsSheet
            anchors.fill: parent
            color: shell.bg
            Bar.PluginDetails {{
                id: detailsCard
                x: 16; y: 16
                width: parent.width - 32
                modelData: {json.dumps(hw_model)}
                entries: Bar.PluginRegistry.entries
                foreground: shell.fg
                background: shell.bg
                accent: shell.activeBg
            }}
        }}
    }}

    property int step: 0
    property bool busy: false
    Timer {{
        interval: 260; repeat: true; running: true
        onTriggered: {{
            if (busy) return;
            if (step === 0) {{
                if (!bar.iconItem("hardware") || !bar.iconItem("hardware").visible) {{
                    console.error("Hardware icon should be visible initially"); Qt.exit(1); return;
                }}
                busy = true;
                detailsSheet.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["details-dark"]))});
                    shell.fg = "#202431";
                    shell.bg = "#f5f3ee";
                    busy = false;
                    step = 1;
                }});
            }} else if (step === 1) {{
                busy = true;
                detailsSheet.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["details-light"]))});
                    shell.fg = "#e4e5ef";
                    shell.bg = "#191b25";
                    // Turn off Show on the bar for hardware
                    Bar.PluginRegistry.change("unplace", {{plugin: "hardware", id: "monitor", kind: "barItems"}});
                    busy = false;
                    step = 2;
                }});
            }} else if (step === 2) {{
                const hwItem = bar.iconItem("hardware");
                if (hwItem && hwItem.visible && hwItem.width > 0) {{
                    console.error("Hardware icon still visible after Show on the bar turned off"); Qt.exit(1); return;
                }}
                if (!bar.iconItem("ai") || !bar.iconItem("ai").visible || !bar.iconItem("idleLock") || !bar.iconItem("idleLock").visible) {{
                    console.error("AI Usage or Idle Lock missing after hiding Hardware"); Qt.exit(1); return;
                }}
                busy = true;
                bar.stripItem.grabToImage(res => {{
                    res.saveToFile({json.dumps(str(captures["bar-hidden"]))});
                    console.log("HARDWARE_PARTS_OK");
                    Qt.quit();
                }});
            }}
        }}
    }}
}}
"""
            (folder / "fixture.qml").write_text(fixture)
            code, output = render(folder / "fixture.qml", render_environment(folder, (1920, 1080)), 20)
            self.assertEqual(code, 0, output)
            self.assertIn("HARDWARE_PARTS_OK", output)
            for key, path in captures.items():
                self.assertTrue(path.is_file(), f"Missing capture {key}: {output}")
                _save_optional_render(path, path.name)
            for err in ("ReferenceError", "TypeError", "Binding loop", "Cannot anchor", "Unable to assign", "Required property", "Error:"):
                self.assertNotIn(err, output)



if __name__ == "__main__":
    unittest.main()
