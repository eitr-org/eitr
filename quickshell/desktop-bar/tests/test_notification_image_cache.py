import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]


class NotificationImageCacheTests(unittest.TestCase):
    def test_thumbnail_remains_available_after_sender_deletes_file(self):
        with tempfile.TemporaryDirectory(prefix="eitr-notification-test-") as directory:
            target = Path(directory)
            fixture = target / "tst_notification_image_cache.qml"
            shutil.copyfile(Path(__file__).with_name(fixture.name), fixture)
            thumbnail = target / "thumbnail.png"
            shutil.copyfile(ROOT / "branding/png/eitr-logo-green-64.png", thumbnail)
            process = subprocess.Popen(
                ["/usr/lib/qt6/bin/qmltestrunner", "-input", str(fixture)],
                env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            output = []
            try:
                for line in process.stdout:
                    output.append(line)
                    if "THUMBNAIL_LOADED" in line:
                        thumbnail.unlink()
                self.assertEqual(process.wait(timeout=10), 0, "".join(output))
                self.assertFalse(thumbnail.exists(), "Sender cleanup was not exercised")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                process.stdout.close()
