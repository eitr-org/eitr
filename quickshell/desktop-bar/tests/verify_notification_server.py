"""Live read/write smoke check; closes only the notifications created here."""
import json
import subprocess
import time


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def dbus(method, *args):
    return run("busctl", "--user", "call", "org.freedesktop.Notifications",
               "/org/freedesktop/Notifications", "org.freedesktop.Notifications", method, *args)


def status():
    for _ in range(10):
        raw = run("quickshell", "ipc", "-c", "desktop-bar", "call", "--", "notifications", "status")
        if raw.startswith("{"):
            return json.loads(raw)
        time.sleep(0.1)
    raise RuntimeError("Notification IPC did not become ready")


def notify(replaces=0, transient=False, timeout=100):
    hints = ("1", "transient", "b", "true") if transient else ("0",)
    result = dbus("Notify", "susssasa{sv}i", "Codex Notification Test", str(replaces), "",
                  "Notification check", "This test notification will be removed.", "0", *hints, str(timeout))
    return int(result.split()[1])


if __name__ == "__main__":
    ids = set()
    original_dnd = status()["doNotDisturb"]
    try:
        assert '"quickshell"' in dbus("GetServerInformation")
        capabilities = dbus("GetCapabilities")
        for name in ("body", "actions", "persistence", "inline-reply"):
            assert f'"{name}"' in capabilities
        if not original_dnd:
            run("quickshell", "ipc", "-c", "desktop-bar", "call", "--", "notifications", "dnd")
        baseline = status()["count"]
        notice_id = notify()
        ids.add(notice_id)
        time.sleep(0.15)
        assert status()["count"] == baseline + 1
        assert notify(replaces=notice_id) == notice_id
        time.sleep(0.3)
        assert status()["count"] == baseline + 1, "DND must retain history without duplicating replacements"
        transient_id = notify(transient=True)
        ids.add(transient_id)
        time.sleep(0.2)
        assert status()["count"] == baseline + 1, "Transient notifications must skip history"
        dbus("CloseNotification", "u", str(notice_id))
        ids.remove(notice_id)
        time.sleep(0.1)
        assert status()["count"] == baseline
        print("Notification server, capabilities, replacement, DND, transient, and close checks passed")
    finally:
        for notice_id in ids:
            dbus("CloseNotification", "u", str(notice_id))
        if status()["doNotDisturb"] != original_dnd:
            run("quickshell", "ipc", "-c", "desktop-bar", "call", "--", "notifications", "dnd")
