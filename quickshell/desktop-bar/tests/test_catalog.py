import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "walker/tests"))
from home_isolation import setUpModule, tearDownModule

from layout_render import copy_runtime, render_environment, render

BAR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('catalog_domain', BAR / 'scripts/catalog-domain.py')
DOMAIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOMAIN)


class SitePaletteTests(unittest.TestCase):
    def test_site_palette_matches_css(self):
        root = BAR.parents[1]
        dark = (root / 'website/src/styles/global.css').read_text().split(':root {', 1)[1].split('}', 1)[0]
        light = (root / 'website/src/styles/appearance.css').read_text().split(':root[data-appearance="light"]{', 1)[1].split('}', 1)[0]
        source = (BAR / 'services/SiteStyle.qml').read_text()
        def qml_color(value):
            if len(value) == 4:
                value = '#' + ''.join(character * 2 for character in value[1:])
            return '#' + value[7:9] + value[1:7] if len(value) == 9 else value
        for key in ('bg', 'night', 'surface', 'raised', 'fg', 'muted', 'accent', 'aurora', 'violet', 'bronze', 'line', 'line-strong', 'glow'):
            name = re.sub(r'-([a-z])', lambda match: match[1].upper(), key)
            values = [qml_color(re.search(r'--' + key + r':\s*(#[0-9a-f]+)', block)[1]) for block in (light, dark)]
            with self.subTest(token=key):
                self.assertIn('property color ' + name + ': light ? "' + values[0] + '" : "' + values[1] + '"', source)


    def test_bundled_fonts_stage_with_their_licenses(self):
        from layout import Layout
        with tempfile.TemporaryDirectory() as directory:
            exported = Path(directory) / 'export'
            staged = Path(directory) / 'stage'
            fonts = 'quickshell/desktop-bar/assets/fonts'
            shutil.copytree(BAR / 'assets/fonts', exported / fonts, ignore=shutil.ignore_patterns('__pycache__'))
            for name in ('layout-manifest.json', 'legacy-layout.json'):
                destination = exported / 'distro' / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(BAR.parents[1] / 'distro' / name, destination)
            Layout(exported).stage(staged)
            for name in ('Cinzel-500.ttf', 'Cinzel-700.ttf', 'CormorantGaramond-500.ttf'):
                self.assertEqual((staged / fonts / name).read_bytes()[:4], b'\x00\x01\x00\x00')
            for name in ('Cinzel-OFL.txt', 'CormorantGaramond-OFL.txt'):
                self.assertIn('SIL OPEN FONT LICENSE Version 1.1', (staged / fonts / name).read_text())
            self.assertFalse((staged / fonts / 'export.py').exists())


class CatalogDomainTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        environment = patch.dict(os.environ, dict(HOME=temporary.name, XDG_CACHE_HOME=temporary.name))
        environment.start()
        self.addCleanup(environment.stop)

    def test_results_and_errors_are_preserved(self):
        domain = DOMAIN.CatalogDomain()
        for result in ({'items': []}, {'updates': {}}, {'error': 'offline'},
                       {'items': [{'id': 'eitr', 'kind': 'builtin', 'source': None}]},
                       {'error': 'Cannot remove the current theme; apply eitr first'}):
            with patch.object(domain, 'exchange', return_value=result):
                self.assertEqual(domain.request('installed', {'kind': 'themes'}, threading.Event()), result)

    def test_cancelled_mutation_is_killed_and_not_replayed(self):
        import sys
        cancelled = threading.Event()
        domain = DOMAIN.CatalogDomain([sys.executable, '-u', '-c',
            'import sys,time; sys.stdin.readline(); time.sleep(10)'])
        cancel = threading.Timer(0.2, cancelled.set)
        cancel.start()
        try:
            result = domain.request('remove', {'kind': 'themes', 'id': 'test'}, cancelled)
            self.assertIn('Outcome unknown', result['error'])
            self.assertIsNone(domain.process)
        finally:
            cancel.cancel()
            domain.close()

    def test_reads_reuse_one_worker(self):
        import sys
        domain = DOMAIN.CatalogDomain([sys.executable, '-u', '-c',
            "import sys, json\nfor line in sys.stdin:\n print(json.dumps({'items': []}), flush=True)"])
        try:
            first = domain.request('installed', {'kind': 'themes'}, threading.Event())
            process = domain.process
            second = domain.request('installed', {'kind': 'themes'}, threading.Event())
            self.assertEqual(first, {'items': []})
            self.assertEqual(second, first)
            self.assertIs(domain.process, process)
        finally:
            domain.close()

    def test_cancel_before_admission_does_no_work(self):
        cancelled = threading.Event()
        cancelled.set()
        with patch.object(DOMAIN.subprocess, 'Popen') as launch:
            self.assertEqual(DOMAIN.CatalogDomain().request('index', {'kind': 'themes'}, cancelled), {})
            launch.assert_not_called()

    def test_validation_and_action_guard(self):
        for name, args in [('remove', {'kind': 'themes', 'id': '../bad'}), ('install', {'kind': 'plugins', 'ids': ['example']}),
                           ('install', {'kind': 'themes', 'ids': []}), ('unknown', {'kind': 'themes'})]:
            with self.assertRaises(ValueError):
                DOMAIN.validate(name, args)
        domain = DOMAIN.CatalogDomain()
        with domain.action_lock:
            self.assertIn('already running', domain.request('apply', {'kind': 'themes', 'id': 'eitr'}, threading.Event())['error'])

    def test_malformed_backend_output(self):
        import sys
        domain = DOMAIN.CatalogDomain([sys.executable, '-u', '-c',
            'import sys; sys.stdin.readline(); print("null", flush=True)'])
        try:
            self.assertIn('error', domain.request('installed', {'kind': 'plugins'}, threading.Event()))
        finally:
            domain.close()



