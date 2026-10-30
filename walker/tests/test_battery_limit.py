import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
import os
import shutil
import subprocess
from eitr_battery import system_batteries
from test_menu_translations import lua_value
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("battery_limit", ROOT / "walker/scripts/actions/system/battery-limit.py")
walker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(walker)


class BatteryMenuConfirmationTests(unittest.TestCase):
    def test_only_system_batteries_enable_laptop_choices(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(system_batteries(root), [])
            peripheral = root / "mouse"
            peripheral.mkdir()
            (peripheral / "type").write_text("Battery")
            (peripheral / "scope").write_text("Device")
            self.assertEqual(system_batteries(root), [])
            laptop = root / "BAT0"
            laptop.mkdir()
            (laptop / "type").write_text("Battery")
            self.assertEqual(system_batteries(root), [laptop])
            (laptop / "scope").write_text("System")
            self.assertEqual(system_batteries(root), [laptop])
            (laptop / "present").write_text("0")
            self.assertEqual(system_batteries(root), [])

    @unittest.skipUnless(shutil.which("lua"), "Lua is required")
    def test_walker_hides_battery_folder_and_checks_the_saved_limit(self):
        decoded = {path.read_text(): json.loads(path.read_text())
                   for path in (ROOT / "elephant/menu-rows").glob("*.json")}
        for available in (False, True):
            with self.subTest(available=available):
                script = "local decoded = " + lua_value(decoded) + "\n" + "local available = " + lua_value(available) + "\n" + r'''
jsonDecode = function(raw)
    if raw == "battery" then return {available=available, current="80"} end
    return decoded[raw] or {}
end
io.popen = function() return {read=function() return "battery" end, close=function() end} end
local root = os.getenv("EITR_CODE_ROOT")
dofile(root .. "/elephant/menus/system-devices.lua")
local found = false
for _, entry in ipairs(GetEntries("")) do
    if entry.SubMenu == "battery-limit" then found = true end
end
assert(found == available)
dofile(root .. "/elephant/menus/battery-limit.lua")
local entries = GetEntries("")
if not available then assert(#entries == 0) end
local checked = 0
for _, entry in ipairs(entries) do
    if entry.State and entry.State[1] == "current" then
        assert(entry.Text == "Charge Limit 80%")
        assert(entry.Icon == "\239\128\140")
        checked = checked + 1
    end
end
assert(checked == (available and 1 or 0))
'''
                environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"), LC_ALL="C.UTF-8")
                result = subprocess.run(["lua", "-"], input=script, text=True, capture_output=True, env=environment)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_limit_requires_typed_yes(self):
        with tempfile.NamedTemporaryFile() as helper:
            for answer, expected in (("", 0), ("y", 0), ("yes", 1)):
                with self.subTest(answer=answer), patch.object(walker, "ROOT_HELPERS", (helper.name,)), \
                        patch("builtins.input", return_value=answer), patch("builtins.print"), \
                        patch.object(walker.subprocess, "run") as run:
                    walker.main(["set", "80"])
                    self.assertEqual(run.call_count, expected)
                    if expected:
                        run.assert_called_once_with(["sudo", helper.name, "battery-limit", "80"], check=True)

    def test_invalid_value_never_prompts(self):
        with tempfile.NamedTemporaryFile() as helper, patch.object(walker, "ROOT_HELPERS", (helper.name,)), \
                patch("builtins.input") as prompt:
            for args in (["set", "40"], ["set"], ["drain"]):
                with self.assertRaises(ValueError):
                    walker.main(args)
            prompt.assert_not_called()


if __name__ == "__main__":
    unittest.main()
