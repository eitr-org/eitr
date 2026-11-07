"""Settings navigation and isolated production window rendering."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from layout_render import BAR, copy_runtime, render_environment, render, capture_path


class SettingsTests(unittest.TestCase):
    def test_search_index(self):
        source = (BAR / 'settings/SettingsIndex.js').read_text().replace('.pragma library', '')
        script = source + '''
const assert = require('node:assert/strict');
assert.equal(pages.length, 19);
assert(!pages.some(page => ["themes", "plugins"].includes(page.id)));
assert(pages.every(page => page.rune && page.description));
assert.equal(pages[0].id, 'system');
assert(!pages.some(page => 'advanced' in page));
assert.equal(new Set(pages.map(page => page.id)).size, pages.length);
assert.equal(filter('cpu', text => text)[0].id, 'system');
assert.equal(filter('nothing matches', text => text).length, 0);
assert.equal(filter('profile avatar', text => text)[0].id, 'system');
for (const [keyword, page] of [['gaps', 'windows'], ['cursor', 'appearance'], ['dnd', 'notifications'], ['rotation', 'displays'], ['wifi', 'connections'], ['workspaces', 'bar'], ['pdf', 'default-apps'], ['kernel', 'about'], ['folder rules', 'git-cloud'], ['fido', 'security']]) assert.equal(filter(keyword, text => text)[0].id, page);
assert.equal(resolve('network/bluetooth').page, 'connections');
assert.equal(entry('network').id, 'connections');
assert.equal(searchDestination('appearance', 'puntero', text => text === 'Cursor family' ? 'Familia del puntero' : text), 'appearance/fonts');
assert.equal(resolve('connections/bluetooth').tab, 'bluetooth');
assert.equal(resolve('connections/unknown').tab, 'wifi');
assert.equal(filter('bluetooth', text => text)[0].destinationId, 'connections/bluetooth');
assert.equal(filter('cursor', text => text)[0].destinationId, 'appearance/fonts');
assert.equal(filter('night light', text => text)[0].destinationId, 'displays/nightlight');
assert.equal(filter('traduit', text => text === 'Displays' ? 'traduit' : text)[0].id, 'displays');
'''
        subprocess.run(['node', '-e', script], check=True, capture_output=True)

    def test_routes_opacity_and_demand(self):
        window = (BAR / 'settings/SettingsWindow.qml').read_text()
        self.assertIn('stateName: "settings"', window)
        self.assertIn('FamilyWindow {', window)
        family = (BAR / 'settings/FamilyWindow.qml').read_text()
        self.assertIn('Qt.rgba(SettingsPalette.background.r, SettingsPalette.background.g, SettingsPalette.background.b, 1)', family)
        for name in ('panels/Handbook.qml', 'panels/Catalog.qml'):
            self.assertIn('FamilyWindow {', (BAR / name).read_text())
        for name in ('settings/SettingsContent.qml', 'panels/Handbook.qml', 'panels/CatalogContent.qml'):
            self.assertIn('FamilySidebar {', (BAR / name).read_text())
        self.assertIn('target: "settings"', window)
        self.assertNotIn('target: "catalog"', window)
        shell = (BAR / 'shell.qml').read_text()
        self.assertIn('SettingsWindow {', shell)
        self.assertIn('function showCatalog() { catalogWindow.show(); }', shell)
        self.assertIn('function showThemes(tone) { catalogWindow.showThemes(tone); }', shell)
        self.assertIn('onThemesRequested: shell.showThemes("all")', shell)
        self.assertTrue((BAR / 'panels/Catalog.qml').exists())
        self.assertFalse((BAR / 'settings/CatalogContent.qml').exists())
        catalog = (BAR / "panels/CatalogContent.qml").read_text()
        self.assertIn("SettingsPalette.", catalog)
        for token in ("SiteStyle.fg", "SiteStyle.card", "SiteStyle.surface", "SiteStyle.raised", "SiteStyle.accent", "SiteStyle.primary"):
            self.assertNotIn(token, catalog)
        overview = (BAR / 'settings/SettingsOverview.qml').read_text()
        self.assertIn('DesktopData.observe("hardware.details", overview)', overview)
        self.assertIn('Component.onDestruction: DesktopData.releaseOwner(overview)', overview)
        content = (BAR / 'settings/SettingsContent.qml').read_text()
        self.assertIn('settings.opened && visible && settings.live', content)
        self.assertNotIn('settings-app.json', content)
        self.assertNotIn('property bool advanced', content)

    def test_shared_controls_and_embedded_lifecycle(self):
        center = (BAR / 'panels/ControlCenter.qml').read_text()
        desktop = (BAR / 'settings/SettingsDesktopPage.qml').read_text()
        devices = (BAR / 'settings/SettingsDevicesPage.qml').read_text()
        self.assertNotIn('SettingsStyleState {', center)
        self.assertIn('SettingsStyleState {', desktop)
        self.assertNotIn('id: cursorQuery', center)
        self.assertIn('ControlCard {', desktop)
        self.assertIn('ChoiceDropdown {', desktop)
        self.assertIn('ChoiceSegmented {', desktop)
        self.assertIn('SettingsAppearanceModel {', (BAR / 'panels/AppearancePicker.qml').read_text())
        for panel in ('AudioMenu', 'WifiMenu', 'BluetoothMenu', 'BrightnessMenu'):
            self.assertIn(panel + ' {', devices)
        for slot in ('displaySlot', 'audioSlot', 'wifiSlot', 'bluetoothSlot'):
            self.assertIn('inlineParent: ' + slot, devices)
        popup = (BAR / 'components/ThemedPopup.qml').read_text()
        self.assertIn('active: !popup.embedded && popup.grabReady', popup)
        self.assertIn('parent: popup.embedded ? popup : panelSurface.contentItem', popup)
        self.assertIn('networkService.detach(menu)', (BAR / 'panels/WifiMenu.qml').read_text())
        self.assertIn('DisplayService.close(menu)', (BAR / 'panels/BrightnessMenu.qml').read_text())
        self.assertIn('EventSoundSettings {', desktop)
        self.assertIn('EventSoundSettings {', (BAR / 'panels/ControlCenterSliders.qml').read_text())
        self.assertIn('KeyboardLayoutRow {', (BAR / 'settings/SettingsInputPage.qml').read_text())
        self.assertIn('workspaceHelper.change([value])', desktop)
        for name in ("ControlCard", "ControlRow", "ChoiceSegmented", "ChoiceDropdown", "SettingsPageHeader"):
            self.assertIn(name + (" components/" if name in ("ControlCard", "ControlRow", "ChoiceSegmented", "ChoiceDropdown") else " settings/") + name + ".qml", (BAR / "qmldir").read_text())
        dropdown = (BAR / "components/ChoiceDropdown.qml").read_text()
        self.assertIn("Accessible.ComboBox", dropdown)
        self.assertIn("function commit(index)", dropdown)
        self.assertIn("Accessible.name:", dropdown)
        self.assertIn("DesktopStyle.motionDuration", (BAR / "settings/FamilySidebar.qml").read_text())

    def test_window_sidebar_overview_render_and_lifetime(self):
        for theme, foreground, background in [('dark', '#e4e5ef', '#191b25'), ('light', '#202431', '#f5f3ee')]:
            with self.subTest(theme=theme), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                copy_runtime(folder)
                (folder / "services/PowerService.qml").write_text('pragma Singleton\nimport QtQuick\nQtObject { property var battery: ({available: false}) }\n')
                (folder / 'services/DesktopData.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
 property var topics: ({})
 property var owners: []
 function observe(topic, owner) { owners = owners.concat([owner]); return topic; }
 function releaseOwner(owner) { owners = owners.filter(entry => entry !== owner); }
}
''')
                (folder / 'services/DisplayService.qml').write_text('''pragma Singleton
import QtQuick
QtObject { property var topology: ({primary: "fixture", monitors: [{name: "fixture", width: 2560, height: 1440, refreshRate: 144}]}) }
''')
                target = capture_path('SETTINGS', directory, theme + '-system.png')
                fixture = '''//@ pragma AppId eitr-catalog
import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 Bar.SettingsWindow {
  id: window; live: false
  property int catalogRequests: 0
  onThemesRequested: catalogRequests++
  foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#9a815c"
 }
 Timer {
  interval: 350; running: true; repeat: true
  property int phase: 0
  onTriggered: {
   const find = function(item, name) { if (item.objectName === name) return item; for (const child of item.children || []) { const found = find(child, name); if (found) return found; } return null; };
   const content = find(window.contentItem, "settings-content");
   const overview = find(content, "settings-overview");
   if (phase === 0) {
    Bar.SiteStyle.light = "BACKGROUND" === "#f5f3ee";
    window.show("you"); window.implicitWidth = 1100; window.implicitHeight = 800;
    overview.artSource = "file://ARTWORK";
    overview.account = {name: "Eitr Explorer", initial: "E"};
    overview.hardware = {data: {sections: [{title: "CPU", name: "8 cores", usage: 12}, {title: "GPU", name: "Graphics", usage: 8}, {title: "RAM", name: "32 GiB", usage: 36}]}};
    overview.version = "0.7.0 · Huginn"; overview.channel = "stable"; overview.uptimeSeconds = 18900;
    overview.themePalette = {background: "BACKGROUND", foreground: "FOREGROUND", accent: "#9a815c", color1: "#ba6472", color2: "#719669", color3: "#d1ad60", color4: "#6a90b9"};
   } else if (phase === 1) {
    if (window.color.a !== 1 || !window.opened) throw new Error("opaque open window");
    content.grabToImage(result => { if (!result.saveToFile("TARGET")) throw new Error("capture"); });
   } else if (phase === 2) {
    overview.observing = true;
    if (Bar.DesktopData.owners.length !== 2) throw new Error("visible subscriptions");
    overview.observing = false;
    if (Bar.DesktopData.owners.length) throw new Error("hidden subscriptions");
    window.show("network/bluetooth");
    if (window.page !== "connections" || content.tab !== "bluetooth") throw new Error("network/tab alias");
    const devices = find(content, "settings-devices-page");
    devices.tabRequested("wifi");
    if (content.tab !== "wifi") throw new Error("tab selection routing");
    window.show("connections/bluetooth");
    if (devices.tab !== "bluetooth") throw new Error("same page deep link after selecting a tab");
    window.show("desktop-bar");
    if (window.page !== "bar") throw new Error("desktop-bar alias");
    window.show("keybinds");
   } else if (phase === 3) {
    content.themesRequested();
    if (window.catalogRequests !== 1 || window.page !== "keybinds") throw new Error("separate catalog request");
    window.show("sound");
    if (window.page !== "sound") throw new Error("device routing");
   } else if (phase === 4) {
    window.live = false;
    window.show("unknown");
    if (window.page !== "system") throw new Error("unknown page fallback");
    window.closeSettings();
    if (window.opened) throw new Error("close");
    console.log("SETTINGS_OK"); Qt.quit();
   }
   phase++;
  }
 }
}
'''.replace('FOREGROUND', foreground).replace('BACKGROUND', background).replace('TARGET', str(target)).replace('ARTWORK', str(BAR.parents[1] / 'themes/vanaheim/backgrounds/01-hidden-garden.jpg'))
                (folder / 'fixture.qml').write_text(fixture)
                code, output = render(folder / 'fixture.qml', render_environment(folder, (1280, 960)), 12)
                self.assertEqual(code, 0, output)
                self.assertIn('SETTINGS_OK', output)
                self.assertNotIn('Error:', output)
                self.assertNotIn('Unable to assign', output)
                self.assertTrue(target.is_file(), output)
                self.assertFalse((folder / 'eitr/settings-app.json').exists())

    def test_every_page_offscreen_with_isolated_models(self):
        for theme, foreground, background in [('dark', '#e4e5ef', '#191b25'), ('light', '#202431', '#f5f3ee'), ('website', '#e4e5ef', '#191b25')]:
            with self.subTest(theme=theme), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                copy_runtime(folder)
                (folder / 'services/DesktopData.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
 property var topics: ({"display.settings": {status: "ready", data: {monitors: [{name: "fixture", mode: "2560x1440@144", modes: ["2560x1440@144Hz", "1920x1080@60Hz"], scale: 1, transform: 0, position: "0x0"}]}}})
 property var client: QtObject { function detachAction(identifier) {} }
 function observe(topic, owner, interval) { return topic; }
 function release(token) {}
 function releaseOwner(owner) {}
 function refresh(topic) {}
}
''')
                (folder / 'services/DisplayService.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
 property var topology: ({primary: "fixture", monitors: [{name: "fixture", width: 2560, height: 1440, refreshRate: 144}]})
 function open(owner, interval) {}
 function close(owner) {}
 function pauseBrightness(owner) {}
 function resumeBrightness(owner) {}
 function pauseNightlight(owner) {}
 function resumeNightlight(owner) {}
 function refresh() {}
 function refreshBrightness() {}
}
''')
                (folder / 'services/PowerService.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
 property var profile: ({available: false, profiles: []})
 property var battery: ({available: false})
 property bool busy: false
 function observe(owner, interval, radios) { return []; }
 function release(tokens) {}
 function refresh() {}
}
''')
                output_folder = capture_path('SETTINGS', directory, 'placeholder').parent
                fixture = (BAR / 'tests/fixtures/settings/pages.qml.in').read_text()
                for original, replacement in {'FOREGROUND': foreground, 'BACKGROUND': background, 'PALETTE': theme,
                                              'OUTPUT': str(output_folder), 'ARTWORK': str(BAR.parents[1] / 'themes/vanaheim/backgrounds/01-hidden-garden.jpg')}.items():
                    fixture = fixture.replace(original, replacement)
                (folder / 'fixture.qml').write_text(fixture)
                code, output = render(folder / 'fixture.qml', render_environment(folder, (1280, 960)), 30)
                self.assertEqual(code, 0, output)
                self.assertIn('PAGES_OK', output)
                for diagnostic in ('TypeError:', 'ReferenceError:', 'Unable to assign', 'Binding loop', 'Error:'):
                    self.assertNotIn(diagnostic, output)
                for page in ('appearance', 'bar', 'windows', 'lockscreen', 'notifications', 'focus',
                             'displays', 'sound', 'connections', 'input', 'keybinds', 'default-apps', 'user', 'git-cloud', 'security', 'updates', 'check-pc', 'about'):
                    self.assertTrue((output_folder / f'{theme}-{page}.png').is_file(), page)

    def test_dropdown_keyboard_and_short_choice_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            fixture = r'''import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
 FloatingWindow {
  id: window; visible: true; implicitWidth: 600; implicitHeight: 220
  color: "#191b25"
  Column {
   Bar.ChoiceDropdown {
    id: dropdown; width: 320; foreground: "#e4e5ef"
    choices: [{value: "first", label: "First"}, {value: "second", label: "Second"}, {value: "third", label: "Third"}]
    current: "first"
    onChosen: value => current = value
   }
   Bar.ChoiceSegmented {
    id: segments; width: 320; foreground: "#e4e5ef"
    choices: [{id: "one", label: "One"}, {id: "two", label: "Two"}]
    current: "one"
    onChosen: value => current = value
   }
   Bar.ChoiceLevel {
    id: level; width: 320; foreground: "#e4e5ef"; accent: "#b08d57"
    choices: [{value: "24", label: "24 px"}, {value: "32", label: "32 px"}]
    current: "24"
    onChosen: value => current = value
   }
  }
 }
 TestCase {
  name: "SettingsControls"; when: window.visible
  function test_keyboard() {
   wait(100);
   dropdown.forceActiveFocus();
   keyClick(Qt.Key_Space); wait(50);
   verify(dropdown.expanded);
   keyClick(Qt.Key_Down); keyClick(Qt.Key_Return); wait(50);
   compare(dropdown.current, "second");
   dropdown.forceActiveFocus(); keyClick(Qt.Key_Space); wait(30);
   keyClick(Qt.Key_Escape); wait(30);
   verify(!dropdown.expanded);
   compare(dropdown.current, "second");
   const segment = segments.children[0].children[1];
   segment.forceActiveFocus(); keyClick(Qt.Key_Space);
   compare(segments.current, "two");
   const slider = level.children[0];
   slider.forceActiveFocus(); keyClick(Qt.Key_Right);
   compare(level.current, "32");
   level.current = "24"; wait(30);
   mouseClick(slider, slider.width - 8, slider.height / 2);
   compare(level.current, "32");
   Bar.DesktopStyle.reduceMotion = true;
   compare(Bar.DesktopStyle.motionDuration(180), 0);
   console.log("CONTROLS_OK"); Qt.quit();
  }
 }
}
'''
            (folder / 'fixture.qml').write_text(fixture)
            code, output = render(folder / 'fixture.qml', render_environment(folder, (1280, 960)), 10)
            self.assertEqual(code, 0, output)
            self.assertIn('CONTROLS_OK', output)
            self.assertNotIn('FAIL!', output)

    def test_tab_and_palette_sources(self):
        tabs = (BAR / 'components/TabStrip.qml').read_text()
        for contract in ('Keys.onLeftPressed', 'Keys.onRightPressed', 'Accessible.PageTab',
                         'Accessible.name', 'Qt.PointingHandCursor'):
            self.assertIn(contract, tabs)
        registry = (BAR / 'qmldir').read_text()
        for source in (BAR / 'components').glob('*Preview.qml'):
            self.assertIn(source.stem + ' components/' + source.name, registry)
        palette = (BAR / 'settings/SettingsPalette.qml').read_text()
        self.assertIn('Eitr.Paths.config("eitr/settings-app.json")', palette)
        self.assertIn('atomicWrites: true', palette)
        self.assertIn('watchChanges: true', palette)
        self.assertIn('SiteStyle.accent', palette)

    def test_tabs_palette_persistence_and_picture_components(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            output_folder = capture_path('SETTINGS', directory, 'previews.png').parent
            fixture = r'''import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
 FloatingWindow {
  id: window; visible: true; implicitWidth: 1000; implicitHeight: 880
  color: Bar.SettingsPalette.background
  Column {
   id: content; width: 960; x: 20; y: 12; spacing: 8
   Bar.TabStrip {
    id: tabs; width: parent.width; height: 42
    choices: [{id: "wifi", label: "Wi-Fi"}, {id: "bluetooth", label: "Bluetooth"}]
    current: "wifi"; onChosen: value => current = value
   }
   Bar.PictureChoices {
    id: layouts; width: parent.width; kind: "layout"
    choices: [{id: "unified", label: "Full"}, {id: "centered", label: "Centered"}, {id: "notch", label: "Tabs"}, {id: "islands", label: "Islands"}, {id: "dynamic", label: "Dynamic"}]
    current: "unified"; onChosen: value => current = value
   }
   Row {
    spacing: 12
    Repeater {
     model: ["top", "bottom", "left", "right"]
     Bar.BarPreview { required property string modelData; width: 220; height: 95; edge: modelData; layout: "islands" }
    }
   }
   Bar.PictureChoices { width: parent.width; kind: "appearance"; compact: true; choices: [{id: "solid", label: "Theme Color"}, {id: "transparent", label: "Blur"}, {id: "website", label: "Website"}] }
   Row {
    spacing: 8
    Bar.MediaPreview { width: 150; height: 75; value: "bars" }
    Bar.MediaPreview { width: 150; height: 75; value: "line" }
    Bar.GapsPreview { width: 150; height: 75; choice: ({inner: 0, outer: 0}) }
    Bar.GapsPreview { width: 150; height: 75; choice: ({inner: 12, outer: 24}) }
    Bar.CornersPreview { width: 150; height: 75; value: "square" }
    Bar.CornersPreview { width: 150; height: 75; value: "extra-rounded" }
   }
   Bar.PictureChoices { width: parent.width; kind: "lockscreen"; choices: [{value: "eitr", label: "Eitr"}, {value: "hyprlock", label: "Hyprlock"}, {value: "clockwork/tape", label: "Clockwork Tape"}] }
   Bar.PictureChoices { width: parent.width; kind: "palette"; choices: [{id: "theme", label: "Theme colours"}, {id: "website", label: "Eitr website"}] }
  }
 }
 TestCase {
  name: "TabStripPalettePictures"; when: window.visible
  function test_choices() {
   wait(150);
   const first = tabs.children[1].children[0];
   first.forceActiveFocus(); keyClick(Qt.Key_Right); compare(tabs.current, "bluetooth");
   keyClick(Qt.Key_Right); compare(tabs.current, "wifi");
   keyClick(Qt.Key_Left); compare(tabs.current, "bluetooth");
   const card = layouts.children[1];
   card.forceActiveFocus(); keyClick(Qt.Key_Space); compare(layouts.current, "centered");
   Bar.SettingsPalette.select("invalid"); compare(Bar.SettingsPalette.palette, "theme");
   Bar.SettingsPalette.select("website"); wait(150);
   compare(Bar.SettingsPalette.background, Bar.SiteStyle.bg);
   compare(Bar.SettingsPalette.accent, Bar.SiteStyle.accent);
   Bar.SettingsPalette.select("theme"); wait(100);
   content.grabToImage(result => result.saveToFile("OUTPUT/previews.png"));
   wait(150);
   Bar.SettingsPalette.select("website"); wait(150);
   console.log("PICTURES_OK"); Qt.quit();
  }
 }
}
'''.replace('OUTPUT', str(output_folder))
            (folder / 'fixture.qml').write_text(fixture)
            code, output = render(folder / 'fixture.qml', render_environment(folder, (1280, 960)), 12)
            self.assertEqual(code, 0, output)
            self.assertIn('PICTURES_OK', output)
            for diagnostic in ('FAIL!', 'TypeError:', 'ReferenceError:', 'Unable to assign', 'Binding loop', 'Error:'):
                self.assertNotIn(diagnostic, output)
            self.assertEqual(json.loads((folder / 'eitr/settings-app.json').read_text()), {'version': 1, 'palette': 'website'})
            self.assertTrue((output_folder / 'previews.png').is_file())
            # Reload in a new process to establish the saved value, rather than an in-memory toggle.
            (folder / 'fixture.qml').write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 property string savedPalette: Bar.SettingsPalette.palette
 Timer { interval: 180; running: true; onTriggered: {
  if (savedPalette !== "website") throw new Error("palette persistence");
  console.log("PREFERENCE_OK"); Qt.quit();
 } }
}
''')
            code, output = render(folder / 'fixture.qml', render_environment(folder), 5)
            self.assertEqual(code, 0, output)
            self.assertIn('PREFERENCE_OK', output)
