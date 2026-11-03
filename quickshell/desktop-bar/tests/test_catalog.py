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
    def test_window_lifecycle_and_saved_size(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            (folder / 'services/DesktopData.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function releaseOwner(owner) {} }\n')
            (folder / "eitr").mkdir()
            (folder / "eitr/catalog-window.json").write_text(json.dumps({"width": 610, "height": 510}))
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
  onTriggered: {
   const content = catalog.contentItem.children[0].children[1];
   content.live = false;
   if (phase === 0) {
    if (catalog.opened || catalog.visible) throw new Error("initially closed");
    if (catalog.title !== "Themes & Plugins" || !catalog.stateReady) throw new Error("window metadata/state");
    catalog.show();
   } else if (phase === 1) {
    if (!catalog.opened || !catalog.visible) throw new Error("show");
    if (catalog.width !== 610 || catalog.height !== 510) throw new Error("restored size");
   } else if (phase === 2) {
    catalog.rememberSize();
    catalog.closed();
    if (catalog.opened || catalog.visible) throw new Error("compositor close");
    catalog.show(); catalog.show();
   } else if (phase === 3) {
    if (!catalog.opened || !catalog.visible) throw new Error("reopen");
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
            self.assertEqual(json.loads((folder / 'eitr/catalog-window.json').read_text()),
                             {'width': 610, 'height': 510})

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
   id: sample; anchors.fill: parent; color: Bar.SiteStyle.card
   Bar.CatalogContent {
    id: panel; anchors.fill: parent; live: false; opened: true
    foreground: Bar.SiteStyle.fg; background: Bar.SiteStyle.card; accent: Bar.SiteStyle.accent
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
      keys.mouseClick(panel, panel.sidebarWidth + 50, 160);
      if (panel.progress !== "Installing plugins from the catalog is coming soon; use Walker > Plugins for now") throw new Error("click shows plugin coming-soon note");
     }
     sample.grabToImage(function(result) { result.saveToFile("TARGET/" + capture.name + "-VARIANT.png"); });
    }
   }
   Timer {
    interval: 650; running: true; repeat: true
    onTriggered: {
     if (Bar.SiteStyle.light !== SITE_LIGHT) throw new Error("light.mode detection");
     if (panel.background !== Bar.SiteStyle.card || panel.accent !== Bar.SiteStyle.accent) throw new Error("site palette binding");
     const names = ["official-themes", "selected-themes", "review", "installing", "community-empty", "installed-hidden", "plugins-official", "plugins-installed", "remove"];
     if (sample.phase === 0) {
      panel.installed = [{id:"eitr",name:"Eitr",kind:"builtin",current:true,description:"Primordial venom",previewUrl:"PREVIEW"},{id:"nord",name:"Nord",kind:"official",description:"Cool northern blues",previewUrl:"PREVIEW2"},{id:"mine",name:"My theme",kind:"own",light:true,description:"A quiet light palette",previewUrl:"PREVIEW3"}];
      panel.availableItems = [{id:"moss",name:"Moss",kind:"official",description:"Deep forest greens",size:3145728},{id:"jade",name:"Jade",kind:"official",light:true,description:"Warm jade and cream",size:2097152},{id:"asgard",name:"Asgard",kind:"official",description:"Gold in the halls of the gods",size:2097152}];
      panel.selected = ["moss"];
      panel.previews = {moss: "PREVIEW2", jade: "PREVIEW3", asgard: "PREVIEW"};
      let checks = 0;
      panel.transport = function(name, args, callback) {
       if (name === "check") { checks++; callback("", {updates:{nord:1}}); }
       else callback("", {items:[]});
      };
      panel.checkUpdates();
      if (checks !== 2 || panel.updates.nord !== 1) throw new Error("background update checks");
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
      if (panel.kind !== "plugins") throw new Error("sidebar Down");
      keys.keyClick(Qt.Key_Up);
      if (panel.kind !== "themes") throw new Error("sidebar Up");
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
     } else if (sample.phase === 2) {
      keys.keyClick(Qt.Key_Return);
      if (!panel.reviewing) throw new Error("Enter opens review");
      if (panel.chosen.length !== 2 || panel.totalSize !== 5242880) throw new Error("selection/total");
     } else if (sample.phase === 3) {
      panel.busy = true; panel.progress = "Installing 1 of 2 themes…";
     } else if (sample.phase === 4) {
      panel.busy = false; panel.progress = "";

      panel.forceActiveFocus(); keys.keyClick(Qt.Key_Escape);
      if (panel.reviewing || !panel.opened) throw new Error("Escape must cancel review");
      panel.tab = "community"; panel.availableItems = []; panel.selected = [];
      panel.repositoryError = "Repository unavailable; retry";
     } else if (sample.phase === 5) {
      panel.tab = "installed"; panel.showHidden = true;
      panel.installed = [{id:"eitr",name:"Eitr",kind:"builtin",current:true,description:"Primordial venom",previewUrl:"PREVIEW"},{id:"nord",name:"Nord",kind:"builtin",hidden:true,description:"Cool northern blues",previewUrl:"PREVIEW2"}];
      panel.availableItems = [{id:"notes",name:"Notes",description:"Notes on the desktop",size:12345}];
     } else if (sample.phase === 6) {
      panel.kind = "plugins";
      panel.tab = "official";
      panel.installed = [];
      panel.availableItems = [{id:"clock",name:"Clock",kind:"official",description:"A desktop clock",previewUrl:"PREVIEW",preview:"preview.png"},{id:"notes",name:"Notes",kind:"official",description:"Notes on the desktop",icon:"ICON",previewUrl:"ICON"},{id:"plain",name:"Plain",kind:"official",description:"A plugin without artwork"}];
      panel.activate(panel.availableItems[0], false);
      if (panel.progress !== "Installing plugins from the catalog is coming soon; use Walker > Plugins for now") throw new Error("plugin coming-soon note");
     } else if (sample.phase === 7) {
      panel.tab = "installed";
      panel.installed = [{id:"clock",name:"Clock",kind:"official",description:"A desktop clock",preview:"PREVIEW"},{id:"notes",name:"Notes",kind:"community",description:"Notes on the desktop",icon:"ICON",enabled:false},{id:"plain",name:"Plain",kind:"third-party",description:"A plugin without artwork"}];
     } else if (sample.phase === 8) {
      let requests = 0;
      panel.transport = function(name, args, callback) { requests++; callback("", {}); };
      panel.activate(panel.installed[0], true);
      if (requests) throw new Error("installed plugin has no Apply action");
      panel.sidebarFocus = false; panel.cursor = 0;
      keys.keyClick(Qt.Key_Down);
      if (panel.cursor !== Math.min(panel.columns, panel.locals.length - 1)) throw new Error("plugin grid Down");
      panel.removing = panel.installed[0];
     } else {
      panel.forceActiveFocus(); keys.keyClick(Qt.Key_Escape);
      if (panel.removing || !panel.opened) throw new Error("Escape cancels removal");
      panel.kind = "themes";
      panel.availableItems = [{id:"new",name:"New",size:1024}]; panel.selected = ["new"];
      panel.reviewing = true;
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
                from eitr_theme_packages import catalog, palette
                themes = BAR.parents[1] / 'themes'
                package_root = folder / 'packages'
                for theme_id in ('eitr', 'nord', 'eitr-light'):
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
                                      [('eitr', 'eitr'), ('nord', 'nord'), ('mine', 'eitr-light')]}
                index_palettes = {theme_id: next(row['palette'] for row in index if row['id'] == source_id)
                                  for theme_id, source_id in [('moss', 'nord'), ('jade', 'eitr-light'), ('asgard', 'eitr')]}
                fixture = fixture.replace('INSTALLED_PALETTES', json.dumps(installed_palettes)).replace('INDEX_PALETTES', json.dumps(index_palettes))
                icon = folder / 'plugin-icon.svg'
                icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect x="4" y="4" width="56" height="56" rx="12" fill="#759456"/><circle cx="32" cy="32" r="15" fill="#181824"/></svg>')
                fixture = fixture.replace('ICON', icon.as_uri())
                fixture = fixture.replace('TARGET', str(target)).replace('VARIANT', variant).replace('WIDTH', width).replace('PREVIEW3', (BAR.parents[1] / 'themes/eitr-light/preview.png').as_uri()).replace('PREVIEW2', (BAR.parents[1] / 'themes/nord/preview.png').as_uri()).replace('PREVIEW', (BAR.parents[1] / 'themes/eitr/preview.png').as_uri())
                (folder / 'fixture.qml').write_text(fixture)
                environment = render_environment(folder)
                environment.pop('QT_QUICK_BACKEND', None)
                environment.update(QSG_RHI_BACKEND='opengl', LIBGL_ALWAYS_SOFTWARE='1')
                code, output = render(folder / 'fixture.qml', environment, 30)
                (target / f'{variant}.log').write_text(output)
                self.assertEqual(code, 0, output)
                self.assertIn('CATALOG_OK', output)
                self.assertNotIn('ReferenceError', output)
                self.assertNotIn('TypeError', output)
                self.assertNotIn('Cannot open:', output)
                self.assertNotIn('Unable to assign', output)
                for state in ('official-themes', 'selected-themes', 'review', 'installing', 'community-empty', 'installed-hidden', 'plugins-official', 'plugins-installed', 'remove'):
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
  savedSize: Qt.size(WIDTH, 800)
 }
 Timer { interval: 150; running: true; onTriggered: { Bar.SiteStyle.light = LIGHT; book.show("getting-started"); book.implicitWidth = WIDTH; book.implicitHeight = 800; } }
 property int stage: 0
 Timer { interval: 650; running: true; repeat: true; onTriggered: {
  if (book.color !== Bar.SiteStyle.card || Bar.SiteStyle.light !== LIGHT) throw new Error("Handbook site palette");
  if (!book.opened || book.title !== "EITR Handbook" || book.chapters.length === 0 || book.loadError) throw new Error("Handbook window/load");
  book.contentItem.children[0].grabToImage(function(result) {
   if (!result.saveToFile("TARGET/handbook-VARIANT-" + stage + ".png")) throw new Error("Handbook capture");
   if (stage === 0) { book.chapters = book.chapters.map(chapter => chapter.id === "terminal" ? Object.assign({}, chapter, {blocks: chapter.blocks.slice(0, 1).concat(chapter.blocks.slice(21, 25))}) : chapter); book.choose("terminal"); stage++; return; }
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
                environment.update(QSG_RHI_BACKEND='opengl', LIBGL_ALWAYS_SOFTWARE='1')
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
                return json.dumps({'schemaVersion': 1, 'plugins': [{'id': 'clock', 'path': 'plugins/clock'}]}) if arguments[2] == 'index-blob' else json.dumps({'id': 'clock', 'name': 'Clock', 'description': 'A desktop clock', 'icon': 'icon.svg', 'preview': 'preview.png'})
            raise AssertionError(arguments)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_CACHE_HOME': directory, 'XDG_STATE_HOME': directory}), patch('eitr_plugin_install.git', side_effect=git):
            self.assertEqual(PluginInstall().catalog(DOMAIN.PLUGINS), [{'id': 'clock', 'name': 'Clock', 'description': 'A desktop clock', 'size': 0, 'commit': 'a' * 40, 'icon': 'plugins/clock/icon.svg', 'preview': 'plugins/clock/preview.png'}])
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
            spec = dict(id='clock', name='Clock', description='A desktop clock', icon='icon.svg')
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64"/></svg>'
            (package / 'icon.svg').write_text(icon)
            Image.new('RGB', (160, 90), 'green').save(package / 'preview.png')
            (package / 'bad.png').write_text('not an image')
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
