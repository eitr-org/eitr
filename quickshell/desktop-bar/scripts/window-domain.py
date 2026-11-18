"""Active window inspection and Hyprland dispatch actions for Control Center."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

for parent in Path(__file__).resolve().parents:
    library = parent / "distro/lib" if (parent / "distro/lib/eitr_paths.py").is_file() else parent / "lib"
    if (library / "eitr_paths.py").is_file():
        if str(library) not in sys.path:
            sys.path.insert(0, str(library))
        break

from eitr_focus import lua
from eitr_workspaces import preferences as workspace_preferences

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]+$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


def normalize_address(value):
    text = str(value or "").strip()
    if text and not text.startswith("0x") and re.fullmatch(r"[0-9a-fA-F]+", text):
        text = "0x" + text
    return text.lower() if ADDRESS_RE.fullmatch(text) else ""


def format_client(client, process_name):
    if not isinstance(client, dict) or not normalize_address(client.get("address")):
        return None
    ws = client.get("workspace") if isinstance(client.get("workspace"), dict) else {}
    at = client.get("at") if isinstance(client.get("at"), list) and len(client.get("at")) >= 2 else [0, 0]
    size = client.get("size") if isinstance(client.get("size"), list) and len(client.get("size")) >= 2 else [0, 0]
    pid = int(client.get("pid") or 0)
    return {
        "address": normalize_address(client.get("address")),
        "title": str(client.get("title") or ""),
        "class": str(client.get("class") or ""),
        "initialClass": str(client.get("initialClass") or ""),
        "pid": pid,
        "process": process_name,
        "workspace": {"id": int(ws.get("id") or 0), "name": str(ws.get("name") or "")},
        "at": [int(at[0]), int(at[1])],
        "size": [int(size[0]), int(size[1])],
        "floating": bool(client.get("floating", False)),
        "pinned": bool(client.get("pinned", False)),
        "fullscreen": int(client.get("fullscreen") or 0),
    }


class WindowDomain:
    def __init__(self, runner=None, proc_root=Path("/proc"), preferences_reader=None):
        self.runner = runner or subprocess.run
        self.proc_root = Path(proc_root)
        self.preferences_reader = preferences_reader or workspace_preferences

    def hyprctl(self, arguments, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("window-timeout")
        result = self.runner(["hyprctl", *arguments], capture_output=True, text=True, check=True,
                             timeout=min(4, remaining))
        return result.stdout

    def hypr_json(self, arguments, deadline):
        raw = self.hyprctl(arguments, deadline).strip()
        return json.loads(raw) if raw else None

    def process_name(self, pid):
        if pid <= 0:
            return ""
        try:
            return (self.proc_root / str(pid) / "comm").read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return ""

    def workspaces(self, deadline):
        by_id = {}
        try:
            count = int(self.preferences_reader().get("workspaceCount", 10))
        except Exception:
            count = 10
        for number in range(1, max(1, count) + 1):
            by_id[number] = {"id": number, "name": str(number)}
        raw_list = self.hypr_json(["workspaces", "-j"], deadline)
        for entry in raw_list if isinstance(raw_list, list) else []:
            ws_id = int(entry.get("id") or 0)
            if ws_id > 0:
                by_id[ws_id] = {"id": ws_id, "name": str(entry.get("name") or ws_id)}
        return [by_id[key] for key in sorted(by_id)]

    def find_window(self, address, deadline):
        target = normalize_address(address)
        client = None
        if target:
            clients = self.hypr_json(["clients", "-j"], deadline)
            for entry in clients if isinstance(clients, list) else []:
                if normalize_address(entry.get("address")) == target:
                    client = entry
                    break
        else:
            active = self.hypr_json(["activewindow", "-j"], deadline)
            if isinstance(active, dict) and normalize_address(active.get("address")):
                client = active
        if not client:
            return None
        pid = int(client.get("pid") or 0)
        return format_client(client, self.process_name(pid))

    def dispatch_window(self, address, expression, deadline):
        target = normalize_address(address)
        if not target:
            raise ValueError("invalid-address")
        script = (
            "local window = hl.get_window(" + lua("address:" + target) + "); "
            "if window and window.mapped then " + expression + " end"
        )
        self.hyprctl(["eval", script], deadline)

    def info(self, address, deadline):
        return {
            "window": self.find_window(address, deadline),
            "workspaces": self.workspaces(deadline),
        }

    def query(self, name, args, deadline):
        address = normalize_address(args.get("address", ""))
        if name == "info":
            return self.info(address, deadline)
        if name == "float":
            self.dispatch_window(address, 'hl.dispatch(hl.dsp.window.float({action="toggle", window=window}))', deadline)
            return self.info(address, deadline)
        if name == "pin":
            self.dispatch_window(address, "hl.dispatch(hl.dsp.window.pin({window=window}))", deadline)
            return self.info(address, deadline)
        if name == "move":
            workspace = args.get("workspace")
            if type(workspace) is int and workspace > 0:
                ws_expr = str(workspace)
            elif isinstance(workspace, str) and SAFE_NAME_RE.fullmatch(workspace):
                ws_expr = lua(workspace)
            else:
                raise ValueError("invalid-workspace")
            self.dispatch_window(
                address,
                f"hl.dispatch(hl.dsp.window.move({{workspace={ws_expr}, window=window, follow=false}}))",
                deadline,
            )
            return self.info(address, deadline)
        if name == "close":
            self.dispatch_window(address, "hl.dispatch(hl.dsp.window.close({window=window}))", deadline)
            return {"window": None, "workspaces": self.workspaces(deadline), "closed": True}
        raise ValueError("invalid-action")
