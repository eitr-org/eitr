"""Bounded line transport for approved plugin streams, with process-group cleanup."""
import contextlib
import ctypes
import os
import selectors
import signal
import subprocess
import time

MAX_LINE = 4096
MAX_RATE = 60


class Lines:
    def __init__(self):
        self.pending = bytearray()
        self.discarding = False
        self.window = 0
        self.count = 0

    def feed(self, chunk, now):
        if now - self.window >= 1:
            self.window, self.count = now, 0
        accepted = []
        parts = chunk.split(b'\n')
        for index, segment in enumerate(parts):
            ended = index < len(parts) - 1
            part = segment + (b'\n' if ended else b'')
            if not self.discarding:
                self.pending.extend(part)
                if len(self.pending) > MAX_LINE + (1 if ended else 0):
                    self.pending.clear()
                    self.discarding = True
            if ended:
                if not self.discarding and self.count < MAX_RATE:
                    accepted.append(self.pending[:-1].decode('utf-8', errors='replace'))
                    self.count += 1
                self.pending.clear()
                self.discarding = False
        return accepted


def supervise_stream(argv, root, parent):
    # The reaper survives even a SIGKILL of the QML-owned launcher.
    ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGTERM, 0, 0, 0)
    stopping = False
    def stop(signum, frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    if os.getppid() != parent:
        return
    process = subprocess.Popen(argv, cwd=root, start_new_session=True, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        parser = Lines()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while not stopping:
                if not selector.select(.25):
                    if process.poll() is not None:
                        break
                    continue
                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                for line in parser.feed(chunk, time.monotonic()):
                    print(line, flush=True)
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        process.stdout.close()


def run_stream(argv, root):
    parent = os.getpid()
    supervisor = os.fork()
    if supervisor == 0:
        try:
            supervise_stream(argv, root, parent)
        finally:
            os._exit(0)
    def stop(signum, frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        os.waitpid(supervisor, 0)
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.kill(supervisor, signal.SIGTERM)
        with contextlib.suppress(ChildProcessError):
            os.waitpid(supervisor, 0)
