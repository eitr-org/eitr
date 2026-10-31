#!/usr/bin/env python3
"""Bounded JSON-lines transport. Blocking domain adapters share a bounded thread pool."""
import asyncio
import json
import importlib.util
from collections import OrderedDict, deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import signal
import sys
import time
import threading
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bar_data_topics import INTERVALS, MAX_FRAME, MAX_RESULT, TOPICS, validate_result


class OutputBuffer:
    """Coalesce snapshots; pause input while reliable replies drain.

    Above the input high-water mark only already-admitted work can emit:
    at most 16 network/power results, 16 capture results, 8 weather replies,
    one broadcast per topic and three domain states. No producer tasks are
    created for output, and the pipe writer holds only one additional frame.
    """
    def __init__(self):
        self.frames = OrderedDict()
        self.sequence = 0
        self.available = asyncio.Event()
        self.room = asyncio.Event()
        self.room.set()

    def emit(self, frame):
        if frame["op"] in {"state", "domain"}:
            key = (frame["op"], frame.get("topic", ""), frame.get("token", ""))
        else:
            self.sequence += 1
            key = self.sequence
        self.frames[key] = (json.dumps(frame, separators=(",", ":")) + "\n").encode()
        self.available.set()
        if len(self.frames) >= 64:
            self.room.clear()

    async def get(self):
        await self.available.wait()
        _, frame = self.frames.popitem(last=False)
        if not self.frames:
            self.available.clear()
        if len(self.frames) < 64:
            self.room.set()
        return frame

    async def writable(self):
        await self.room.wait()


class CaptureController:
    def __init__(self, broker):
        self.broker = broker
        self.has_window = False
        self.queue = deque()
        self.history = deque(maxlen=256)
        self.task = None

    def state(self):
        self.broker.domain_state("capture", bool(self.task), self.queue[0]["name"] if self.queue else "")

    def result(self, request, error="", message=""):
        self.broker.emit(dict(v=1, op="result", topic="capture", epoch=self.broker.epoch,
                              id=request, error=error, message=message, busy=bool(self.task)))

    def enqueue(self, frame):
        request, name, args = frame.get("id"), frame.get("name"), frame.get("args")
        allowed = {"record", "stop", "pause", "resume", "stream", "stop-stream", "prepare",
                   "chapter", "mic-mute", "mic-unmute", "camera-on", "camera-off", "scene", "open", "folder", "set-option"}
        if not request or request in self.history or not isinstance(args, dict):
            self.result(request or "", "invalid-request")
            return
        if name not in allowed or not isinstance(args.get("argument", ""), str):
            self.result(request, "invalid-action")
            return
        if name == "set-option" and (args.get("key") not in {"audio", "mic", "webcam"} or type(args.get("enabled")) is not bool):
            self.result(request, "invalid-request")
            return
        if len(self.queue) >= 16:
            self.result(request, "queue-full")
            return
        self.history.append(request)
        self.queue.append(frame)
        if self.task is None:
            self.task = asyncio.create_task(self.run())
            self.broker.jobs.add(self.task)
            self.task.add_done_callback(self.broker.jobs.discard)
        self.state()

    async def run(self):
        try:
            while self.queue:
                frame = self.queue[0]
                for topic in ("capture.summary", "capture.details"):
                    self.broker.states[topic]["generation"] += 1
                process = None
                error, message = "", ""
                try:
                    command = [sys.executable, str(Path(__file__).with_name("obs-control.py")), frame["name"]]
                    if frame["name"] == "set-option":
                        command.extend([frame["args"]["key"], str(frame["args"]["enabled"]).lower()])
                    argument = frame["args"].get("argument", "")
                    if argument:
                        command.append(argument)
                    process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.DEVNULL, start_new_session=True,
                        env=dict(os.environ, EITR_BAR_ACTION="1"))
                    async def exchange():
                        output = bytearray()
                        while True:
                            chunk = await process.stdout.read(8192)
                            if not chunk:
                                break
                            output.extend(chunk)
                            if len(output) > 131072:
                                raise ValueError("oversize-result")
                        await process.wait()
                        return output.decode().strip()
                    # Stop's obs-cmd call retains its 30 s deadline; allow bounded
                    # time for saved-file notification and idle-window cleanup.
                    budget = 45 if frame["name"] in {"stop", "stop-stream"} else 90 if frame["name"] == "prepare" else 30
                    output = await asyncio.wait_for(exchange(), budget)
                    if process.returncode:
                        result = json.loads(output)
                        if not isinstance(result, dict) or result.get("error") not in {"action-failed", "outcome-unknown"}:
                            raise ValueError("invalid-result")
                        error, message = result["error"], result.get("message", "")
                        if not isinstance(message, str):
                            raise ValueError("invalid-result")
                except asyncio.CancelledError:
                    raise
                except Exception:
                    error = "outcome-unknown" if process else "backend-unavailable"
                finally:
                    if process is not None and process.returncode is None:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        await process.wait()
                self.result(frame["id"], error, message)
                self.queue.popleft()
                if error == "outcome-unknown":
                    for topic in ("capture.summary", "capture.details"):
                        state = self.broker.states[topic]
                        state.update(status="stale" if state["success"] is not None else "unavailable", error=error)
                        state["seq"] += 1
                        self.broker.snapshot(topic)
                    while self.queue:
                        self.result(self.queue.popleft()["id"], "outcome-unknown")
                for topic in ("capture.details", "capture.summary", "capture.options"):
                    self.broker.states[topic]["generation"] += 1
                    self.broker.refresh(topic)
                self.state()
        finally:
            self.queue.clear()
            self.task = None
            for topic in ("capture.details", "capture.summary", "capture.options"):
                self.broker.states[topic]["due"] = 0
            self.broker.schedule_changed.set()
            self.state()


