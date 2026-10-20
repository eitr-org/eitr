"""Live thumbnail lifecycle check; dismisses only its own test notifications."""
import json
from pathlib import Path
import shutil
import tempfile
import time

from verify_notification_server import dbus, run


def image_status():
    return json.loads(run("quickshell", "ipc", "-c", "desktop-bar", "call", "--",
                          "notifications", "imageStatus"))


if __name__ == "__main__":
    ids = []
    try:
        with tempfile.TemporaryDirectory(prefix="eitr-thumbnail-test-") as directory:
            image = Path(directory) / "thumbnail.png"
            shutil.copyfile(Path(__file__).resolve().parents[3] /
                            "branding/png/eitr-logo-green-64.png", image)
            result = dbus("Notify", "susssasa{sv}i", "Screenshot Preview Test", "0", "",
                          "Thumbnail check", "Temporary test; removed automatically.", "0",
                          "1", "image-path", "s", str(image), "100")
            first = int(result.split()[1])
            ids.append(first)
            time.sleep(0.15)
            assert any(entry == {"id": first, "status": 1} for entry in image_status()), "Thumbnail was not decoded on receipt"
            image.unlink()
            second = int(dbus("Notify", "susssasa{sv}i", "Screenshot Preview Test", "0", "",
                              "Second notification", "Tests list updates.", "0", "0", "100").split()[1])
            ids.append(second)
            time.sleep(0.15)
            assert any(entry == {"id": first, "status": 1} for entry in image_status()), "List update lost the cached thumbnail"
            print("Live thumbnail survives sender cleanup and a second notification")
    finally:
        for notice_id in ids:
            dbus("CloseNotification", "u", str(notice_id))
