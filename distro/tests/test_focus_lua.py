"""Exercise the shipped Lua configuration, bindings and pane geometry offline."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from eitr_focus import FOCUS_KEYS, bindings

ROOT = Path(__file__).resolve().parents[2]
HARNESS = r'''
local mode = arg[2] == "on"
local bindings = assert(io.open(arg[3])):read("*a")
local real_popen = io.popen
io.popen = function(command)
    if command:match("focus%-mode.py.* status$") then
        return {read=function() return mode and "on" or "off" end, close=function() return true end}
    elseif command:match("focus%-mode.py.* bindings$") then
        return {read=function() return bindings end, close=function() return true end}
    end
    error("Unexpected subprocess: " .. command)
end
local keys, events, options = {}, {}, {}
local gestures = 0
local focused = nil
local provider = nil
local function namespace(prefix)
    return setmetatable({}, {
        __index=function(self, key) local result=namespace(prefix .. "." .. key); rawset(self,key,result); return result end,
        __call=function(self, arguments) return {kind=prefix, arguments=arguments} end,
    })
end
hl = setmetatable({
    dsp=namespace("dsp"),
    bind=function(key, action) keys[key:lower()]=action end,
    unbind=function(key) keys[key:lower()]=nil end,
    on=function(name, callback) events[name]=callback end,
    config=function(values) for key,value in pairs(values) do options[key]=value end end,
    gesture=function() gestures=gestures+1 end,
    get_active_window=function() return focused end,
    layout={register=function(name, value) assert(name == "eitr-focus"); provider=value end},
}, {__index=function() return function() end end})
dofile(arg[1])
assert(keys["super + return"], "terminal key must stay available")
if not mode then
    assert(gestures == 1 and provider == nil)
    assert(keys["super + 1"].kind == "dsp.focus")
    assert(options.general.gaps_in == 6)
    print("NORMAL_LUA_OK")
    return
end
assert(gestures == 0)
assert(keys["super + 1"].arguments:match("tab 1$"))
assert(keys["super + tab"].arguments:match("next$"))
assert(keys["super + shift + tab"].arguments:match("previous$"))
assert(keys["super + backslash"].arguments:match("horizontal$"))
assert(keys["super + shift + backslash"].arguments:match("join$"))
assert(keys["super + h"].kind == "dsp.focus")
assert(keys["super + shift + h"].kind == "dsp.layout")
assert(not keys["super + ctrl + h"] and not keys["super + t"] and not keys["super + 0"])
assert(options.general.gaps_in == 0 and options.general.gaps_out == 0)
assert(options.decoration.rounding == 0 and not options.animations.enabled)
assert(not options.group.groupbar.enabled)
-- A reload applies policy again after machine-local options and binds.
options.general.gaps_in = 20
keys["super + 1"] = {kind="local-override"}
events["config.reloaded"]()
assert(options.general.gaps_in == 0 and keys["super + 1"].arguments:match("tab 1$"))
local function context(count, monitor)
    local ctx = {area={x=0,y=28,w=1000,h=800},targets={}}
    for index=1,count do
        local target={window={address="0x"..index,workspace={name="eitr-focus-"..monitor}}}
        target.place=function(self, box) self.box=box end
        table.insert(ctx.targets,target)
    end
    return ctx
end
provider.recalculate(context(0, 0))
for count=1,4 do
    local ctx=context(count,0)
    provider.recalculate(ctx)
    local total=0
    for _,target in ipairs(ctx.targets) do
        local box=target.box
        assert(box.x>=0 and box.y>=28 and box.x+box.w<=1000 and box.y+box.h<=828)
        total=total+box.w*box.h
    end
    assert(math.abs(total-800000)<.01, "panes must cover the work area without holes")
end
local ctx=context(2,1)
provider.layout_msg(ctx,"vertical")
provider.recalculate(ctx)
assert(ctx.targets[1].box.w==1000 and ctx.targets[1].box.h==400)
focused=ctx.targets[2].window
provider.layout_msg(ctx,"shorter")
provider.recalculate(ctx)
assert(ctx.targets[2].box.h<400, "resizing must use the focused side")
local other=context(2,0)
provider.recalculate(other)
assert(other.targets[1].box.w==500 and other.targets[1].box.h==800, "monitor policies stay separate")
for iteration=1,100 do provider.layout_msg(ctx,"taller") end
provider.recalculate(ctx)
assert(ctx.targets[1].box.h>=159 and ctx.targets[2].box.h>=159)
print("FOCUS_LUA_OK")
'''


@unittest.skipUnless(shutil.which('lua'), 'Lua required')
class FocusLuaTests(unittest.TestCase):
    def test_normal_and_focus_binds_and_grid(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            script = folder / 'harness.lua'
            script.write_text(HARNESS)
            generated = folder / 'bindings.lua'
            environment = dict(os.environ, HOME=directory, XDG_CONFIG_HOME=directory,
                               EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'), EITR_CODE_ROOT=str(ROOT))
            from unittest.mock import patch
            with patch.dict(os.environ, environment):
                generated.write_text(bindings())
            self.assertEqual(len({entry['key'].lower() for entry in FOCUS_KEYS}), len(FOCUS_KEYS))
            for mode in ('off', 'on'):
                result = subprocess.run(['lua', str(script), str(ROOT / 'hypr/hyprland.lua'), mode, str(generated)],
                                        env=environment, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('FOCUS_LUA_OK' if mode == 'on' else 'NORMAL_LUA_OK', result.stdout)
