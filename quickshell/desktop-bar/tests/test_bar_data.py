"""Headless broker tests: no network, session bus, or credentials."""
import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
import threading
from unittest.mock import patch, AsyncMock, Mock
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

    async def test_admitted_refresh_survives_close_before_worker_dispatch(self):
        # Deliver open and close in one event-loop turn, as the QML transport can.
        self.subscribe('brief-open')
        self.broker.request(dict(v=1, op='unsubscribe', topic='network.details', token='brief-open'))
        self.assertEqual(self.calls, [])
        self.gate.set()
        await self.settle(lambda: self.broker.states['network.details']['task'] is None)
        self.assertEqual(self.calls, ['network.details'])
        self.assertEqual(self.broker.states['network.details']['data'], {}, 'closed generation cannot publish')
        self.assertFalse(self.broker.scheduled('network.details'), 'closing stops periodic sampling')
        self.broker.refresh('network.details')
        await asyncio.sleep(.02)
        self.assertEqual(self.calls, ['network.details'], 'no new refresh without demand')
        self.subscribe('reopen')
        await self.settle(lambda: self.broker.states['network.details']['task'] is None)
        self.assertEqual(self.calls, ['network.details', 'network.details'])
        self.assertEqual(self.broker.states['network.details']['status'], 'ready')

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
            'scripts/remote-domain.py', 'scripts/hardware-domain.py', 'scripts/system-details.py', 'PowerService.qml', 'scripts/power-domain.py', 'DesktopData.qml', 'DesktopDataProtocol.js', 'ObsStatus.qml', 'scripts/bar-data.py', 'scripts/capture-domain.py']]
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
        wait = asyncio.wait
        async def timed(awaitables, *, timeout=None):
            return await wait(awaitables, timeout=.02 if timeout == 25 else timeout)
        try:
            with patch.object(broker_module.asyncio, "wait", side_effect=timed):
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
            for name in ("bar-data.py", "capture-domain.py", "power-domain.py"):
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


