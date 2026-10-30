"""Headless broker tests: no network, session bus, or credentials."""
import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
import threading
from unittest.mock import patch, AsyncMock
import tempfile
from pathlib import Path
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'bar-data.py'
spec = importlib.util.spec_from_file_location('bar_data', SCRIPT)
broker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(broker_module)


class BrokerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.frames = []
        self.calls = []
        self.gate = threading.Event()
        def reader(topic):
            self.calls.append(topic)
            self.gate.wait(2)
            return {'devices': []}
        self.broker = broker_module.Broker(self.frames.append, reader)

    async def asyncTearDown(self):
        self.gate.set()
        await self.broker.close()

    async def settle(self, predicate):
        for attempt in range(200):
            if predicate():
                return
            await asyncio.sleep(.005)
        self.fail("read did not settle")

    def subscribe(self, token, topic='network.details'):
        self.broker.request(dict(v=1, op='subscribe', topic=topic, token=token))

    async def test_actions_order_secrets_errors_and_enterprise_deadline(self):
        gate = asyncio.Event()
        processes = []
        commands = []
        response = {"ok": True}

        class Process:
            returncode = None
            pid = 12345
            def __init__(self):
                self.delivered = False
                self.stdin = type("Input", (), {"write": lambda stream, payload: processes.append(payload),
                    "drain": AsyncMock(), "close": lambda stream: None})()
                self.stdout = type("Output", (), {"read": AsyncMock(side_effect=self.read)})()
            async def read(self, limit):
                await gate.wait()
                if self.delivered:
                    return b""
                self.delivered = True
                return json.dumps(response).encode()
            async def wait(self):
                self.returncode = 0
                return 0

        async def spawn(*command, **options):
            commands.append(command)
            self.assertEqual(options["stderr"], asyncio.subprocess.DEVNULL)
            return Process()

        def action(request, name="connect", secret=None):
            self.broker.request(dict(v=1, op="action", topic="network", id=request,
                name=name, args={"path": "/fixture", "input": secret or {"password": "secret"}}))

        with patch.object(broker_module.asyncio, "create_subprocess_exec", side_effect=spawn), \
                patch.object(broker_module.os, "killpg") as kill_group:
            action("first")
            action("second", "forget")
            await asyncio.sleep(.01)
            self.assertEqual(len(commands), 1)
            self.assertNotIn("secret", str(commands))
            self.assertIn(b'"password": "secret"', processes[0])
            gate.set()
            await self.settle(lambda: self.broker.action_task is None)
            self.assertEqual([frame["id"] for frame in self.frames if frame["op"] == "result"], ["first", "second"])
            self.assertTrue(all(not frame["error"] for frame in self.frames if frame["op"] == "result"))
            action("first")
            self.assertEqual(self.frames[-1]["error"], "invalid-request")
            response = {"error": True, "code": "action-failed", "message": "Enter the WiFi password"}
            action("refused")
            await self.settle(lambda: self.broker.action_task is None)
            refused = next(frame for frame in self.frames if frame.get("id") == "refused")
            self.assertEqual(refused["error"], "action-failed")
            self.assertEqual(refused["message"], "Enter the WiFi password")
            gate.clear()
            self.broker.action_timeouts["enterprise"] = .01
            action("enterprise", secret={"identity": "name", "password": "secret"})
            await self.settle(lambda: self.broker.action_task is None)
            self.assertEqual(next(frame for frame in self.frames if frame.get("id") == "enterprise")["error"], "outcome-unknown")
            self.assertEqual(len(commands), 4, "timeout never retries writes")
            kill_group.assert_called_once_with(12345, broker_module.signal.SIGKILL)
        self.assertNotIn("secret", json.dumps(self.frames))

    async def test_action_queue_is_bounded_and_close_discards_secrets(self):
        for number in range(17):
            self.broker.request(dict(v=1, op="action", topic="network", id=str(number), name="connect",
                args={"path": "/fixture", "input": {"password": "secret"}}))
        self.assertEqual(len(self.broker.actions), 16)
        self.assertEqual(self.frames[-1]["error"], "queue-full")
        await self.broker.close()
        self.assertEqual(self.broker.actions, [])
        self.assertNotIn("secret", json.dumps(self.frames))

    async def test_action_backend_unavailable_and_refused(self):
        frame = dict(v=1, op="action", topic="network", id="missing", name="power",
                     args={"path": "/device", "extra": "false"})
        with patch.object(broker_module.asyncio, "create_subprocess_exec", side_effect=OSError):
            self.broker.request(frame)
            await self.settle(lambda: self.broker.action_task is None)
        self.assertTrue(any(item.get("error") == "backend-unavailable" for item in self.frames))
        frame = dict(frame, id="bad", name="unknown")
        self.broker.request(frame)
        self.assertEqual(self.frames[-1]["error"], "invalid-action")

    async def test_screens_share_reader_and_stop_at_zero(self):
        self.subscribe('screen-one')
        self.subscribe('screen-two')
        await asyncio.sleep(.02)
        self.assertEqual(self.calls, ['network.details'])
        self.assertEqual(self.broker.diagnostics()['network.details']['observers'], 2)
        for token in ['screen-one', 'screen-two', 'screen-two']:
            self.broker.request(dict(v=1, op='unsubscribe', topic='network.details', token=token))
        self.gate.set()
        await self.settle(lambda: self.broker.states['network.details']['task'] is None)
        self.assertFalse(self.broker.states['network.details']['task'])
        self.broker.refresh('network.details')
        self.assertEqual(len(self.calls), 1)

    async def test_snapshot_coalesce_and_stale(self):
        self.subscribe('first')
        self.assertEqual(next(frame for frame in self.frames if frame['op'] == 'state')['status'], 'loading')
        for count in range(10):
            self.broker.refresh('network.details')
        self.gate.set()
        await self.settle(lambda: len(self.calls) == 2 and self.broker.states['network.details']['task'] is None)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.frames[-1]['status'], 'ready')
        def failed(topic):
            raise TimeoutError()
        self.broker.reader = failed
        self.broker.refresh('network.details')
        await self.settle(lambda: self.broker.states['network.details']['task'] is None)
        self.assertEqual(self.frames[-1]['status'], 'stale')
        self.assertEqual(self.frames[-1]['error'], 'timeout')
        self.subscribe('second')
        self.assertEqual(self.frames[-1]['token'], 'second')
        self.assertNotIn('devices', json.dumps(self.broker.diagnostics()))

    async def test_unsubscribed_late_result_discarded(self):
        self.subscribe('first')
        await asyncio.sleep(.02)
        self.broker.request(dict(v=1, op='unsubscribe', topic='network.details', token='first'))
        self.gate.set()
        await self.settle(lambda: self.broker.states['network.details']['task'] is None)
        self.assertEqual(self.broker.states['network.details']['data'], {})

    async def test_hung_read_blocks_only_its_topic(self):
        self.broker.timeout = .03
        def reader(topic):
            self.calls.append(topic)
            if topic == 'network.details':
                self.gate.wait(2)
            return {'devices': []}
        self.broker.reader = reader
        self.subscribe('details')
        await asyncio.sleep(.06)
        self.assertEqual(self.broker.states['network.details']['error'], 'timeout')
        for count in range(10):
            self.broker.refresh('network.details')
        self.subscribe('summary', 'network.summary')
        await asyncio.sleep(.03)
        self.assertEqual(self.calls.count('network.details'), 1)
        self.assertEqual(self.broker.states['network.summary']['status'], 'ready')
        self.assertIsNotNone(self.broker.states['network.details']['task'])
        self.gate.set()
        for attempt in range(100):
            if self.broker.states['network.details']['task'] is None:
                break
            await asyncio.sleep(.005)
        self.assertIsNone(self.broker.states['network.details']['task'])

    async def test_scheduler_sleeps_until_demand_or_due(self):
        class CountingEvent(asyncio.Event):
            waits = 0
            async def wait(event):
                event.waits += 1
                return await super().wait()
        event = CountingEvent()
        self.broker.schedule_changed = event
        with patch.object(self.broker, 'refresh', wraps=self.broker.refresh) as refresh:
            task = asyncio.create_task(self.broker.schedule())
            try:
                await asyncio.sleep(.25)
                self.assertEqual(refresh.call_count, 0)
                self.assertEqual(event.waits, 1)
                self.gate.set()
                self.subscribe('summary', 'network.summary')
                await asyncio.sleep(.25)
                self.assertEqual(self.calls, ['network.summary'])
                self.assertLessEqual(refresh.call_count, 2)
                self.assertLessEqual(event.waits, 4)
                self.assertFalse(any(frame['op'] == 'status' for frame in self.frames))
            finally:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    async def test_pool_uses_fake_adapter_without_processes(self):
        class Adapter:
            def read_state(adapter, action, interface):
                self.assertNotEqual(threading.current_thread(), threading.main_thread())
                self.calls.append((action, interface))
                return {'devices': []}
        self.broker.adapter = Adapter()
        self.broker.reader = self.broker.read
        with patch.object(asyncio, 'create_subprocess_exec', side_effect=AssertionError('worker process')):
            self.subscribe('summary', 'network.summary')
            self.subscribe('details')
            await asyncio.sleep(.03)
        self.assertEqual(sorted(self.calls), [('icon', ''), ('status', '')])
        self.assertEqual(self.broker.executor._max_workers, 3)

    async def test_invalid_requests(self):
        for frame in [None, [], {}, {'v': 2}, {'v': 1, 'op': 'action', 'topic': 'network.details'},
                      {'v': 1, 'op': 'subscribe', 'topic': 'network.details', 'token': []}]:
            with self.assertRaises((ValueError, TypeError)):
                self.broker.request(frame)

    async def test_protocol_recovers_after_bad_lines(self):
        process = await asyncio.create_subprocess_exec(sys.executable, str(SCRIPT),
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
        try:
            hello = json.loads(await asyncio.wait_for(process.stdout.readline(), 2))
            self.assertEqual(hello['op'], 'hello')
            for payload in [b'bad\n', b'x' * 300000 + b'\n', b'[]\n', b'[' * 2000 + b']' * 2000 + b'\n']:
                process.stdin.write(payload)
                await process.stdin.drain()
                result = json.loads(await asyncio.wait_for(process.stdout.readline(), 2))
                self.assertEqual(result['op'], 'error')
            process.stdin.write(b'{"v":1,"op":"status","id":"test"}\n')
            await process.stdin.drain()
            while True:
                result = json.loads(await asyncio.wait_for(process.stdout.readline(), 2))
                if result['op'] == 'status':
                    break
            self.assertEqual(result['id'], 'test')
            with self.assertRaises(TimeoutError):
                await asyncio.wait_for(process.stdout.readline(), .15)
            process.stdin.close()
            self.assertEqual(await asyncio.wait_for(process.wait(), 2), 0)
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()


class PackagingTests(unittest.TestCase):
    def test_runtime_stage_and_modes(self):
        from layout import Layout
        root = SCRIPT.parents[3]
        files = ['quickshell/desktop-bar/' + name for name in [
            'DesktopData.qml', 'DesktopDataProtocol.js', 'ObsStatus.qml', 'scripts/bar-data.py', 'scripts/capture-domain.py']]
        layout = Layout(root)
        layout.files = lambda: files
        with tempfile.TemporaryDirectory() as directory:
            layout.stage(Path(directory))
            for relative in files:
                target = Path(directory) / relative
                self.assertTrue(layout.classify(relative)['runtime'])
                self.assertEqual(target.read_bytes(), (root / relative).read_bytes())
                if relative.endswith('bar-data.py'):
                    self.assertTrue(target.stat().st_mode & 0o111)


class CaptureTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.frames = []
        self.calls = []
        self.snapshot = dict(running=True, ready=True, recording=True, paused=True, streaming=True)
        def reader(topic):
            self.calls.append(topic)
            return dict(self.snapshot, recordingSeconds=12, recordingBytes=2048, streamingSeconds=4)
        self.broker = broker_module.Broker(self.frames.append, reader)

    async def asyncTearDown(self):
        await self.broker.close()

    async def settled(self):
        for attempt in range(200):
            if not any(state["task"] for state in self.broker.states.values()) and self.broker.capture.task is None:
                return
            await asyncio.sleep(.005)
        self.fail("capture did not settle")

    def subscribe(self, topic, token):
        self.broker.request(dict(v=1, op="subscribe", topic=topic, token=token))

    async def test_shared_details_feed_summary_and_release(self):
        self.subscribe("capture.summary", "bar")
        await self.settled()
        self.subscribe("capture.details", "one")
        self.subscribe("capture.details", "two")
        await self.settled()
        self.assertEqual(self.calls, ["capture.summary", "capture.details"])
        self.assertTrue(self.broker.states["capture.summary"]["data"]["paused"])
        self.assertFalse(self.broker.scheduled("capture.summary"))
        for token in ("one", "two"):
            self.broker.request(dict(v=1, op="unsubscribe", topic="capture.details", token=token))
        self.assertFalse(self.broker.scheduled("capture.details"))
        self.assertTrue(self.broker.scheduled("capture.summary"))

    async def test_headless_process_absence_reconnect_and_unknown(self):
        self.snapshot.update(running=False, recording=False, streaming=False)
        self.subscribe("capture.summary", "bar")
        await self.settled()
        self.assertFalse(self.broker.scheduled("capture.summary"), "no idle process polling")
        self.snapshot.update(running=True, recording=True)
        self.broker.refresh("capture.summary")
        await self.settled()
        self.assertTrue(self.broker.scheduled("capture.summary"), "headless OBS is observed")
        self.subscribe("capture.details", "panel")
        await self.settled()
        self.snapshot.update(ready=False, recording=False)
        self.broker.refresh("capture.details")
        await self.settled()
        summary = self.broker.states["capture.summary"]
        self.assertEqual(summary["status"], "stale")
        self.assertTrue(summary["data"]["recording"], "failure retains last known active state")
        self.snapshot.update(ready=True, recording=False, running=False)
        self.broker.refresh("capture.details")
        await self.settled()
        self.assertEqual(summary["status"], "ready")
        self.assertFalse(summary["data"]["running"])

    async def test_capture_action_queue_and_stop_budget(self):
        commands, budgets = [], []
        gate = asyncio.Event()
        class Process:
            returncode = None
            pid = 23456
            def __init__(self):
                self.delivered = False
                self.stdout = type("Output", (), {"read": AsyncMock(side_effect=self.read)})()
            async def read(self, limit):
                await gate.wait()
                if self.delivered:
                    return b""
                self.delivered = True
                return b"Command applied"
            async def wait(self):
                self.returncode = 0
        async def spawn(*command, **options):
            commands.append(command)
            return Process()
        wait_for = asyncio.wait_for
        async def timed(awaitable, budget):
            budgets.append(budget)
            return await wait_for(awaitable, budget)
        with patch.object(broker_module.asyncio, "create_subprocess_exec", side_effect=spawn),                 patch.object(broker_module.asyncio, "wait_for", side_effect=timed):
            for request, name in (("first", "pause"), ("second", "stop")):
                self.broker.request(dict(v=1, op="action", topic="capture", id=request, name=name, args={}))
            await asyncio.sleep(.01)
            self.assertEqual(len(commands), 1)
            gate.set()
            await self.settled()
        self.assertEqual([command[-1] for command in commands], ["pause", "stop"])
        self.assertEqual(budgets, [30, 45])
        self.assertEqual([frame["id"] for frame in self.frames if frame["op"] == "result"], ["first", "second"])
        self.broker.request(dict(v=1, op="action", topic="capture", id="first", name="pause", args={}))
        self.assertEqual(self.frames[-1]["error"], "invalid-request")


    async def test_capture_timeout_discards_queued_writes_and_reaps_child(self):
        process = type("Process", (), {"pid": 23456, "returncode": None})()
        process.stdout = type("Output", (), {"read": AsyncMock(side_effect=TimeoutError)})()
        async def wait():
            process.returncode = -9
        process.wait = AsyncMock(side_effect=wait)
        with patch.object(broker_module.asyncio, "create_subprocess_exec", new=AsyncMock(return_value=process)) as spawn,                 patch.object(broker_module.os, "killpg") as kill_group:
            for request, name in (("first", "record"), ("second", "pause")):
                self.broker.request(dict(v=1, op="action", topic="capture", id=request, name=name, args={}))
            await self.settled()
            self.assertEqual(spawn.await_count, 1, "unknown outcome cannot run queued dependent writes")
            kill_group.assert_called_once_with(process.pid, broker_module.signal.SIGKILL)
            process.wait.assert_awaited_once()
        results = [frame for frame in self.frames if frame["op"] == "result"]
        self.assertEqual([frame["id"] for frame in results], ["first", "second"])
        self.assertTrue(all(frame["error"] == "outcome-unknown" for frame in results))
        self.assertIsNone(self.broker.capture.task)

    async def test_capture_read_deadline_marks_summary_stale_before_thread_returns(self):
        self.subscribe("capture.summary", "bar")
        await self.settled()
        gate = threading.Event()
        def reader(topic):
            self.calls.append(topic)
            if topic == "capture.details":
                gate.wait(2)
                return dict(self.snapshot, recording=False)
            return {"devices": []}
        self.broker.reader = reader
        wait_for = asyncio.wait_for
        async def timed(awaitable, budget):
            return await wait_for(awaitable, .02 if budget == 25 else budget)
        try:
            with patch.object(broker_module.asyncio, "wait_for", side_effect=timed):
                self.subscribe("capture.details", "panel")
                await asyncio.sleep(.05)
                summary = self.broker.states["capture.summary"]
                self.assertEqual(summary["status"], "stale")
                self.assertTrue(summary["data"]["recording"])
                self.assertIsNotNone(self.broker.states["capture.details"]["task"])
                self.subscribe("capture.details", "second")
                self.subscribe("network.summary", "network")
                await asyncio.sleep(.02)
                self.assertEqual(self.calls.count("capture.details"), 1)
                self.assertEqual(self.broker.states["network.summary"]["status"], "ready")
                for token in ("panel", "second"):
                    self.broker.request(dict(v=1, op="unsubscribe", topic="capture.details", token=token))
                gate.set()
                await self.settled()
                self.assertTrue(summary["data"]["recording"], "timed-out result never overwrites state")
        finally:
            gate.set()


class CaptureServiceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("quickshell"), "Quickshell unavailable")
    def test_controller_ordering_shared_demand_and_panel_destruction(self):
        bar = SCRIPT.parent.parent
        with tempfile.TemporaryDirectory(prefix="eitr-capture-test-") as directory:
            root = Path(directory)
            for name in ("DesktopData.qml", "DesktopDataProtocol.js", "ObsStatus.qml", "ObsQueue.js", "PanelStyle.js"):
                shutil.copy(bar / name, root / name)
            # Exercise production controller/demand logic without Wayland surfaces.
            for name, boundary in (("ObsMenu.qml", "    Column {"), ("RecordingMenu.qml", "    component Toggle:")):
                source = (bar / name).read_text()
                source = source[:source.index(boundary)] + "}\n"
                (root / name).write_text(source)
            (root / "ThemedPopup.qml").write_text("""
import QtQuick
Item {
    property bool opened: false
    property bool waitForFreshData: false
    property int transitionDuration: 20
    property real verticalContentInset: 0
    property var content: ({implicitHeight: 20})
    function updateContent(action) { action(); }
    function applySnapshot(name, value) { this[name] = value; }
}
""")
            (root / "qmldir").write_text("singleton DesktopData DesktopData.qml\nsingleton ObsStatus ObsStatus.qml\nObsMenu ObsMenu.qml\nRecordingMenu RecordingMenu.qml\nThemedPopup ThemedPopup.qml\n")
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("bar-data.py", "capture-domain.py"):
                shutil.copy(bar / "scripts" / name, scripts / name)
            (scripts / "state.json").write_text(json.dumps(dict(
                running=False, ready=True, recording=False, paused=False, streaming=False)))
            (scripts / "obs-control.py").write_text("""
import json, sys, time
from pathlib import Path
folder = Path(__file__).parent
def status():
    return json.loads((folder / "state.json").read_text())
def capture_options():
    return {key: {"enabled": True, "available": True} for key in ("audio", "mic", "webcam")}
def details():
    with (folder / "reads").open("a") as output:
        output.write("details\\n")
    return dict(status(), recordingSeconds=12, recordingBytes=2048, scenes=["Desk", "Game"], scene="Desk")
if __name__ == "__main__":
    action = sys.argv[1]
    with (folder / "actions").open("a") as output:
        output.write(json.dumps(sys.argv[1:]) + "\\n")
    time.sleep(.05)
    state = status()
    if action == "prepare":
        state["running"] = True
    elif action == "record":
        state["recording"] = True
    elif action == "pause":
        state["paused"] = True
    elif action == "stop":
        state.update(recording=False, paused=False, running=False)
    elif action == "scene":
        print(json.dumps({"error": "action-failed", "message": "That OBS scene no longer exists"}))
        sys.exit(1)
    (folder / "state.json").write_text(json.dumps(state))
    print("Command applied")
""")
            (root / "shell.qml").write_text("""
import QtQuick
import Quickshell
ShellRoot {
    id: harness
    property int phase: 0
    property int ticks: 0
    property var first: null
    property var second: null
    property var one: null
    property var two: null
    function check(condition, message) {
        if (!condition) { console.error("CAPTURE FAIL", message); Qt.exit(1); }
    }
    Component { id: controller; ObsMenu {} }
    Component { id: panel; RecordingMenu { controller: harness.first } }
    Timer {
        interval: 100; repeat: true; running: true
        onTriggered: {
            harness.check(++harness.ticks < 100, "phase timeout " + harness.phase);
            if (harness.phase === 0) {
                if (!ObsStatus.state.ready) return;
                harness.first = controller.createObject(harness);
                harness.second = controller.createObject(harness);
                harness.first.opened = true;
                harness.first.saveOption("mic", false);
                harness.first.saveOption("mic", true);
                harness.first.run("record");
                harness.second.run("stream");
                harness.check(harness.second.pendingAction === "", "cross-screen conflict guard");
            } else if (harness.phase === 1) {
                if (harness.first.busy || !harness.first.obsState.recording) return;
                harness.check(!harness.first.opened, "prepare closes panel");
                harness.one = panel.createObject(harness);
                harness.two = panel.createObject(harness);
                harness.one.opened = true;
                harness.two.opened = true;
            } else if (harness.phase === 2) {
                if (!harness.one.details.recordingSeconds || !harness.two.details.recordingSeconds) return;
                harness.check(ObsStatus.detailObservers === 2, "shared detail observers");
                harness.check(DesktopData.client.count("capture.details") === 1, "one canonical detail token");
                harness.one.destroy(); harness.two.destroy();
            } else if (harness.phase === 3) {
                harness.check(ObsStatus.detailObservers === 0, "destruction releases demand");
                harness.check(DesktopData.client.count("capture.details") === 0, "reader stopped");
                harness.first.run("pause");
            } else if (harness.phase === 4) {
                if (harness.first.busy || !harness.first.obsState.paused) return;
                harness.first.run("scene", "Gone");
            } else if (harness.phase === 5) {
                if (harness.first.busy) return;
                harness.check(harness.first.actionError === "That OBS scene no longer exists", "action error at origin");
                harness.check(harness.second.actionError === "", "action error stays private");
                harness.first.run("stop");
            } else {
                if (harness.first.busy || harness.first.obsState.recording) return;
                harness.first.destroy(); harness.second.destroy();
                console.log("CAPTURE PASS"); Qt.quit();
            }
            harness.phase++;
            harness.ticks = 0;
        }
    }
}
""")
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            environment = dict(os.environ, QT_QPA_PLATFORM="offscreen", QML_IMPORT_PATH=str(bar.parent),
                               DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent", XDG_RUNTIME_DIR=str(runtime),
                               HYPRLAND_INSTANCE_SIGNATURE="")
            for kind in ("CONFIG", "CACHE", "STATE", "DATA"):
                environment[f"XDG_{kind}_HOME"] = str(root / kind.lower())
            for name in ("WAYLAND_DISPLAY", "DISPLAY", "QS_CONFIG_PATH", "QS_CONFIG_NAME"):
                environment.pop(name, None)
            result = subprocess.run(["quickshell", "--no-color", "-p", str(root / "shell.qml")],
                                    env=environment, capture_output=True, text=True, timeout=20)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn("CAPTURE PASS", output)
            self.assertNotIn("ReferenceError", output)
            self.assertNotIn("TypeError", output)
            actions = [json.loads(line) for line in (scripts / "actions").read_text().splitlines()]
            self.assertEqual(actions, [["set-option", "mic", "false"], ["set-option", "mic", "true"],
                                       ["prepare"], ["record"], ["pause"], ["scene", "Gone"], ["stop"]])


if __name__ == '__main__':
    unittest.main()