class Broker:
    def __init__(self, emit, reader=None, timeout=5):
        self.emit = emit
        self.closing = False
        self.capture = CaptureController(self)
        self.domains = {}
        self.domain_jobs = {}
        self.read_slots = {name: asyncio.Semaphore(2) for name in ("network", "capture", "power", "display", "hardware", "remote", "weather", "ai", "updates")}
        self.domain_locks = {name: threading.Lock() for name in ("network", "capture", "power", "display", "hardware", "remote", "weather", "ai", "updates")}
        self.read_slots["weather"] = asyncio.Semaphore(1)
        self.ai_cooldowns = {}
        self.queries = {}
        self.query_history = deque(maxlen=256)
        self.periods = {}
        self.adapter = None
        self.reader = reader or self.read
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="bar-data")
        self.schedule_changed = asyncio.Event()
        self.epoch = uuid.uuid4().hex
        self.domain_states = {}
        self.latency_interface = None
        self.tokens = {}
        self.actions = []
        self.action_task = None
        self.action_ids = set()
        self.action_history = deque()
        self.action_process = None
        self.action_timeouts = {"enterprise": 120, "connect": 60, "scan": 15, "airplane": 30, "profile": 20}
        self.jobs = set()
        self.started = time.monotonic()
        self.states = {topic: dict(seq=0, status="loading", data={}, success=None, error="", task=None,
                                   pending=False, due=0, generation=0, durationMs=0, id="") for topic in INTERVALS}
        self.states["updates.status"]["due"] = self.started + 45

    def load_domain(self, name):
        with self.domain_locks[name]:
            if name not in self.domains:
                filename = "wifi-popup.py" if name == "network" else "updates.py" if name == "updates" else name + "-domain.py"
                spec = importlib.util.spec_from_file_location("bar_" + name, Path(__file__).with_name(filename))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.domains[name] = module if name == "network" else getattr(module, name.title() + "Domain")()
                if name == "ai":
                    self.domains[name].backend.COOLDOWNS = self.ai_cooldowns
            return self.domains[name]

    @property
    def power(self):
        return self.load_domain("power")

    @property
    def display(self):
        return self.load_domain("display")

    @display.setter
    def display(self, value):
        self.domains["display"] = value

    def read(self, topic):
        domain = TOPICS[topic].domain
        if domain != "network":
            return self.load_domain(domain).read(topic)
        if self.adapter is None:
            self.adapter = self.load_domain("network")
        interface = ""
        if topic == "network.latency":
            devices = self.states["network.details"]["data"].get("devices", [])
            if not devices or devices[0].get("state") != "connected":
                return {"ping": None, "loss": None}
            interface = devices[0]["name"]
        return self.adapter.read_state({"network.summary": "icon", "network.details": "status",
                                        "network.latency": "probe"}[topic], interface)

    async def read_in_pool(self, topic, deadline):
        if self.closing:
            return {}
        loop = asyncio.get_running_loop()
        domain = TOPICS[topic].domain
        if self.reader == self.read and domain not in self.domains and not (domain == "network" and self.adapter is not None):
            # Share initialization before submitting reads, so sibling topics cannot
            # occupy pool threads waiting for a slow domain's import lock.
            if domain not in self.domain_jobs:
                self.domain_jobs[domain] = loop.run_in_executor(self.executor, self.load_domain, domain)
            future = self.domain_jobs[domain]
            try:
                await asyncio.wait([future])
                future.result()
            finally:
                if future.done():
                    self.domain_jobs.pop(domain, None)
        if topic == "ai.usage" and self.reader == self.read:
            generation = self.states[topic]["generation"]
            adapter = self.domains["ai"]
            cached = await loop.run_in_executor(self.executor, adapter.cached)
            state = self.states[topic]
            try:
                validate_result(topic, cached)
            except ValueError:
                pass
            else:
                if self.wanted(topic) and generation == state["generation"] and loop.time() < deadline:
                    state.update(data=cached, status="ready", success=time.monotonic())
                    state["seq"] += 1
                    self.snapshot(topic)
            return cached
        async with self.read_slots[domain]:
            # refresh() already admitted this read while observed. A later close
            # invalidates its result in update(), without retracting the read.
            if self.closing or loop.time() >= deadline:
                return {}
            return await loop.run_in_executor(self.executor, self.reader, topic)

    def wanted(self, topic):
        return topic in self.tokens.values()

    def scheduled(self, topic):
        if not self.wanted(topic):
            return False
        if topic == "display.brightness" and self.states[topic]["data"].get("kind") == "ddc":
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
                       error=state["error"], **({"inFlight": bool(state["task"]), "pending": state["pending"]}
                                              if topic.startswith(("remote.", "ai.", "weather.", "updates.")) else {})))

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
            if topic.startswith(("remote.", "ai.", "weather.", "updates.")):
                self.snapshot(topic)
            return
        state["pending"] = False
        state["id"] = request
        state["task"] = asyncio.create_task(self.update(topic, state["generation"]))
        self.schedule_changed.set()
        if topic.startswith(("remote.", "ai.", "weather.", "updates.")):
            self.snapshot(topic)
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
            budget = TOPICS[topic].budget(self.timeout)
            future = asyncio.create_task(self.read_in_pool(topic, asyncio.get_running_loop().time() + budget))
            future.add_done_callback(lambda completed: completed.exception() if not completed.cancelled() else None)
            try:
                done, _ = await asyncio.wait([future], timeout=budget)
                if not done:
                    raise TimeoutError()
                result = future.result()
                if topic == "ai.usage" and self.reader == self.read and generation == state["generation"]:
                    adapter = self.domains["ai"]
                    budget = max(30, 25 * ((len(adapter.accounts) + 1) // 2))
                    if self.timeout < 5:
                        budget = min(budget, self.timeout)
                    future = asyncio.create_task(adapter.collect(self.executor,
                        lambda: self.wanted(topic) and generation == state["generation"],
                        asyncio.get_running_loop().time() + budget))
                    future.add_done_callback(lambda completed: completed.exception() if not completed.cancelled() else None)
                    done, _ = await asyncio.wait([future], timeout=budget)
                    if not done:
                        raise TimeoutError()
                    result = future.result()
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
                    await asyncio.wait([future])
                    future.result()
                except Exception:
                    pass
                return
            if generation != state["generation"]:
                return
            validate_result(topic, result)
            if topic in {"capture.summary", "capture.details"} and not result.get("ready"):
                state["data"] = dict(state["data"], running=result.get("running", True))
                raise ValueError("capture-unavailable")
            if topic == "updates.status" and result.get("state") != "ready":
                raise ValueError("offline" if result.get("state") == "offline" else "updates-unavailable")
            state.update(data=result, success=time.monotonic(), status="ready", error="")
        except asyncio.CancelledError:
            return
        except Exception as error:
            if generation != state["generation"]:
                return
            code = "timeout" if isinstance(error, TimeoutError) else "offline" if topic == "updates.status" and str(error) == "offline" else "read-failed"
            state.update(status="stale" if state["success"] is not None else "unavailable", error=code)
        finally:
            state["task"] = None
            state["durationMs"] = int((time.monotonic() - started) * 1000)
            state["due"] = time.monotonic() + min([self.periods.get(token, INTERVALS[topic]) for token, subscribed in self.tokens.items() if subscribed == topic] or [INTERVALS[topic]])
            if topic == "updates.status":
                elapsed = time.monotonic() - self.started
                state["due"] = self.started + (45 if elapsed < 45 else (int(elapsed // 21600) + 1) * 21600)
            if topic == "weather.default":
                expiry = getattr(self.domains.get("weather"), "next_refresh", None)
                if isinstance(expiry, (int, float)):
                    state["due"] = max(time.monotonic(), expiry)
            if (timed_out or generation != state["generation"]) and state["pending"] and self.wanted(topic):
                state["pending"] = False
                state["due"] = time.monotonic()
            self.release_ai()
            self.schedule_changed.set()
            if timed_out and topic.startswith("remote.") and generation == state["generation"]:
                self.snapshot(topic, request=state["id"])
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

    def domain_state(self, topic, busy, name):
        current = (busy, name)
        if self.domain_states.get(topic) == current:
            return
        self.domain_states[topic] = current
        self.emit(dict(v=1, op="domain", topic=topic, epoch=self.epoch, busy=busy, name=name))

    def action_state(self):
        for domain in ("network", "power"):
            self.domain_state(domain, bool(self.action_task), self.actions[0]["name"] if self.actions else "")

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

    def release_ai(self):
        if not self.wanted("ai.usage") and not self.states["ai.usage"]["task"]:
            self.domains.pop("ai", None)

    async def query_weather(self, frame, cancelled):
        request = frame["id"]
        error, result = "", {}
        loop = asyncio.get_running_loop()
        deadline = loop.time() + 17
        def read():
            if cancelled.is_set() or time.monotonic() >= deadline:
                return {}
            adapter = self.load_domain("weather")
            if cancelled.is_set():
                return {}
            if frame["name"] == "search":
                return adapter.search(frame["args"]["query"], deadline)
            return adapter.weather(frame["args"]["city"], deadline=deadline)
        async def admitted():
            async with self.read_slots["weather"]:
                return await loop.run_in_executor(self.executor, read)
        future = asyncio.create_task(admitted())
        try:
            done, _ = await asyncio.wait([future], timeout=17)
            if not done:
                error = "timeout"
                cancelled.set()
            else:
                result = future.result()
                if len(json.dumps(result).encode()) > MAX_RESULT:
                    raise ValueError("oversize-result")
        except Exception:
            error = "read-failed"
        if not cancelled.is_set() or error:
            self.emit(dict(v=1, op="reply", topic="weather", id=request, epoch=self.epoch,
                           error=error, data=result))
        # Hold the admission slot until a timed out worker actually drains.
        if not future.done():
            await asyncio.wait([future])
            try:
                future.result()
            except Exception:
                pass
        self.queries.pop(request, None)

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
        if operation == "cancel" and topic == "weather":
            if request in self.queries:
                self.queries[request].set()
            return
        if operation == "query" and topic == "weather":
            args, name = frame.get("args"), frame.get("name")
            if len(self.queries) >= 8:
                self.emit(dict(v=1, op="reply", topic="weather", id=request, epoch=self.epoch,
                               error="busy", data={}))
                return
            if not request or request in self.query_history or not isinstance(args, dict):
                raise ValueError("invalid-query")
            if name == "search":
                if not isinstance(args.get("query"), str) or not 2 <= len(args["query"]) <= 200:
                    raise ValueError("invalid-query")
            elif name == "city":
                city = args.get("city")
                if not isinstance(city, dict) or not isinstance(city.get("name"), str) or any(
                        type(city.get(key)) not in (int, float) or not -limit <= city[key] <= limit
                        for key, limit in (("latitude", 90), ("longitude", 180))):
                    raise ValueError("invalid-query")
            else:
                raise ValueError("invalid-query")
            self.query_history.append(request)
            cancelled = threading.Event()
            self.queries[request] = cancelled
            task = asyncio.create_task(self.query_weather(frame, cancelled))
            self.jobs.add(task)
            task.add_done_callback(self.jobs.discard)
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
            was_wanted = self.wanted(topic)
            self.tokens[token] = topic
            if topic in {"power.profile", "display.brightness", "display.nightlight"}:
                self.periods[token] = 3 if frame.get("interval") == 3 else 5
            self.action_state()
            self.capture.state()
            self.snapshot(topic, token)
            if fresh and topic != "updates.status" and (not self.states[topic]["task"] or not was_wanted):
                self.refresh(topic)
        elif operation == "unsubscribe":
            if self.tokens.get(token) == topic:
                del self.tokens[token]
                self.periods.pop(token, None)
            if not self.wanted(topic):
                state = self.states[topic]
                state["generation"] += 1
                state["pending"] = False
                self.release_ai()
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
        self.closing = True
        self.tokens.clear()
        for cancelled in self.queries.values():
            cancelled.set()
        self.periods.clear()
        tasks = list(self.jobs)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.actions.clear()
        self.action_task = None
        self.executor.shutdown(wait=False, cancel_futures=True)


async def main():
    queue = OutputBuffer()
    emit = queue.emit
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
                    await queue.writable()
                    if discarding:
                        discarding = False
                    else:
                        try:
                            broker.request(json.loads(buffer))
                        except (ValueError, UnicodeError, TypeError, RecursionError):
                            emit(dict(v=1, op="error", epoch=broker.epoch, error="invalid-frame"))
                    buffer.clear()
                    await asyncio.sleep(0)
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