class PowerTests(unittest.IsolatedAsyncioTestCase):
    async def test_shared_demand_cadence_and_suspend_gap(self):
        frames, calls = [], []
        def read(topic):
            calls.append(topic)
            return {'available': True, 'percent': 9, 'status': 'Discharging'}
        broker = broker_module.Broker(frames.append, read)
        scheduler = None
        try:
            for token in ('screen1', 'screen2'):
                broker.request(dict(v=1, op='subscribe', topic='power.battery', token=token))
            await asyncio.sleep(.03)
            self.assertEqual(calls, ['power.battery'])
            broker.states['power.battery']['due'] = asyncio.get_running_loop().time() - 3600
            scheduler = asyncio.create_task(broker.schedule())
            await asyncio.sleep(.03)
            self.assertEqual(calls, ['power.battery'] * 2, 'resume must not catch up every missed tick')
            for token in ('screen1', 'screen2'):
                broker.request(dict(v=1, op='unsubscribe', topic='power.battery', token=token))
            self.assertFalse(broker.scheduled('power.battery'))
            self.assertFalse(broker.scheduled('power.profile'))
            self.assertFalse(broker.scheduled('power.radios'))
        finally:
            if scheduler:
                scheduler.cancel()
                await asyncio.gather(scheduler, return_exceptions=True)
            await broker.close()

    async def test_system_capability_once_and_cli_parity(self):
        from types import SimpleNamespace
        broker = broker_module.Broker(lambda frame: None)
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for name, percent, scope in [('BAT0', 40, 'System'), ('BAT1', 80, 'System'), ('mouse', 1, 'Device')]:
                    supply = root / name
                    supply.mkdir()
                    for key, value in dict(type='Battery', scope=scope, capacity=percent, status='Discharging',
                                           energy_full=100, energy_now=percent, energy_full_design=100, power_now=20).items():
                        (supply / key).write_text(str(value))
                from eitr_battery import system_batteries
                with patch.dict(broker.power.read.__globals__, system_batteries=lambda: system_batteries(root)):
                    snapshot = broker.power.read('power.battery')
                    self.assertEqual(snapshot['percent'], 60)
                    battery = broker.power.adapters['battery']
                    self.assertEqual(snapshot, battery.status(root))
                    (root / 'BAT0' / 'capacity').write_text('20')
                    with patch.dict(broker.power.read.__globals__, system_batteries=lambda: self.fail('capability re-read')):
                        self.assertEqual(broker.power.read('power.battery')['percent'], 50)
                        broker.power.read('power.profile')
                    profile = broker.power.adapters['power-profile']
                    with patch.object(profile.shutil, 'which', return_value='powerprofilesctl'), patch.object(
                            profile.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'powerprofilesctl')):
                        self.assertEqual(broker.power.read('power.profile'), profile.unavailable())
                for name in ('BAT0', 'BAT1'):
                    (root / name / 'present').write_text('0')
                broker.power.batteries = None
                with patch.dict(broker.power.read.__globals__, system_batteries=lambda: system_batteries(root)):
                    self.assertFalse(broker.power.read('power.battery')['available'])
                    self.assertFalse(broker.power.read('power.profile')['available'])
        finally:
            await broker.close()

    async def test_power_action_rejects_invalid_requests_at_source(self):
        frames = []
        broker = broker_module.Broker(frames.append, lambda topic: {})
        try:
            broker.request(dict(v=1, op='action', topic='power', id='invalid', name='profile', args={'path': 'turbo'}))
            self.assertEqual(frames[-1]['topic'], 'power')
            self.assertEqual(frames[-1]['error'], 'invalid-request')
            self.assertFalse(broker.actions)
        finally:
            await broker.close()

    def test_warning_thresholds_once_across_suspend_and_repeated_snapshots(self):
        source = (SCRIPT.parents[1] / 'shell.qml').read_text()
        start = source.index('    function checkBatteryLow()')
        end = source.index('\n    }', start) + 6
        function = source[start:end]
        code = '''const assert = require('assert');
const hooks = [], notifications = [];
let batteryLowHookRan = false, batteryWarned = 0;
const shell = {battery: {available:true, status:'Discharging', percent:50}};
const runHook = args => hooks.push(args);
const Quickshell = {execDetached: args => notifications.push(args)};
''' + function + '''
[50,15,15,9,9,4,4].forEach(percent => {shell.battery.percent = percent; checkBatteryLow();});
assert.equal(hooks.length,1); assert.equal(notifications.length,2);
shell.battery.status = 'Charging'; checkBatteryLow();
shell.battery.status = 'Discharging'; shell.battery.percent = 4;
checkBatteryLow(); checkBatteryLow();
assert.equal(hooks.length,2); assert.equal(notifications.length,3);
'''
        subprocess.run(['node', '-e', code], check=True, capture_output=True, timeout=5)

    async def test_power_helpers_order_results_and_radio_reconciliation(self):
        from types import SimpleNamespace
        frames = []
        broker = broker_module.Broker(frames.append, lambda topic: {})
        processes = []
        for output in (b'{"active":"balanced"}', b'{"error":true,"code":"action-failed"}'):
            processes.append(SimpleNamespace(
                returncode=0, stdin=SimpleNamespace(write=lambda payload: None, drain=AsyncMock(), close=lambda: None),
                stdout=SimpleNamespace(read=AsyncMock(side_effect=[output, b''])), wait=AsyncMock()))
        start = AsyncMock(side_effect=processes)
        try:
            with patch.object(broker_module.asyncio, 'create_subprocess_exec', start):
                broker.request(dict(v=1, op='action', topic='power', id='profile1', name='profile', args={'path': 'balanced'}))
                broker.request(dict(v=1, op='action', topic='power', id='radio1', name='airplane', args={'extra': 'true'}))
                await broker.action_task
            commands = [call.args for call in start.call_args_list]
            self.assertEqual(commands[0][-3:], (str(SCRIPT.with_name('power-profile.py')), 'set', 'balanced'))
            self.assertEqual(commands[1][-3:], (str(SCRIPT.with_name('airplane.py')), 'set', 'true'))
            results = [frame for frame in frames if frame['op'] == 'result']
            self.assertEqual([(frame['topic'], frame['id'], frame['error']) for frame in results],
                             [('power', 'profile1', ''), ('power', 'radio1', 'action-failed')])
            self.assertEqual(broker.states['power.radios']['due'], 0)
            broker.request(dict(v=1, op='action', topic='power', id='radio1', name='airplane', args={'extra': 'true'}))
            self.assertEqual(frames[-1]['error'], 'invalid-request')
            self.assertEqual(start.call_count, 2, 'duplicate writes must not replay')
        finally:
            await broker.close()


class DisplayIsolationTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_display_domain_is_lazy_and_does_not_break_network(self):
        loop_thread = threading.get_ident()
        imports = []
        original_spec = importlib.util.spec_from_file_location
        def locate(name, path):
            if Path(path).name == "display-domain.py":
                imports.append(threading.get_ident())
                raise FileNotFoundError("display fixture absent")
            return original_spec(name, path)
        with patch.object(broker_module.importlib.util, "spec_from_file_location", side_effect=locate):
            broker = broker_module.Broker(lambda frame: None)
            try:
                self.assertEqual(imports, [], "startup must not load an unobserved display domain")
                broker.adapter = Mock()
                broker.adapter.read_state.return_value = {"devices": []}
                broker.request(dict(v=1, op="subscribe", topic="display.topology", token="display"))
                broker.request(dict(v=1, op="subscribe", topic="network.summary", token="network"))
                self.assertEqual(imports, [], "subscribe must not import on the event loop")
                await asyncio.wait_for(asyncio.gather(broker.states["display.topology"]["task"],
                                                     broker.states["network.summary"]["task"]), 3)
                self.assertEqual(broker.states["display.topology"]["status"], "unavailable")
                self.assertEqual(broker.states["network.summary"]["status"], "ready")
                self.assertEqual(len(imports), 1)
                self.assertNotEqual(imports[0], loop_thread, "display import belongs in the worker pool")
            finally:
                await broker.close()

    async def test_slow_display_read_has_deadline_without_blocking_network(self):
        gate = threading.Event()
        calls = []
        loop_thread = threading.get_ident()
        def read(topic):
            calls.append(threading.get_ident())
            gate.wait(2)
            return {"available": True, "kind": "ddc", "value": 50}
        broker = broker_module.Broker(lambda frame: None, timeout=.02)
        broker.display = Mock()
        broker.display.read.side_effect = read
        broker.adapter = Mock()
        broker.adapter.read_state.return_value = {"devices": []}
        try:
            broker.request(dict(v=1, op="subscribe", topic="display.brightness", token="display"))
            display_task = broker.states["display.brightness"]["task"]
            broker.request(dict(v=1, op="subscribe", topic="network.summary", token="network"))
            await asyncio.wait_for(broker.states["network.summary"]["task"], 1)
            await asyncio.sleep(.04)
            self.assertEqual(broker.states["network.summary"]["status"], "ready")
            self.assertEqual(broker.states["display.brightness"]["error"], "timeout")
            self.assertFalse(display_task.done(), "timed-out read retains its bounded worker slot")
            self.assertEqual(len(calls), 1)
            self.assertNotEqual(calls[0], loop_thread)
            broker.refresh("display.brightness")
            broker.refresh("display.brightness")
            self.assertEqual(len(calls), 1, "refreshes must not spawn more blocked reads")
            broker.request(dict(v=1, op="unsubscribe", topic="display.brightness", token="display"))
            gate.set()
            await asyncio.wait_for(display_task, 1)
            self.assertEqual(broker.states["display.brightness"]["data"], {}, "late result is discarded")
        finally:
            gate.set()
            await broker.close()


