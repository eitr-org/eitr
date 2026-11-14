"""The real bundled loader uses the native weather view with an inert data broker."""
import json
from pathlib import Path
import tempfile
import unittest

from layout_render import BAR, copy_runtime, render, render_environment


class BundledWeatherRenderTests(unittest.TestCase):
    def test_weather_capability_observation_and_stable_dimensions(self):
        with tempfile.TemporaryDirectory(prefix='eitr-bundled-render-') as directory:
            folder = Path(directory)
            self.runtime(folder)
            source = BAR.parents[1] / 'distro/plugins/bundled/weather/Weather.qml'
            entry = dict(plugin='weather', id='weather', kind='barItems', slot='clockEnd', title='Weather',
                         disabled=False, commit='a' * 64, source=source.as_uri(), qml='Weather.qml',
                         capabilities=['weather'], panel='forecast')
            fixture = '''import QtQuick
import Quickshell
import "quickshell/desktop-bar" as Bar
ShellRoot {
 FloatingWindow {
  id:weatherWindow; property bool showIcons:true
  visible:true; implicitWidth:500; implicitHeight:200
  Bar.PluginBarItems {
   id: horizontal; x:20; y:20; placementSlot:"clockEnd"
   foreground:"white"; background:"black"; accent:"gold"; entries:[ENTRY]
  }
  Bar.PluginBarItems {
   id: vertical; x:20; y:70; placementSlot:"clockEnd"; vertical:true
   foreground:"white"; background:"black"; accent:"gold"; entries:[ENTRY]
  }
  Repeater {
   id: icons
   model:[{slot:"start",vertical:false},{slot:"status",vertical:false},{slot:"start",vertical:true},{slot:"status",vertical:true}]
   Bar.PluginBarItems {
    required property var modelData
    required property int index
    placementSlot:modelData.slot; vertical:modelData.vertical; x:100 + index * 50; y:100
    open:weatherWindow.showIcons
    foreground:"white"; background:"black"; accent:"gold"; entries:[ENTRY]
   }
  }
  Timer {
   interval:600; running:true; repeat:true
   property int phase:0
   onTriggered: {
    if (phase === 0) {
     if (horizontal.width !== 64 || horizontal.height !== 24 || vertical.width !== 24 || vertical.height !== 24)
      throw new Error("Weather geometry " + [horizontal.width,horizontal.height,vertical.width,vertical.height]);
     if (Bar.DesktopData.observers !== 6) throw new Error("Missing observations " + Bar.DesktopData.observers);
     for (let index = 0; index < icons.count; index++) {
      // Status is a fixed icon slot; start sizes to its content (the full reading across, the icon down the side).
      const item = icons.itemAt(index), wide = item.placementSlot === "start" && !item.vertical;
      if (item.width !== (wide ? 64 : 24) || item.height !== 24) throw new Error("Weather slot geometry " + [item.placementSlot, item.vertical, item.width, item.height]);
     }
     horizontal.observing = false;
     Bar.DesktopData.topics = {"weather.default": {data:{temp:"-100°C",text:"󰖐 -100°C"}}};
    } else if (phase === 1) {
     if (Bar.DesktopData.observers !== 5) throw new Error("Collapsed island kept observing");
     if (horizontal.width !== 64) throw new Error("Weather shifted neighbours");
     horizontal.open = false; vertical.open = false; weatherWindow.showIcons = false;
    } else {
     if (Bar.DesktopData.observers !== 0) throw new Error("Weather observation leaked " + Bar.DesktopData.observers);
     if (horizontal.width !== 0 || vertical.height !== 0) throw new Error("Empty slot gap");
     console.log("BUNDLED_WEATHER_OK"); Qt.quit();
    }
    phase++;
   }
  }
 }
}'''.replace('ENTRY', json.dumps(entry))
            (folder / 'fixture.qml').write_text(fixture)
            environment = render_environment(directory)
            environment['EITR_CODE_ROOT'] = str(folder)
            code, output = render(folder / 'fixture.qml', environment, 8)
            self.assertEqual(code, 0, output)
            self.assertIn('BUNDLED_WEATHER_OK', output)
            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Error:'):
                self.assertNotIn(error, output)

    @staticmethod
    def runtime(folder):
        bar = folder / 'quickshell/desktop-bar'
        copy_runtime(bar)
        (bar / 'plugins/PluginRegistry.qml').write_text("""pragma Singleton
import QtQuick
QtObject {
 property string clockFormat: "24h"
 property var palette: ({})
 property bool weatherEnabled: true
 property var entries: []
 function slotItems(slot) { return entries.filter(entry => entry.slot === slot); }
 function registerSource(entry) {}
 function recordError(plugin, file, line, message) { console.error(message); }
}""")
        (bar / 'services/DesktopData.qml').write_text("""pragma Singleton
import QtQuick
QtObject {
 property int observers: 0
 property var owners: []
 property var topics: ({"weather.default": {data:{temp:"21°C", text:"󰖐 21°C"}}})
 function cancelQuery(token) {}
 function observe(topic, owner) { owners = owners.concat([owner]); observers = owners.length; }
 function releaseOwner(owner) { owners = owners.filter(candidate => candidate !== owner); observers = owners.length; }
}""")

    def test_drop_removal_hides_weather_and_reclaims_calendar_space(self):
        from layout_render import capture_path
        with tempfile.TemporaryDirectory(prefix='eitr-drop-weather-') as directory:
            folder = Path(directory)
            self.runtime(folder)
            capture = capture_path('CLOCK_SLOT', directory, 'drop-home-weather-removed.png')
            fixture = r'''import QtQuick
import Quickshell
import "quickshell/desktop-bar" as Bar
ShellRoot {
 FloatingWindow {
  id:window; visible:true; implicitWidth:620; implicitHeight:320; color:"#18212b"
  Bar.DropHomePage {
   id: home; x:18; y:18; width:584; height:284
   foreground:"#e9eef1"; background:"#18212b"; accent:"#e8ba64"
   now:new Date(2026,10,14)
   barHost: ({calendarMenu:{reminders:[],events:[]}})
  }
  function temperatures(item) {
   let count = item.visible && item.text !== undefined && item.text === "21°C" ? 1 : 0;
   for (const child of item.children || []) count += window.temperatures(child);
   return count;
  }
  Timer {
   interval:300; running:true; repeat:true
   property int phase:0
   onTriggered: {
    try {
     if (phase === 0) {
      if (Bar.DesktopData.observers !== 1 || !home.weatherEnabled) throw new Error("Drop did not observe Weather");
      if (window.temperatures(home) !== 1) throw new Error("Missing weather temperature");
      home.selectedDay = new Date(2026,10,15);
     } else if (phase === 1) {
      if (Bar.DesktopData.observers !== 0 || window.temperatures(home) !== 0) throw new Error("Hidden weather kept observing");
      home.selectedDay = null;
      home.weatherOpen = true;
      Bar.PluginRegistry.weatherEnabled = false;
     } else {
      if (home.weatherOpen || window.temperatures(home) !== 0 || Bar.DesktopData.observers !== 0)
       throw new Error("Drop weather leaked after removal");
      const month = home.children.find(child => child.lead !== undefined);
      if (!month || month.x !== 6 || month.width !== home.width - 10) throw new Error("Calendar left an empty gap");
      home.grabToImage(result => { result.saveToFile(CAPTURE); console.log("DROP_WEATHER_REMOVED_OK"); Qt.quit(); });
      stop();
     }
     phase++;
    } catch (error) { console.error(error); Qt.exit(1); }
   }
  }
 }
}'''.replace('CAPTURE', json.dumps(str(capture)))
            (folder / 'fixture.qml').write_text(fixture)
            environment = render_environment(directory)
            environment['EITR_CODE_ROOT'] = str(folder)
            code, output = render(folder / 'fixture.qml', environment, 8)
            self.assertEqual(code, 0, output)
            self.assertIn('DROP_WEATHER_REMOVED_OK', output)
            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Error:'):
                self.assertNotIn(error, output)