@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class CatalogRenderTests(unittest.TestCase):
    def test_window_lifecycle_and_default_size(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            (folder / 'services/DesktopData.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function releaseOwner(owner) {} }\n')
            fixture = r'''//@ pragma AppId eitr-catalog
import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 Bar.Catalog {
  id: catalog
  foreground: "#cdd6f4"; background: "#181824"; accent: "#759456"
 }
 Timer {
  interval: 200; running: true; repeat: true
  property int phase: 0
  property real openedWidth: 0
  onTriggered: {
   const find = function(item, name) { if (item.objectName === name) return item; for (const child of item.children || []) { const found = find(child, name); if (found) return found; } return null; };
   const content = find(catalog.contentItem, "catalog-content");
   content.live = false;
   if (phase === 0) {
    if (catalog.opened || catalog.visible) throw new Error("initially closed");
    if (catalog.title !== "Themes & Plugins") throw new Error("window metadata");
    catalog.show();
   } else if (phase === 1) {
    if (!catalog.opened || !catalog.visible) throw new Error("show");
    openedWidth = catalog.implicitWidth;
    if (openedWidth <= 0 || openedWidth > catalog.defaultSize.width) throw new Error("default size");
    catalog.implicitWidth = 610; catalog.implicitHeight = 510;
   } else if (phase === 2) {
    catalog.closed();
    if (catalog.opened || catalog.visible) throw new Error("compositor close");
    catalog.show(); catalog.show();
   } else if (phase === 3) {
    if (!catalog.opened || !catalog.visible) throw new Error("reopen");
    if (catalog.implicitWidth !== openedWidth) throw new Error("reopened at the resized width");
    content.closeRequested();
    if (catalog.opened) throw new Error("content close");
    console.log("CATALOG_WINDOW_OK"); Qt.quit();
   }
   phase++;
  }
 }
}
'''
            (folder / 'fixture.qml').write_text(fixture)
            code, output = render(folder / 'fixture.qml', render_environment(folder), 10)
            self.assertEqual(code, 0, output)
            self.assertIn('CATALOG_WINDOW_OK', output)
            self.assertNotIn('Error:', output)
            self.assertNotIn('Unable to assign', output)
            self.assertFalse((folder / 'eitr/catalog-window.json').exists())

    def test_empty_community_index_shows_the_welcome_card(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            (folder / 'services/DesktopData.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function releaseOwner(owner) {} }\n')
            (folder / 'fixture.qml').write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 FloatingWindow {
  visible: true; implicitWidth: 900; implicitHeight: 600
  Bar.CatalogContent {
   id: panel; anchors.fill: parent; live: false; opened: true
   transport: function(name, args, callback) { callback("", {items: []}); }
  }
  Timer {
   interval: 300; running: true; repeat: true
   property int phase: 0
   onTriggered: {
    function find(root, name) { if (root.objectName === name) return root; for (const child of root.children || []) { const found = find(child, name); if (found) return found; } return null; }
    const cases = [["themes", "", true], ["plugins", "", true], ["themes", "Index unavailable", false]];
    if (phase === cases.length * 2) { console.log("COMMUNITY_EMPTY_OK"); Qt.quit(); return; }
    const entry = cases[Math.floor(phase / 2)];
    if (phase % 2 === 0) {
     panel.kind = entry[0]; panel.tab = "community";
     panel.store = Object.assign({}, panel.store, {[entry[0] + ":community"]: {items: [], error: entry[1], pending: false, loaded: !entry[1]}});
     panel.sync();
    } else {
     const welcome = find(panel, "catalog-community-welcome");
     if (!welcome || welcome.visible !== entry[2] || panel.communityEmpty !== entry[2]) throw new Error("welcome card for " + entry);
     if (entry[2]) {
      panel.tab = "official";
      if (panel.communityEmpty) throw new Error("Official is never the community welcome");
      panel.tab = "community";
     }
    }
    phase++;
   }
  }
 }
}
''')
            code, output = render(folder / 'fixture.qml', render_environment(folder), 15)
            self.assertEqual(code, 0, output)
            self.assertIn('COMMUNITY_EMPTY_OK', output)
            self.assertNotIn('Error:', output)

    def test_window_states_in_both_palettes(self):
        for variant in ('dark-1100', 'light-1100', 'dark-700', 'light-700'):
            theme, width = variant.split('-')
            with self.subTest(theme=theme), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                copy_runtime(folder)
                (folder / "assets").mkdir(exist_ok=True)
                shutil.copy(BAR / "assets/eitr-logo-white.svg", folder / "assets/eitr-logo-white.svg")
                # The view has an injectable transport; no broker or live reads in fixtures.
                (folder / 'services/DesktopData.qml').write_text('''pragma Singleton
import QtQuick
QtObject { function releaseOwner(owner) {} }
''')
                target = Path(os.environ.get('EITR_CATALOG_RENDERS', directory))
                target.mkdir(parents=True, exist_ok=True)
                fixture = '''import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
 FloatingWindow {
  visible: true; implicitWidth: WIDTH; implicitHeight: 800
  Rectangle {
   id: sample; anchors.fill: parent; color: Bar.SettingsPalette.background
   Component.onCompleted: { Bar.SettingsPalette.themeBackground = "BACKGROUND"; Bar.SettingsPalette.themeForeground = "FOREGROUND"; Bar.SettingsPalette.themeAccent = "ACCENT"; }
   Bar.CatalogContent {
    id: panel; anchors.fill: parent; live: false; opened: true
    transport: function(name, args, callback) { callback("", {items: []}); }
   }
   TestCase { id: keys; name: "CatalogKeys"; when: false }
   property var installedPalettes: INSTALLED_PALETTES
   property var indexPalettes: INDEX_PALETTES
   property int phase: 0
   property var installReply: null
   Timer {
    id: capture; property string name: ""; interval: 130
    onTriggered: {
     if (capture.name === "plugins-official") {
      panel.progress = "";
      function find(root, name) { if (root.objectName === name) return root; for (const child of root.children || []) { const found = find(child, name); if (found) return found; } return null; }
      const firstCard = find(panel, "card-" + panel.navigable[0].id);
      keys.mouseClick(firstCard, firstCard.width / 2, 40);
      if (!panel.detail) throw new Error("click opens plugin details");
      panel.closeDetail();
     }
     sample.grabToImage(function(result) { result.saveToFile("TARGET/" + capture.name + "-VARIANT.png"); });
    }
   }
   Timer {
    interval: 650; running: true; repeat: true
    onTriggered: {
     if (Bar.SiteStyle.light !== SITE_LIGHT) throw new Error("light.mode detection");
     if (!Qt.colorEqual(panel.background, "BACKGROUND") || !Qt.colorEqual(panel.foreground, "FOREGROUND") || !Qt.colorEqual(panel.accent, "ACCENT")) throw new Error("Settings palette binding");
     const names = ["official-themes", "selected-themes", "detail-overview", "detail-wallpaper", "review", "installing", "community-detail", "installed-search", "plugins-official", "plugins-installed", "remove", "plugin-cards-install", "plugin-images", "plugin-video", "plugin-review-official", "plugin-review-third-party", "plugin-update-review", "git-address"];
     if (sample.phase === 0) {
      panel.installed = [{id:"eitr",name:"Eitr",kind:"builtin",current:true,description:"Primordial venom",previewUrl:"PREVIEW"},{id:"afterglow",name:"Afterglow",kind:"official",description:"Warm ember colors",previewUrl:"PREVIEW2"},{id:"mine",name:"My theme",kind:"own",light:true,description:"A quiet light palette",previewUrl:"PREVIEW3"}];
      panel.availableItems = [{id:"moss",name:"Moss",kind:"official",description:"Deep forest greens",size:3145728},{id:"jade",name:"Jade",kind:"official",light:true,description:"Warm jade and cream",size:2097152},{id:"asgard",name:"Asgard",kind:"official",description:"Gold in the halls of the gods",size:2097152}];
      panel.selected = ["moss"];
      panel.previews = {moss: "PREVIEW2", jade: "PREVIEW3", asgard: "PREVIEW"};
      let checks = 0;
      panel.transport = function(name, args, callback) {
       if (name === "check") { checks++; callback("", {updates:{afterglow:1}}); }
       else callback("", {items:[]});
      };
      panel.checkUpdates();
      if (checks !== 2 || panel.updates.afterglow !== 1) throw new Error("background update checks");
      const installedThemes = panel.installed;
      panel.transport = function(name, args, callback) { callback("", name === "update" ? {result:["afterglow"]} : {items:[]}); };
      panel.act("update", {id:"afterglow"});
      if (panel.updates.afterglow || panel.updateCache.themes.afterglow) throw new Error("an updated theme keeps its Update label");
      const updated = [];
      panel.installed = installedThemes; panel.updates = {afterglow:1, mine:2};
      if (panel.pendingUpdates.join() !== "afterglow,mine") throw new Error("pending updates follow the check");
      panel.transport = function(name, args, callback) { if (name === "update") updated.push(args.id); callback("", name === "update" ? {result:[args.id]} : {items:[]}); };
      panel.updateAll();
      if (updated.join() !== "afterglow,mine" || panel.pendingUpdates.length) throw new Error("Update all updates every theme in turn");
      panel.installed = installedThemes; panel.updates = {afterglow:1}; panel.selected = ["moss"]; panel.busy = false;
      panel.live = true;
      panel.transport = function(name, args, callback) { callback("Preview unavailable", {}); };
      panel.preview({id:"missing"});
      if (panel.repositoryError || panel.previews.missing) throw new Error("preview failure must stay on card");
      panel.live = false;
      panel.transport = function(name, args, callback) { callback("", {items:[]}); };
      if (panel.width < 800) { panel.installed = panel.installed.slice(0, 2); panel.availableItems = panel.availableItems.slice(0, 2); }
     } else if (sample.phase === 1) {
      panel.tab = "official"; panel.selected = [];
      panel.forceActiveFocus();
      keys.keyClick(Qt.Key_Down);
      if (panel.kind !== "themes" || panel.tab !== "community") throw new Error("sidebar Down");
      keys.keyClick(Qt.Key_Down);
      if (panel.kind !== "plugins" || panel.tab !== "installed") throw new Error("sidebar Down into Plugins");
      keys.keyClick(Qt.Key_Up); keys.keyClick(Qt.Key_Up);
      if (panel.kind !== "themes" || panel.tab !== "official") throw new Error("sidebar Up");
      panel.availableItems = [{id:"moss",name:"Moss",kind:"official",description:"Deep forest greens",size:3145728,previewUrl:"PREVIEW2"},{id:"jade",name:"Jade",kind:"official",light:true,description:"Warm jade and cream",size:2097152,previewUrl:"PREVIEW3"}];
      keys.keyClick(Qt.Key_Right);
      if (panel.sidebarFocus || panel.cursor !== 0) throw new Error("Right enters content");
      keys.keyClick(Qt.Key_Space);
      if (panel.selected.length) throw new Error("installed themes cannot be selected for install");
      keys.keyClick(Qt.Key_Right); keys.keyClick(Qt.Key_Right);
      keys.keyClick(Qt.Key_Space);
      keys.keyClick(Qt.Key_Right);
      keys.keyClick(Qt.Key_Space);
      if (panel.selected.length !== 2) throw new Error("keyboard selection");
      function find(root, name) { if (root.objectName === name) return root; for (const child of root.children || []) { const found = find(child, name); if (found) return found; } return null; }
      keys.wait(50);
      const install = find(panel, "install-jade");
      const viewport = find(panel, "catalog-scroll");
      const bottom = install.mapToItem(viewport, 0, install.height).y;
      viewport.contentY = Math.max(0, Math.min(viewport.contentHeight - viewport.height, viewport.contentY + Math.max(0, bottom - viewport.height)));
      keys.wait(20);
      keys.mouseClick(install, install.width / 2, install.height / 2);
      if (panel.selected.includes("jade")) throw new Error("Install toggles off");
      keys.mouseClick(install, install.width / 2, install.height / 2);
      if (!panel.selected.includes("jade")) throw new Error("Install toggles on");
      const card = install.parent.parent.parent;
      keys.mouseClick(card, card.width / 2, 50);
      if (!panel.detail || panel.detail.id !== "jade") throw new Error("card click opens detail");
      keys.keyClick(Qt.Key_Escape);
     } else if (sample.phase === 2) {
      panel.availableItems = panel.availableItems.map(item => Object.assign({}, item, {wallpapers:[{path:"backgrounds/wall.jpg", thumbnail:"thumbnails/wall.jpg", imageUrl:"WALLPAPER", size:345678}]}));
      keys.keyClick(Qt.Key_Return);
      if (!panel.detail || panel.detail.id !== "jade" || panel.reviewing) throw new Error("Enter opens focused detail with selection");
      if (panel.wallpapers.length !== 1) throw new Error("detail gallery");
     } else if (sample.phase === 3) {
      function find(root, name) { if (root.objectName === name) return root; for (const child of root.children || []) { const found = find(child, name); if (found) return found; } return null; }
      const scroller = find(panel, "detail-scroll");
      scroller.contentY = Math.max(0, scroller.contentHeight - scroller.height);
      const wallpaper = find(panel, "wallpaper-0");
      keys.mouseClick(wallpaper, wallpaper.width / 2, 30);
      if (panel.wallpaperIndex !== 0) throw new Error("large wallpaper");
     } else if (sample.phase === 4) {
      keys.keyClick(Qt.Key_Escape);
      if (panel.detail || panel.cursor !== 3 || !panel.activeFocus) throw new Error("detail Escape restores card focus");
      function find(root, name) { if (root.objectName === name) return root; for (const child of root.children || []) { const found = find(child, name); if (found) return found; } return null; }
      const button = find(panel, "review-selection");
      button.forceActiveFocus(); keys.keyClick(Qt.Key_Return);
      if (!panel.reviewing) throw new Error("bottom Enter opens review");
      if (panel.chosen.length !== 2 || panel.totalSize !== 5242880) throw new Error("selection/total");
     } else if (sample.phase === 5) {
      panel.busy = true; panel.progress = "Installing 1 of 2 themes…";
     } else if (sample.phase === 6) {
      panel.busy = false; panel.progress = "";

      panel.forceActiveFocus(); keys.keyClick(Qt.Key_Escape);
      if (panel.reviewing || !panel.opened) throw new Error("Escape must cancel review");
      panel.tab = "community"; panel.selected = [];
      panel.availableItems = [{id:"community-dusk", name:"Community Dusk", kind:"community", description:"Indigo and warm stone", maintainer:"Example artist", license:"MIT", repository:"https://example.invalid/themes", folder:"themes/dusk", size:4567890, wallpapers:[{path:"themes/dusk/backgrounds/dusk.jpg",size:456789},{path:"themes/dusk/backgrounds/stone.png",size:null}]}];
      panel.openDetail(panel.availableItems[0]);
      if (panel.wallpapers[0].thumbnail || panel.wallpapers[0].imageUrl) throw new Error("community uses name tiles");
     } else if (sample.phase === 7) {
      panel.closeDetail(); panel.tab = "installed";
      panel.installed = [{id:"eitr",name:"Eitr",kind:"builtin",current:true,description:"Primordial venom",previewUrl:"PREVIEW"},{id:"afterglow",name:"Afterglow",kind:"builtin",description:"Warm dusk",previewUrl:"PREVIEW3"},{id:"nord",name:"Nord",kind:"official",description:"Cool northern blues",previewUrl:"PREVIEW2"}];
      panel.updates = {nord:1};
      panel.forceActiveFocus(); keys.keyClick("n"); keys.keyClick("o"); keys.keyClick("r");
      if (panel.query !== "nor" || panel.locals.length !== 1 || panel.locals[0].id !== "nord") throw new Error("Typing searches installed themes: " + JSON.stringify(panel.query) + " " + panel.locals.length);
      panel.query = "northern BLUES";
      if (panel.locals.length !== 1) throw new Error("Search matches descriptions, any case");
      panel.query = "warm";
      if (panel.locals.length !== 1 || panel.locals[0].id !== "afterglow") throw new Error("Search by description");
      panel.forceActiveFocus(); keys.keyClick(Qt.Key_Escape);
      if (panel.query !== "" || !panel.opened) throw new Error("Escape clears search before closing");
      panel.query = "nord";
      panel.availableItems = [{id:"notes",name:"Notes",description:"Notes on the desktop",size:12345}];
     } else if (sample.phase === 8) {
      function find(root, name) { if (root.objectName === name) return root; for (const child of root.children || []) { const found = find(child, name); if (found) return found; } return null; }
      panel.query = "";
      const builtinRemove = find(panel, "remove-afterglow"), officialRemove = find(panel, "remove-nord");
      if (!builtinRemove || !officialRemove || builtinRemove.visible || !officialRemove.visible) throw new Error("Only non built-in themes have a remove button");
      let applies = 0;
      panel.transport = function(name, args, callback) { if (name === "apply") applies++; callback("", {items:[]}); };
      panel.activate({id:"afterglow", name:"Afterglow"}, true);
      if (applies !== 1 || panel.detail) throw new Error("Installed still applies");
      panel.kind = "plugins";
      panel.tab = "official";
      panel.installed = [];
      panel.availableItems = [{id:"clock",name:"Clock",kind:"official",description:"A desktop clock",previewUrl:"PREVIEW",preview:"preview.png"},{id:"notes",name:"Notes",kind:"official",description:"Notes on the desktop",icon:"ICON",previewUrl:"ICON"},{id:"plain",name:"Plain",kind:"official",description:"A plugin without artwork"}];
      panel.activate(panel.availableItems[0], false);
      if (!panel.detail || panel.detail.id !== "clock") throw new Error("plugin opens detail");
      panel.closeDetail();
     } else if (sample.phase === 9) {
      panel.tab = "installed";
      panel.installed = [{id:"clock",name:"Clock",kind:"official",description:"A desktop clock",preview:"PREVIEW"},{id:"notes",name:"Notes",kind:"community",description:"Notes on the desktop",icon:"ICON",enabled:false},{id:"plain",name:"Plain",kind:"third-party",description:"A plugin without artwork"}];
     } else if (sample.phase === 10) {
      let requests = 0;
      panel.transport = function(name, args, callback) { requests++; callback("", {}); };
      panel.activate(panel.installed[0], true);
      if (requests) throw new Error("installed plugin has no Apply action");
      panel.sidebarFocus = false; panel.cursor = 0;
      keys.keyClick(Qt.Key_Down);
      if (panel.cursor !== Math.min(panel.columns, panel.locals.length - 1)) throw new Error("plugin grid Down");
      panel.removing = panel.installed[0];
     } else if (sample.phase === 11) {
      panel.cancelSheet(); panel.tab = "official"; panel.installed = [];
      panel.availableItems = [{id:"gallery",name:"Gallery plugin",kind:"official",author:"Example author",version:"1.2",description:"A plugin with pictures and video",repository:"https://example.invalid/plugins",folder:"plugins/gallery",preview:"preview.png",previewUrl:"PREVIEW",components:{rows:[{title:"Open notes",run:"notes.sh"}],ui:{widgets:[{title:"Desktop notes",qml:"Notes.qml"}]}},media:[{type:"image",path:"picture.png",caption:"Desktop picture"},{type:"video",path:"clip.webm",caption:"A short demonstration"}]}];
     } else if (sample.phase === 12) {
      panel.openDetail(panel.availableItems[0]);
      panel.artwork = {[panel.artworkKey("preview.png")]:"PREVIEW",[panel.artworkKey("picture.png")]:"PREVIEW2",[panel.artworkKey("clip.webm")]:"VIDEO"};
      panel.selectMedia(1);
      if (panel.currentMedia.caption !== "Desktop picture") throw new Error("selected image");
     } else if (sample.phase === 13) {
      panel.videoPosterOnly = true; panel.selectMedia(2);
      function find(root, name) { if (root.objectName === name) return root; for (const child of root.children || []) { const found = find(child, name); if (found) return found; } return null; }
      const player = panel.videoPlayer;
      if (!player || !player.source.toString().endsWith("clip.webm") || !player.muted || player.loops !== -1) throw new Error("video state/source/muted/loop");
     } else if (sample.phase === 14) {
      panel.mediaIndex = 0;
      panel.transport = function(name,args,callback) {
       if (name === "prepare") callback("",{review:{token:"fixture-token",spec:{name:"Gallery plugin",author:"Example author",version:"1.2",rows:[{title:"Open notes",run:"notes.sh"}],ui:{widgets:[{title:"Desktop notes",qml:"Notes.qml"}]}},url:"https://github.com/eitr-org/eitr-plugins",folder:"plugins/gallery",commit:"0123456789abcdef0123456789abcdef01234567",official:true,author:"Example author · 2026-11-03",files:["eitr-plugin.json","Notes.qml","notes.sh"],flags:[]}});
       else callback("",{});
      };
      panel.prepareReview({id:"gallery"});
      if (!panel.nativeReviewing || !panel.nativeReview.token || panel.busy) throw new Error("native prepare");
     } else if (sample.phase === 15) {
      panel.nativeReview = Object.assign({},panel.nativeReview,{official:false,url:"https://example.invalid/plugin"});
     } else if (sample.phase === 16) {
      panel.nativeReview = Object.assign({},panel.nativeReview,{changes:{old:"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",new:"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",subjects:["b123456 Add desktop notes"],files:[{status:"M",path:"Notes.qml",added:"12",removed:"3"}],flags:["Commit by a different author than the approved one: Example author"]}});
     } else if (sample.phase === 17) {
      panel.discardReview(); panel.closeDetail(); panel.addingAddress = true;
     } else {
      panel.addingAddress = false;
      panel.forceActiveFocus(); keys.keyClick(Qt.Key_Escape);
      if (panel.removing) throw new Error("Escape cancels removal");
      panel.opened = true;
      panel.kind = "themes";
      panel.tab = "official";
      panel.availableItems = [{id:"new",name:"New",size:1024},{id:"other",name:"Other",size:2048}]; panel.selected = ["other"];
      panel.openDetail(panel.availableItems[0]);
      function find(root, name) { if (root.objectName === name) return root; for (const child of root.children || []) { const found = find(child, name); if (found) return found; } return null; }
      const install = find(panel, "detail-install");
      keys.mouseClick(install, install.width / 2, install.height / 2);
      if (panel.chosen.length !== 1 || panel.chosen[0].id !== "new" || panel.selected[0] !== "other") throw new Error("detail review isolates theme and preserves selection");
      panel.transport = function(name, args, callback) {
       if (name === "install") sample.installReply = callback;
       else callback("", {items:[{id:"new",name:"New",kind:"official"}]});
      };
      panel.confirm();
      if (!panel.busy || !panel.reviewing) throw new Error("install stays in sheet");
      sample.installReply("Install failed", {});
      if (!panel.reviewing || panel.error !== "Install failed") throw new Error("install error stays in sheet");
      panel.confirm();
      sample.installReply("", {});
      if (panel.busy || panel.reviewing || panel.selected.length || panel.installed[0].id !== "new") throw new Error("install returns to refreshed gallery");
      if (!panel.detail || !panel.isInstalled(panel.detailItem)) throw new Error("detail reflects successful install");
      const apply = find(panel, "detail-install");
      if (apply.text !== "Apply") throw new Error("detail offers Apply after install");
      const prepared = [];
      panel.transport = function(name, args, callback) { if (name === "prepare") prepared.push(args); callback("", {}); };
      panel.nativeReviewing = true;
      panel.nativeReview = {url: "https://example.invalid/themes", choices: [{id: "alpha", name: "Alpha", description: "First", light: false, size: 2048}, {id: "beta", name: "Beta", description: "Second", light: true, size: 4096}], dataOnly: true};
      panel.toggleGitTheme("alpha"); panel.toggleGitTheme("beta"); panel.toggleGitTheme("alpha");
      find(panel, "git-continue").clicked();
      if (prepared.length !== 1 || JSON.stringify(prepared[0].ids) !== JSON.stringify(["beta"])) throw new Error("Continue reviews the chosen Git themes: " + JSON.stringify(prepared));
      panel.nativeReviewing = false; panel.nativeReview = null; panel.busy = false;
      const applied = [];
      panel.transport = function(name, args, callback) { if (name === "apply") applied.push(args.id); callback("", {items: panel.installed}); };
      apply.clicked();
      if (panel.detail || applied[0] !== "new") throw new Error("Apply closes the pop-up and applies the theme");
      prepared.length = 0;
      panel.kind = "plugins";
      panel.transport = function(name, args, callback) { if (name === "prepare") prepared.push(args); callback("", {}); };
      panel.nativeReviewing = true;
      panel.nativeReview = {url: "https://example.invalid/plugins", choices: [{id: "clock", name: "Clock", description: "A clock", icon: "plugins/clock/icon.svg"}, {id: "notes", name: "Notes", description: "Notes", icon: "plugins/notes/icon.svg"}]};
      panel.gitSelected = []; panel.toggleGitTheme("clock"); panel.toggleGitTheme("notes");
      find(panel, "git-continue").clicked();
      if (prepared.length !== 1 || prepared[0].id !== "clock" || panel.pluginQueue[0].id !== "notes") throw new Error("plugins from an address are reviewed one by one: " + JSON.stringify(prepared));
      panel.busy = false; panel.nativeReview = {url: "https://example.invalid/plugins", token: "first"};
      panel.nativeConfirm();
      if (prepared.length !== 2 || prepared[1].id !== "notes" || panel.pluginQueue.length) throw new Error("the next chosen plugin follows a confirmed one");
      panel.discardReview(); panel.busy = false;
      panel.addingAddress = true; find(panel, "git-address").text = "https://example.invalid/old";
      panel.live = false; panel.opened = false; panel.opened = true;
      if (panel.addingAddress || find(panel, "git-address").text !== "" || panel.gitSelected.length) throw new Error("closing resets the address form and selections");
      panel.kind = "themes";
      panel.tone = "light"; panel.kind = "plugins";
      panel.installed = [{id:"clock",name:"Clock",kind:"official"}];
      if (panel.locals.length !== 1) throw new Error("theme filter must not hide plugins");
      const calls = [];
      panel.live = true;
      panel.transport = function(name, args, callback) { calls.push(name + ":" + args.kind + ":" + args.channel); callback("", {items: [{id: args.channel + "-" + args.kind, name: "Row"}]}); };
      panel.load();
      if (calls.length !== 6 || !calls.includes("index:themes:community") || !calls.includes("installed:plugins:installed")) throw new Error("opening loads every source once: " + calls);
      panel.tab = "community"; panel.kind = "themes"; panel.tab = "installed"; panel.tab = "official";
      if (calls.length !== 6) throw new Error("switching tabs must not reload: " + calls);
      if (panel.availableItems[0].id !== "official-themes" || panel.installed[0].id !== "installed-themes") throw new Error("views come from the loaded store");
      panel.tab = "community";
      const replies = [];
      const artworkPaths = [];
      panel.transport = function(name, args, callback) {
       if (name === "detail") replies.push(callback);
       if (name === "artwork") { artworkPaths.push(args.path); callback("", {image:""}); }
      };
      panel.openDetail({id:"fresh",kind:"community",name:"Original"});
      panel.closeDetail();
      panel.openDetail({id:"fresh",kind:"community",name:"Original"});
      replies[0]("", {item:{name:"Stale"}});
      if (panel.detail.name !== "Original") throw new Error("stale detail must not replace reopened sheet");
      replies[1]("", {item:{name:"Fresh"}});
      if (panel.detail.name !== "Fresh") throw new Error("current detail reply");
      panel.closeDetail(); panel.tab = "official";
      panel.openDetail({id:"lazy",kind:"official",name:"Lazy",wallpapers:[{path:"themes/lazy/backgrounds/wall.png",thumbnail:"thumbnails/lazy/wall.jpg",size:123} ]});
      if (artworkPaths.length !== 1 || artworkPaths[0] !== "thumbnails/lazy/wall.jpg") throw new Error("opening details fetches thumbnail only");
      panel.showWallpaper(0);
      if (artworkPaths.length !== 2 || artworkPaths[1] !== "themes/lazy/backgrounds/wall.png") throw new Error("wallpaper loads only on selection");
      keys.mouseClick(panel, 2, panel.height / 2);
      if (panel.detail || !panel.activeFocus) throw new Error("outside click closes detail and restores focus");
      panel.live = false;
      console.log("CATALOG_OK"); Qt.quit(); return;
     }
     panel.installed = panel.installed.map(item => Object.assign({}, item, {palette: sample.installedPalettes[item.id]}));
     panel.availableItems = panel.availableItems.map(item => Object.assign({}, item, {palette: sample.indexPalettes[item.id]}));
     const name = names[sample.phase++];
     capture.name = name; capture.restart();
    }
   }
  }
 }
}
'''
                if theme == 'light':
                    marker = folder / 'theme/current/light.mode'
                    marker.parent.mkdir(parents=True)
                    marker.touch()
                fixture = fixture.replace('SITE_LIGHT', 'true' if theme == 'light' else 'false')
                fixture = fixture.replace('BACKGROUND', '#181824' if theme == 'dark' else '#f4f2e8').replace('FOREGROUND', '#cdd6f4' if theme == 'dark' else '#202824')
                fixture = fixture.replace('ACCENT', '#9a815c' if theme == 'dark' else '#6f5a2c')
                from eitr_theme_packages import catalog, palette
                themes = BAR.parents[1] / 'themes'
                package_root = folder / 'packages'
                for theme_id in ('eitr', 'afterglow', 'eitr-light'):
                    source = themes / theme_id
                    destination = package_root / theme_id
                    destination.mkdir(parents=True)
                    for filename in ('colors.toml', 'display-name', 'eitr-theme.json', 'preview.png', 'light.mode'):
                        if (source / filename).exists():
                            shutil.copyfile(source / filename, destination / filename)
                    (destination / 'backgrounds').mkdir()
                    wallpaper = next(path for path in (source / 'backgrounds').iterdir() if path.is_file())
                    shutil.copyfile(wallpaper, destination / 'backgrounds' / wallpaper.name)
                index = catalog(package_root)
                installed_palettes = {theme_id: palette(themes / folder_name) for theme_id, folder_name in
                                      [('eitr', 'eitr'), ('afterglow', 'afterglow'), ('mine', 'eitr-light')]}
                index_palettes = {theme_id: next(row['palette'] for row in index if row['id'] == source_id)
                                  for theme_id, source_id in [('moss', 'afterglow'), ('jade', 'eitr-light'), ('asgard', 'eitr')]}
                fixture = fixture.replace('INSTALLED_PALETTES', json.dumps(installed_palettes)).replace('INDEX_PALETTES', json.dumps(index_palettes))
                icon = folder / 'plugin-icon.svg'
                icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect x="4" y="4" width="56" height="56" rx="12" fill="#759456"/><circle cx="32" cy="32" r="15" fill="#181824"/></svg>')
                video = folder / 'clip.webm'
                subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=0x53664a:s=160x90:d=0.3', '-c:v', 'libvpx-vp9', '-an', str(video)], check=True)
                fixture = fixture.replace('VIDEO', video.as_uri())
                fixture = fixture.replace('ICON', icon.as_uri()).replace('WALLPAPER', next((themes / 'afterglow/backgrounds').glob('*')).as_uri())
                fixture = fixture.replace('TARGET', str(target)).replace('VARIANT', variant).replace('WIDTH', width).replace('PREVIEW3', (BAR.parents[1] / 'themes/eitr-light/preview.png').as_uri()).replace('PREVIEW2', (BAR.parents[1] / 'themes/afterglow/preview.png').as_uri()).replace('PREVIEW', (BAR.parents[1] / 'themes/eitr/preview.png').as_uri())
                (folder / 'fixture.qml').write_text(fixture)
                environment = render_environment(folder)
                environment.pop('QT_QUICK_BACKEND', None)
                environment.update(QSG_RHI_BACKEND='opengl', LIBGL_ALWAYS_SOFTWARE='1', QT_AUDIO_BACKEND='null', PULSE_SERVER='unix:/nonexistent')
                code, output = render(folder / 'fixture.qml', environment, 30)
                (target / f'{variant}.log').write_text(output)
                self.assertEqual(code, 0, output)
                self.assertIn('CATALOG_OK', output)
                self.assertNotIn('ReferenceError', output)
                self.assertNotIn('TypeError', output)
                self.assertNotIn('Cannot open:', output)
                self.assertNotIn('Error decoding:', output)
                self.assertNotIn('Unable to assign', output)
                for state in ('official-themes', 'selected-themes', 'detail-overview', 'detail-wallpaper', 'review', 'installing', 'community-detail', 'installed-search', 'plugins-official', 'plugins-installed', 'remove', 'plugin-cards-install', 'plugin-images', 'plugin-video', 'plugin-review-official', 'plugin-review-third-party', 'plugin-update-review', 'git-address'):
                    self.assertGreater((target / f'{state}-{variant}.png').stat().st_size, 10000)

    def test_handbook_uses_shared_native_window(self):
        for variant in ('dark-1100', 'light-1100', 'dark-700', 'light-700'):
            theme, width = variant.split('-')
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                copy_runtime(folder)
                shutil.copytree(BAR / 'handbook', folder / 'handbook', dirs_exist_ok=True)
                shutil.copytree(BAR / 'assets', folder / 'assets', dirs_exist_ok=True)
                target = Path(os.environ.get('EITR_HANDBOOK_RENDERS', directory))
                target.mkdir(parents=True, exist_ok=True)
                fixture = '''//@ pragma AppId eitr-catalog
