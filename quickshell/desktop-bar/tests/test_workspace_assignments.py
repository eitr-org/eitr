"""Monitor allocation, preference and offline compositor regressions."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from test_desktop_style import style
from layout_render import BAR, copy_runtime, render_environment, render, capture_path
from eitr_workspaces import assignments, preferences, migration
import sys
sys.path.insert(0, str(BAR.parents[1] / "walker/tests"))
from home_isolation import setUpModule, tearDownModule

SPEC = importlib.util.spec_from_file_location('workspace_controller', BAR / 'scripts/workspaces.py')
controller = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controller)


class WorkspaceAssignmentsTests(unittest.TestCase):
    def test_assignment_matrix_and_javascript_parity(self):
        for total in range(1, 5):
            monitors = [dict(id=index, name='screen-' + str(index), x=index * 1920) for index in range(total)]
            for count in range(5, 11):
                for mode in ['shared', 'split']:
                    preference = preferences(dict(workspaceCount=count, workspaceMode=mode))
                    rows = assignments(monitors, monitors[-1]['name'], preference)
                    self.assertEqual(rows[0]['monitor'], monitors[-1]['name'])
                    lengths = [sum(row['monitor'] == monitor['name'] for row in rows) for monitor in monitors]
                    self.assertEqual(sum(lengths), count * total if mode == 'shared' else count)
                    self.assertLessEqual(max(lengths) - min(lengths), 1)
                    self.assertEqual(len({row['id'] for row in rows}), len(rows))
                    source = (BAR / 'WorkspaceModel.js').read_text().replace('.pragma library', '')
                    script = source + '\nconsole.log(JSON.stringify(assignments(' + json.dumps(monitors) + ',' + json.dumps(monitors[-1]['name']) + ',' + json.dumps(mode) + ',' + str(count) + ')));'
                    result = subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)
                    self.assertEqual(json.loads(result.stdout), rows)
                    for remaining in [monitors[:-1], monitors[1:]]:
                        recomputed = assignments(remaining, monitors[-1]['name'], preference)
                        self.assertTrue(all(row['monitor'] in {monitor['name'] for monitor in remaining} for row in recomputed))

    def test_preferences_and_lua_rules(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(style, 'SETTINGS', Path(directory) / 'style.json'), patch.object(style.subprocess, 'run'):
            for count in range(5, 11):
                style.select(str(count), 'workspaceCount')
                style.select(str(count), 'workspaceAlwaysShow')
                for mode in ['shared', 'split']:
                    style.select(mode, 'workspaceMode')
                    self.assertEqual(preferences(json.loads(style.SETTINGS.read_text())), dict(workspaceCount=count, workspaceAlwaysShow=count, workspaceMode=mode))
            style.select('5', 'workspaceCount')
            self.assertEqual(preferences(json.loads(style.SETTINGS.read_text()))['workspaceAlwaysShow'], 5)
            for key, value in [('workspaceCount', '4'), ('workspaceCount', '11'), ('workspaceAlwaysShow', '6'), ('workspaceMode', 'bad')]:
                with self.assertRaises(ValueError):
                    style.select(value, key)
        rows = assignments([dict(id=0, name='A'), dict(id=1, name='B')], 'A', preferences())
        fixture = 'local count=0; hl={workspace_rule=function(row) assert(row.workspace and row.monitor); count=count+1 end};\n' + controller.rules(rows, preferences()).replace('return {', 'local plan = {') + '\nassert(count == 20 and #plan.rows == 20)'
        subprocess.run(['lua', '-'], input=fixture, text=True, check=True)
        self.assertEqual(preferences(dict(workspaceCount=True, workspaceAlwaysShow=[], workspaceMode=[])), preferences({}))

    def test_migration_preserves_monitor_and_clamps_count(self):
        monitors = [dict(id=0, name='A'), dict(id=1, name='B')]
        old = assignments(monitors, 'A', preferences())
        rows = assignments(monitors, 'B', preferences(dict(workspaceMode='split', workspaceCount=5)))
        clients = [dict(address='0x1', monitor=0, workspace=dict(id=10)), dict(address='0x2', monitor=1, workspace=dict(id=18)), dict(address='0x3', monitor=0, workspace=dict(id=-1))]
        moved = migration(clients, monitors, old, rows)
        self.assertEqual([(address, row['monitor'], row['number']) for address, row in moved], [('0x1', 'A', 5), ('0x2', 'B', 3)])

    def test_marker_visibility_per_monitor(self):
        source = (BAR / 'WorkspaceModel.js').read_text().replace('.pragma library', '')
        source += '''
const assert = require('node:assert/strict');
for (const mode of ['shared', 'split']) {
 const rows = assignments([{name:'A'}, {name:'B', x:1920}], 'A', mode, 10);
 const local = rows.filter(row => row.monitor === 'B');
 assert.equal(visibleRows(rows, 'B', 2, [], local[0].id).length, 2);
 assert.equal(visibleRows(rows, 'B', 2, [local[local.length-1].id], local[0].id).length, local.length);
 assert.equal(visibleRows(rows, 'A', 2, [local[local.length-1].id], 1).length, 2);
 assert.equal(visibleRows(rows, 'B', 2, [], local[0].id).length, 2);
}
'''
        subprocess.run(['node', '-e', source], check=True)

    def test_navigation_and_reconcile_are_monitor_aware(self):
        from unittest.mock import Mock
        monitors = [dict(id=0, name='A', focused=True, activeWorkspace=dict(id=1)),
                    dict(id=1, name='B', activeWorkspace=dict(id=11))]
        for mode in ['shared', 'split']:
            preference = preferences(dict(workspaceMode=mode, workspaceCount=6))
            rows = assignments(monitors, 'A', preference)
            hypr = Mock()
            hypr.query.side_effect = lambda kind: {'activewindow': {'monitor': 1}, 'workspaces': [{'id': row['id']} for row in rows]}[kind]
            with patch.object(controller, 'plan', return_value=(monitors, rows, preference)), patch.object(controller, 'focus_enabled', return_value=False):
                controller.navigate(hypr, 'focus', 7)
                hypr.evaluate.assert_not_called()
                controller.navigate(hypr, 'focus', 2)
                self.assertEqual(hypr.evaluate.call_count, 2 if mode == 'shared' else 1)
                self.assertIn('monitor="A"', hypr.evaluate.call_args.args[0])
                hypr.reset_mock()
                controller.navigate(hypr, 'move', 2)
                self.assertIn('workspace=' + ('12' if mode == 'shared' else '2'), hypr.evaluate.call_args.args[0])
                hypr.reset_mock()
                controller.navigate(hypr, 'step', 1)
                self.assertEqual(hypr.evaluate.call_count, 2 if mode == 'shared' else 1)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_CONFIG_HOME': directory, 'XDG_STATE_HOME': directory}):
            hypr = Mock()
            preference = preferences()
            rows = assignments(monitors, 'A', preference)
            hypr.query.side_effect = lambda kind: {'clients': [], 'workspaces': [{'id': 1}, {'id': 11}]}[kind]
            with patch.object(controller, 'plan', return_value=(monitors, rows, preference)), patch.object(controller, 'focus_enabled', return_value=False):
                controller.reconcile(hypr)
                self.assertTrue((Path(directory) / 'eitr/workspaces.lua').is_file())
                hypr.run.assert_called_once_with('reload')
                hypr.reset_mock()
                controller.reconcile(hypr)
                hypr.run.assert_not_called()

    def test_walker_rows_and_settings_anchors(self):
        rows = json.loads((BAR.parents[1] / 'elephant/menu-rows/workspaces.json').read_text())
        self.assertEqual([row['submenu'] for row in rows], ['workspace-always-show', 'workspace-monitors', 'workspace-count', 'workspace-style'])
        catalog = (BAR / 'settings/SettingsCatalog.js').read_text()
        card = (BAR / 'settings/SettingsWorkspacesCard.qml').read_text()
        for identifier in ['workspace-monitors', 'workspace-count', 'workspace-always-show']:
            self.assertIn('windows-' + identifier, catalog)
            self.assertIn('setting-windows-' + identifier, card)
        fixture = r'''
local root = os.getenv("EITR_CODE_ROOT")
local real_dofile = dofile
io.popen = function(command)
    local value = command:find("workspaceMode", 1, true) and "shared" or command:find("workspaceCount", 1, true) and "6" or "5"
    return {read=function() return value end, close=function() end}
end
dofile = function(path)
    if path:match("live%-menu.lua$") then return function(name, loader) return loader end end
    return real_dofile(path)
end
for _, spec in ipairs({{"workspace-monitors",2}, {"workspace-count",6}, {"workspace-always-show",5}}) do
    real_dofile(root .. "/elephant/menus/" .. spec[1] .. ".lua")
    assert(Parent == "workspaces")
    local entries=GetEntries()
    assert(#entries == spec[2], spec[1] .. " count " .. #entries)
    local current=0
    for _,entry in ipairs(entries) do
        assert(entry.Actions.open:find("desktop-style.py",1,true))
        for _,state in ipairs(entry.State or {}) do if state == "current" then current=current+1 end end
    end
    assert(current == 1, spec[1])
end
jsonDecode = function(raw) return {current="Runes", previewCount=2} end
real_dofile(root .. "/elephant/menus/workspace-style.lua")
local samples = GetEntries()
assert(#samples == 4 and Parent == "workspaces")
for _,entry in ipairs(samples) do
    local bounded=false
    for _,value in ipairs(entry.State) do if value == "workspace-preview-2" then bounded=true end end
    assert(bounded)
end
'''
        subprocess.run(['lua', '-'], input=fixture, text=True, check=True,
                       env=dict(os.environ, EITR_CODE_ROOT=str(BAR.parents[1]), EITR_LIBRARY_ROOT=str(BAR.parents[1] / 'distro/lib')))

    def test_focus_exit_is_bounded_and_compact_samples_follow_capacity(self):
        from eitr_focus import spread_plan
        from eitr_workspaces import preview_count
        monitors = [dict(id=index, name=str(index), x=index) for index in range(4)]
        clients = [dict(address=hex(index + 1), monitor=index % 4) for index in range(60)]
        for mode in ['shared', 'split']:
            preference = preferences(dict(workspaceCount=5, workspaceMode=mode))
            rows = assignments(monitors, '0', preference)
            rows = [{**row, 'monitorId': int(row['monitor'])} for row in rows]
            destinations = spread_plan(clients, rows)
            self.assertEqual(len(destinations), len(clients))
            self.assertTrue(all(any(row['id'] == workspace and row['monitorId'] == monitor for row in rows)
                                for address, monitor, workspace in destinations))
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_CONFIG_HOME': directory, 'XDG_STATE_HOME': directory}):
            folder = Path(directory) / 'eitr'
            folder.mkdir()
            (folder / 'style.json').write_text(json.dumps(dict(workspaceMode='split', workspaceCount=5, workspaceAlwaysShow=5)))
            (folder / 'workspaces.json').write_text(json.dumps(dict(rows=rows)))
            self.assertEqual(preview_count(), 2)
            (folder / 'style.json').write_text(json.dumps(dict(workspaceAlwaysShow=2)))
            self.assertEqual(preview_count(), 2)

    def test_lua_workspace_hooks_and_dispatch(self):
        for mode, plan in [('shared', '{id=1, number=1, monitor="A"}, {id=3, number=3, monitor="A"}, {id=11, number=1, monitor="B"}, {id=13, number=3, monitor="B"}'),
                           ('split', '{id=1, number=1, monitor="A"}, {id=3, number=3, monitor="A"}, {id=6, number=6, monitor="B"}, {id=7, number=7, monitor="B"}')]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                (Path(directory) / 'eitr').mkdir()
                (Path(directory) / 'eitr/workspaces.lua').write_text(
                    'return {mode="' + mode + '", count=7, rows={' + plan + '}}\n')
                fixture = r'''
local root, config, mode = os.getenv("EITR_CODE_ROOT"), os.getenv("TEST_CONFIG"), os.getenv("TEST_MODE")
local events, commands, dispatched = {}, {}, {}
local active_monitor = {name = "A", active_workspace = {id = 1}}
hl = {on = function(name, callback) events[name] = callback end,
      exec_cmd = function(command) table.insert(commands, command) end,
      dispatch = function(value) table.insert(dispatched, value) end,
      get_active_monitor = function() return active_monitor end,
      get_active_window = function() return {monitor = {name = "B"}} end,
      get_workspaces = function() return {{id = 1}, {id = 3}} end,
      dsp = {focus = function(spec) return "focus " .. tostring(spec.monitor or spec.workspace) end,
             window = {move = function(spec) return "move " .. tostring(spec.workspace) end}}}
local action = dofile(root .. "/hypr/workspaces.lua")({config = config, code = function(relative) return root .. "/" .. relative end},
    function(value) return string.format("%q", value) end)
for _, name in ipairs({"monitor.added", "monitor.removed", "config.reloaded"}) do assert(events[name]); events[name]() end
assert(#commands == 4)
assert(type(action("focus", 3)) == "function")
action("focus", 3)()
if mode == "shared" then
    assert(table.concat(dispatched, ",") == "focus B,focus 13,focus A,focus 3", table.concat(dispatched, ","))
else
    assert(table.concat(dispatched, ",") == "focus A,focus 3", table.concat(dispatched, ","))
end
dispatched = {}
action("move", 1)()
assert(dispatched[1] == (mode == "shared" and "move 11" or "move 1"), tostring(dispatched[1]))
dispatched = {}
action("focus", 8)()
assert(#dispatched == 0)
action("step", 1)()
assert(dispatched[1] == "focus 3", tostring(dispatched[1]))
local focus = io.open(config .. "/eitr/focus.json", "w"); focus:write('{"enabled": true}'); focus:close()
dispatched = {}
action("focus", 1)()
assert(#dispatched == 0)
'''
                subprocess.run(['lua', '-'], input=fixture, text=True, check=True,
                               env=dict(os.environ, EITR_CODE_ROOT=str(BAR.parents[1]), TEST_CONFIG=directory, TEST_MODE=mode))

    def test_offscreen_workspaces_and_settings(self):
        for mode in ['shared', 'split']:
            for light in [False, True]:
                theme = 'light' if light else 'dark'
                with tempfile.TemporaryDirectory() as directory:
                    folder = Path(directory)
                    copy_runtime(folder)
                    target = capture_path('WORKSPACE', directory, mode + '-' + theme + '.png')
                    fixture = '''import QtQuick
import QtTest
import Quickshell
import "." as Bar
import "WorkspaceModel.js" as Model
ShellRoot {
 FloatingWindow { id: window; visible: true; implicitWidth: 760; implicitHeight: 600
  color: Bar.SettingsPalette.background
  Rectangle { id: canvas; anchors.fill: parent; color: Bar.SettingsPalette.background
   Column { x:24; y:24; width:712; spacing:20
    Repeater { model: ['DP-3', 'HDMI-A-1']
     Column { required property string modelData; spacing:8
      Text { text:modelData; color:Bar.SettingsPalette.foreground; font.pixelSize:16 }
      Row { spacing:4
       Repeater { model: Model.visibleRows(Model.assignments([{name:'DP-3'}, {name:'HDMI-A-1',x:2560}], 'DP-3', 'MODE', 10), modelData, 5, [], 1)
        Bar.WorkspaceMarker { required property var modelData; style:'Numbers'; label:String(modelData.number); active:modelData.position===1; width:24; foreground:Bar.SettingsPalette.foreground; accent:Bar.SettingsPalette.accent; selectedForeground:Bar.SettingsPalette.background }
       }
      }
     }
    }
    Bar.SettingsWorkspacesCard { foreground:Bar.SettingsPalette.foreground; live:false }
   }
  }
 }
 TestCase { name:'WorkspaceRender'; when:window.visible
  function test_capture() {
   Bar.SiteStyle.light = LIGHT;
   Bar.SettingsPalette.themeBackground = LIGHT ? '#f5f3ee' : '#191b25';
   Bar.SettingsPalette.themeForeground = LIGHT ? '#202431' : '#e4e5ef';
   Bar.DesktopStyle.applyLayout({workspaceMode:'MODE'});
   wait(300); canvas.grabToImage(result => result.saveToFile('TARGET')); wait(200); console.log('WORKSPACE_RENDER_OK'); Qt.quit();
  }
 }
}
'''.replace('MODE', mode).replace('LIGHT', str(light).lower()).replace('TARGET', str(target))
                    (folder / 'fixture.qml').write_text(fixture)
                    code, log = render(folder / 'fixture.qml', render_environment(folder), 15)
                    self.assertEqual(code, 0, log)
                    self.assertNotIn('FAIL!', log)
                    self.assertNotIn('Error:', log)
                    self.assertTrue(target.is_file(), log)
