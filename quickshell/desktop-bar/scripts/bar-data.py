#!/usr/bin/env python3
"""Bounded JSON-lines transport. Blocking domain adapters share a bounded thread pool."""
import asyncio
import json
import importlib.util
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import signal
import sys
import time
import uuid

MAX_FRAME = 262144
MAX_RESULT = MAX_FRAME // 2
INTERVALS = {"network.summary": 10, "network.details": 2, "network.latency": 15,
             "power.battery": 30, "power.profile": 5, "power.radios": 5,
             "capture.summary": 2, "capture.details": 2, "capture.options": float("inf")}


class Broker:
    def __init__(self, emit, reader=None, timeout=5):
        self.emit = emit
        spec = importlib.util.spec_from_file_location("capture_domain", Path(__file__).with_name("capture-domain.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.capture = module.CaptureDomain(self)
        spec = importlib.util.spec_from_file_location("power_domain", Path(__file__).with_name("power-domain.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.power = module.PowerDomain()
        self.periods = {}
        self.adapter = None
        self.reader = reader or self.read
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="bar-data")
        self.schedule_changed = asyncio.Event()
        self.epoch = uuid.uuid4().hex
        self.latency_interface = None
        self.tokens = {}
        self.actions = []
        self.action_task = None
        self.action_ids = set()
        self.action_history = deque()
        self.action_process = None
        self.action_timeouts = {"enterprise": 120, "connect": 60, "scan": 15, "airplane": 30, "profile": 20}
        self.jobs = set()
        self.states = {topic: dict(seq=0, status="loading", data={}, success=None, error="", task=None,
                                   pending=False, due=0, generation=0, durationMs=0, id="") for topic in INTERVALS}

    def read(self, topic):
        if topic.startswith("power."):
            return self.power.read(topic)
        if topic.startswith("capture."):
            return self.capture.read(topic)
        interface = ""
        if topic == "network.latency":
            devices = self.states["network.details"]["data"].get("devices", [])
            if not devices or devices[0].get("state") != "connected":
                return {"ping": None, "loss": None}
            interface = devices[0]["name"]
        return self.adapter.read_state({"network.summary": "icon", "network.details": "status",
                                        "network.latency": "probe"}[topic], interface)

    def wanted(self, topic):
        return topic in self.tokens.values()

    def scheduled(self, topic):
        if not self.wanted(topic):
            return False
        if topic == "capture.summary":
            return not self.wanted("capture.details") and (self.capture.has_window or self.states[topic]["data"].get("running", False))
        if topic in {"power.profile", "power.radios"} and self.action_task:
            return False
        return True

    def age(self, state):
        return None if state["success"] is None else int((time.monotonic() - state["success"]) * 1000)

    def snapshot(self, topic, token="", request=""):
        state = self.states[topic]
        self.emit(dict(v=1, op="state", topic=topic, token=token, id=request, epoch=self.epoch,
                       seq=state["seq"], status=state["status"], data=state["data"], ageMs=self.age(state),
                       error=state["error"]))

    def diagnostics(self):
        return {topic: dict(ageMs=self.age(state), lastError=state["error"],
                            inFlight=int(state["task"] is not None), pending=int(state["pending"]),
                            observers=list(self.tokens.values()).count(topic), durationMs=state["durationMs"],
                            id=state["id"]) for topic, state in self.states.items()}

    def refresh(self, topic, request=""):
        if not self.wanted(topic):
            return
        state = self.states[topic]
        if topic == "capture.details" and self.states["capture.summary"]["task"]:
            state["pending"] = True
            return
        if topic == "capture.summary" and self.states["capture.details"]["task"] and not self.wanted("capture.details"):
            state["pending"] = True
            return
        if topic == "capture.summary" and self.wanted("capture.details"):
            self.refresh("capture.details", request)
            return
        if topic.startswith("capture.") and self.capture.task:
            state["pending"] = True
            return
        if topic.startswith("power.") and topic != "power.battery" and self.action_task:
            state["pending"] = True
            return
        if topic == "network.latency" and self.states["network.details"]["success"] is None:
            return
        if state["task"]:
            state["pending"] = True
            return
        state["pending"] = False
        state["id"] = request
        state["task"] = asyncio.create_task(self.update(topic, state["generation"]))
        self.schedule_changed.set()
        self.jobs.add(state["task"])
        state["task"].add_done_callback(self.jobs.discard)

    def capture_summary(self, state):
        summary = self.states["capture.summary"]
        if state["status"] == "ready":
            summary.update(data={key: state["data"][key] for key in ("running", "ready", "recording", "paused", "streaming")},
                           success=state["success"], status="ready", error="")
        else:
            if "running" in state["data"]:
                summary["data"] = dict(summary["data"], running=state["data"]["running"])
            summary.update(status="stale" if summary["success"] is not None else "unavailable", error=state["error"])
        summary["seq"] += 1
        self.snapshot("capture.summary")

    async def update(self, topic, generation):
        state = self.states[topic]
        started = time.monotonic()
        timed_out = False
        try:
            if self.reader == self.read and self.adapter is None and topic.startswith("network."):
                spec = importlib.util.spec_from_file_location("wifi_popup", Path(__file__).with_name("wifi-popup.py"))
                adapter = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(adapter)
                self.adapter = adapter
            future = asyncio.get_running_loop().run_in_executor(self.executor, self.reader, topic)
            budget = 25 if topic == "capture.details" else 10 if topic == "capture.summary" else self.timeout
            try:
                result = await asyncio.wait_for(asyncio.shield(future), budget)
            except TimeoutError:
                timed_out = True
                if generation == state["generation"]:
                    state.update(status="stale" if state["success"] is not None else "unavailable", error="timeout")
                    state["seq"] += 1
                    self.snapshot(topic, request=state["id"])
                    if topic == "capture.details":
                        self.capture_summary(state)
                # The deadline cannot stop a thread. Keep this topic occupied until it returns.
                try:
                    await asyncio.shield(future)
                except Exception:
                    pass
                return
            if generation != state["generation"]:
                return
            if not isinstance(result, dict) or (topic.endswith("latency") and "ping" not in result) or (
                    topic.startswith("network.") and not topic.endswith("latency") and not isinstance(result.get("devices"), list)):
                raise ValueError("invalid-result")
            if len(json.dumps(result).encode()) > MAX_RESULT:
                raise ValueError("oversize-result")
            if topic in {"capture.summary", "capture.details"} and any(
                    type(result.get(key)) is not bool for key in ("running", "ready", "recording", "paused", "streaming")):
                raise ValueError("invalid-result")
            if topic in {"capture.summary", "capture.details"} and not result.get("ready"):
                state["data"] = dict(state["data"], running=result.get("running", True))
                raise ValueError("capture-unavailable")
            state.update(data=result, success=time.monotonic(), status="ready", error="")
        except asyncio.CancelledError:
            return
        except Exception as error:
            if generation != state["generation"]:
                return
            code = "timeout" if isinstance(error, TimeoutError) else "read-failed"
            state.update(status="stale" if state["success"] is not None else "unavailable", error=code)
        finally:
            state["task"] = None
            state["durationMs"] = int((time.monotonic() - started) * 1000)
            state["due"] = time.monotonic() + min([self.periods.get(token, INTERVALS[topic]) for token, subscribed in self.tokens.items() if subscribed == topic] or [INTERVALS[topic]])
            if (timed_out or generation != state["generation"]) and state["pending"] and self.wanted(topic):
                state["pending"] = False
                state["due"] = time.monotonic()
            self.schedule_changed.set()
        if generation != state["generation"]:
            return
        state["seq"] += 1
        self.snapshot(topic, request=state["id"])
        if topic == "capture.summary" and self.wanted("capture.details"):
            self.refresh("capture.details")
        if topic == "capture.details":
            self.capture_summary(state)
        if topic == "network.details":
            devices = state["data"].get("devices", [])
            interface = devices[0].get("name", "") if devices and devices[0].get("state") == "connected" else ""
            if interface != self.latency_interface or (self.states["network.latency"]["success"] is None
                                                      and self.states["network.latency"]["task"] is None):
                self.latency_interface = interface
                self.refresh("network.latency")
        if state["pending"]:
            state["pending"] = False
            self.refresh(topic)

    def action_state(self):
        for domain in ("network", "power"):
            self.emit(dict(v=1, op="domain", topic=domain, epoch=self.epoch,
                           busy=bool(self.action_task), name=self.actions[0]["name"] if self.actions else ""))

    def action_result(self, request, code="", message="", topic="network"):
        self.emit(dict(v=1, op="result", topic=topic, epoch=self.epoch,
                       id=request, error=code, message=message, busy=bool(self.action_task)))

    def enqueue_action(self, frame):
        request, name, args = frame.get("id"), frame.get("name"), frame.get("args")
        def reject(request, code):
            self.action_result(request, code, topic=frame.get("topic", "network"))
        if not request or request in self.action_ids or not isinstance(args, dict):
            reject(request or "", "invalid-request")
            return
        allowed = ("profile", "airplane") if frame.get("topic") == "power" else ("connect", "disconnect", "forget", "power", "scan")
        if name not in allowed:
            reject(request, "invalid-action")
            return
        if not isinstance(args.get("path", ""), str) or args.get("extra") not in (None, "true", "false"):
            reject(request, "invalid-request")
            return
        if name == "airplane" and args.get("extra") not in ("true", "false"):
            reject(request, "invalid-request")
            return
        if len(self.actions) >= 16:
            reject(request, "queue-full")
            return
        secret = args.get("input", {})
        if not isinstance(secret, dict) or any(not isinstance(value, str) for value in secret.values()):
            reject(request, "invalid-request")
            return
        if len(self.action_history) >= 256:
            self.action_ids.discard(self.action_history.popleft())
        self.action_history.append(request)
        self.action_ids.add(request)
        if name == "profile" and args.get("path") not in ("power-saver", "balanced", "performance"):
            self.action_result(request, "invalid-request", topic=frame.get("topic", "network"))
            return
        self.actions.append(frame)
        if self.action_task is None:
            self.action_task = asyncio.create_task(self.run_actions())
            self.jobs.add(self.action_task)
            self.action_task.add_done_callback(self.jobs.discard)
        self.action_state()

    async def run_actions(self):
        try:
            while self.actions:
                frame = self.actions[0]
                for topic in ("network.summary", "network.details", "power.profile", "power.radios"):
                    self.states[topic]["generation"] += 1
                args, name = frame["args"], frame["name"]
                secret = args.pop("input", {})
                budget = self.action_timeouts.get("enterprise" if name == "connect" and secret.get("identity") else name, 10)
                command = [sys.executable, str(Path(__file__).with_name("wifi-popup.py")), name, args.get("path", "")]
                if name == "profile":
                    command = [sys.executable, str(Path(__file__).with_name("power-profile.py")), "set", args["path"]]
                if name == "airplane":
                    command = [sys.executable, str(Path(__file__).with_name("airplane.py")), "set"]
                if args.get("extra") is not None:
                    command.append(args["extra"])
                code = ""
                message = ""
                process = None
                try:
                    process = await asyncio.create_subprocess_exec(*command, stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, start_new_session=True,
                        limit=MAX_RESULT, env=dict(os.environ, EITR_BAR_ACTION="1"))
                    self.action_process = process
                    payload = (json.dumps(secret) + "\n").encode()
                    secret = None
                    async def exchange():
                        process.stdin.write(payload)
                        await process.stdin.drain()
                        process.stdin.close()
                        output = bytearray()
                        while True:
                            chunk = await process.stdout.read(min(8192, MAX_RESULT + 1 - len(output)))
                            if not chunk:
                                break
                            output.extend(chunk)
                            if len(output) > MAX_RESULT:
                                raise ValueError("oversize-result")
                        await process.wait()
                        return json.loads(output)
                    result = await asyncio.wait_for(exchange(), budget)
                    payload = None
                    if not isinstance(result, dict):
                        code = "outcome-unknown"
                    elif process.returncode or result.get("error"):
                        code = result.get("code", "action-failed")
                        message = result.get("message", "")
                except TimeoutError:
                    code = "outcome-unknown"
                except asyncio.CancelledError:
                    raise
                except Exception:
                    code = "backend-unavailable" if process is None else "outcome-unknown"
                finally:
                    secret = None
                    payload = None
                    if process is not None and process.returncode is None:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        await process.wait()
                    self.action_process = None
                self.action_result(frame["id"], code, message, frame.get("topic", "network"))
                self.actions.pop(0)
                for topic in ("network.details", "network.summary", "power.profile", "power.radios"):
                    self.states[topic]["generation"] += 1
                    self.refresh(topic)
                self.action_state()
        finally:
            self.actions.clear()
            self.action_task = None
            for topic in ("power.profile", "power.radios"):
                self.states[topic]["due"] = 0
            self.schedule_changed.set()
            self.action_state()

    def request(self, frame):
        if not isinstance(frame, dict) or type(frame.get("v")) is not int or frame["v"] != 1:
            raise ValueError("invalid-version")
        request = frame.get("id", "")
        if not isinstance(request, str) or len(request) > 128:
            raise ValueError("invalid-id")
        operation, topic = frame.get("op"), frame.get("topic")
        self.schedule_changed.set()
        if operation == "status":
            self.emit(dict(v=1, op="status", epoch=self.epoch, id=frame.get("id", ""), data=self.diagnostics()))
            return
        if operation == "presence" and topic == "capture":
            if type(frame.get("present")) is not bool:
                raise ValueError("invalid-presence")
            self.capture.has_window = frame["present"]
            self.refresh("capture.summary")
            return
        if operation == "action" and topic == "capture":
            self.capture.enqueue(frame)
            return
        if operation == "action" and topic == "power":
            self.enqueue_action(frame)
            return
        if operation == "action" and topic == "network":
            self.enqueue_action(frame)
            return
        if topic not in self.states:
            raise ValueError("invalid-topic")
        token = frame.get("token")
        if operation == "subscribe":
            if not isinstance(token, str) or not token or len(token) > 128 or len(self.tokens) >= 256:
                raise ValueError("invalid-token")
            if token in self.tokens and self.tokens[token] != topic:
                raise ValueError("token-conflict")
            fresh = token not in self.tokens
            self.tokens[token] = topic
            if topic == "power.profile":
                self.periods[token] = 3 if frame.get("interval") == 3 else 5
            self.action_state()
            self.capture.state()
            self.snapshot(topic, token)
            if fresh and not self.states[topic]["task"]:
                self.refresh(topic)
        elif operation == "unsubscribe":
            if self.tokens.get(token) == topic:
                del self.tokens[token]
                self.periods.pop(token, None)
            if not self.wanted(topic):
                state = self.states[topic]
                state["generation"] += 1
                state["pending"] = False
        elif operation == "refresh":
            request = frame.get("id", "")
            if not isinstance(request, str) or len(request) > 128:
                raise ValueError("invalid-id")
            self.refresh(topic, request)
        else:
            raise ValueError("invalid-operation")

    async def schedule(self):
        while True:
            self.schedule_changed.clear()
            now = time.monotonic()
            for topic, state in self.states.items():
                if self.scheduled(topic) and not state["task"] and not (topic.startswith("capture.") and self.capture.task) and now >= state["due"]:
                    self.refresh(topic)
            due = [state["due"] for topic, state in self.states.items()
                   if self.scheduled(topic) and not state["task"] and not (topic.startswith("capture.") and self.capture.task)
                   and not (topic == "capture.details" and self.states["capture.summary"]["task"])
                   and not (topic == "capture.summary" and self.states["capture.details"]["task"])
                   and (topic != "network.latency" or self.states["network.details"]["success"] is not None)]
            delay = max(0, min(due) - time.monotonic()) if due else None
            try:
                await asyncio.wait_for(self.schedule_changed.wait(), delay)
            except TimeoutError:
                pass

    async def close(self):
        tasks = list(self.jobs)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.actions.clear()
        self.action_task = None
        self.executor.shutdown(wait=False, cancel_futures=True)


async def main():
    queue = asyncio.Queue(maxsize=64)
    def emit(frame):
        try:
            queue.put_nowait((json.dumps(frame, separators=(",", ":")) + "\n").encode())
        except asyncio.QueueFull:
            raise SystemExit("output-backpressure")
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout.buffer)
    writer = asyncio.StreamWriter(transport, protocol, None, loop)
    async def output():
        while True:
            writer.write(await queue.get())
            await writer.drain()
    main_task = asyncio.current_task()
    loop.add_signal_handler(signal.SIGTERM, main_task.cancel)
    broker = Broker(emit)
    emit(dict(v=1, op="hello", epoch=broker.epoch))
    reader = asyncio.StreamReader(limit=MAX_FRAME)
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin.buffer)
    tasks = [asyncio.create_task(output()), asyncio.create_task(broker.schedule())]
    buffer = bytearray()
    discarding = False
    try:
        while True:
            chunk = await reader.read(8192)
            if not chunk:
                break
            for byte in chunk:
                if byte == 10:
                    if discarding:
                        discarding = False
                    else:
                        try:
                            broker.request(json.loads(buffer))
                        except (ValueError, UnicodeError, TypeError, RecursionError):
                            emit(dict(v=1, op="error", epoch=broker.epoch, error="invalid-frame"))
                    buffer.clear()
                elif not discarding:
                    buffer.append(byte)
                    if len(buffer) > MAX_FRAME:
                        buffer.clear()
                        discarding = True
                        emit(dict(v=1, op="error", epoch=broker.epoch, error="oversize-frame"))
    finally:
        await broker.close()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
