#!/usr/bin/env python3
"""Bounded JSON-lines transport. Blocking network adapters share a bounded thread pool."""
import asyncio
import json
import importlib.util
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import signal
import sys
import time
import uuid

MAX_FRAME = 262144
MAX_RESULT = MAX_FRAME // 2
INTERVALS = {"network.summary": 10, "network.details": 2, "network.latency": 15}


class Broker:
    def __init__(self, emit, reader=None, timeout=5):
        self.emit = emit
        self.adapter = None
        self.reader = reader or self.read
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="bar-data")
        self.schedule_changed = asyncio.Event()
        self.epoch = uuid.uuid4().hex
        self.latency_interface = None
        self.tokens = {}
        self.jobs = set()
        self.states = {topic: dict(seq=0, status="loading", data={}, success=None, error="", task=None,
                                   pending=False, due=0, generation=0, durationMs=0, id="") for topic in INTERVALS}

    def read(self, topic):
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
        state = self.states[topic]
        if topic == "network.latency" and self.states["network.details"]["success"] is None:
            return
        if not self.wanted(topic):
            return
        if state["task"]:
            state["pending"] = True
            return
        state["id"] = request
        state["task"] = asyncio.create_task(self.update(topic, state["generation"]))
        self.schedule_changed.set()
        self.jobs.add(state["task"])
        state["task"].add_done_callback(self.jobs.discard)

    async def update(self, topic, generation):
        state = self.states[topic]
        started = time.monotonic()
        timed_out = False
        try:
            if self.reader == self.read and self.adapter is None:
                spec = importlib.util.spec_from_file_location("wifi_popup", Path(__file__).with_name("wifi-popup.py"))
                adapter = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(adapter)
                self.adapter = adapter
            future = asyncio.get_running_loop().run_in_executor(self.executor, self.reader, topic)
            try:
                result = await asyncio.wait_for(asyncio.shield(future), self.timeout)
            except TimeoutError:
                timed_out = True
                if generation == state["generation"]:
                    state.update(status="stale" if state["success"] is not None else "unavailable", error="timeout")
                    state["seq"] += 1
                    self.snapshot(topic, request=state["id"])
                # The deadline cannot stop a thread. Keep this topic occupied until it returns.
                try:
                    await asyncio.shield(future)
                except Exception:
                    pass
                return
            if generation != state["generation"]:
                return
            if not isinstance(result, dict) or (topic.endswith("latency") and "ping" not in result) or (
                    not topic.endswith("latency") and not isinstance(result.get("devices"), list)):
                raise ValueError("invalid-result")
            if len(json.dumps(result).encode()) > MAX_RESULT:
                raise ValueError("oversize-result")
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
            state["due"] = time.monotonic() + INTERVALS[topic]
            if timed_out and state["pending"] and self.wanted(topic):
                state["pending"] = False
                state["due"] = time.monotonic()
            self.schedule_changed.set()
        if generation != state["generation"]:
            return
        state["seq"] += 1
        self.snapshot(topic, request=state["id"])
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
            self.snapshot(topic, token)
            if fresh:
                self.refresh(topic)
        elif operation == "unsubscribe":
            if self.tokens.get(token) == topic:
                del self.tokens[token]
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
                if self.wanted(topic) and not state["task"] and now >= state["due"]:
                    self.refresh(topic)
            due = [state["due"] for topic, state in self.states.items()
                   if self.wanted(topic) and not state["task"]
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
