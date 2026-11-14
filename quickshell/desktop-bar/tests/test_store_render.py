"""Inert Store UI: every kind, provenance filters and sheets in both palettes."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from layout_render import copy_runtime, render_environment, render

BAR = Path(__file__).resolve().parents[1]
ROOT = BAR.parents[1]


class StoreRenderTests(unittest.TestCase):
    def test_store_palettes_kinds_filter_and_sheets(self):
        for palette in ('dark', 'light'):
            with self.subTest(palette=palette), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                copy_runtime(folder)
                (folder / 'services/DesktopData.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
 function releaseOwner(owner) {}
 function queryCatalog(name, args, owner, callback) { callback("", {}); }
}
''')
                image = (ROOT / 'themes/eitr/preview.png').as_uri()
                rows = [dict(id='eitr', name='Eitr', kind='builtin', channel='official', current=True, previewUrl=image),
                        dict(id='northern-art', name='Northern art', description='Drawn northern skies', kind='community',
                             light=True, channel='community', repository='https://example.invalid/art', folder='art/northern',
                             maintainer='Example artist', license='MIT', previewUrl=image, size=1048576)]
                target = Path(os.environ.get('EITR_STORE_RENDERS', ROOT.parent / 'renders'))
                target.mkdir(parents=True, exist_ok=True)
                fixture = r'''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 function find(item, name) {
  if (item.objectName === name) return item;
  for (const child of item.children || []) { const found = find(child, name); if (found) return found; }
  return null;
 }
 FloatingWindow {
  id: window
  function findNamed(item, name) {
   if (item.objectName === name) return item;
   for (const child of item.children || []) { const found = window.findNamed(child, name); if (found) return found; }
   return null;
  }
  visible: true; implicitWidth: 1100; implicitHeight: 900
  Bar.StoreContent {
   id: panel; anchors.fill: parent; live: false; opened: true
   transport: function(name, args, callback) { callback("", {}); }
  }
  Timer {
   interval: 350; running: true; repeat: true
   property int phase: 0
   property var cases: []
   Component.onCompleted: {
    for (const kind of ["themes", "plugins", "lockscreens", "wallpapers"])
     for (const tab of ["installed", "discover"]) cases.push({kind:kind, tab:tab, name:kind+"-"+tab});
    cases.push({kind:"themes",tab:"discover",filter:"community",name:"community-filter"});
    cases.push({kind:"themes",tab:"discover",search:true,name:"search-filter"});
    cases.push({kind:"themes",tab:"discover",popup:true,name:"appearance-filter"});
    cases.push({kind:"themes",tab:"discover",detail:true,name:"community-detail"});
    cases.push({kind:"wallpapers",tab:"discover",review:true,name:"wallpaper-review"});
    cases.push({kind:"plugins",tab:"discover",native:true,name:"plugin-review"});
    cases.push({kind:"wallpapers",tab:"installed",remove:true,name:"wallpaper-remove"});
   }
   onTriggered: {
    if (phase === cases.length * 2) { console.log("STORE_RENDER_OK"); Qt.quit(); return; }
    const entry = cases[Math.floor(phase / 2)];
    if (phase % 2 === 0) {
     panel.query = ""; panel.tone = "all";
     const filter = find(panel, "catalog-tone-filter"); if (filter) filter.expanded = false;
     panel.detail = null; panel.reviewing = false; panel.nativeReviewing = false; panel.removing = null;
     panel.kind = entry.kind; panel.tab = entry.tab; panel.sourceFilter = entry.filter || "all";
     panel.installed = ROWS.slice(0,1); panel.availableItems = ROWS; panel.loading = false; panel.indexLoaded = true;
     if (entry.kind === "plugins") {
      const weather = {id:"weather", name:"Weather", kind:"builtin", builtin:true, official:true, removable:true, previewUrl:"WEATHER_ICON"};
      panel.installed = [weather]; panel.availableItems = ROWS.concat([weather]);
     }
     panel.selected = []; panel.reviewIds = null;
     if (entry.filter && (panel.discoveries.length !== 1 || panel.badge(panel.discoveries[0]) !== "Community")) throw new Error("Provenance filter");
     const field = find(panel, "catalog-search");
     if (!field || !field.visible || field !== panel.searchField) throw new Error("Visible shared header search missing");
     if (entry.search) {
      field.forceActiveFocus(); panel.query = "northern"; panel.tone = "light";
      if (field.text !== "northern" || panel.discoveries.length !== 1) throw new Error("Search and tone must combine");
      filter.commit(2);
      if (panel.discoveries.length !== 0) throw new Error("Tone filter ignored");
      filter.commit(1);
      field.accepted();
      if (panel.cursor !== 0) throw new Error("Search acceptance must enter the grid");
      find(panel, "catalog-search-clear").clicked();
      if (panel.query !== "" || field.text !== "") throw new Error("Clear search did not clear the shared query");
      panel.query = "northern";
     }
     if (entry.popup) filter.expanded = true;
     if (entry.detail) panel.openDetail(ROWS[1]);
     if (entry.review) { panel.reviewIds = ["northern-art"]; panel.reviewing = true; }
     if (entry.native) {
      panel.nativeReview = {token:"inert-token",official:false,url:"https://example.invalid/plugins",commit:"0123456789abcdef0123456789abcdef01234567",spec:{name:"Northern plugin",version:"1",author:"Example"},files:["main.qml"],flags:["Review the source before installing"]};
      panel.nativeReviewing = true;
     }
     if (entry.remove) panel.removing = ROWS[1];
    } else {
     if (entry.popup) find(panel, "catalog-tone-filter").popup.background.parent.grabToImage(result => { if (!result.saveToFile("TARGET/PALETTE-appearance-menu.png")) throw new Error("Filter capture failed"); });
     if (entry.kind === "plugins" && entry.tab === "installed") {
      const remove = window.findNamed(panel, "remove-weather");
      if (!remove || !remove.visible) throw new Error("Bundled Weather cannot be removed");
     }
     const filename = "TARGET/" + "PALETTE-" + entry.name + ".png";
     panel.grabToImage(result => { if (!result.saveToFile(filename)) throw new Error("Store capture failed"); });
    }
    phase++;
   }
  }
  Component.onCompleted: {
   Bar.SettingsPalette.themeBackground = "BACKGROUND";
   Bar.SettingsPalette.themeForeground = "FOREGROUND";
   Bar.SettingsPalette.themeAccent = "ACCENT";
  }
  Binding { target: Bar.SiteStyle; property: "light"; value: LIGHT }
 }
}
'''.replace('ROWS', json.dumps(rows)).replace('TARGET', str(target)).replace('PALETTE', palette).replace('LIGHT', 'true' if palette == 'light' else 'false').replace('BACKGROUND', '#f4f2e8' if palette == 'light' else '#181824').replace('FOREGROUND', '#202824' if palette == 'light' else '#cdd6f4').replace('ACCENT', '#6f5a2c' if palette == 'light' else '#9a815c')
                (folder / 'fixture.qml').write_text(fixture)
                code, output = render(folder / 'fixture.qml', render_environment(folder), 20)
                self.assertEqual(code, 0, output)
                self.assertIn('STORE_RENDER_OK', output)
                for error in ('TypeError', 'ReferenceError', 'Unable to assign', 'Error:'):
                    self.assertNotIn(error, output)
                for kind in ('themes', 'plugins', 'lockscreens', 'wallpapers'):
                    for tab in ('installed', 'discover'):
                        self.assertTrue((target / f'{palette}-{kind}-{tab}.png').exists())
