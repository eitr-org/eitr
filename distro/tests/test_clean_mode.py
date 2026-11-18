"""Tests for Cleaning mode CLI, controller state machine, and Hyprland Lua submap."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "distro/lib"))
import eitr_clean  # noqa: E402

LOADER = importlib.machinery.SourceFileLoader("eitr_clean_cli_test", str(ROOT / "distro/bin/eitr"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
EITR_CLI = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(EITR_CLI)


class CleanModeControllerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.runtime = Path(self.temporary.name) / "runtime"
        self.state_home = Path(self.temporary.name) / "state"
        self.env = patch.dict(
            os.environ,
            {
                "XDG_RUNTIME_DIR": str(self.runtime),
                "XDG_STATE_HOME": str(self.state_home),
                "EITR_CODE_ROOT": str(ROOT),
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def _spawn_real_sleeper(self, command):
        token = command[command.index("--token") + 1]
        return subprocess.Popen(
            [sys.executable, str(ROOT / "distro/lib/eitr_clean.py"), "_hold", "--token", token, "--max-seconds", "30"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    def test_cli_parses_and_plans_clean_actions(self):
        for action in ("start", "stop", "status"):
            parsed = EITR_CLI.parser().parse_args(["clean", action])
            planned = EITR_CLI.plan(parsed, code=ROOT)
            self.assertEqual(planned, ["python3", str(ROOT / "distro/lib/eitr_clean.py"), action])
        self.assertEqual(EITR_CLI.parser().parse_args(["clean"]).action, "status")
        self.assertIn("clean", EITR_CLI.overview())

    def test_start_is_idempotent_and_status_tracks_state(self):
        commands = []
        spawned = []
        submap = {"name": ""}

        def fake_run(command):
            commands.append(command)
            if command == ["hyprctl", "dispatch", 'hl.dsp.submap("clean")']:
                submap["name"] = "clean"
            elif command == ["hyprctl", "dispatch", 'hl.dsp.submap("reset")']:
                submap["name"] = ""
            elif command == ["hyprctl", "submap"]:
                return subprocess.CompletedProcess(command, 0, stdout=submap["name"] + "\n", stderr="")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        def fake_spawn(command):
            proc = self._spawn_real_sleeper(command)
            spawned.append((command, proc))
            self.addCleanup(lambda p=proc: p.poll() is None and p.terminate())
            return proc

        self.assertEqual(eitr_clean.status(runner=fake_run), "off")
        eitr_clean.start(runner=fake_run, spawner=fake_spawn)
        self.assertEqual(len(spawned), 1)
        inhibit_cmd = spawned[0][0]
        self.assertEqual(inhibit_cmd[0], "systemd-inhibit")
        self.assertIn(f"--what={eitr_clean.INHIBIT_WHAT}", inhibit_cmd)
        self.assertIn("--mode=block", inhibit_cmd)
        self.assertIn(["eitr-shell", "desktop-bar", "ipc", "call", "--", "panels", "close"], commands)
        self.assertIn(["eitr-shell", "desktop-bar", "ipc", "call", "--", "clean", "show"], commands)
        self.assertIn(["hyprctl", "dispatch", 'hl.dsp.submap("clean")'], commands)
        self.assertEqual(eitr_clean.status(runner=fake_run), "on")

        # Second start reuses the running inhibitor instead of spawning another.
        eitr_clean.start(runner=fake_run, spawner=fake_spawn)
        self.assertEqual(len(spawned), 1)

        eitr_clean.stop(runner=fake_run)
        spawned[0][1].wait(timeout=5)
        self.assertEqual(eitr_clean.status(runner=fake_run), "off")
        self.assertFalse(eitr_clean.state_path().exists())

    def test_stop_restores_submap_and_ends_inhibitor_when_bar_crashed(self):
        commands = []
        procs = []

        def fake_run(command):
            commands.append(command)
            if command[:5] == ["eitr-shell", "desktop-bar", "ipc", "call", "--"] and command[-1] == "hide":
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="bar socket gone")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        def fake_spawn(command):
            proc = self._spawn_real_sleeper(command)
            procs.append(proc)
            return proc

        eitr_clean.start(runner=fake_run, spawner=fake_spawn)
        self.assertIsNone(procs[0].poll())

        eitr_clean.stop(runner=fake_run)
        procs[0].wait(timeout=5)
        self.assertIn(procs[0].poll(), (0, -signal.SIGTERM))
        self.assertIn(["hyprctl", "dispatch", 'hl.dsp.submap("reset")'], commands)
        self.assertFalse(eitr_clean.state_path().exists())

    def test_start_rolls_back_inhibitor_if_overlay_or_submap_fails(self):
        procs = []

        def fake_spawn(command):
            proc = self._spawn_real_sleeper(command)
            procs.append(proc)
            return proc

        def fail_overlay(command):
            if command[-2:] == ["clean", "show"]:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="no bar")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with self.assertRaises(RuntimeError):
            eitr_clean.start(runner=fail_overlay, spawner=fake_spawn)
        procs[0].wait(timeout=5)
        self.assertFalse(eitr_clean.state_path().exists())

        def fail_submap(command):
            if command == ["hyprctl", "dispatch", 'hl.dsp.submap("clean")']:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="no hypr")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        seen = []

        def tracking_fail_submap(command):
            seen.append(command)
            return fail_submap(command)

        with self.assertRaises(RuntimeError):
            eitr_clean.start(runner=tracking_fail_submap, spawner=fake_spawn)
        procs[1].wait(timeout=5)
        self.assertIn(["eitr-shell", "desktop-bar", "ipc", "call", "--", "clean", "hide"], seen)
        self.assertFalse(eitr_clean.state_path().exists())

    def test_stale_state_or_reused_pid_is_not_treated_as_active(self):
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        def cleanup_unrelated():
            if unrelated.poll() is None:
                unrelated.terminate()
                unrelated.wait(timeout=5)
        self.addCleanup(cleanup_unrelated)
        eitr_clean.write_state({"pid": unrelated.pid, "token": "wrong-token"})
        self.assertFalse(eitr_clean.is_inhibitor_alive(eitr_clean.read_state()))
        self.assertEqual(eitr_clean.status(runner=lambda command: subprocess.CompletedProcess(command, 0, "", "")), "off")
        eitr_clean.stop(runner=lambda command: subprocess.CompletedProcess(command, 0, "", ""))
        # Unrelated process must still be alive.
        self.assertIsNone(unrelated.poll())

    def test_hold_exits_cleanly_on_sigterm(self):
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / "distro/lib/eitr_clean.py"), "_hold", "--token", "abc", "--max-seconds", "30"]
        )
        time.sleep(0.15)
        proc.send_signal(signal.SIGTERM)
        self.assertIn(proc.wait(timeout=5), (0, -signal.SIGTERM))

    @unittest.skipUnless(shutil.which("lua"), "Lua is required to exercise clean-mode.lua")
    def test_hyprland_lua_submap_and_timers(self):
        script = r'''
local timers = {}
local submaps = {}
local events = {}
local layer_rules = {}
local current_submap = ""
local execs = {}
local dispatches = {}

hl = {
    timer = function(cb, opts)
        local obj = { cb = cb, opts = opts, enabled = false }
        function obj:set_enabled(val) self.enabled = val end
        function obj:is_enabled() return self.enabled end
        function obj:set_timeout(ms) self.opts.timeout = ms end
        timers[#timers + 1] = obj
        return obj
    end,
    on = function(name, cb)
        events[name] = cb
    end,
    define_submap = function(name, fn)
        submaps[name] = {}
        local prev = current_submap
        current_submap = name
        fn()
        current_submap = prev
    end,
    bind = function(key, cb, opts)
        local target = submaps[current_submap]
        assert(target, "expected bind inside clean submap")
        target[#target + 1] = { key = key, cb = cb, opts = opts }
    end,
    get_current_submap = function()
        return current_submap
    end,
    dsp = {
        submap = function(arg) return "submap:" .. arg end
    },
    dispatch = function(action)
        dispatches[#dispatches + 1] = action
        if action == "submap:reset" then current_submap = "" end
    end,
    exec_cmd = function(cmd)
        execs[#execs + 1] = cmd
    end,
    layer_rule = function(rule)
        layer_rules[#layer_rules + 1] = rule
    end,
}

local paths = { code = function(rel) return os.getenv("EITR_CODE_ROOT") .. "/" .. rel end }
local quote = function(val) return "'" .. val .. "'" end
dofile(paths.code("hypr/clean-mode.lua"))(paths, quote)

assert(#timers == 2)
local hold_timer, safety_timer = timers[1], timers[2]
assert(hold_timer.opts.timeout == 3000 and hold_timer.opts.type == "oneshot")
assert(safety_timer.opts.timeout == 300000 and safety_timer.opts.type == "oneshot")
assert(not hold_timer.enabled and not safety_timer.enabled)

local clean_binds = submaps["clean"]
assert(#clean_binds == 2)
assert(clean_binds[1].key == "Escape" and clean_binds[1].opts.locked and clean_binds[1].opts.ignore_mods and clean_binds[1].opts.non_consuming and not clean_binds[1].opts.release)
assert(clean_binds[2].key == "Escape" and clean_binds[2].opts.release and clean_binds[2].opts.locked and clean_binds[2].opts.ignore_mods and clean_binds[2].opts.non_consuming)

-- Entering clean starts safety timer; pressing and releasing Esc toggles hold timer.
current_submap = "clean"
events["keybinds.submap"]("clean")
assert(safety_timer.enabled and not hold_timer.enabled)
clean_binds[1].cb()
assert(hold_timer.enabled)
clean_binds[2].cb()
assert(not hold_timer.enabled)

-- Holding Esc to completion resets submap and runs stop script.
clean_binds[1].cb()
hold_timer.cb()
assert(current_submap == "")
assert(not hold_timer.enabled and not safety_timer.enabled)
assert(dispatches[1] == "submap:reset")
assert(execs[1]:find("clean-mode.py' stop", 1, true))

-- Safety timeout also exits cleanly.
current_submap = "clean"
events["keybinds.submap"]("clean")
assert(safety_timer.enabled)
safety_timer.cb()
assert(current_submap == "")
assert(dispatches[2] == "submap:reset")
assert(execs[2]:find("clean-mode.py' stop", 1, true))

-- Blur layer rule registered for desktop-clean.
assert(#layer_rules == 2)
assert(layer_rules[1].match.namespace == "desktop-clean" and layer_rules[1].blur == true)
assert(layer_rules[2].match.namespace == "desktop-clean" and layer_rules[2].ignore_alpha == 0.2)
'''
        result = subprocess.run(
            ["lua", "-"],
            input=script,
            text=True,
            capture_output=True,
            env=dict(os.environ, EITR_CODE_ROOT=str(ROOT)),
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