class HardwareBrokerTests(unittest.IsolatedAsyncioTestCase):
    async def settle(self, predicate):
        for attempt in range(200):
            if predicate():
                return
            await asyncio.sleep(.005)
        self.fail("hardware read did not settle")

    async def test_observed_sampler_refresh_reopen_and_no_idle_work(self):
        calls = []
        gate = threading.Event()
        def read(topic):
            calls.append(topic)
            gate.wait(2)
            return {"sections": [], "identity": {"cached": True}}
        broker = broker_module.Broker(lambda frame: None, read)
        scheduler = asyncio.create_task(broker.schedule())
        def demand(operation, token):
            broker.request(dict(v=1, op=operation, topic="hardware.details", token=token))
        try:
            self.assertEqual(broker_module.INTERVALS["hardware.details"], 2)
            await asyncio.sleep(.02)
            self.assertEqual(calls, [])
            demand("subscribe", "one")
            demand("subscribe", "two")
            await self.settle(lambda: len(calls) == 1)
            self.assertEqual(broker.diagnostics()["hardware.details"]["observers"], 2)
            gate.set()
            await self.settle(lambda: broker.states["hardware.details"]["task"] is None)
            self.assertEqual(len(calls), 1)
            broker.states["hardware.details"]["due"] = 0
            broker.schedule_changed.set()
            await self.settle(lambda: len(calls) == 2 and broker.states["hardware.details"]["task"] is None)
            demand("unsubscribe", "one")
            demand("unsubscribe", "two")
            broker.states["hardware.details"]["due"] = 0
            broker.schedule_changed.set()
            await asyncio.sleep(.03)
            self.assertEqual(len(calls), 2)
            demand("subscribe", "reopened")
            await self.settle(lambda: len(calls) == 3)
        finally:
            gate.set()
            scheduler.cancel()
            await asyncio.gather(scheduler, return_exceptions=True)
            await broker.close()

    async def test_remote_observers_refresh_reopen_and_no_idle_work(self):
        calls = []
        gate = threading.Event()
        def read(topic):
            calls.append(topic)
            gate.wait(2)
            return {"allowed": True, "tailscale": {}, "streaming": {}}
        broker = broker_module.Broker(lambda frame: None, read)
        scheduler = asyncio.create_task(broker.schedule())
        def demand(operation, token):
            broker.request(dict(v=1, op=operation, topic="remote.status", token=token))
        try:
            self.assertEqual(broker_module.INTERVALS["remote.status"], 10)
            await asyncio.sleep(.02)
            self.assertEqual(calls, [])
            demand("subscribe", "one")
            demand("subscribe", "two")
            await self.settle(lambda: len(calls) == 1)
            self.assertEqual(broker.diagnostics()["remote.status"]["observers"], 2)
            gate.set()
            await self.settle(lambda: broker.states["remote.status"]["task"] is None)
            self.assertEqual(len(calls), 1)
            broker.states["remote.status"]["due"] = 0
            broker.schedule_changed.set()
            await self.settle(lambda: len(calls) == 2 and broker.states["remote.status"]["task"] is None)
            demand("unsubscribe", "one")
            demand("unsubscribe", "two")
            broker.states["remote.status"]["due"] = 0
            broker.schedule_changed.set()
            await asyncio.sleep(.03)
            self.assertEqual(len(calls), 2)
            demand("subscribe", "reopened")
            await self.settle(lambda: len(calls) == 3)
        finally:
            gate.set()
            scheduler.cancel()
            await asyncio.gather(scheduler, return_exceptions=True)
            await broker.close()

    async def test_remote_availability_has_no_periodic_work_and_read_failure_is_isolated(self):
        calls = []
        def read(topic):
            calls.append(topic)
            if topic == "remote.status":
                raise RuntimeError("fixture service failure")
            return {"allowed": True} if topic == "remote.availability" else {"sections": []}
        frames = []
        broker = broker_module.Broker(frames.append, read)
        scheduler = asyncio.create_task(broker.schedule())
        try:
            self.assertEqual(broker_module.INTERVALS["remote.availability"], float("inf"))
            for topic in ("remote.availability", "remote.status", "hardware.details"):
                broker.request(dict(v=1, op="subscribe", topic=topic, token=topic))
            await self.settle(lambda: all(broker.states[topic]["task"] is None for topic in calls) and len(calls) == 3)
            self.assertEqual(broker.states["remote.status"]["error"], "read-failed")
            self.assertEqual(broker.states["hardware.details"]["status"], "ready")
            self.assertEqual(broker.states["remote.availability"]["due"], float("inf"))
            remote = [frame for frame in frames if frame.get("topic") == "remote.status"]
            self.assertTrue(any(frame.get("inFlight") for frame in remote))
            self.assertFalse(remote[-1]["inFlight"])
            broker.request(dict(v=1, op="unsubscribe", topic="remote.status", token="remote.status"))
            await asyncio.sleep(.03)
            self.assertEqual(calls.count("remote.availability"), 1)
        finally:
            scheduler.cancel()
            await asyncio.gather(scheduler, return_exceptions=True)
            await broker.close()

    async def test_all_domain_import_failures_and_deadlines_are_isolated(self):
        from types import SimpleNamespace
        for broken in ("network", "power", "capture", "display", "hardware", "remote"):
            for slow in (False, True):
                gate = threading.Event()
                imports = []
                main_thread = threading.get_ident()
                def spec(name, path):
                    def execute(module):
                        imports.append(Path(path).name)
                        self.assertNotEqual(threading.get_ident(), main_thread)
                        if Path(path).name == ("wifi-popup.py" if broken == "network" else broken + "-domain.py"):
                            if slow:
                                gate.wait(2)
                            raise ImportError("broken fixture domain")
                        module.PowerDomain = lambda: SimpleNamespace(read=lambda topic: {"available": False})
                        module.HardwareDomain = lambda: SimpleNamespace(read=lambda topic: {"sections": []})
                    return SimpleNamespace(loader=SimpleNamespace(exec_module=execute))
                broker = broker_module.Broker(lambda frame: None, timeout=.03)
                try:
                    self.assertEqual(imports, [], "construction must not import any domain")
                    with patch.object(broker_module.importlib.util, "spec_from_file_location", side_effect=spec), \
                            patch.object(broker_module.importlib.util, "module_from_spec", side_effect=lambda spec: SimpleNamespace()):
                        topic = {"network": "network.details", "power": "power.battery", "capture": "capture.options",
                                 "display": "display.topology", "hardware": "hardware.details", "remote": "remote.status"}[broken]
                        broker.request(dict(v=1, op="subscribe", token="broken", topic=topic))
                        siblings = {"network": ["network.summary"], "power": ["power.profile", "power.radios"],
                                    "capture": ["capture.details", "capture.summary"],
                                    "display": ["display.settings", "display.brightness", "display.nightlight"], "hardware": [], "remote": ["remote.availability"]}[broken]
                        if slow:
                            for sibling in siblings:
                                broker.request(dict(v=1, op="subscribe", token=sibling, topic=sibling))
                        await self.settle(lambda: broker.states[topic]["status"] == "unavailable")
                        self.assertEqual(broker.states[topic]["error"], "timeout" if slow else "read-failed")
                        healthy = "hardware.details" if broken != "hardware" else "power.battery"
                        broker.request(dict(v=1, op="subscribe", token="healthy", topic=healthy))
                        await self.settle(lambda: broker.states[healthy]["status"] == "ready")
                        if slow:
                            filename = "wifi-popup.py" if broken == "network" else broken + "-domain.py"
                            self.assertEqual(imports.count(filename), 1, "sibling topics share a single import job")
                        gate.set()
                        await self.settle(lambda: all(broker.states[entry]["task"] is None for entry in [topic, *siblings]))
                        self.assertNotIn(broken, broker.domains, "failed import must never install a partial adapter")
                finally:
                    gate.set()
                    await broker.close()

    async def test_hardware_identity_survives_read_failure_and_reopen(self):
        broker = broker_module.Broker(lambda frame: None)
        try:
            domain = broker.load_domain("hardware")
            adapter = domain.adapter
            with patch.object(adapter, "cpu_identity", return_value={"name": "CPU", "cores": "4 / 8"}) as cpu_identity, \
                    patch.object(adapter, "storage_identity", return_value={"name": "Root", "rows": []}) as storage_identity, \
                    patch.object(adapter, "query", return_value="") as query, \
                    patch.object(adapter, "cpu", side_effect=[OSError("fixture"), {"title": "CPU"}, {"title": "CPU"}]), \
                    patch.object(adapter, "memory", return_value={"title": "RAM"}), \
                    patch.object(adapter, "storage", return_value=[]):
                for token, expected in (("first", "unavailable"), ("reopen", "ready"), ("again", "ready")):
                    broker.request(dict(v=1, op="subscribe", topic="hardware.details", token=token))
                    await self.settle(lambda: broker.states["hardware.details"]["task"] is None)
                    self.assertEqual(broker.states["hardware.details"]["status"], expected)
                    broker.request(dict(v=1, op="unsubscribe", topic="hardware.details", token=token))
                cpu_identity.assert_called_once()
                storage_identity.assert_called_once()
                query.assert_called_once()
                self.assertFalse(domain.identity["gpu"]["available"])
        finally:
            await broker.close()


    async def test_close_reopen_during_inflight_refreshes_without_duplicate_sampler(self):
        gate = threading.Event()
        calls = []
        def reader(topic):
            calls.append(topic)
            gate.wait(2)
            return {"identity": {}, "sections": []}
        broker = broker_module.Broker(lambda frame: None, reader)
        scheduler = asyncio.create_task(broker.schedule())
        try:
            broker.request(dict(v=1, op="subscribe", topic="hardware.details", token="first"))
            await self.settle(lambda: len(calls) == 1)
            broker.request(dict(v=1, op="unsubscribe", topic="hardware.details", token="first"))
            broker.request(dict(v=1, op="subscribe", topic="hardware.details", token="reopen"))
            self.assertEqual(len(calls), 1)
            gate.set()
            await self.settle(lambda: len(calls) == 2 and broker.states["hardware.details"]["task"] is None)
            self.assertEqual(broker.states["hardware.details"]["status"], "ready")
        finally:
            gate.set()
            scheduler.cancel()
            await asyncio.gather(scheduler, return_exceptions=True)
            await broker.close()

    async def test_slow_reads_in_one_domain_leave_pool_capacity_for_others(self):
        gate = threading.Event()
        calls = []
        def slow_read(topic):
            calls.append(topic)
            gate.wait(2)
            return {"available": False}
        broker = broker_module.Broker(lambda frame: None, timeout=.03)
        broker.domains['power'] = Mock(read=slow_read)
        broker.domains['hardware'] = Mock(read=lambda topic: {"identity": {}, "sections": []})
        try:
            for topic in ('power.battery', 'power.profile', 'power.radios'):
                broker.request(dict(v=1, op='subscribe', topic=topic, token=topic))
            await self.settle(lambda: all(broker.states[topic]['status'] == 'unavailable'
                                         for topic in ('power.battery', 'power.profile', 'power.radios')))
            broker.request(dict(v=1, op='subscribe', topic='hardware.details', token='healthy'))
            await self.settle(lambda: broker.states['hardware.details']['status'] == 'ready')
            self.assertEqual(len(calls), 2, 'one stalled domain leaves a pool worker available')
            gate.set()
            await self.settle(lambda: not any(state['task'] for state in broker.states.values()))
            self.assertEqual(len(calls), 2, 'queued reads past their deadline never start')
        finally:
            gate.set()
            await broker.close()


