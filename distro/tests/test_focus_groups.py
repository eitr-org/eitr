"""Run conversion Lua against native-group stand-ins, without a live session."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from eitr_focus import Hypr, change, gather, lua, lua_value, tab_action

FIXTURE = r'''
local state = assert(load("return " .. arg[1]))()
local windows = state.clients
local function find(address)
    for _,window in ipairs(windows) do if window.address == address then return window end end
end
local function members(group)
    local result={}
    for _,window in ipairs(windows) do if window.group == group then table.insert(result,window) end end
    return result
end
local function remove(group, window)
    if window.group == group then window.group=nil end
    if group.current == window.address then local remaining=members(group); group.current=remaining[1] and remaining[1].address end
end
local function add(group, window)
    if window.group then remove(window.group,window) end
    local anchor=members(group)[1]
    window.group=group
    if anchor then window.monitor=anchor.monitor; window.workspace={name=anchor.workspace.name} end
end
local groups={}
for _,window in ipairs(windows) do
    if #window.grouped>0 then
        local key=table.concat(window.grouped, ",")
        local group=groups[key] or {current=window.grouped[1],remove=remove,add=add}
        groups[key]=group
        window.group=group
    end
end
local function action(kind) return function(values) return {kind=kind,values=values} end end
hl={
    get_window=function(selector) return find(selector:gsub("^address:","")) end,
    config=function() end,
    dsp={
        window={fullscreen_state=action("fullscreen"),float=action("float"),pin=action("pin"),move=action("move")},
        group={toggle=action("group")},
        workspace={move=action("workspace_move"),toggle_special=action("special")},
        focus=action("focus"),layout=action("layout"),
    },
}
hl.dispatch=function(action)
    local values=action.values
    local window=type(values)=="table" and values.window
    if action.kind=="group" then
        if not window.group then window.group={current=window.address,remove=remove,add=add} end
    elseif action.kind=="move" then
        window.workspace={name=tostring(values.workspace):gsub("^name:","")}
    elseif action.kind=="workspace_move" then
        for _,candidate in ipairs(windows) do
            if candidate.workspace.name==tostring(values.workspace):gsub("^name:","") then candidate.monitor=values.monitor end
        end
    elseif action.kind=="focus" then
        if values.window then
            state.active=window.address
            if window.group then window.group.current=window.address end
        elseif values.monitor then
            for _,monitor in ipairs(state.monitors) do if monitor.name==values.monitor then state.monitor=monitor.id end end
        elseif values.workspace then
            for _,monitor in ipairs(state.monitors) do
                if monitor.id==state.monitor then monitor.activeWorkspace={name=tostring(values.workspace):gsub("^name:","")} end
            end
        end
    end
end
assert(load(arg[2]))()
local function quote(value) return string.format("%q",value) end
local rows={}
for _,window in ipairs(windows) do
    local grouped={}
    if window.group then for _,member in ipairs(members(window.group)) do table.insert(grouped,quote(member.address)) end end
    table.insert(rows,'{"address":'..quote(window.address)..',"monitor":'..window.monitor..
        ',"mapped":true,"workspace":{"name":'..quote(window.workspace.name)..'},"grouped":['..table.concat(grouped,",")..
        '],"hidden":'..tostring(window.group~=nil and window.group.current~=window.address)..'}')
end
local monitors={}
for _,monitor in ipairs(state.monitors) do
    table.insert(monitors,'{"id":'..monitor.id..',"name":'..quote(monitor.name)..',"activeWorkspace":{"name":'..quote(monitor.activeWorkspace.name)..'}}')
end
print('{"clients":['..table.concat(rows,",")..'],"active":'..quote(state.active)..',"monitor":'..state.monitor..
    ',"monitors":['..table.concat(monitors,",")..']}')
'''


def literal(value):
    if isinstance(value, list):
        return '{' + ','.join(literal(item) for item in value) + '}'
    if isinstance(value, dict):
        return '{' + ','.join('[' + lua(key) + ']=' + literal(item) for key, item in value.items()) + '}'
    return lua_value(value)


class NativeFakeHypr(Hypr):
    def __init__(self, folder):
        self.fixture = folder / 'groups.lua'
        self.fixture.write_text(FIXTURE)
        self.state = {'clients': [dict(address=hex(number), monitor=number % 2, mapped=True,
                                      workspace={'name': str(number)}, grouped=[], hidden=False)
                                  for number in range(1, 9)],
                      'active': '0x1', 'monitor': 1,
                      'monitors': [{'id': index, 'name': 'Test-' + str(index), 'activeWorkspace': {'name': str(index+1)}}
                                   for index in (0, 1)]}

    def ensure_bar(self):
        self.bar_recovered = True

    def option(self, name):
        return {'css': '6 6 6 6', 'int': 1, 'bool': True, 'str': 'dwindle'}

    def run(self, *arguments):
        if arguments[0] == 'reload':
            return 'ok'
        if arguments[:1] == ('-j',):
            kind = arguments[1]
            if kind == 'clients':
                return json.dumps(self.state['clients'])
            if kind == 'monitors':
                return json.dumps(self.state['monitors'])
            if kind == 'activewindow':
                return json.dumps(next((client for client in self.state['clients'] if client['address'] == self.state['active']), {}))
        raise AssertionError(arguments)

    def evaluate(self, expression):
        result = subprocess.run(['lua', str(self.fixture), literal(self.state), expression],
                                capture_output=True, text=True, check=True, timeout=5)
        self.state = json.loads(result.stdout)
        return 'ok'


@unittest.skipUnless(shutil.which('lua'), 'Lua required')
class FocusGroupTests(unittest.TestCase):
    def test_gather_split_close_reconcile_and_spread(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,
                XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, HYPRLAND_INSTANCE_SIGNATURE='fake'):
            hypr = NativeFakeHypr(Path(directory))
            change('on', hypr)
            self.assertTrue(all(len(client['grouped']) == 4 for client in hypr.state['clients']))
            self.assertTrue(all(client['workspace']['name'] == 'eitr-focus-' + str(client['monitor'])
                                for client in hypr.state['clients']))
            tab_action('horizontal', '', hypr)
            monitor = hypr.query('activewindow')['monitor']
            self.assertEqual(sum(not client['hidden'] for client in hypr.state['clients'] if client['monitor'] == monitor), 2)
            change('on', hypr)
            self.assertEqual(sum(not client['hidden'] for client in hypr.state['clients'] if client['monitor'] == monitor), 2)
            for direction in ('horizontal', 'vertical'):
                hypr.window('0x1', 'hl.dispatch(hl.dsp.focus({window=window}))')
                tab_action(direction, '', hypr)
            self.assertEqual(sum(not client['hidden'] for client in hypr.state['clients'] if client['monitor'] == monitor), 4)
            tab_action('join', '', hypr)
            self.assertEqual(sum(not client['hidden'] for client in hypr.state['clients'] if client['monitor'] == monitor), 1)
            # A new client mapped directly onto the Focus workspace joins its existing group.
            hypr.state['clients'].append(dict(address='0x9', monitor=monitor, mapped=True,
                                             workspace={'name': 'eitr-focus-' + str(monitor)}, grouped=[], hidden=False))
            gather(hypr)
            self.assertEqual(len(hypr.state['clients'][-1]['grouped']), 5)
            # A client can close between the compositor snapshot and the guarded Lua mutation.
            original_window = hypr.window
            closing = hypr.state['clients'][0]['address']
            def close_then_mutate(address, expression):
                hypr.state['clients'] = [client for client in hypr.state['clients'] if client['address'] != closing]
                return original_window(address, expression)
            with patch.object(hypr, 'window', side_effect=close_then_mutate):
                change('off', hypr)
            self.assertTrue(hypr.bar_recovered)
            self.assertTrue(all(not client['grouped'] for client in hypr.state['clients']))
            counts = {}
            for client in hypr.state['clients']:
                name = client['workspace']['name']
                self.assertTrue(name.isdigit())
                counts[name] = counts.get(name, 0) + 1
            self.assertLessEqual(max(counts.values()), 2)
            change('off', hypr)
            self.assertTrue(hypr.bar_recovered)
            self.assertTrue(all(not client['grouped'] for client in hypr.state['clients']))
