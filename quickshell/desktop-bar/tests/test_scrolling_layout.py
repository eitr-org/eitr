"""Preference, compositor, menu and offscreen Settings regressions for scrolling."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from test_desktop_style import style
from layout_render import BAR, copy_runtime, render_environment, render, capture_path

REPO = BAR.parents[1]


class ScrollingLayoutTests(unittest.TestCase):
    def test_all_options_roundtrip_generate_and_preserve_other_preferences(self):
        run_lua = subprocess.run
        source = (REPO / 'hypr/hyprland.lua').read_text()
        loader = source.split('local window_layout =', 1)[1].split('local window_rounding', 1)[0]
        with tempfile.TemporaryDirectory() as directory, patch.object(style, 'SETTINGS', Path(directory) / 'eitr/style.json'), patch.object(style.subprocess, 'run') as refresh:
            self.assertEqual(style.current_layout(), style.LAYOUT_DEFAULTS)
            style.select('square')
            style.select('large', 'gaps')
            for key, default in style.LAYOUT_DEFAULTS.items():
                options = [choice['id'] for choice in style.LAYOUT_CHOICES[key]] if key in style.LAYOUT_CHOICES else ['yes', 'no']
                for value in options:
                    style.select(value, key)
                    self.assertEqual(style.current_layout()[key], value)
                    style.generate_layout()
                    fixture = 'local paths = {config = ' + json.dumps(directory) + '}\nlocal window_layout =' + loader
                    fixture += '\nprint(window_layout.layout, window_layout.direction, window_layout.column_width, window_layout.focus_fit_method, window_layout.follow_focus, tostring(window_layout.fullscreen_on_one_column))'
                    result = run_lua(['lua', '-'], input=fixture, text=True, capture_output=True, check=True)
                    preference = style.current_layout()
                    def native(setting):
                        return next(choice.get('value', choice['id']) for choice in style.LAYOUT_CHOICES[setting] if choice['id'] == preference[setting])
                    self.assertEqual(result.stdout.strip().split(), [preference['layout'], preference['scrollDirection'],
                        native('scrollWidth'), native('scrollFocusFit'),
                        '1' if preference['scrollFollowFocus'] == 'yes' else '0',
                        'true' if preference['scrollFullscreen'] == 'yes' else 'false'])
                    self.assertEqual(style.current(), 'square')
                    self.assertEqual(style.current_gaps(), 'large')
                with self.assertRaises(ValueError):
                    style.select('unknown', key)
                style.select(default, key)
            saved = style.current_layout()
            style.select('scrolling', 'layout')
            style.select('rounded')
            self.assertEqual(style.current_layout(), {**saved, 'layout': 'scrolling'})
            generated = style.SETTINGS.with_name('window-layout.lua').read_text()
            self.assertIn('column_width = 0.5', generated)
            self.assertIn('focus_fit_method = 1', generated)
            self.assertIn('explicit_column_widths = "0.333, 0.5, 0.667, 1.0"', generated)
            self.assertTrue(any(call.args[0] == ['hyprctl', 'reload'] for call in refresh.call_args_list))
            self.assertNotIn('restart', str(refresh.call_args_list))
            style.SETTINGS.write_text(json.dumps({key: [] for key in style.LAYOUT_DEFAULTS}))
            self.assertEqual(style.current_layout(), style.LAYOUT_DEFAULTS)
        self.assertIn('layout = window_layout.layout', source)
        for option in ['direction', 'column_width', 'focus_fit_method', 'follow_focus', 'fullscreen_on_one_column', 'explicit_column_widths']:
            self.assertIn(option + ' = window_layout.' + option, source)

    def test_shortcut_dispatch_is_guarded_by_live_layout(self):
        for layout in ['dwindle', 'scrolling']:
            with patch.object(style.subprocess, 'run') as run:
                run.return_value.stdout = json.dumps({'str': layout})
                style.scroll_action(['colresize', '+conf'])
                self.assertEqual(run.call_count, 2 if layout == 'scrolling' else 1)
                if layout == 'scrolling':
                    self.assertEqual(run.call_args.args[0], ['hyprctl', 'dispatch', 'layoutmsg', 'colresize +conf'])
            with patch.object(style.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    style.scroll_action(['unexpected'])
                run.assert_not_called()
        source = (REPO / 'hypr/hyprland.lua').read_text()
        guarded = source.split('if window_layout.layout == "scrolling" then', 1)[1].split('\nend', 1)[0]
        from eitr_menu import shortcut_reference
        entries = shortcut_reference()
        for entry in entries:
            if '(scrolling only)' in entry.get('description', ''):
                self.assertIn(entry['command'].split(' scroll ', 1)[1], guarded)

    def test_walker_choices_and_submenus_without_live_processes(self):
        def lua_value(value):
            if isinstance(value, str):
                return json.dumps(value, ensure_ascii=False)
            if isinstance(value, list):
                return "{" + ",".join(lua_value(item) for item in value) + "}"
            return "{" + ",".join("[" + lua_value(key) + "]=" + lua_value(item) for key, item in value.items()) + "}"
        path = REPO / 'elephant/menu-rows/window-layout.json'
        decoded = {path.read_text(): json.loads(path.read_text())}
        fixture = 'local decoded = ' + lua_value(decoded) + '\n' + r'''
local root = os.getenv("EITR_CODE_ROOT")
local calls = 0
jsonDecode = function(raw) return decoded[raw] or {} end
io.popen = function(command)
    calls = calls + 1
    local current = command:find("scrollWidth", 1, true) and "half" or command:find("scrollDirection", 1, true) and "right" or "scrolling"
    return {read=function() return current end, close=function() end}
end
for _, spec in ipairs({{"window-layout", "style", "scrolling", 4}, {"scrolling-width", "window-layout", "half", 4}, {"scrolling-direction", "window-layout", "right", 4}}) do
    dofile(root .. "/elephant/menus/" .. spec[1] .. ".lua")
    assert(Parent == spec[2])
    local entries = GetEntries("")
    assert(#entries == spec[4])
    local selected = 0
    for _, entry in ipairs(entries) do
        if entry.Value == spec[3] then
            assert(entry.State[1] == "current")
            assert(entry.Actions.open:find(" set ", 1, true))
            selected = selected + 1
        end
    end
    assert(selected == 1)
    local before = calls
    GetEntries("column")
    assert(calls == before, "typed query reran helper")
end
'''
        with tempfile.TemporaryDirectory() as directory:
            environment = {**os.environ, 'EITR_CODE_ROOT': str(REPO), 'EITR_LIBRARY_ROOT': str(REPO / 'distro/lib'),
                           'HOME': directory, 'XDG_CONFIG_HOME': directory, 'XDG_CACHE_HOME': directory, 'LC_ALL': 'C.UTF-8'}
            result = subprocess.run(['lua', '-'], input=fixture, text=True, capture_output=True, env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_summary_exposes_layout_and_broker_contract(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(style, 'SETTINGS', Path(directory) / 'style.json'), patch.object(style.sys, 'argv', ['desktop-style.py', 'summary']), patch('builtins.print') as printed:
            style.main()
            summary = json.loads(printed.call_args.args[0])
            for key, value in style.LAYOUT_DEFAULTS.items():
                self.assertEqual(summary[key], value)
        from test_display_domain import domain_module
        domain = domain_module.DisplayDomain()
        with patch.object(domain, 'monitors', return_value=[]), patch.object(domain, 'adapter') as adapter, patch.object(domain_module.subprocess, 'run') as run:
            adapter.return_value.current_layout.return_value = {'layout': 'scrolling'}
            adapter.return_value.preferred_outputs.return_value = []
            adapter.return_value.choose_primary.return_value = ''
            run.return_value.stdout = '{"css":"6 6 6 6"}'
            result = domain.read('display.topology')
            self.assertEqual(result['windowLayout'], {'layout': 'scrolling'})

    def test_windows_page_dark_light_and_both_layouts(self):
        from PIL import Image
        for theme in ['dark', 'light']:
            with self.subTest(theme=theme), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                copy_runtime(folder)
                (folder / 'services/FocusMode.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property bool enabled: false }\n')
                tiling = capture_path('SCROLLING', directory, theme + '-tiling.png')
                scrolling = capture_path('SCROLLING', directory, theme + '-scrolling.png')
                fixture = '''import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
 FloatingWindow {
  id: window; visible: true; implicitWidth: 760; implicitHeight: 1080
  color: Bar.SettingsPalette.background
  QtObject {
   id: context
   property bool live: false
   property string page: "windows"
   property color foreground: Bar.SettingsPalette.foreground
   property color accent: Bar.SettingsPalette.accent
   property QtObject styleState: QtObject { property string barPosition: "top"; property string appearance: "theme" }
  }
  Rectangle { id: canvas; anchors.fill: parent; color: Bar.SettingsPalette.background
  Bar.SettingsWindowsPage { id: page; x: 24; y: 24; width: window.width - 48; context: context }
  }
 }
 TestCase {
  name: "ScrollingSettings"; when: window.visible
  function find(item, name) { if (item.objectName === name) return item; for (const child of item.children || []) { const result = find(child, name); if (result) return result; } return null; }
  function test_layouts() {
   Bar.SiteStyle.light = LIGHT;
   Bar.SettingsPalette.themeBackground = LIGHT ? "#f5f3ee" : "#191b25";
   Bar.SettingsPalette.themeForeground = LIGHT ? "#202431" : "#e4e5ef";
   Bar.DesktopStyle.applyLayout({});
   wait(300);
   const options = find(page, "scrollingOptions");
   verify(!options.visible);
   canvas.grabToImage(result => result.saveToFile("TILING"));
   wait(150);
   Bar.DesktopStyle.applyLayout({layout: "scrolling"});
   wait(300);
   verify(options.visible);
   verify(page.height < window.height - 24);
   compare(find(page, "windowLayoutChoice").current, "scrolling");
   const dropdowns = options.children.filter(child => child.current !== undefined);
   compare(dropdowns.length, 3);
   compare(dropdowns[1].currentIndex, 1);
   compare(dropdowns[2].currentIndex, 1);
   let chosen = "";
   dropdowns[1].chosen.connect(value => { chosen = value; });
   dropdowns[1].commit(0);
   compare(chosen, "third");
   canvas.grabToImage(result => result.saveToFile("SCROLLING"));
   wait(200); console.log("SCROLLING_RENDER_OK"); Qt.quit();
  }
 }
}
'''.replace('LIGHT', 'true' if theme == 'light' else 'false').replace('TILING', str(tiling)).replace('SCROLLING"', str(scrolling) + '"')
                (folder / 'fixture.qml').write_text(fixture)
                code, output = render(folder / 'fixture.qml', render_environment(folder, (900, 1200)), 12)
                self.assertEqual(code, 0, output)
                self.assertIn('SCROLLING_RENDER_OK', output)
                self.assertNotIn('FAIL!', output)
                self.assertNotIn('Error:', output)
                self.assertNotIn('Unable to assign', output)
                for image in [tiling, scrolling]:
                    self.assertTrue(image.is_file(), output)
                    with Image.open(image) as captured:
                        self.assertEqual(captured.size, (760, 1080))
                        self.assertEqual(captured.getpixel((0, 0))[:3], (245, 243, 238) if theme == 'light' else (25, 27, 37))