class WeatherAiBrokerTests(unittest.IsolatedAsyncioTestCase):
    async def settle(self, predicate):
        for attempt in range(400):
            if predicate():
                return
            await asyncio.sleep(.005)
        self.fail('broker did not settle')

    async def test_weather_shared_default_scoped_cities_and_cancel(self):
        frames, calls = [], []
        gate = threading.Event()
        def weather(city=None, **options):
            calls.append(city)
            if city:
                gate.wait(2)
            return dict(temp='17°C', location=city['name'] if city else 'default')
        adapter = Mock(read=lambda topic: weather(), weather=weather,
                       search=lambda query, deadline: dict(cities=[], error='No cities found'))
        broker = broker_module.Broker(frames.append)
        broker.domains['weather'] = adapter
        try:
            for token in ('screen-one', 'screen-two', 'menu'):
                broker.request(dict(v=1, op='subscribe', topic='weather.default', token=token))
            await self.settle(lambda: broker.states['weather.default']['task'] is None)
            self.assertEqual(calls, [None])
            city = dict(name='alternate', latitude=1, longitude=2)
            for request in ('closed-panel', 'other-panel'):
                broker.request(dict(v=1, op='query', topic='weather', id=request, name='city', args=dict(city=city)))
            await self.settle(lambda: len(calls) == 2)
            broker.request(dict(v=1, op='cancel', topic='weather', id='closed-panel'))
            self.assertEqual(broker.states['weather.default']['data']['location'], 'default')
            gate.set()
            await self.settle(lambda: not broker.queries)
            replies = [frame for frame in frames if frame['op'] == 'reply']
            self.assertEqual([frame['id'] for frame in replies], ['other-panel'])
            self.assertEqual(replies[0]['data']['location'], 'alternate')
            self.assertEqual(broker.states['weather.default']['data']['location'], 'default')
        finally:
            gate.set()
            await broker.close()

    async def test_ai_many_accounts_close_stops_queue_and_unloads_backend(self):
        specification = importlib.util.spec_from_file_location('test_ai_domain', SCRIPT.with_name('ai-domain.py'))
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        adapter = module.AiDomain.__new__(module.AiDomain)
        gate = threading.Event()
        calls = []
        def account(identifier, row):
            calls.append(row['id'])
            gate.wait(2)
            return dict(id=row['id'], windows=[dict(used=10)])
        adapter.backend = Mock(usage_accounts=lambda: [('claude', dict(id=str(index))) for index in range(100)],
                               collect_account=account, group_results=lambda results: dict(providers=list(results)))
        adapter.accounts = adapter.backend.usage_accounts()
        adapter.cached = lambda: dict(providers=[], updated=1)
        adapter.save = lambda data: data
        broker = broker_module.Broker(lambda frame: None)
        self.assertEqual(broker.domains, {}, 'AI backend must be absent before demand')
        broker.domains['ai'] = adapter
        try:
            for token in ('one', 'two'):
                broker.request(dict(v=1, op='subscribe', topic='ai.usage', token=token))
            await self.settle(lambda: len(calls) == 2)
            self.assertEqual(broker.states['ai.usage']['data']['updated'], 1, 'cache appears before provider jobs finish')
            broker.domains['power'] = Mock(read=lambda topic: dict(available=False))
            broker.request(dict(v=1, op='subscribe', topic='power.battery', token='power'))
            await self.settle(lambda: broker.states['power.battery']['status'] == 'ready')
            for token in ('one', 'two'):
                broker.request(dict(v=1, op='unsubscribe', topic='ai.usage', token=token))
            gate.set()
            await self.settle(lambda: broker.states['ai.usage']['task'] is None)
            self.assertEqual(len(calls), 2, 'closed panels must not start queued provider jobs')
            self.assertNotIn('ai', broker.domains, 'heavy AI backend released after last job drains')
            self.assertNotIn('claude', json.dumps(broker.diagnostics()))
        finally:
            gate.set()
            await broker.close()

    async def test_new_domain_import_failure_does_not_break_other_domains(self):
        for domain, topic in [('weather', 'weather.default'), ('ai', 'ai.usage')]:
            broker = broker_module.Broker(lambda frame: None)
            broker.domains['power'] = Mock(read=lambda topic: dict(available=False))
            original = broker.load_domain
            def load(name):
                if name == domain:
                    raise ImportError('private fixture text')
                return original(name)
            try:
                with patch.object(broker, 'load_domain', side_effect=load):
                    broker.request(dict(v=1, op='subscribe', topic=topic, token='bad'))
                    broker.request(dict(v=1, op='subscribe', topic='power.battery', token='good'))
                    await self.settle(lambda: all(broker.states[current]['task'] is None for current in (topic, 'power.battery')))
                self.assertEqual(broker.states[topic]['error'], 'read-failed')
                self.assertEqual(broker.states['power.battery']['status'], 'ready')
                self.assertNotIn('private', json.dumps(broker.diagnostics()))
            finally:
                await broker.close()

    async def test_ai_many_accounts_complete_in_order_with_offline_accounts_omitted(self):
        specification = importlib.util.spec_from_file_location('test_ai_domain', SCRIPT.with_name('ai-domain.py'))
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        adapter = module.AiDomain.__new__(module.AiDomain)
        adapter.accounts = [('claude', dict(id=str(index))) for index in range(60)]
        calls = []
        def collect(identifier, account):
            calls.append(account['id'])
            return None if int(account['id']) % 3 == 0 else dict(id=account['id'], windows=[dict(used=10)])
        adapter.backend = Mock(collect_account=collect, group_results=lambda results: dict(
            providers=[account for identifier, account in results if account is not None]))
        saved = []
        adapter.save = lambda data: saved.append(data) or data
        adapter.cached = lambda: dict(providers=[], updated=1)
        broker = broker_module.Broker(lambda frame: None)
        broker.domains['ai'] = adapter
        try:
            for token in ('screen-one', 'screen-two'):
                broker.request(dict(v=1, op='subscribe', topic='ai.usage', token=token))
            await self.settle(lambda: broker.states['ai.usage']['task'] is None)
            self.assertEqual(len(calls), 60, 'each account is queried once across screens')
            self.assertEqual(len(saved), 1)
            self.assertEqual([account['id'] for account in saved[0]['providers']],
                             [str(index) for index in range(60) if index % 3])
            self.assertEqual(broker.states['ai.usage']['status'], 'ready')
        finally:
            await broker.close()


