"""Inert dark/light Settings editor renders; no desktop or compositor writes."""
import os
from pathlib import Path
import tempfile
import unittest
from layout_render import copy_runtime, render_environment, render


class EditorsRenderTests(unittest.TestCase):
    def test_editors(self):
        output = Path(os.environ.get('EITR_EDITORS_RENDERS', '/tmp/eitr-editors-renders'))
        output.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            folder = Path(directory)
            copy_runtime(folder)
            fixture = '''import QtQuick
import Quickshell
import "." as Bar
import "settings/KeyCapture.js" as KeyCapture
ShellRoot {
 id: root
 property bool light: false
 property bool rules: false
 property bool form: false
 function find(item, name) {
  if (item.objectName === name) return item;
  for (const child of item.children || []) { const result = find(child, name); if (result) return result; }
  return null;
 }
 Bar.SettingsWindow { id: window; live: false; implicitWidth: 1100; implicitHeight: 800 }
 property var keysData: ({items:[
   {default:"SUPER + RETURN",effective:"SUPER + RETURN",title:"Open terminal",group:"Launchers",changed:false,protected:false},
   {default:"SUPER + E",effective:"SUPER + SHIFT + E",title:"Open file manager",group:"Launchers",changed:true,protected:false},
   {default:"SUPER + P",effective:null,title:"Fuzzy-find files",group:"Launchers",changed:true,protected:false}]})
 property var rulesData: ({rules:[{class:"example.app",float:true,workspace:"3",size:"900 600",opacity:0.9}],apps:[{class:"installed.app",name:"An installed app",icon:"",title:""},{class:"example.app",name:"Example app",icon:"applications-internet",title:"Example"}]})
 Component.onCompleted: {
  const combinations = [
   [Qt.Key_Return, Qt.MetaModifier, "SUPER + RETURN"],
   [Qt.Key_Colon, Qt.MetaModifier | Qt.ShiftModifier, "SUPER + SHIFT + SEMICOLON"],
   [Qt.Key_F12, Qt.ControlModifier, "CTRL + F12"],
   [Qt.Key_MonBrightnessUp, Qt.NoModifier, "XF86MONBRIGHTNESSUP"]];
  for (const combination of combinations) {
   const result = KeyCapture.combination({key: combination[0], modifiers: combination[1]});
   if (result !== combination[2]) throw new Error("Qt capture mapping failed: " + result);
  }
 }

 Timer {
  interval: 500; running: true; repeat: true
  property int step: 0
  onTriggered: {
   if (step % 3 === 0) {
    Bar.SiteStyle.light = root.light;
    Bar.SettingsPalette.select("theme",false);
    Bar.SettingsPalette.themeBackground = root.light ? "#f3f8f1" : "#10231c";
    Bar.SettingsPalette.themeForeground = root.light ? "#203b30" : "#e6f1e9";
    Bar.SettingsPalette.themeAccent = root.light ? "#32644c" : "#68aa87";
    window.show(root.rules ? "window-rules" : "keybinds");
    step++; return;
   }
   if (step % 3 === 1) {
    const page = root.find(window.contentItem, root.rules ? "editor-windowrules" : "editor-keybinds");
    if (!page) throw new Error("editor missing");
    page.editorHelper.summary = root.rules ? root.rulesData : root.keysData;
    if (root.form) {
     page.edit(-1);
     if (page.otherApp) throw new Error("new form must wait for Other app selection");
     page.edit(0);
     if (page.appChoices[0].value !== "example.app") throw new Error("open windows must come first");
     if (page.sizeError !== "") throw new Error("valid pixel size rejected");
     page.sizeUnit = "%";
     if (page.sizeError === "") throw new Error("oversize percentage accepted");
     page.sizeUnit = "px";
     if (page.appChoices[page.appChoices.length - 1].value !== "__other__") throw new Error("Other app must be last");
    }
    step++; return;
   }
   root.find(window.contentItem, "settings-content").grabToImage(function(result) {
    if (!result.saveToFile("OUTPUT/" + (root.form ? "window-rules-form" : root.rules ? "window-rules" : "keybinds") + "-" + (root.light ? "light" : "dark") + ".png")) throw new Error("save failed");
    if (root.form && root.light) { console.log("EDITORS_OK"); Qt.quit(); }
    if (root.rules && root.light && !root.form) { root.form = true; root.light = false;  step++; return; }
    if (root.light) { root.rules = true; root.light = false; }
    else root.light = true;
    step++;
   });
  }
 }
}
'''.replace('OUTPUT', str(output))
            (folder / 'EditorsRender.qml').write_text(fixture)
            status, log = render(folder / 'EditorsRender.qml', render_environment(folder, (1400, 1000)), 30)
            self.assertEqual(status, 0, log)
            self.assertIn('EDITORS_OK', log)
            self.assertNotIn('QML error', log)
            self.assertNotIn('polish() loop', log)
            self.assertNotIn('ReferenceError', log)
            self.assertNotIn('TypeError', log)
            self.assertNotIn('Error:', log)
            self.assertNotIn('was not initialized', log)
