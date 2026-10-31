"""Exercise application isolation entirely with fake executables."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / 'walker/bin/app-launch'


class AppLaunchTests(unittest.TestCase):
    def launch(self, arguments, *, available=True, active=True, status=0):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / 'bash').symlink_to('/usr/bin/bash')
            script = '''#!/usr/bin/python3
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
if os.environ['MENU_PATH'] in os.environ['PATH'].split(':'):
    sys.exit(99)
with open(os.environ['CALLS'], 'a') as output:
    output.write(json.dumps([name, *sys.argv[1:]]) + '\\n')
sys.exit(int(os.environ['ACTIVE_STATUS'] if name == 'systemctl' else os.environ['APP_STATUS']))
'''
            for name in ['systemctl', 'gtk-launch', 'application', *(['uwsm'] if available else [])]:
                target = directory / name
                target.write_text(script)
                target.chmod(0o755)
            calls = directory / 'calls'
            environment = dict(os.environ, PATH=str(ROOT / "walker/bin/menu-path") + ":" + str(directory),
                               MENU_PATH=str(ROOT / "walker/bin/menu-path"), CALLS=str(calls),
                               ACTIVE_STATUS='0' if active else '3', APP_STATUS=str(status))
            result = subprocess.run([str(LAUNCHER), *arguments], env=environment,
                                    capture_output=True, text=True)
            return result, [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []

    def test_scope_and_slice_are_explicit_and_arguments_survive(self):
        result, calls = self.launch(['application', 'two words', "quote'", '; touch ignored', '--flag'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls, [
            ['systemctl', '--user', '--quiet', 'is-active', 'wayland-wm@*.service'],
            ['uwsm', 'app', '-s', 'a', '-t', 'scope', '--', 'application',
             'two words', "quote'", '; touch ignored', '--flag']])

    def test_desktop_id_reaches_uwsm_unchanged(self):
        result, calls = self.launch(['--desktop', 'org.example.App.desktop'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls[-1][-1], 'org.example.App.desktop')
        self.assertEqual(calls[-1][0], 'uwsm')

    def test_missing_uwsm_skips_systemctl_and_runs_original(self):
        result, calls = self.launch(['application', 'two words'], available=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls, [['application', 'two words']])

    def test_non_uwsm_session_uses_original_desktop_launcher(self):
        result, calls = self.launch(['--desktop', 'example.desktop'], active=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(calls[-1], ['gtk-launch', 'example.desktop'])

    def test_scope_failure_is_returned_without_duplicate_launch(self):
        result, calls = self.launch(['application'], status=42)
        self.assertEqual(result.returncode, 42)
        self.assertEqual([call[0] for call in calls], ['systemctl', 'uwsm'])

    def test_no_arguments_fail_without_starting_anything(self):
        result, calls = self.launch([])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(calls, [])

    def test_apps_lua_uses_desktop_id_and_keeps_uninstall_as_helper(self):
        harness = r'''local original_dofile = dofile
function dofile(path)
    if path:match("/elephant/i18n.lua$") then
        return {tr = function(value) return value end, entries = function(entries) return entries end,
            language = function() return "English" end}
    end
    return original_dofile(path)
end
local original_open = io.open
io.open = function(path, mode)
    if path == "/mock/org.example.App.desktop" then
        return {lines = function()
            local rows = {"[Desktop Entry]", "Type=Application", "Name=Example", "Exec=example"}
            local index = 0
            return function() index = index + 1; return rows[index] end
        end, close = function() end}
    end
    return original_open(path, mode)
end
io.popen = function(command)
    return {lines = function()
        local emitted = false
        return function()
            if emitted then return nil end
            emitted = true
            return "/mock/org.example.App.desktop"
        end
    end, close = function() end}
end
dofile(os.getenv("EITR_CODE_ROOT") .. "/elephant/menus/apps.lua")
local entries = GetEntries()
assert(#entries == 1)
print(entries[1].Actions.open)
print(entries[1].Actions.app_uninstall)
'''
        result = subprocess.run(['lua', '-'], input=harness, text=True, capture_output=True,
                                env=dict(os.environ, EITR_CODE_ROOT=str(ROOT),
                                         EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib')), check=True)
        commands = result.stdout.splitlines()
        self.assertIn("walker/bin/app-launch' --desktop 'org.example.App.desktop'", commands[0])
        self.assertIn('software.py', commands[1])
        self.assertNotIn('app-launch', commands[1])

    def test_helpers_stay_direct_and_bar_apps_share_terminal_shim(self):
        hypr = (ROOT / 'hypr/hyprland.lua').read_text()
        self.assertIn('hl.dsp.exec_cmd("playerctl play-pause")', hypr)
        startup = (ROOT / 'hypr/scripts/session-start.sh').read_text()
        self.assertIn('systemctl --user start --no-block elephant.service', startup)
        self.assertNotIn('app-launch', startup)
        scoped = (ROOT / 'elephant/scoped-menu.lua').read_text()
        self.assertIn('Actions = row.actions', scoped)
        self.assertNotIn('app-launch', scoped)
        for name in ['panels/SystemMonitorMenu.qml', 'shell.qml']:
            source = (ROOT / 'quickshell/desktop-bar' / name).read_text()
            if name == 'shell.qml':
                source += (ROOT / 'quickshell/desktop-bar/services/UpdatesStatus.qml').read_text()
            self.assertIn('/walker/bin/menu-path/kitty' if name == 'shell.qml' else 'walker/bin/menu-path/kitty', source)
        self.assertIn('["notify-send",', (ROOT / 'quickshell/desktop-bar/services/SessionHooks.qml').read_text())


if __name__ == '__main__':
    unittest.main()
