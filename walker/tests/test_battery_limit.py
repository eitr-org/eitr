import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("battery_limit", ROOT / "walker/scripts/actions/system/battery-limit.py")
walker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(walker)


class BatteryMenuConfirmationTests(unittest.TestCase):
    def test_limit_requires_typed_yes(self):
        with tempfile.NamedTemporaryFile() as helper:
            for answer, expected in (("", 0), ("y", 0), ("yes", 1)):
                with self.subTest(answer=answer), patch.object(walker, "ROOT_HELPERS", (helper.name,)), \
                        patch("builtins.input", return_value=answer), patch("builtins.print"), \
                        patch.object(walker.subprocess, "run") as run:
                    walker.main(["set", "80"])
                    self.assertEqual(run.call_count, expected)
                    if expected:
                        run.assert_called_once_with(["sudo", helper.name, "battery-limit", "80"], check=True)

    def test_invalid_value_never_prompts(self):
        with tempfile.NamedTemporaryFile() as helper, patch.object(walker, "ROOT_HELPERS", (helper.name,)), \
                patch("builtins.input") as prompt:
            for args in (["set", "40"], ["set"], ["drain"]):
                with self.assertRaises(ValueError):
                    walker.main(args)
            prompt.assert_not_called()


if __name__ == "__main__":
    unittest.main()
