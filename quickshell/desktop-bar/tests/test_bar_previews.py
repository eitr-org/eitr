"""Offscreen bar geometry and shared consumer render matrix."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from layout_render import BAR, copy_runtime, render_environment, render


class BarPreviewTests(unittest.TestCase):
    def test_layouts_edges_and_consumers(self):
        output = Path(os.environ.get('EITR_BAR_PREVIEW_RENDERS', '/tmp/bar-preview-renders'))
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            shots = []
            for theme in ('dark', 'light'):
                for edge in ('top', 'bottom', 'left', 'right'):
                    for layout in ('unified', 'centered', 'notch', 'islands', 'dynamic', 'drop'):
                        shots.append(dict(theme=theme, edge=edge, layout=layout, mode='large'))
                        if edge in ('left', 'right'):
                            shots.append(dict(theme=theme, edge=edge, layout=layout, mode='compact'))
                    for mode in ('settings', 'narrow', 'figure'):
                        shots.append(dict(theme=theme, edge=edge, layout='unified', mode=mode))
                    for layout in ('unified', 'centered', 'notch', 'islands', 'dynamic', 'drop'):
                        shots.append(dict(theme=theme, edge=edge, layout=layout, mode='welcome'))
                shots.append(dict(theme=theme, edge='top', layout='unified', mode='anatomy'))
            fixture = r'''import QtQuick
import Quickshell
import "." as Bar
import "ChoiceLists.js" as Choices
ShellRoot {
 id: root
 property var shots: SHOTS
 property int shot: 0
 readonly property var current: shots[shot]
 readonly property color foreground: current.theme === "dark" ? "#e4e5ef" : "#202431"
 readonly property color background: current.theme === "dark" ? "#191b25" : "#f5f3ee"
 FloatingWindow {
  id: window; visible: true; implicitWidth: 1000; implicitHeight: 1600
  color: root.background
  Rectangle {
   id: canvas; width: 960; height: content.item ? content.item.height + 40 : 500
   color: root.background
   Loader {
    id: content; x: 20; y: 20
    sourceComponent: ({large: large, compact: compact, settings: settings, narrow: narrow, figure: figure, anatomy: anatomy, welcome: welcome})[root.current.mode]
   }
  }
 }
 Component { id: large
  Bar.BarPreview { width: 900; height: 500; zoom: 2; layout: root.current.layout; edge: root.current.edge; foreground: root.foreground; background: root.background }
 }
 Component { id: compact
  Bar.BarPreview { width: 220; height: 95; layout: root.current.layout; edge: root.current.edge; foreground: root.foreground; background: root.background }
 }
 Component { id: settings
  Bar.SettingsBarPage {
   width: 900
   context: QtObject {
    property string page: "bar"
    property bool live: false
    property color foreground: root.foreground
    property color accent: root.foreground
    property var workspaceHelper: ({summary: {current: "Dots"}})
    property var styleState: ({barPosition: root.current.edge, appearance: "solid", layout: "unified", barScreens: "main", clockFormat: "24h", mediaStyle: "bars", workspaceStyle: "Dots", terminalAppearance: {}, terminalAppearanceChoices: {}, barAutoHide: false, barDock: true, barLyrics: false, bar: {pinned: "no"}})
   }
  }
 }
 Component { id: narrow
  Column {
   width: 380; spacing: 12
   Repeater {
    model: ["layout", "position", "appearance"]
    Bar.PictureChoices {
     required property string modelData
     width: 380; kind: modelData; edge: root.current.edge; compact: true
     foreground: root.foreground; background: root.background
     choices: modelData === "layout" ? Choices.barLayouts : modelData === "appearance" ? Choices.barAppearances : [{id:"top",label:"Top"},{id:"bottom",label:"Bottom"},{id:"left",label:"Left"},{id:"right",label:"Right"}]
    }
   }
  }
 }
 Component { id: figure; Bar.BarLayoutsFigure {
  width: 900; height: implicitHeight
  Component.onCompleted: children[0].edge = Qt.binding(function() { return root.current.edge; })
 } }
 Component { id: anatomy; Bar.BarAnatomyFigure { width: 900; height: implicitHeight } }
 Component { id: welcome
  Bar.WelcomeTourArt {
   id: tour; width: 660; height: 360; step: "bar"; animate: false
   foreground: root.foreground; background: root.background; accent: root.foreground
   artSource: "ARTWORK"
   function findPreview(item) {
    if (item.layouts !== undefined) return item;
    for (const child of item.children) { const found = findPreview(child); if (found) return found; }
    return null;
   }
   Component.onCompleted: Qt.callLater(function() {
    const preview = findPreview(tour);
    if (!preview) throw new Error("Missing shared tour preview");
    preview.shown = Qt.binding(function() { return preview.layouts.indexOf(root.current.layout); });
    preview.edge = Qt.binding(function() { return root.current.edge; });
   })
  }
 }
 Timer {
  interval: 300; running: true; repeat: true
  property bool capturing: false
  onTriggered: {
   if (capturing) return;
   Bar.SiteStyle.light = root.current.theme === "light";
   Bar.SettingsPalette.select("theme", false);
   Bar.SettingsPalette.themeBackground = root.background;
   Bar.SettingsPalette.themeForeground = root.foreground;
   function validate(item) {
    if (item.slots !== undefined) {
     const clock = item.slots.find(slot => slot.kind === "clock");
     if (Math.abs(clock.start + clock.extent / 2 - item.length / 2) > 0.01) throw new Error("Off-centre clock");
     const ordered = item.slots.slice().sort((first, second) => first.start - second.start);
     for (let index = 1; index < ordered.length; index++) {
      if (ordered[index - 1].start + ordered[index - 1].extent > ordered[index].start) throw new Error("Overlapping slots");
     }
    }
    for (const child of item.children) validate(child);
   }
   validate(content.item);
   if (root.current.mode === "welcome") {
    const preview = content.item.findPreview(content.item);
    if (preview.layout !== root.current.layout || preview.edge !== root.current.edge) throw new Error("Tour state mismatch");
   }
   const entry = root.current;
   const name = [entry.theme, entry.mode, entry.edge, entry.layout].join("-");
   capturing = true;
   canvas.grabToImage(function(result) {
    if (!result.saveToFile("OUTPUT/" + name + ".png")) throw new Error("Save failed " + name);
    if (root.shot + 1 === root.shots.length) { console.log("PREVIEWS_OK"); Qt.quit(); }
    else { root.shot++; capturing = false; }
   });
  }
 }
}
'''
            fixture = fixture.replace('SHOTS', json.dumps(shots)).replace('OUTPUT', str(output))
            fixture = fixture.replace('ARTWORK', str(BAR.parents[1] / 'themes/vanaheim/backgrounds/01-hidden-garden.jpg'))
            (folder / 'fixture.qml').write_text(fixture)
            code, diagnostics = render(folder / 'fixture.qml', render_environment(folder, (1200, 1800)), 90)
            (output / 'render.log').write_text(diagnostics)
            self.assertEqual(code, 0, diagnostics)
            self.assertIn('PREVIEWS_OK', diagnostics)
            for error in ('TypeError:', 'ReferenceError:', 'Unable to assign', 'Binding loop', 'Error:'):
                self.assertNotIn(error, diagnostics)
            for shot in shots:
                filename = '-'.join(shot[key] for key in ('theme', 'mode', 'edge', 'layout')) + '.png'
                self.assertTrue((output / filename).is_file(), filename)


if __name__ == '__main__':
    unittest.main()
