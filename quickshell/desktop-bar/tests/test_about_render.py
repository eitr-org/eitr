"""Render the About logo cards with inert system information in both themes."""
import os
from pathlib import Path
import tempfile
import unittest
from layout_render import copy_runtime, render_environment, render


class AboutRenderTests(unittest.TestCase):
    def test_about_logo_cards(self):
        output = Path(os.environ.get('EITR_ABOUT_RENDERS', '/tmp/eitr-about-renders'))
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            fixture = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 id: root
 property bool light: false
 FloatingWindow {
  visible: true; implicitWidth: 900; implicitHeight: 900
  Rectangle {
   id: canvas; width: 860; height: page.height + 40
   color: root.light ? "#f3f8f1" : "#10231c"
   Bar.SettingsAboutPage {
    id: page; x: 20; y: 20; width: 820
    context: QtObject {
     property string page: "about"
     property color foreground: root.light ? "#203b30" : "#e6f1e9"
     property var matches: [{title:"Version",detail:"0.6.4"},{title:"Codename",detail:"Mimir"}]
     property var helper: QtObject {
      property bool busy: false
      property var summary: ({aboutLogo:"runes",aboutLogos:[{id:"emblem",label:"Emblem"},{id:"runes",label:"Runes"}],hardware:[{title:"CPU",name:"Example processor"}]})
      function change(arguments) {}
     }
    }
   }
  }
 }
 Timer {
  interval: 500; running: true; repeat: true
  property int step: 0
  onTriggered: {
   if (step === 0 || step === 2) {
    Bar.SiteStyle.light = root.light;
    Bar.SettingsPalette.select("theme",false);
    Bar.SettingsPalette.themeBackground = root.light ? "#f3f8f1" : "#10231c";
    Bar.SettingsPalette.themeForeground = root.light ? "#203b30" : "#e6f1e9";
    Bar.SettingsPalette.themeAccent = root.light ? "#32644c" : "#68aa87";
    step++; return;
   }
   canvas.grabToImage(function(result) {
    if (!result.saveToFile("OUTPUT/about-" + (root.light ? "light" : "dark") + ".png")) throw new Error("save failed");
    if (root.light) { console.log("ABOUT_OK"); Qt.quit(); }
    root.light = true; step++;
   });
  }
 }
}
'''.replace('OUTPUT',str(output))
            (folder/'AboutRender.qml').write_text(fixture)
            status, log = render(folder / 'AboutRender.qml', render_environment(folder), 30)
            self.assertEqual(status, 0, log)
            self.assertIn('ABOUT_OK', log)
            self.assertNotIn('QML error', log)
            from PIL import Image
            for theme, accent in (('dark', (104, 170, 135)), ('light', (50, 100, 76))):
                with Image.open(output / ('about-' + theme + '.png')) as screenshot:
                    for bounds in ((36, 72, 426, 277), (434, 72, 824, 277)):
                        crop = screenshot.convert('RGB').crop(bounds)
                        colours = crop.getcolors(crop.width * crop.height)
                        self.assertGreater(sum(count for count, colour in colours if colour == accent), 100,
                                           'Missing theme-coloured logo preview: ' + theme)
