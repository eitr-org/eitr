"""Exercise retained window IPC and demand-loaded panel owners offscreen."""
from pathlib import Path
import tempfile
import unittest

from lazy_runtime import prepare_runtime, expose_ipc, WINDOW_FIXTURE
from layout_render import render


class LazyWindowTests(unittest.TestCase):
    def test_window_ipc_and_retained_routes(self):
        with tempfile.TemporaryDirectory(prefix='eitr-lazy-windows-') as directory:
            folder = Path(directory)
            environment = prepare_runtime(folder)
            for relative, aliases in (
                ('settings/SettingsWindow.qml', ['SettingsIpc']),
                ('panels/Catalog.qml', ['StoreIpc', 'CatalogIpc']),
                ('services/WelcomeSession.qml', ['HandbookIpc']),
                ('capture/BeautifyWindow.qml', ['BeautifyIpc']),
            ):
                expose_ipc(folder, relative, aliases)
            body = '''
 function find(item, name) {
  if (item.objectName === name) return item;
  for (const child of item.children || []) { const found = find(child, name); if (found) return found; }
  return null;
 }
 Timer {
  interval: 350; running: true; repeat: true
  property int phase: 0
  property int catalogWaits: 0
  onTriggered: {
   if (phase === 0) {
    if (settings.opened || catalog.opened || find(catalog.contentItem, "catalog-content")) throw new Error("eager window content");
    const status = JSON.parse(welcome.testHandbookIpc.status());
    if (status.opened || status.chapters !== 0) throw new Error("eager handbook catalog");
    settings.testSettingsIpc.show("appearance");
    catalog.testStoreIpc.show("wallpapers", "installed");
    find(catalog.contentItem, "catalog-content").live = false;
    welcome.testHandbookIpc.open("getting-started");
   } else if (phase === 1) {
    if (!settings.opened || settings.page !== "appearance" || !catalog.opened) throw new Error("window IPC open");
    if (catalog.kind !== "wallpapers" || catalog.tab !== "installed") throw new Error("store route");
    const status = JSON.parse(welcome.testHandbookIpc.status());
    if (!status.chapters && !status.error && catalogWaits++ < 20) return;
    if (!status.opened || !status.chapters || status.error) throw new Error("handbook IPC open " + JSON.stringify(status));
    settings.testSettingsIpc.close(); catalog.testStoreIpc.close(); welcome.testHandbookIpc.close();
   } else if (phase === 2) {
    settings.testSettingsIpc.toggle(); catalog.testCatalogIpc.toggle(); welcome.testHandbookIpc.toggle();
    if (settings.page !== "appearance" || catalog.kind !== "wallpapers" || catalog.tab !== "installed") throw new Error("retained navigation");
    welcome.testHandbookIpc.scroll(20);
   } else if (phase === 3) {
    catalog.testCatalogIpc.show("plugins", "discover");
    if (find(catalog.contentItem, "catalog-content").kind !== "plugins") throw new Error("second IPC route");
    catalog.showThemes("light");
    if (find(catalog.contentItem, "catalog-content").kind !== "themes") throw new Error("theme route after interaction");
    settings.testSettingsIpc.palette("dark");
    welcome.testHandbookIpc.close();
    welcome.reader().showWelcome(true);
    if (!welcome.reader().opened || !welcome.reader().welcomeShown) throw new Error("first-login welcome");
    beautify.testBeautifyIpc.open("MISSING_IMAGE");
   } else {
    console.log("LAZY_WINDOWS_OK"); Qt.quit();
   }
   phase++;
  }
 }
'''.replace('MISSING_IMAGE', str(folder / 'missing.png'))
            path = folder / 'shell.qml'
            path.write_text(WINDOW_FIXTURE.replace('TEST_BODY', body))
            returncode, output = render(path, environment, timeout=12)
            self.assertEqual(returncode, 0, output)
            self.assertIn('LAZY_WINDOWS_OK', output)
            for message in ('TypeError:', 'ReferenceError:', 'Binding loop', 'Error:'):
                self.assertNotIn(message, output)


