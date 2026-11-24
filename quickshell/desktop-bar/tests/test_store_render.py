"""Inert Store UI: every kind, provenance filters and sheets in both palettes."""
import json
import os
import re
from pathlib import Path
import tempfile
import unittest

from PIL import Image

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
                # Captures stay in the temporary folder unless EITR_STORE_RENDERS asks to keep them;
                # the folder beside the checkout is not writable in CI and is no place for test output.
                target = folder / 'renders'
                updates_target = Path(os.environ.get('EITR_STORE_RENDERS') or target)
                target.mkdir(parents=True)
                updates_target.mkdir(parents=True, exist_ok=True)
                fixture = r'''import QtQuick
import Quickshell
import QtTest
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
   TestEvent { id: input }
   property var queueCalls: []
   property bool cachedVisibleDuringRefresh: false
   transport: function(name, args, callback) {
    if (name === "cached-index") {
     callback("", {items: [ROWS[1]]});
    } else if (name === "index" && args.kind === "themes" && args.channel === "community") {
     const cached = panel.availableItems.find(item => item.id === ROWS[1].id);
     panel.cachedVisibleDuringRefresh = !!cached && panel.imageFor(cached) === ROWS[1].previewUrl;
     callback("Offline", {});
    } else if (name === "prepare") {
     queueCalls.push("review " + args.id);
     callback("", {review:{token:args.id,official:false,commit:"0123456789abcdef",spec:{name:args.id,author:"Example",version:"2"},files:[]}});
    } else if (name === "confirm") {
     queueCalls.push("confirm " + args.token);
     callback("", {});
    } else if (name === "update") {
     queueCalls.push("update " + args.id);
     callback("", {});
    } else if (name === "changes") {
     const data = {before:"1.2.0",after:"1.3.0",commits:[{date:"2026-11-20",subject:"Refresh the clock face"},{date:"2026-11-18",subject:"Add a new clock mode"}],more:3};
     if (args.kind === "plugins") data.permissions = {capabilities:["hardware"],packages:["lm_sensors"],service:true,hooks:["login"]};
     callback("", data);
    } else callback("", {});
   }
  }
  Timer {
   interval: 350; running: true; repeat: true
   property int phase: 0
   property var cases: []
   property real collapsedHeight: 0
   function assertUpdateStatus(expected) {
    const footer = find(panel, "store-updates-footer");
    if (!footer.Accessible.name.startsWith(expected))
     throw new Error("Expected " + expected + " but saw " + footer.Accessible.name);
    const status = find(panel, "store-update-status");
    if (expected === "Checking for updates…" || expected === "Up to date")
     if (status.text !== expected) throw new Error("Unexpected Updates page status " + status.text);
   }
   function verifyUpdateCheck() {
    const transport = panel.transport;
    const replies = {};
    panel.opened = false;
    panel.live = true;
    panel.tab = "updates";
    panel.transport = function(name, args, callback) {
     if (name === "check") replies[args.kind] = callback;
     else if (name === "installed" && args.kind === "themes") {
      // load() dispatches this before it starts the background check.
      assertUpdateStatus("Checking for updates…");
      replies.installed = callback;
     } else callback("", {});
    };
    panel.opened = true;
    assertUpdateStatus("Checking for updates…");
    replies.themes("", {updates: {eitr: 1}});
    assertUpdateStatus("Checking for updates…");
    if (panel.updateItems.length || panel.updates.eitr)
     throw new Error("Partial counts must stay hidden");
    replies.plugins("", {updates: {}});
    assertUpdateStatus("Checking for updates…");
    replies.installed("", {items: [ROWS[0]]});
    assertUpdateStatus("Updates available");
    if (panel.updateItems.length !== 1) throw new Error("Missing fresh update result");

    panel.checkUpdates();
    assertUpdateStatus("Checking for updates…");
    replies.themes("", {updates: {eitr: 1}});
    replies.plugins("", {incomplete: true});
    assertUpdateStatus("Update check failed");
    if (panel.updateItems.length !== 1) throw new Error("Missing update from the successful kind");

    panel.checkUpdates();
    replies.themes("Offline", {});
    assertUpdateStatus("Checking for updates…");
    replies.plugins("Offline", {});
    assertUpdateStatus("Update check failed");
    if (find(panel, "store-update-status").text !== "Offline") throw new Error("Expected an offline error");
    if (panel.updateItems.length) throw new Error("Offline check showed stale results");

    panel.checkUpdates();
    replies.themes("", {updates: {}});
    replies.plugins("", {updates: {}});
    assertUpdateStatus("Up to date");
    panel.opened = false;
    panel.live = false;
    panel.transport = transport;
    panel.opened = true;
   }
   Component.onCompleted: {
    verifyUpdateCheck();
    // Switching from a kind with other sources must list the new kind's own sources.
    panel.live = true; panel.kind = "themes"; panel.tab = "discover";
    panel.fetch("themes", "community");
    if (!panel.cachedVisibleDuringRefresh || !panel.availableItems.some(item => item.id === ROWS[1].id))
     throw new Error("Cached theme preview must show before refresh and survive refresh failure");
    panel.kind = "wallpapers";
    panel.store = {"lockscreens:official": {items: [{id: "nothing", name: "Nothing", kind: "official"}], loaded: true}, "lockscreens:installed": {items: [], loaded: true}};
    panel.kind = "lockscreens";
    if (panel.availableItems.length !== 1) throw new Error("Lockscreens empty after Wallpapers");
    panel.live = false;
    for (const kind of ["themes", "plugins", "lockscreens", "wallpapers"])
     for (const tab of ["installed", "discover"]) cases.push({kind:kind, tab:tab, name:kind+"-"+tab});
    for (const tab of ["discover", "installed"])
     for (const waiting of [true, false])
      cases.push({kind:"plugins", tab, waiting, name:tab + (waiting ? "-loading" : "-empty")});
    cases.push({kind:"themes",tab:"discover",filter:"community",name:"community-filter"});
    cases.push({kind:"themes",tab:"discover",search:true,name:"search-filter"});
    cases.push({kind:"themes",tab:"discover",popup:true,name:"appearance-filter"});
    cases.push({kind:"themes",tab:"discover",popup:true,dropdown:true,name:"sort-dropdown"});
    cases.push({kind:"plugins",tab:"discover",popup:true,name:"plugin-filters"});
    cases.push({kind:"themes",tab:"discover",checking:true,name:"updates-footer-checking"});
    cases.push({kind:"themes",tab:"discover",name:"updates-footer-current"});
    cases.push({kind:"themes",tab:"discover",updates:true,name:"updates-footer-available"});
    cases.push({kind:"themes",tab:"discover",updates:true,many:true,name:"updates-footer-many"});
    cases.push({kind:"themes",tab:"updates",checking:true,name:"updates-checking"});
    cases.push({kind:"themes",tab:"updates",updates:true,name:"updates-collapsed"});
    cases.push({kind:"themes",tab:"updates",updates:true,expanded:true,name:"updates-expanded"});
    cases.push({kind:"themes",tab:"discover",detail:true,name:"community-detail"});
    cases.push({kind:"wallpapers",tab:"discover",review:true,name:"wallpaper-review"});
    cases.push({kind:"plugins",tab:"discover",native:true,name:"plugin-review"});
    cases.push({kind:"wallpapers",tab:"installed",remove:true,name:"wallpaper-remove"});
   }
   onTriggered: {
    if (phase === cases.length * 2) {
     panel.removing = null;
     panel.tab = "discover"; panel.kind = "themes";
     panel.query = "Northern"; panel.cursor = 1;
     panel.store = {"plugins:installed": {items:[{id:"clock",name:"Clock"},{id:"weather",name:"Weather"},{id:"skip",name:"Skip"}]}};
     panel.updateCache = {plugins:{clock:1,weather:2,skip:1}};
     find(panel, "store-updates-footer").clicked();
     phase++; return;
    }
    if (phase === cases.length * 2 + 1) {
     find(panel, "store-update-skip").toggleChecked();
     find(panel, "update-selected").clicked();
     if (panel.nativeReview.token !== "clock" || panel.queueCalls.join(",") !== "review clock")
      throw new Error("The selected queue did not pause for its first review");
     panel.nativeConfirm();
     if (panel.nativeReview.token !== "weather" || panel.queueCalls.join(",") !== "review clock,confirm clock,review weather")
      throw new Error("The selected queue did not pause for its second review");
     panel.nativeConfirm();
     if (panel.nativeReviewing || panel.queueCalls.join(",") !== "review clock,confirm clock,review weather,confirm weather")
      throw new Error("The selected queue included an unchecked plugin or missed a confirmation");
     panel.leaveUpdates();
     if (panel.tab !== "discover" || panel.kind !== "themes" || panel.query !== "Northern" || panel.cursor !== 1)
      throw new Error("Back lost the previous Store view");
     console.log("STORE_RENDER_OK"); Qt.quit(); return;
    }
    const entry = cases[Math.floor(phase / 2)];
    if (phase % 2 === 0) {
     panel.updateCheck = {pending: entry.checking ? 1 : 0, date:new Date(2026, 10, 23, 10, 30), error:""};
     panel.query = ""; panel.tone = "all"; panel.sortOrder = "name"; panel.filterValues = ({}); panel.updateCache = ({}); panel.store = ({});
     const filter = find(panel, "catalog-tone-filter"); if (filter) filter.expanded = false;
     panel.detail = null; panel.reviewing = false; panel.nativeReviewing = false; panel.removing = null;
     panel.kind = entry.kind; panel.tab = entry.tab; panel.sourceFilter = entry.filter || "all";
     panel.installed = ROWS.slice(0,1); panel.availableItems = ROWS; panel.installedLoaded = true; panel.indexLoaded = true;
     if (entry.kind === "plugins") {
      const weather = {id:"weather", name:"Weather", kind:"builtin", builtin:true, official:true, removable:true, previewUrl:"WEATHER_ICON", components:{ui:{widgets:[{}],barItems:[{}]}}};
      panel.installed = [weather]; panel.availableItems = ROWS.concat([weather]);
     }
     if (entry.waiting !== undefined) {
      panel.store = entry.waiting ? {"plugins:installed": {items:[], pending:true}} : {
       "plugins:installed": {items:[], loaded:true},
       "plugins:official": {items:[], loaded:true},
       "plugins:community": {items:[], loaded:true}
      };
      panel.sync();
      const empty = find(panel, "catalog-empty-state");
      const status = find(panel, "catalog-status");
      if (!empty || empty.visible === entry.waiting || !status || status.visible !== entry.waiting
          || (entry.waiting && status.text !== "Loading…"))
       throw new Error("Wrong listing state for " + entry.name);
     }
     panel.selected = []; panel.reviewIds = null;
     if (entry.filter && (panel.discoveries.length !== 1 || panel.badge(panel.discoveries[0]) !== "Community")) throw new Error("Provenance filter");
     const field = find(panel, "catalog-search");
     if (entry.tab !== "updates" && (!field || !field.visible || field !== panel.searchField)) throw new Error("Visible shared header search missing");
     if (entry.search) {
      panel.store = {"plugins:official": {items:[{id:"other",name:"Other kind",kind:"official"}]}};
      panel.query = "other";
      if (panel.navigable.length) throw new Error("Search escaped the selected kind");
      field.forceActiveFocus(); panel.query = "northern"; panel.tone = "light";
      if (field.text !== "northern" || panel.discoveries.length !== 1) throw new Error("Search and tone must combine");
      panel.chooseFilter(panel.definition.filters[0], "dark");
      if (panel.discoveries.length !== 0) throw new Error("Tone filter ignored");
      panel.chooseFilter(panel.definition.filters[0], "light");
      field.accepted();
      if (panel.cursor !== 0) throw new Error("Search acceptance must enter the grid");
      find(panel, "catalog-search-clear").clicked();
      if (panel.query !== "" || field.text !== "") throw new Error("Clear search did not clear the shared query");
      panel.query = "northern";
     }
     if (entry.updates) {
      panel.store = {"themes:installed": {items:[ROWS[0]]}, "plugins:installed": {items:[{id:"clock",name:"Clock widget",kind:"official",components:{ui:{widgets:[{}]}}}]}};
      panel.updateCache = {themes:{eitr:1}, plugins:{clock:2}};
      if (panel.updateItems.length !== 2 || panel.navigation.length !== 2) throw new Error("Updates across kinds");
      if (entry.many) {
       // Twenty updates across every kind: the footer's kinds line wraps instead of being cut off.
       const installed = (prefix, count) => ({items: Array.from({length: count}, (_, index) => ({id: prefix + "-" + index, name: prefix + " " + index}))});
       panel.store = {"themes:installed": installed("theme", 5), "plugins:installed": installed("plugin", 5),
                      "lockscreens:installed": installed("lock", 5), "wallpapers:installed": installed("wall", 5)};
       const cache = {};
       for (const [kind, prefix] of [["themes","theme"],["plugins","plugin"],["lockscreens","lock"],["wallpapers","wall"]]) {
        cache[kind] = {};
        for (let index = 0; index < 5; index++) cache[kind][prefix + "-" + index] = 1;
       }
       panel.updateCache = cache;
       if (panel.updateItems.length !== 20) throw new Error("Twenty updates");
      }
     }
     if (entry.expanded) {
      const plugin = find(panel, "store-update-clock");
      collapsedHeight = plugin.height;
      plugin.toggleExpanded();
      if (!plugin.expanded || plugin.height !== collapsedHeight || plugin.expandDuration !== 320)
       throw new Error("Expansion should animate from the collapsed height");
     }
     if (entry.popup) {
      filter.expanded = true;
      if (entry.dropdown) find(filter.popup.contentItem, "store-filter-sort").expanded = true;
     }
     if (entry.detail) panel.openDetail(ROWS[1]);
     if (entry.review) { panel.reviewIds = ["northern-art"]; panel.reviewing = true; }
     if (entry.native) {
      panel.nativeReview = {token:"inert-token",official:false,url:"https://example.invalid/plugins",commit:"0123456789abcdef0123456789abcdef01234567",spec:{name:"Northern plugin",version:"1",author:"Example"},files:["main.qml"],flags:["Review the source before installing"]};
      panel.nativeReviewing = true;
     }
     if (entry.remove) panel.removing = ROWS[1];
    } else {
     const footer = find(panel, "store-updates-footer");
     if (!footer || footer.height < 60 || !footer.activeFocusOnTab || footer.found !== !!entry.updates)
      throw new Error("Update footer state or sizing");
     if (entry.checking && (!panel.checkingUpdates || panel.updateItems.length || !footer.Accessible.name.includes("Checking for updates…")))
      throw new Error("Checking state exposed an update result");
     if (entry.tab === "updates" && !entry.checking) {
      const page = find(panel, "store-updates-page");
      const plugin = find(panel, "store-update-clock");
      const theme = find(panel, "store-update-eitr");
      if (!page.visible || !plugin.checked || plugin.version !== "1.2.0 → 1.3.0") throw new Error("Update preview");
      const select = find(panel, "updates-select");
      select.clicked();
      if (page.selected.length !== 0 || plugin.checked) throw new Error("Select none");
      select.clicked();
      if (page.selected.length !== page.items.length || !plugin.checked) throw new Error("Select all");
      if (find(panel, "update-clock").width < 50) throw new Error("Clipped per-row Update button");
      if (entry.expanded) {
       plugin.moveFocus(-1);
       if (!theme.activeFocus) throw new Error("Previous update row focus");
       theme.moveFocus(1);
       if (!plugin.activeFocus) throw new Error("Next update row focus");
       theme.toggleChecked();
       if (page.selected.length !== 1 || find(panel, "update-selected").text !== "Update selected (1)") throw new Error("Update selection");
       if (!plugin.expanded || plugin.height <= collapsedHeight || !Qt.colorEqual(plugin.border.color, panel.accent))
        throw new Error("Expanded details should extend the original surface");
       if (Qt.colorEqual(theme.border.color, panel.accent))
        throw new Error("Collapsed rows should have a neutral outline");
      }
     }
     if (entry.popup) {
      const filter = find(panel, "catalog-tone-filter");
      const popupContent = filter.popup.contentItem;
      const sort = find(popupContent, "store-filter-sort");
      if (!sort || sort.current !== "name" || sort.choices.length !== 3
          || !find(popupContent, "store-filter-source")
          || !!find(popupContent, "store-filter-tone") !== (entry.kind === "themes"))
       throw new Error("Single-choice filters must use dropdowns");
      if (entry.kind === "plugins") {
       const widgets = find(popupContent, "store-filter-adds-widgets");
       const barItems = find(popupContent, "store-filter-adds-barItems");
       if (!widgets || !barItems || find(popupContent, "store-filter-adds"))
        throw new Error("Adds must use a checklist");
       if (!input.mouseClick(widgets, 20, widgets.height / 2, Qt.LeftButton, Qt.NoModifier, -1)
           || !input.mouseClick(barItems, 20, barItems.height / 2, Qt.LeftButton, Qt.NoModifier, -1))
        throw new Error("Adds checklist is not clickable");
       if (!widgets.selected || !barItems.selected || !panel.filtersActive
           || panel.discoveries.length !== 1 || panel.discoveries[0].id !== "weather")
        throw new Error("Adds must keep both selections and filter for their intersection");
      }
      if (entry.dropdown) {
       if (!sort.popup.opened || sort.popup.z <= filter.popup.z) throw new Error("Dropdown must open above the filter popup");
       const dropdown = sort.popup.background.parent;
       const menu = filter.popup.background.parent;
       const offset = dropdown.mapToItem(menu, 0, 0);
       console.log("DROPDOWN_OFFSET " + Math.round(offset.x) + " " + Math.round(offset.y));
       menu.grabToImage(result => {
        if (!result.saveToFile("TARGET/sort-menu-base.png")) throw new Error("Filter capture failed");
       });
       dropdown.grabToImage(result => {
        if (!result.saveToFile("TARGET/sort-menu-list.png")) throw new Error("Dropdown capture failed");
        if (!input.keyClick(Qt.Key_Escape, Qt.NoModifier, -1) || sort.popup.opened || !filter.popup.opened)
         throw new Error("Escape must close the dropdown first");
        if (!input.keyClick(Qt.Key_Escape, Qt.NoModifier, -1) || filter.popup.opened)
         throw new Error("Second Escape must close the filter popup");
        sort.chosen("creation-date");
        if (panel.sortOrder !== "creation-date" || panel.filtersActive)
         throw new Error("Sort must not light the filter indicator");
       });
      } else {
       filter.popup.background.parent.grabToImage(result => {
        if (!result.saveToFile("REVIEW_TARGET/PALETTE-" + entry.name + "-menu.png")) throw new Error("Filter capture failed");
       });
      }
     }
     if (entry.kind === "plugins" && entry.tab === "installed" && entry.waiting === undefined) {
      const remove = window.findNamed(panel, "remove-weather");
      if (!remove || !remove.visible) throw new Error("Bundled Weather cannot be removed");
     }
     const folder = entry.waiting !== undefined || entry.name.startsWith("updates-") || entry.name === "themes-discover" || entry.name === "community-detail" ? "REVIEW_TARGET" : "TARGET";
     const filename = folder + "/PALETTE-" + entry.name + ".png";
     panel.grabToImage(result => {
      if (!result.saveToFile(filename)) throw new Error("Store capture failed");
      if (entry.expanded) {
       const plugin = find(panel, "store-update-clock");
       Bar.DesktopStyle.reduceMotion = true;
       plugin.toggleExpanded();
       if (plugin.height !== collapsedHeight) throw new Error("Reduce motion should collapse instantly");
       plugin.toggleExpanded();
       if (plugin.height <= collapsedHeight) throw new Error("Reduce motion should expand instantly");
       Bar.DesktopStyle.reduceMotion = false;
      }
     });
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
'''.replace('WEATHER_ICON', (ROOT / 'distro/plugins/bundled/weather/icon.svg').as_uri()).replace('ROWS', json.dumps(rows)).replace('REVIEW_TARGET', str(updates_target)).replace('TARGET', str(target)).replace('PALETTE', palette).replace('LIGHT', 'true' if palette == 'light' else 'false').replace('BACKGROUND', '#f4f2e8' if palette == 'light' else '#181824').replace('FOREGROUND', '#202824' if palette == 'light' else '#cdd6f4').replace('ACCENT', '#6f5a2c' if palette == 'light' else '#9a815c')
                (folder / 'fixture.qml').write_text(fixture)
                code, output = render(folder / 'fixture.qml', render_environment(folder), 30)
                self.assertEqual(code, 0, output)
                self.assertIn('STORE_RENDER_OK', output)
                for error in ('TypeError', 'ReferenceError', 'Unable to assign', 'Error:'):
                    self.assertNotIn(error, output)
                # Qt Quick draws popups as separate overlay items. Compose their actual
                # offscreen grabs in z-order using the rendered position of the dropdown.
                offset = re.search(r'DROPDOWN_OFFSET (-?\d+) (-?\d+)', output)
                self.assertIsNotNone(offset, output)
                left, top = map(int, offset.groups())
                with Image.open(target / 'sort-menu-base.png') as base, Image.open(target / 'sort-menu-list.png') as dropdown:
                    origin = min(0, left), min(0, top)
                    width = max(base.width, left + dropdown.width) - origin[0]
                    height = max(base.height, top + dropdown.height) - origin[1]
                    combined = Image.new('RGBA', (width, height))
                    combined.alpha_composite(base.convert('RGBA'), (-origin[0], -origin[1]))
                    combined.alpha_composite(dropdown.convert('RGBA'), (left - origin[0], top - origin[1]))
                    combined.save(updates_target / f'{palette}-sort-dropdown-menu.png')
                for menu in ('appearance-filter', 'sort-dropdown', 'plugin-filters'):
                    self.assertTrue((updates_target / f'{palette}-{menu}-menu.png').exists())
                for state in ('footer-checking', 'footer-current', 'footer-available', 'footer-many', 'checking', 'collapsed', 'expanded'):
                    self.assertTrue((updates_target / f'{palette}-updates-{state}.png').exists())
                for kind in ('themes', 'plugins', 'lockscreens', 'wallpapers'):
                    for tab in ('installed', 'discover'):
                        destination = updates_target if (kind, tab) == ('themes', 'discover') else target
                        self.assertTrue((destination / f'{palette}-{kind}-{tab}.png').exists())
                self.assertTrue((updates_target / f'{palette}-community-detail.png').exists())
