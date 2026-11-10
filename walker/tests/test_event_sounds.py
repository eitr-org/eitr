"""Walker's Event Sounds menus and the helper that saves eitr/sounds.json for the bar."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from home_isolation import setUpModule, tearDownModule  # noqa: F401
from test_menu_translations import lua_value

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("event_sounds", ROOT / "walker/scripts/actions/system/event-sounds.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class EventSoundsHelperTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.settings = Path(self.directory.name) / "eitr/sounds.json"
        patcher = patch.object(helper, "SETTINGS", self.settings)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.directory.cleanup)

    def run_helper(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()):
            status = helper.main(list(arguments))
        return status, output.getvalue()

    def test_sounds_are_off_until_turned_on(self):
        self.assertEqual(self.run_helper("get", "notifications"), (0, "off\n"))
        self.assertEqual(self.run_helper("get", "charger"), (0, "off\n"))
        self.assertFalse(self.settings.exists())

    def test_set_writes_the_bar_format_and_keeps_other_fields(self):
        # EventSounds.qml reads booleans and keeps fields it does not know.
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(json.dumps({"version": 1, "notifications": True, "future": "kept"}))
        self.assertEqual(self.run_helper("set", "charger", "on")[0], 0)
        self.assertEqual(json.loads(self.settings.read_text()),
                         {"version": 1, "notifications": True, "charger": True, "future": "kept"})
        self.assertEqual(self.run_helper("get", "charger"), (0, "on\n"))
        self.run_helper("set", "notifications", "off")
        self.assertIs(json.loads(self.settings.read_text())["notifications"], False)
        self.assertEqual(self.run_helper("get", "notifications"), (0, "off\n"))

    def test_only_true_counts_as_on(self):
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(json.dumps({"version": 1, "notifications": "yes"}))
        self.assertEqual(self.run_helper("get", "notifications"), (0, "off\n"))

    def test_unknown_keys_and_values_change_nothing(self):
        for arguments in (("set", "volume", "on"), ("set", "charger", "maybe"), ("get",), ("toggle", "charger")):
            with self.subTest(arguments=arguments):
                self.assertEqual(self.run_helper(*arguments)[0], 2)
        self.assertFalse(self.settings.exists())

    def test_bar_watches_the_file_it_shares_with_walker(self):
        service = (ROOT / "quickshell/desktop-bar/services/EventSounds.qml").read_text()
        self.assertIn('Eitr.Paths.config("eitr/sounds.json")', service)
        self.assertIn("watchChanges: true", service)
        self.assertIn("sounds.data.notifications === true", service)
        self.assertIn("sounds.data.charger === true", service)


@unittest.skipUnless(shutil.which("lua"), "Lua is required")
class EventSoundsMenuTests(unittest.TestCase):
    def run_lua(self, available, saved):
        decoded = {path.read_text(): json.loads(path.read_text())
                   for path in (ROOT / "elephant/menu-rows").glob("*.json")}
        script = ("local decoded = " + lua_value(decoded) + "\nlocal available = " + lua_value(available)
                  + "\nlocal saved = " + lua_value(saved) + "\n" + r'''
local root = os.getenv("EITR_CODE_ROOT")
local battery_reads = 0
jsonDecode = function(raw)
    if raw == "battery" then return {available=available} end
    return decoded[raw] or {}
end
io.popen = function(command)
    if command:find("battery-limit.py", 1, true) then
        battery_reads = battery_reads + 1
        return {read=function() return "battery" end, close=function() end}
    end
    assert(command:find("event-sounds.py", 1, true), command)
    local key = command:match(" get (%a+)$")
    return {read=function() return saved[key] end, close=function() end}
end
dofile(root .. "/elephant/menus/system-devices.lua")
local folder = false
for _, entry in ipairs(GetEntries("")) do
    if entry.SubMenu == "event-sounds" then folder = true end
end
assert(folder, "Devices lists Event Sounds")
dofile(root .. "/elephant/menus/event-sounds.lua")
assert(Parent == "system-devices")
local listed = {}
for _, entry in ipairs(GetEntries("")) do table.insert(listed, entry.SubMenu) end
assert(table.concat(listed, ",") == (available and "sound-charger,sound-notifications" or "sound-notifications"),
    table.concat(listed, ","))
for _, spec in ipairs({{"sound-notifications", "notifications"}, {"sound-charger", "charger"}}) do
    dofile(root .. "/elephant/menus/" .. spec[1] .. ".lua")
    assert(Parent == "event-sounds")
    local checked = 0
    for _, entry in ipairs(GetEntries("")) do
        assert(entry.Actions.open:find("event-sounds.py' set " .. spec[2] .. " " .. entry.Value, 1, true), entry.Actions.open)
        if entry.State[1] == "current" then
            assert(entry.Value == saved[spec[2]])
            assert(entry.Icon == "\239\128\140")
            checked = checked + 1
        end
    end
    assert(checked == 1)
end
print(battery_reads)
''')
        environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"), LC_ALL="C.UTF-8")
        result = subprocess.run(["lua", "-"], input=script, text=True, capture_output=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        return int(result.stdout.strip())

    def test_charger_sounds_only_with_a_battery_and_current_choice_checked(self):
        for available in (False, True):
            with self.subTest(available=available):
                self.assertGreater(self.run_lua(available, {"notifications": "on", "charger": "off"}), 0)

    def test_menus_without_battery_rows_read_no_battery_state(self):
        decoded = {path.read_text(): json.loads(path.read_text()) for path in (ROOT / "elephant/menu-rows").glob("*.json")}
        script = "local decoded = " + lua_value(decoded) + "\n" + r'''
jsonDecode = function(raw) return decoded[raw] or {} end
io.popen = function(command) error("unexpected helper: " .. command) end
dofile(os.getenv("EITR_CODE_ROOT") .. "/elephant/menus/appearance.lua")
assert(#GetEntries("") > 0)
'''
        environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"), LC_ALL="C.UTF-8")
        result = subprocess.run(["lua", "-"], input=script, text=True, capture_output=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
