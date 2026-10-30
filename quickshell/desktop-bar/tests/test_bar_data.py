"""Headless broker tests: no network, session bus, or credentials."""
import asyncio
import importlib.util
import json
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
            'DesktopData.qml', 'DesktopDataProtocol.js', 'scripts/bar-data.py']]
        layout = Layout(root)
        layout.files = lambda: files
        with tempfile.TemporaryDirectory() as directory:
            layout.stage(Path(directory))
            for relative in files:
                target = Path(directory) / relative
                self.assertTrue(layout.classify(relative)['runtime'])
                self.assertEqual(target.read_bytes(), (root / relative).read_bytes())
                if relative.endswith('.py'):
                    self.assertTrue(target.stat().st_mode & 0o111)


if __name__ == '__main__':
    unittest.main()