import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 Bar.Handbook {
  id: book
  foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#759456"
  opened: true; implicitWidth: WIDTH; implicitHeight: 800
  defaultSize: Qt.size(WIDTH, 800)
 }
 Timer { interval: 150; running: true; onTriggered: { Bar.SiteStyle.light = LIGHT; book.show("getting-started"); book.implicitWidth = WIDTH; book.implicitHeight = 800; } }
 property int stage: 0
 Timer { interval: 650; running: true; repeat: true; onTriggered: {
  if (book.color.a !== 1 || !Qt.colorEqual(Bar.SettingsPalette.background, "BACKGROUND") || !Qt.colorEqual(Bar.SettingsPalette.foreground, "FOREGROUND")) throw new Error("Handbook follows the Settings palette");
  if (Bar.SiteStyle.light !== LIGHT) throw new Error("light marker");
  if (!book.opened || book.title !== "EITR Handbook" || book.chapters.length === 0 || book.loadError) throw new Error("Handbook window/load");
  book.contentItem.children[0].grabToImage(function(result) {
   if (!result.saveToFile("TARGET/handbook-VARIANT-" + stage + ".png")) throw new Error("Handbook capture");
   if (stage === 0 && (!book.welcomeVisible || !book.chapter.welcome.tour.items.length)) throw new Error("Welcome layout");
   if (stage === 0) { book.stepWelcome(1); book.chapters = book.chapters.map(chapter => chapter.id === "terminal" ? Object.assign({}, chapter, {blocks: chapter.blocks.slice(0, 1).concat(chapter.blocks.slice(21, 25))}) : chapter); book.choose("terminal"); stage++; return; }
   if (stage === 1) { book.choose("getting-started"); book.query = "keyboard"; stage++; return; }
   book.closed();
   if (book.opened) throw new Error("Compositor close");
   book.showWelcome(true);
   if (!book.opened || !book.welcomeShown) throw new Error("Welcome reopen");
   console.log("HANDBOOK_WINDOW_OK"); Qt.quit();
  });
 } }
}
'''
                fixture = fixture.replace('BACKGROUND', '#181824' if theme == 'dark' else '#f4f2e8').replace('FOREGROUND', '#cdd6f4' if theme == 'dark' else '#202824')
                fixture = fixture.replace('LIGHT', 'true' if theme == 'light' else 'false')
                fixture = fixture.replace('WIDTH', width).replace('TARGET', str(target)).replace('VARIANT', variant)
                (folder / 'fixture.qml').write_text(fixture)
                environment = render_environment(folder)
                environment.pop('QT_QUICK_BACKEND', None)
                environment.update(QSG_RHI_BACKEND='opengl', LIBGL_ALWAYS_SOFTWARE='1', QT_AUDIO_BACKEND='null', PULSE_SERVER='unix:/nonexistent')
                code, output = render(folder / 'fixture.qml', environment, 15)
                (target / f'handbook-{variant}.log').write_text(output)
                self.assertEqual(code, 0, output)
                self.assertIn('HANDBOOK_WINDOW_OK', output)
                self.assertNotIn('TypeError', output)
                self.assertNotIn('ReferenceError', output)
                self.assertNotIn('Unable to assign', output)

class CatalogBackendTests(unittest.TestCase):
    def test_theme_backend_results_and_offline_errors(self):
        from eitr_theme_packages import Themes
        with patch.object(Themes, 'installed', return_value=[]) as installed:
            self.assertEqual(DOMAIN.worker('installed', {'kind': 'themes'}), {'items': []})
            installed.assert_called_once()
        with patch.object(Themes, 'index', side_effect=OSError('offline')):
            with self.assertRaisesRegex(OSError, 'offline'):
                DOMAIN.worker('index', {'kind': 'themes'})
        with patch.object(Themes, 'remove', side_effect=ValueError('Cannot remove the current theme; apply eitr first')):
            with self.assertRaisesRegex(ValueError, 'Cannot remove the current theme'):
                DOMAIN.worker('remove', {'kind': 'themes', 'id': 'eitr'})

    def test_theme_artwork_is_row_scoped_and_single_blob(self):
        from eitr_theme_packages import Themes, catalog
        from eitr_plugin_install import git as theme_git
        from eitr_paths import cache
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'XDG_CACHE_HOME': directory + '/cache', 'XDG_STATE_HOME': directory + '/state'}):
            root = Path(directory) / 'repository'
            package = root / 'themes/alpha'
            package.mkdir(parents=True)
            (package / 'backgrounds').mkdir()
            (package / 'colors.toml').write_text((BAR.parents[1] / 'themes/eitr/colors.toml').read_text())
            (package / 'display-name').write_text('Alpha')
            (package / 'eitr-theme.json').write_text(json.dumps(dict(schemaVersion=1, id='alpha', name='Alpha', description='Fixture', version='1', light=False)))
            Image.new('RGB', (160, 90), 'green').save(package / 'preview.png')
            Image.new('RGB', (1920, 1080), 'red').save(package / 'backgrounds/wall.jpg')
            subprocess.run([sys.executable, str(BAR.parents[1] / 'tools/theme-catalog-index.py'), str(root)], check=True)
            for arguments in (['init', '-q'], ['config', 'uploadpack.allowFilter', 'true'], ['add', '.'],
                              ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture']):
                subprocess.run(['git', '-C', str(root), *arguments], check=True)
            backend = Themes(allow_file=True)
            url = root.as_uri()
            index = backend.index(url)
            target = cache('eitr/catalog-previews/index.json')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(index))
            row = index['themes'][0]
            for asset in (row['preview'], row['wallpapers'][0]['thumbnail'], row['wallpapers'][0]['path']):
                with patch.object(DOMAIN, 'THEMES', url), patch('eitr_plugin_install.git', wraps=theme_git) as reads:
                    result = DOMAIN.artwork_preview('themes', 'alpha', backend, asset)
                    self.assertTrue(Path(result['image'].removeprefix('file://')).is_file())
                    blobs = [call for call in reads.call_args_list if call.args[1:3] == ('cat-file', 'blob')]
                    self.assertEqual(len(blobs), 1)
                    DOMAIN.artwork_preview('themes', 'alpha', backend, asset)
                    self.assertEqual(len([call for call in reads.call_args_list if call.args[1:3] == ('cat-file', 'blob')]), 1)
            with patch.object(DOMAIN, 'THEMES', url), patch('eitr_plugin_install.git', wraps=theme_git) as reads:
                for asset in ('themes/alpha/colors.toml', 'themes/beta/preview.png', '../preview.png'):
                    with self.assertRaises(ValueError):
                        DOMAIN.artwork_preview('themes', 'alpha', backend, asset)
                self.assertFalse(reads.called)
            wallpaper_blob = theme_git(root, 'rev-parse', index['commit'] + ':themes/alpha/backgrounds/wall.jpg')
            # Use a separate sparse cache so earlier artwork requests cannot hide eager downloads.
            isolated = Themes(allow_file=True)
            isolated.cache = Path(directory) / 'community-repositories'
            community_index = {'themes': [dict(id='alpha', repository=url, folder='themes/alpha', maintainer='Fixture', license='MIT', description='Fixture')]}
            cache('eitr/community-index.json').write_text(json.dumps(community_index))
            with patch('eitr_community.validate_index', side_effect=lambda value: value), patch('eitr_plugin_install.git', wraps=theme_git) as reads:
                detail = DOMAIN.community_detail('alpha', isolated)['item']
                self.assertEqual(detail['wallpapers'], [dict(path='themes/alpha/backgrounds/wall.jpg', size=None)])
                self.assertEqual(detail['preview'], 'themes/alpha/preview.png')
                community_repository = next(asset for asset in isolated.cache.iterdir() if asset.is_dir())
                missing = theme_git(community_repository, 'rev-list', '--objects', '--missing=print', detail['commit'])
                self.assertIn('?' + wallpaper_blob, missing)
                self.assertEqual(detail['name'], 'Alpha')
                self.assertFalse(detail['light'])
                self.assertEqual(len(detail['palette']), 19)
                blobs = [call for call in reads.call_args_list if call.args[1:3] == ('cat-file', 'blob')]
                self.assertEqual(len(blobs), 2)
                self.assertEqual({call.args[3] for call in blobs}, {
                    theme_git(root, 'rev-parse', index['commit'] + ':themes/alpha/' + filename)
                    for filename in ('eitr-theme.json', 'colors.toml')})
                DOMAIN.artwork_preview('themes', 'alpha', isolated, detail['wallpapers'][0]['path'], 'community')
                with self.assertRaisesRegex(ValueError, 'not listed'):
                    DOMAIN.artwork_preview('themes', 'alpha', isolated, 'themes/alpha/colors.toml', 'community')
            # Size checks reject before reading the blob, for each artwork class.
            for asset in (row['preview'], row['wallpapers'][0]['thumbnail'], row['wallpapers'][0]['path']):
                for cached in target.parent.glob('*'):
                    if cached.suffix != '.json': cached.unlink()
                def oversized(repository, *arguments, **options):
                    if arguments[:2] == ('cat-file', '-s'): return str(17 * 1024 * 1024)
                    return theme_git(repository, *arguments, **options)
                with patch.object(DOMAIN, 'THEMES', url), patch('eitr_plugin_install.git', side_effect=oversized) as reads:
                    with self.assertRaisesRegex(ValueError, 'size limit'):
                        DOMAIN.artwork_preview('themes', 'alpha', backend, asset)
                    self.assertFalse(any(call.args[1:3] == ('cat-file', 'blob') for call in reads.call_args_list))

    def test_plugin_catalog_reads_only_metadata(self):
        from eitr_plugin_install import PluginInstall
        calls = []
        def git(root, *arguments, **options):
            calls.append(arguments)
            if arguments[0] == 'clone':
                self.assertIn('--filter=blob:none', arguments)
                self.assertIn('--no-checkout', arguments)
                Path(arguments[-1]).mkdir(parents=True)
                return ''
            if arguments[0] == 'rev-parse':
                if len(arguments) == 2 and ':' not in arguments[1]:
                    return 'a' * 40
                return 'index-blob' if arguments[1].endswith(':eitr-plugins.json') else 'manifest-blob'
            if arguments[0] == 'ls-tree':
                if '-rlz' in arguments:
                    return '100644 blob abc 120\tmain.qml\0'
                return '100644 blob abc\tmetadata.json'
            if arguments[:2] == ('cat-file', '-s'):
                return '120'
            if arguments[:2] == ('cat-file', 'blob'):
                return json.dumps({'schemaVersion': 1, 'plugins': [{'id': 'clock', 'path': 'plugins/clock'}]}) if arguments[2] == 'index-blob' else json.dumps({'id': 'clock', 'name': 'Clock', 'description': 'A desktop clock', 'author': 'Fixture', 'version': '1', 'media': [{'type': 'video', 'path': 'clip.webm', 'caption': 'Demo'}], 'icon': 'icon.svg', 'preview': 'preview.png'})
            raise AssertionError(arguments)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_CACHE_HOME': directory, 'XDG_STATE_HOME': directory}), patch('eitr_plugin_install.git', side_effect=git):
            self.assertEqual(PluginInstall().catalog(DOMAIN.PLUGINS), [{'id': 'clock', 'name': 'Clock', 'description': 'A desktop clock', 'size': 0, 'author': 'Fixture', 'version': '1', 'components': {}, 'repository': DOMAIN.PLUGINS, 'folder': 'plugins/clock', 'media': [{'type': 'video', 'path': 'plugins/clock/clip.webm', 'caption': 'Demo'}], 'commit': 'a' * 40, 'icon': 'plugins/clock/icon.svg', 'preview': 'plugins/clock/preview.png'}])
        self.assertEqual(sum(arguments[:2] == ('cat-file', 'blob') for arguments in calls), 2)

    def test_plugin_artwork_from_local_repository(self):
        from eitr_plugin_install import PluginInstall, git as plugin_git
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'XDG_CACHE_HOME': directory + '/cache', 'XDG_STATE_HOME': directory + '/state'}):
            root = Path(directory) / 'repository'
            root.mkdir()
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'uploadpack.allowFilter', 'true'], check=True)
            package = root / 'plugins/clock'
            package.mkdir(parents=True)
            (root / 'eitr-plugins.json').write_text(json.dumps({'schemaVersion': 1, 'plugins': [{'id': 'clock', 'path': 'plugins/clock'}]}))
            spec = dict(id='clock', name='Clock', author='Fixture', version='1', description='A desktop clock', icon='icon.svg')
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64"/></svg>'
            (package / 'icon.svg').write_text(icon)
            Image.new('RGB', (160, 90), 'green').save(package / 'preview.png')
            (package / 'bad.png').write_text('not an image')
            (package / 'clip.webm').write_bytes(bytes.fromhex('1a45dfa3') + b'fixture')
            spec['media'] = [dict(type='video', path='clip.webm', caption='Demo')]
            (package / 'script.svg').write_text(icon.replace('</svg>', '<script>alert(1)</script></svg>'))
            (package / 'large.png').write_bytes(b'x' * (2 * 1024 * 1024 + 1))
            (package / 'link.png').symlink_to('preview.png')
            backend = PluginInstall(allow_file=True)
            url = root.as_uri()

            def commit_spec():
                (package / 'eitr-plugin.json').write_text(json.dumps(spec))
                subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
                subprocess.run(['git', '-C', str(root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'], check=True)

            for artwork, failure in [(None, None), ('preview.png', None), ('large.png', 'size limit'),
                                     ('link.png', 'regular file'), ('script.svg', 'image'), ('bad.png', 'image')]:
                with self.subTest(artwork=artwork):
                    spec.pop('preview', None)
                    if artwork:
                        spec['preview'] = artwork
                    commit_spec()
                    with patch('eitr_plugin_install.git', wraps=plugin_git) as reads:
                        rows = backend.catalog(url)
                        blobs = [call.args for call in reads.call_args_list if call.args[1:3] == ('cat-file', 'blob')]
                        self.assertEqual(len(blobs), 2)
                    target = Path(directory) / 'cache/eitr/catalog-previews/plugins.json'
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(json.dumps(rows))
                    import hashlib
                    from eitr_plugin_install import normalized_url
                    repository = Path(directory) / 'cache/eitr/plugin-repositories' / hashlib.sha256(normalized_url(url).encode()).hexdigest()
                    def missing_blobs():
                        output = subprocess.check_output(['git', '-C', str(repository), 'rev-list', '--objects', '--missing=print', rows[0]['commit']], text=True)
                        return {line[1:] for line in output.splitlines() if line.startswith('?')}
                    before = missing_blobs()
                    requested = 'plugins/clock/' + (artwork or 'icon.svg')
                    expected_blob = plugin_git(root, 'rev-parse', rows[0]['commit'] + ':' + requested)
                    if artwork in (None, 'preview.png'):
                        self.assertIn(expected_blob, before)
                    with patch.object(DOMAIN, 'PLUGINS', url), patch('eitr_plugin_install.git', wraps=plugin_git) as reads:
                        if failure:
                            with self.assertRaisesRegex(ValueError, failure):
                                DOMAIN.artwork_preview('plugins', 'clock', backend)
                        else:
                            result = DOMAIN.artwork_preview('plugins', 'clock', backend)
                            self.assertTrue(Path(result['image'].removeprefix('file://')).is_file())
                        blobs = [call.args for call in reads.call_args_list if call.args[1:3] == ('cat-file', 'blob')]
                        self.assertLessEqual(len(blobs), 1)
                        self.assertLessEqual(before - missing_blobs(), {expected_blob})
                        if artwork in (None, 'preview.png'):
                            self.assertEqual(len(blobs), 1)
            with patch('eitr_plugin_install.git', wraps=plugin_git) as reads:
                result = DOMAIN.artwork_preview('plugins', 'clock', backend, 'plugins/clock/clip.webm')
                self.assertTrue(result['image'].endswith('.webm'))
                self.assertEqual(sum(call.args[1:3] == ('cat-file', 'blob') for call in reads.call_args_list), 1)
            with patch('eitr_plugin_install.git', wraps=plugin_git) as reads:
                self.assertEqual(DOMAIN.artwork_preview('plugins', 'clock', backend, 'plugins/clock/clip.webm'), result)
                self.assertFalse(reads.called)
            with self.assertRaisesRegex(ValueError, 'not listed'):
                DOMAIN.artwork_preview('plugins', 'clock', backend, 'plugins/clock/unlisted.webm')
            spec.pop('preview', None)
            spec['icon'] = 'script.svg'
            commit_spec()
            rows = backend.catalog(url)
            target.write_text(json.dumps(rows))
            with patch.object(DOMAIN, 'PLUGINS', url), self.assertRaisesRegex(ValueError, 'shapes'):
                DOMAIN.artwork_preview('plugins', 'clock', backend)
            for escape in ('../outside.png', '/tmp/outside.png'):
                spec['icon'] = escape
                commit_spec()
                with self.assertRaisesRegex(ValueError, 'inside'):
                    backend.catalog(url)

    def test_plugin_index_rejects_overlaps_and_empty_accepts_installed(self):
        from eitr_plugin_manifest import index_entries
        from eitr_plugin_install import PluginInstall
        with self.assertRaisesRegex(ValueError, 'overlap'):
            index_entries({'schemaVersion': 1, 'plugins': [{'id': 'one', 'path': 'plugins'}, {'id': 'two', 'path': 'plugins/two'}]})
        with patch.object(PluginInstall, 'installed', return_value=[]):
            self.assertEqual(DOMAIN.worker('installed', {'kind': 'plugins'}), {'items': []})

    def test_installed_plugins_use_the_runtime_owner(self):
        from eitr_plugins import Plugins
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'HOME': directory, 'XDG_DATA_HOME': directory, 'XDG_STATE_HOME': directory,
                'XDG_CONFIG_HOME': directory, 'XDG_CACHE_HOME': directory}), patch.object(
                    Plugins, 'installed', return_value=[{'id': 'clock', 'official': True}]) as installed:
            result = DOMAIN.worker('installed', {'kind': 'plugins'})
            installed.assert_called_once()
            self.assertEqual(result['items'][0]['kind'], 'official')


class CatalogBrokerTests(unittest.IsolatedAsyncioTestCase):
    async def test_lazy_dispatch_duplicate_and_empty_reply(self):
        import asyncio
        spec = importlib.util.spec_from_file_location('catalog_broker', BAR / 'scripts/bar-data.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        frames = []
        broker = module.Broker(frames.append)
        self.assertNotIn('catalog', broker.domains)
        adapter = Mock()
        adapter.request.return_value = {'items': []}
        broker.domains['catalog'] = adapter
        frame = dict(v=1, op='query', topic='catalog', id='request', name='installed', args={'kind': 'themes'})
        try:
            broker.request(frame)
            with self.assertRaisesRegex(ValueError, 'invalid-query'):
                broker.request(frame)
            for attempt in range(100):
                if frames:
                    break
                await asyncio.sleep(0.01)
            self.assertEqual(frames[0]['data'], {'items': []})
            self.assertEqual(frames[0]['topic'], 'catalog')
            adapter.request.assert_called_once()
        finally:
            await broker.close()
        adapter.close.assert_called_once()

    async def test_get_more_burst_queues_independently_of_weather(self):
        import asyncio
        spec = importlib.util.spec_from_file_location('catalog_broker', BAR / 'scripts/bar-data.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        frames = []
        broker = module.Broker(frames.append)
        adapter = Mock()
        adapter.request.return_value = {'items': []}
        broker.domains['catalog'] = adapter
        for index in range(8):
            broker.queries[f'weather-{index}'] = threading.Event()
        try:
            for kind in ('themes', 'plugins'):
                for index, name in enumerate(['installed', 'index'] + ['preview'] * 12):
                    broker.request(dict(v=1, op='query', topic='catalog', id=f'{kind}-{index}',
                                        name=name, args={'kind': kind, 'id': f'theme-{index}'}))
            self.assertEqual(frames, [])
            self.assertEqual(len(broker.catalog_queries), 28)
            await asyncio.gather(*list(broker.jobs))
            self.assertEqual(len(frames), 28)
            self.assertTrue(all(not frame['error'] for frame in frames))
            self.assertEqual(len(broker.catalog_queries), 0)
        finally:
            await broker.close()

    async def test_catalog_queue_cap(self):
        import asyncio
        spec = importlib.util.spec_from_file_location('catalog_broker', BAR / 'scripts/bar-data.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        frames = []
        broker = module.Broker(frames.append)
        slots = broker.read_slots['catalog']
        await slots.acquire()
        await slots.acquire()
        try:
            for index in range(257):
                broker.request(dict(v=1, op='query', topic='catalog', id=f'request-{index}',
                                    name='index', args={'kind': 'themes'}))
            self.assertEqual(len(broker.catalog_queries), 256)
            self.assertEqual(len(frames), 1)
            self.assertEqual(frames[0]['id'], 'request-256')
            self.assertEqual(frames[0]['error'], 'Catalog busy; retry')
        finally:
            await broker.close()
            slots.release()
            slots.release()

    async def test_close_cancels_requests_waiting_for_admission(self):
        import asyncio
        spec = importlib.util.spec_from_file_location('catalog_broker', BAR / 'scripts/bar-data.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        frames = []
        broker = module.Broker(frames.append)
        slots = broker.read_slots['catalog']
        await slots.acquire()
        await slots.acquire()
        try:
            broker.request(dict(v=1, op='query', topic='catalog', id='request', name='index', args={'kind': 'themes'}))
            await asyncio.sleep(0)
            broker.request(dict(v=1, op='cancel', topic='catalog', id='request'))
            slots.release()
            for attempt in range(100):
                if not broker.queries:
                    break
                await asyncio.sleep(0.01)
            self.assertNotIn('catalog', broker.domains)
            self.assertEqual(frames, [])
        finally:
            slots.release()
            await broker.close()
