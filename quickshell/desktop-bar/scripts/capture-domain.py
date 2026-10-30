"""OBS adapter and ordered, non-replaying capture actions for the data broker."""
import asyncio
from collections import deque
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import threading


class CaptureDomain:
    def __init__(self, broker):
        self.broker = broker
        self.adapter = None
        self.adapter_lock = threading.Lock()
        self.has_window = False
        self.queue = deque()
        self.history = deque(maxlen=256)
        self.task = None

    def read(self, topic):
        with self.adapter_lock:
            if self.adapter is None:
                spec = importlib.util.spec_from_file_location("capture_obs", Path(__file__).with_name("obs-control.py"))
                self.adapter = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.adapter)
        if topic == "capture.options":
            return self.adapter.capture_options()
        return self.adapter.details() if topic == "capture.details" else self.adapter.status()

    def state(self):
        self.broker.emit(dict(v=1, op="domain", topic="capture", epoch=self.broker.epoch,
                              busy=bool(self.task), name=self.queue[0]["name"] if self.queue else ""))

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
