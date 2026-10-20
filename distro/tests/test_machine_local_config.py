from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HYPRLAND = ROOT / "hypr/hyprland.lua"
LOCAL_EXAMPLE = ROOT / "hypr/local.lua.example"

CONNECTOR = re.compile(r"\b(?:e?DP|HDMI-[A-C]|DVI-[DIA]|VGA|Virtual|Unknown)-\d")
OWNER_DEVICES = ("epic-mouse-v1",)

# Runs hyprland.lua against a recording hl mock and prints the applied calls.
HARNESS = r"""
local calls = {}
local function record(name, arg)
	local summary = name
	if type(arg) == "table" then
		summary = summary .. " " .. tostring(arg.output or arg.name or arg.workspace or "")
	end
	calls[#calls + 1] = summary
end
local dsp = setmetatable({}, {
	__index = function(self, key)
		local child = setmetatable({}, getmetatable(self))
		rawset(self, key, child)
		return child
	end,
	__call = function() return {} end,
})
hl = setmetatable({ dsp = dsp }, {
	__index = function(_, key)
		return function(arg) record(key, arg) end
	end,
})
dofile(arg[1])
dofile(arg[2])
for _, call in ipairs(calls) do print(call) end
"""


def run_hyprland(home):
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as harness:
        harness.write(HARNESS)
    try:
        # A deliberately broken local.lua must not notify the developer's live session.
        env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(Path(home) / ".config"),
                   XDG_RUNTIME_DIR=str(home), DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent")
        return subprocess.run(["lua", harness.name, str(HYPRLAND), str(ROOT / 'hypr/local-loader.lua')], env=env,
                              capture_output=True, text=True, timeout=30)
    finally:
        os.unlink(harness.name)


class MachineLocalConfigTests(unittest.TestCase):
    def test_hyprland_update_notice_is_disabled(self):
        self.assertIn("no_update_news = true", HYPRLAND.read_text())

    def test_launcher_backends_start_with_the_desktop(self):
        text = HYPRLAND.read_text()
        startup = text.split('hl.on("hyprland.start", function()', 1)[1].split('end)', 1)[0]
        self.assertIn('hl.exec_cmd("systemctl --user start elephant.service")', startup)
        self.assertIn('hl.exec_cmd("eitr-session && eitr-walker --gapplication-service")', startup)

    def test_shared_hyprland_config_has_no_machine_specific_outputs_or_devices(self):
        text = HYPRLAND.read_text()
        self.assertIsNone(CONNECTOR.search(text), CONNECTOR.findall(text))
        for device in OWNER_DEVICES:
            self.assertNotIn(device, text)
        self.assertNotIn("portable.mode", text)
        self.assertIn('hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })',
                      text)

    def test_owner_layout_lives_in_the_example(self):
        text = LOCAL_EXAMPLE.read_text()
        for name in ("DP-3", "HDMI-A-1", "eDP-1", "epic-mouse-v1"):
            self.assertIn(name, text)
        self.assertIn("~/.config/hypr/local.lua", text)

    def test_local_config_loading_is_error_guarded(self):
        text = (ROOT / 'hypr/local-loader.lua').read_text()
        self.assertIn('load_local_config(paths.config .. "/hypr/local.lua")', text)
        self.assertRegex(text, r"loadfile\(path, \"t\", environment\)")
        self.assertRegex(text, r"pcall\(chunk\)")
        self.assertRegex(text, r"pcall\(hl\[call\.name\]")

    def test_machine_local_files_are_ignored(self):
        ignored = (ROOT / ".gitignore").read_text().splitlines()
        for path in ("/hypr/local.lua", "/hypr/preferred-outputs", "/hypr/primary-display"):
            self.assertIn(path, ignored)

    def test_no_portable_mode_marker_remains(self):
        for path in ("distro/install.sh", "AGENTS.md", ".gitignore",
                     "quickshell/desktop-bar/scripts/display-primary.py",
                     "quickshell/desktop-bar/shell.qml"):
            self.assertNotIn("portable.mode", (ROOT / path).read_text(), path)

    @unittest.skipUnless(shutil.which("luac"), "luac is not installed")
    def test_example_and_config_parse(self):
        for path in (HYPRLAND, LOCAL_EXAMPLE):
            result = subprocess.run(["luac", "-p", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("lua"), "lua is not installed")
    def test_generic_layout_without_local_config(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hyprland(home)
        self.assertEqual(result.returncode, 0, result.stderr)
        monitors = [line for line in result.stdout.splitlines() if line.startswith("monitor")]
        self.assertEqual(monitors, ["monitor "])
        self.assertNotIn("eitr:", result.stderr)

    @unittest.skipUnless(shutil.which("lua"), "lua is not installed")
    def test_valid_local_config_applies_after_shared_config(self):
        with tempfile.TemporaryDirectory() as home:
            config = Path(home) / ".config/hypr"
            config.mkdir(parents=True)
            (config / "local.lua").write_text(
                'hl.monitor({ output = "DP-1", mode = "preferred" })\n'
                'hl.device({ name = "test-mouse", sensitivity = 0 })\n'
                'hl.bind("SUPER + F12", hl.dsp.exec_cmd("true"))\n'
            )
            result = run_hyprland(home)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[-3:], ["monitor DP-1", "device test-mouse", "bind"])
        self.assertLess(lines.index("monitor "), lines.index("monitor DP-1"))

    @unittest.skipUnless(shutil.which("lua"), "lua is not installed")
    def test_failing_local_config_keeps_generic_layout_and_reports(self):
        cases = {
            "runtime": 'hl.monitor({ output = "DP-1" })\nerror("broken override")\n',
            "syntax": 'hl.monitor({ output = "DP-1" \n',
        }
        for kind, source in cases.items():
            with self.subTest(kind), tempfile.TemporaryDirectory() as home:
                config = Path(home) / ".config/hypr"
                config.mkdir(parents=True)
                (config / "local.lua").write_text(source)
                result = run_hyprland(home)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("monitor DP-1", result.stdout.splitlines())
                self.assertIn("monitor ", result.stdout.splitlines())
                self.assertIn("eitr: local.lua was not applied", result.stderr)

    @unittest.skipUnless(shutil.which("lua"), "lua is not installed")
    def test_owner_example_runs_as_local_config(self):
        with tempfile.TemporaryDirectory() as home:
            config = Path(home) / ".config/hypr"
            config.mkdir(parents=True)
            shutil.copy(LOCAL_EXAMPLE, config / "local.lua")
            result = run_hyprland(home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("eitr:", result.stderr)
        lines = result.stdout.splitlines()
        self.assertIn("device epic-mouse-v1", lines)
        self.assertTrue(any(line.startswith("workspace_rule ") for line in lines))


if __name__ == "__main__":
    unittest.main()