class LazyPanelTests(unittest.TestCase):
    def test_panel_ipc_creates_only_requested_panel(self):
        with tempfile.TemporaryDirectory(prefix='eitr-lazy-panels-') as directory:
            folder = Path(directory)
            environment = prepare_runtime(folder)
            stub = '''import QtQuick
Item {
 property var service
 property var screen
 property bool shown: false
 property color foreground
 property color background
 property color accent
 property color surfaceColor
 property var target
 property string barEdge
 property string clockFormat
 property string placementSlot
 property bool clockSlot: false
 property bool centered: false
 property var entry
 property real maximumHeight: 900
 property var screenMargins
 property var wifiControl
 property var bluetoothControl
 property var displayControl
 property string wifiGlyph
 property var battery
 property var mediaPlayer
 property var player
 property var host
 property var barHost
 property bool idleEnabled: false
 property bool idleBusy: false
 property string barPosition
 property string page
 property string timerFold: "timer"
 property bool timerSet: false
 property bool opened: false
 visible: opened
 signal idleToggleRequested()
 signal lockRequested()
 signal panelRequested(string kind)
 signal settingsRequested(string page)
 property var barRef
 function setFold(name, open) { timerSet = open; }
 function runAfterClose(command) {}
}
'''
            for relative in ('notifications/NotificationPopups.qml', 'notifications/NotificationCenter.qml',
                             'plugins/PluginPanel.qml', 'panels/ControlCenter.qml', 'media/MediaMenu.qml',
                             'panels/DropDashboard.qml', 'panels/BatteryMenu.qml'):
                (folder / relative).write_text(stub)
            fixture = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 id: shell
 property color fg: "white"
 property color activeBg: "cyan"
 property color workspaceMenuBg: "black"
 property bool verticalBar: false
 property string barEdge: "top"
 property string barClock: "24h"
 property var screenGaps: [0,0,0,0]
 property var battery: ({})
 property bool idleLockEnabled: true
 function barBackground() { return "black"; }
 function activeBar(fallback) { return bar; }
 function showSettings(page) {}
 Item {
  id: bar
  property bool isMainBar: true
  property var screen: ({height:1080})
  property var notificationsRef: ({popupsOnAllDisplays:false})
  property var networkServiceRef: ({})
  property var bluetoothMenu: ({})
  property var brightnessMenu: ({})
  property var mediaStrip: ({player:null})
  property var idleLockProcessRef: ({running:false})
  property var stripItem: null
  property var notificationIcon: null
  property var verticalNotificationIcon: null
  property var wifiIcon: ({text:"wifi"})
  property var verticalWifiIcon: wifiIcon
  property var verticalCalendarIcon: null
  property var centerInfo: null
  property var verticalBatteryIcon: null
  property var batteryBarIcon: null
  property var host: shell
  property var dropDashboard: panels.dropDashboardItem
  property var current: null
  function showPanel(panel) { current = panel; panel.opened = true; }
  function togglePanel(panel) { current = panel; panel.opened = !panel.opened; }
  function toggleControlCenter() { panels.toggleControlCenter(); }
  function showControlCenter(page) { panels.showControlCenter(page); }
  function showKind(kind) { panels.showKind(kind); }
  Bar.BarPanels { id: panels; host: shell; barHost: bar }
 }
 Timer {
  interval: 40; running: true; onTriggered: {
   if (panels.controlCenterItem || panels.notificationCenterItem || panels.mediaMenuItem || panels.dropDashboardItem || panels.batteryMenuItem || panels.pluginPanelItem) throw new Error("eager panel tree");
   for (const kind of ["notifications", "media", "battery", "dashboard"]) {
    panels.panelIpcItem.show(kind);
    if (!bar.current || !bar.current.opened) throw new Error("panel IPC " + kind);
    bar.current.opened = false;
   }
   panels.showControlCenter("timer");
   if (!panels.controlCenterItem.opened || !panels.controlCenterItem.timerSet) throw new Error("queued Control Center page");
   panels.toggleControlCenter();
   if (panels.controlCenterItem.opened) throw new Error("Control Center toggle");
   const retained = panels.mediaMenuItem;
   panels.panelIpcItem.show("media");
   if (retained !== panels.mediaMenuItem || !retained.opened) throw new Error("panel retention");
   if (!panels.ensure("plugin")) throw new Error("plugin panel creation");
   console.log("LAZY_PANELS_OK"); Qt.quit();
  }
 }
}
'''
            path = folder / 'shell.qml'
            path.write_text(fixture)
            returncode, output = render(path, environment, timeout=6)
            self.assertEqual(returncode, 0, output)
            self.assertIn('LAZY_PANELS_OK', output)
            for message in ('TypeError:', 'ReferenceError:', 'Binding loop', 'Error:'):
                self.assertNotIn(message, output)


class LazyLayoutTests(unittest.TestCase):
    def test_layout_loaders_select_one_tree_and_release_it(self):
        import re
        from lazy_runtime import BAR
        from qml_source import qml_block
        source = (BAR / 'bar/BarWindow.qml').read_text()
        blocks = []
        names = ('barCenteredOutline', 'barTabs', 'barIslands', 'barDynamic', 'barDrop', 'barVerticalPlacement')
        for name in names:
            match = re.search(r'^( *)Loader \{\n\s*id: ' + name + 'Loader', source, re.M)
            block = qml_block(source, match[0])
            blocks.append(block)
        with tempfile.TemporaryDirectory(prefix='eitr-lazy-layouts-') as directory:
            folder = Path(directory)
            environment = prepare_runtime(folder)
            # The test uses production Loader predicates, with inert trees to isolate
            # construction/teardown from the geometry covered by layout render tests.
            for component in ('BarCenteredOutline', 'BarTabs', 'BarIslands', 'BarDynamic', 'BarDrop', 'BarVerticalPlacement'):
                path = folder / 'bar' / (component + '.qml')
                path.write_text('import QtQuick\nItem { required property var host; required property var barHost }\n')
            fixture = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 id: shell
 property bool verticalBar: bar.verticalBar
 FloatingWindow {
  visible: true
  Item {
   id: bar
   property var host: shell
   property bool verticalBar: false
   property bool centeredLayout: false
   property bool notchLayout: false
   property bool islandsLayout: false
   property bool dynamicLayout: false
   property bool dropLayout: false
   LOADERS
   Timer {
    interval: 20; running: true; repeat: true
    property int phase: 0
    onTriggered: {
     const loaders = [barCenteredOutlineLoader, barTabsLoader, barIslandsLoader, barDynamicLoader, barDropLoader, barVerticalPlacementLoader];
     const flags = ["centeredLayout", "notchLayout", "islandsLayout", "dynamicLayout", "dropLayout", "verticalBar"];
     const previous = phase - 1;
     for (let index = 0; index < loaders.length; index++) {
      if (!!loaders[index].item !== (index === previous % 7)) throw new Error("wrong layout tree " + phase + "/" + index);
     }
     if (phase === 14) { console.log("LAZY_LAYOUTS_OK"); Qt.quit(); return; }
     for (let index = 0; index < flags.length; index++) bar[flags[index]] = index === phase % 7;
     phase++;
    }
   }
  }
 }
}
'''.replace('LOADERS', '\n'.join(blocks).replace('sourceComponent: Bar', 'sourceComponent: Bar.Bar'))
            path = folder / 'shell.qml'
            path.write_text(fixture)
            returncode, output = render(path, environment, timeout=6)
            self.assertEqual(returncode, 0, output)
            self.assertIn('LAZY_LAYOUTS_OK', output)
            for message in ('TypeError:', 'ReferenceError:', 'Binding loop', 'Error:'):
                self.assertNotIn(message, output)


class DynamicTeardownTests(unittest.TestCase):
    def test_unloading_layout_returns_borrowed_items(self):
        from lazy_runtime import dynamic_switch_fixture
        with tempfile.TemporaryDirectory(prefix='eitr-layout-teardown-') as directory:
            folder = Path(directory)
            environment = prepare_runtime(folder)
            path = folder / 'fixture.qml'
            path.write_text(dynamic_switch_fixture())
            returncode, output = render(path, environment, timeout=8)
            self.assertEqual(returncode, 0, output)
            self.assertIn('LAYOUT_SWITCH_MS', output)
            for message in ('TypeError:', 'ReferenceError:', 'Binding loop', 'Error:', 'invalid context'):
                self.assertNotIn(message, output)


if __name__ == '__main__':
    unittest.main()
