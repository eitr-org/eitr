"""Offscreen Settings wallpaper controls in both theme palettes."""
import os
from pathlib import Path
import tempfile
import unittest
from layout_render import copy_runtime, render_environment, render


class WallpaperRenderTests(unittest.TestCase):
    def test_wallpaper_scope_controls(self):
        output = Path(os.environ.get('EITR_WALLPAPER_RENDERS', '/tmp/eitr-wallpaper-renders'))
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
  visible: true; implicitWidth: 720; implicitHeight: 440
  Rectangle {
   id: canvas; width: 720; height: 440
   color: root.light ? "#f3f8f1" : "#10231c"
   Bar.ControlCard {
    x: 24; y: 24; width: 672
    title: "Theme & Wallpaper"
    foreground: root.light ? "#203b30" : "#e6f1e9"
    surface: root.light ? "#e6eee3" : "#19382b"
    gold: root.light ? "#32644c" : "#68aa87"
    Bar.WallpaperScopeControls {
     width: parent.width
     foreground: root.light ? "#203b30" : "#e6f1e9"
     background: root.light ? "#e6eee3" : "#19382b"
     gold: root.light ? "#32644c" : "#68aa87"
     live: false
     model: QtObject {
      property string scope: "workspace"
      property string monitorName: "Display-1"
      property int workspaceNumber: 3
      property var assignments: [{key:"display",monitor:"Display-1",number:0,path:"/art/aurora-fjord.jpg"}, {key:"workspace",monitor:"Display-1",number:3,path:"/art/runestone.jpg"}]
     }
    }
    Row {
     spacing: 8
     Bar.PanelButton { text: "Apply"; foreground: root.light ? "#203b30" : "#e6f1e9" }
     Bar.PanelButton { width: 156; text: "Cancel preview"; foreground: root.light ? "#203b30" : "#e6f1e9" }
    }
   }
  }
 }
 Timer {
  interval: 700; running: true; repeat: true
  onTriggered: canvas.grabToImage(function(result) {
   if (!result.saveToFile("OUTPUT/wallpaper-" + (root.light ? "light" : "dark") + ".png")) throw new Error("save failed");
   if (root.light) { console.log("WALLPAPER_OK"); Qt.quit(); }
   root.light = true;
  })
 }
}
'''.replace('OUTPUT', str(output))
            (folder / 'WallpaperRender.qml').write_text(fixture)
            status, log = render(folder / 'WallpaperRender.qml', render_environment(folder), 30)
            self.assertEqual(status, 0, log)
            self.assertIn('WALLPAPER_OK', log)
            self.assertNotIn('QML error', log)
            for tone in ('dark', 'light'):
                self.assertGreater((output / ('wallpaper-' + tone + '.png')).stat().st_size, 5000)