class UpdatesSchedulingTests(unittest.IsolatedAsyncioTestCase):
    async def test_initial_delay_and_manual_refresh_during_scheduled_read(self):
        gate = threading.Event()
        calls = []
        def read(topic):
            calls.append(topic)
            gate.wait(2)
            return {'state': 'ready', 'count': 0}
        broker = broker_module.Broker(lambda frame: None, read)
        scheduler = None
        try:
            broker.request(dict(v=1, op='subscribe', topic='updates.status', token='shell'))
            state = broker.states['updates.status']
            self.assertAlmostEqual(state['due'] - broker.started, 45)
            self.assertIsNone(state['task'])
            broker.started -= 45
            state['due'] = 0
            scheduler = asyncio.create_task(broker.schedule())
            for attempt in range(100):
                if calls:
                    break
                await asyncio.sleep(.005)
            broker.request(dict(v=1, op='refresh', topic='updates.status', id='manual'))
            broker.request(dict(v=1, op='refresh', topic='updates.status', id='again'))
            self.assertTrue(state['pending'])
            self.assertEqual(len(calls), 1)
            gate.set()
            for attempt in range(100):
                if len(calls) == 2 and state['task'] is None:
                    break
                await asyncio.sleep(.005)
            self.assertEqual(len(calls), 2)
            self.assertEqual(state['status'], 'ready')
            self.assertEqual(state['due'], broker.started + 21600)
        finally:
            gate.set()
            if scheduler:
                scheduler.cancel()
                await asyncio.gather(scheduler, return_exceptions=True)
            await broker.close()

    async def test_broken_lazy_domain_does_not_stop_other_domains(self):
        for broken in ('network', 'power', 'capture', 'display'):
            broker = broker_module.Broker(lambda frame: None)
            original = broker_module.importlib.util.spec_from_file_location
            imports = []
            def specification(name, filename):
                imports.append(threading.current_thread().name)
                if name == 'bar_' + broken:
                    raise ImportError('fixture broken adapter')
                return original(name, filename)
            healthy = 'network' if broken != 'network' else 'power'
            topic = {'network': 'network.summary', 'power': 'power.battery',
                     'capture': 'capture.summary', 'display': 'display.topology'}[broken]
            broker.domains[healthy] = Mock()
            if healthy == 'network':
                broker.domains[healthy].read_state.return_value = {'devices': []}
            else:
                broker.domains[healthy].read.return_value = {'available': False}
            healthy_topic = 'network.summary' if healthy == 'network' else 'power.battery'
            try:
                with patch.object(broker_module.importlib.util, 'spec_from_file_location', side_effect=specification):
                    broker.request(dict(v=1, op='subscribe', topic=topic, token='broken'))
                    broker.request(dict(v=1, op='subscribe', topic=healthy_topic, token='healthy'))
                    for attempt in range(100):
                        if broker.states[topic]['task'] is None and broker.states[healthy_topic]['task'] is None:
                            break
                        await asyncio.sleep(.005)
                self.assertEqual(broker.states[topic]['status'], 'unavailable')
                self.assertEqual(broker.states[healthy_topic]['status'], 'ready')
                self.assertTrue(imports)
                self.assertTrue(all(name.startswith('bar-data') for name in imports))
            finally:
                await broker.close()

    async def test_updates_timeout_and_offline_retain_known_count_without_ready(self):
        gate = threading.Event()
        mode = 'ready'
        def read(topic):
            if mode == 'slow':
                gate.wait(1)
            return {'state': 'offline'} if mode == 'offline' else {'state': 'ready', 'count': 4}
        frames = []
        broker = broker_module.Broker(frames.append, read, timeout=.03)
        try:
            broker.request(dict(v=1, op='subscribe', topic='updates.status', token='shell'))
            for next_mode, expected_error in (('ready', ''), ('offline', 'offline'), ('slow', 'timeout')):
                mode = next_mode
                broker.refresh('updates.status')
                for attempt in range(100):
                    if broker.states['updates.status']['error'] == expected_error and (
                            expected_error == 'timeout' or broker.states['updates.status']['task'] is None):
                        break
                    await asyncio.sleep(.005)
                state = broker.states['updates.status']
                self.assertEqual(state['data']['count'], 4)
                self.assertEqual(state['error'], expected_error)
                self.assertEqual(state['status'], 'stale' if expected_error else 'ready')
                broker.request(dict(v=1, op='status', id='responsive'))
                self.assertEqual(frames[-1]['op'], 'status')
        finally:
            gate.set()
            await broker.close()

    async def test_early_manual_check_preserves_login_deadline(self):
        broker = broker_module.Broker(lambda frame: None, lambda topic: {'state': 'ready', 'count': 0})
        try:
            broker.request(dict(v=1, op='subscribe', topic='updates.status', token='shell'))
            broker.refresh('updates.status')
            await broker.states['updates.status']['task']
            self.assertEqual(broker.states['updates.status']['due'], broker.started + 45)
        finally:
            await broker.close()


class VmAcceptanceRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_update_adapter_retains_repo_updates_after_slow_check_and_empty_aur(self):
        import time
        broker = broker_module.Broker(lambda frame: None)
        commands = []
        entered = threading.Event()
        def command(arguments, **options):
            commands.append(arguments)
            self.assertEqual(options['timeout'], 120)
            self.assertEqual(options['env']['XDG_RUNTIME_DIR'], '/fixture/session-runtime')
            self.assertEqual(options['env']['EITR_TEST_SESSION'], 'inherited')
            self.assertEqual(options['env']['LC_ALL'], 'C')
            self.assertNotEqual(threading.current_thread(), threading.main_thread())
            if arguments == ['checkupdates']:
                self.assertEqual(options['env']['CHECKUPDATES_DB'], '/fixture/session-runtime/eitr-checkupdates-db')
                entered.set()
                time.sleep(5.1)
                return subprocess.CompletedProcess(arguments, 0,
                    'eitr-desktop 1 -> 2\nlinux 1 -> 2\nmesa 1 -> 2\n', '')
            if arguments[0] == 'pacman':
                self.assertEqual(arguments, ['pacman', '--dbpath', '/fixture/session-runtime/eitr-checkupdates-db',
                                            '-Si', 'eitr-desktop', 'linux', 'mesa'])
                return subprocess.CompletedProcess(arguments, 0, 'Download Size : 8527667 B\n', '')
            self.assertEqual(arguments, ['yay', '-Qua'])
            return subprocess.CompletedProcess(arguments, 1, '', '')
        try:
            with patch.dict(os.environ, XDG_RUNTIME_DIR='/fixture/session-runtime', EITR_TEST_SESSION='inherited'), \
                    patch.object(subprocess, 'run', side_effect=command), \
                    patch.object(shutil, 'which', return_value='/fixture/bin/yay'):
                broker.request(dict(v=1, op='subscribe', topic='updates.status', token='shell'))
                broker.refresh('updates.status')
                task = broker.states['updates.status']['task']
                for attempt in range(100):
                    if entered.is_set():
                        break
                    await asyncio.sleep(.005)
                self.assertTrue(entered.is_set())
                self.assertFalse(task.done())
                broker.request(dict(v=1, op='status', id='responsive-during-check'))
                await asyncio.wait_for(asyncio.shield(task), 10)
            state = broker.states['updates.status']
            self.assertEqual(state['status'], 'ready')
            self.assertEqual(state['error'], '')
            self.assertIsNotNone(broker.age(state))
            self.assertEqual(state['data'], {'state': 'ready', 'count': 3, 'repository': 3, 'aur': 0,
                                            'downloadBytes': 8527667})
            self.assertEqual(len(commands), 3)
        finally:
            await broker.close()

    async def test_imported_brightness_without_backlight_or_ddc_has_no_broker_error(self):
        broker = broker_module.Broker(lambda frame: None)
        try:
            loop = asyncio.get_running_loop()
            domain = await loop.run_in_executor(broker.executor, broker.load_domain, 'display')
            brightness = await loop.run_in_executor(broker.executor, domain.adapter, 'brightness')
            for error in (None, subprocess.CalledProcessError(1, ['ddcutil', 'getvcp', '10', '--brief']),
                          subprocess.TimeoutExpired('ddcutil', 8)):
                with self.subTest(error=error), patch.object(brightness, 'backlight', return_value=None), \
                        patch.object(brightness.shutil, 'which', return_value='/fixture/bin/ddcutil' if error else None), \
                        patch.object(brightness, 'run', side_effect=error):
                    broker.request(dict(v=1, op='subscribe', topic='display.brightness', token='panel'))
                    if broker.states['display.brightness']['task'] is None:
                        broker.refresh('display.brightness')
                    await broker.states['display.brightness']['task']
                    state = broker.states['display.brightness']
                    self.assertEqual(state['status'], 'ready')
                    self.assertEqual(state['error'], '')
                    self.assertEqual(state['data']['available'], False)
                    self.assertEqual(state['data']['kind'], '')
                    self.assertEqual(state['data']['value'], 0)
                    if error:
                        self.assertEqual(state['data']['name'], 'Brightness unavailable')
                        self.assertEqual(state['data']['error'], str(error))
        finally:
            await broker.close()
