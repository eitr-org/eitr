"""tools/choice-lists.py: the ordered lists and the modules generated from them."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
specification = importlib.util.spec_from_file_location("choice_lists_tool", ROOT / "tools/choice-lists.py")
tool = importlib.util.module_from_spec(specification)
specification.loader.exec_module(tool)
sys.path.insert(0, str(ROOT / "distro/lib"))
import eitr_choice_lists  # noqa: E402

GROUPS = {"window_layouts": ("windowLayouts", "WINDOW_LAYOUTS"), "scrolling_directions": ("scrollingDirections", "SCROLLING_DIRECTIONS"),
          "scrolling_widths": ("scrollingWidths", "SCROLLING_WIDTHS"), "scrolling_focus_fit": ("scrollingFocusFit", "SCROLLING_FOCUS_FIT"), "window_gaps": ("windowGaps", "WINDOW_GAPS"), "bar_layouts": ("barLayouts", "BAR_LAYOUTS"), "bar_appearances": ("barAppearances", "BAR_APPEARANCES"),
          "update_channels": ("updateChannels", "UPDATE_CHANNELS")}


class ChoiceListTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "tools/choice-lists.json").read_text())

    def test_generated_modules_are_current(self):
        self.assertEqual(tool.synchronize(check=True), [])

    def test_every_language_sees_the_same_ids_labels_and_order(self):
        javascript = (ROOT / "quickshell/desktop-bar/ChoiceLists.js").read_text().replace(".pragma library", "")
        script = javascript + "\nconsole.log(JSON.stringify({windowLayouts, scrollingDirections, scrollingWidths, scrollingFocusFit, windowGaps, barLayouts, barAppearances, updateChannels}));"
        exported = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
        lua = None
        interpreter = shutil.which("lua") or shutil.which("luajit")
        if interpreter:
            program = ('local t = dofile("elephant/choice-lists.lua") for _, group in ipairs({"window_layouts", "scrolling_directions", "scrolling_widths", "scrolling_focus_fit", "window_gaps", "bar_layouts", "bar_appearances", "update_channels"}) do '
                       'for _, row in ipairs(t[group]) do print(group .. "\\t" .. row.id .. "\\t" .. row.label .. "\\t" .. (row.icon or "")) end end')
            lua = subprocess.run([interpreter, "-e", program], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
        rows = []
        for group, (javascript_name, python_name) in GROUPS.items():
            expected = [(row["id"], row["label"], chr(int(row["icon"], 16)) if "icon" in row else "") for row in self.catalog[group]]
            self.assertEqual([(row["id"], row["label"], row.get("icon", "")) for row in exported[javascript_name]], expected)
            self.assertEqual([(row["id"], row["label"], row.get("icon", "")) for row in getattr(eitr_choice_lists, python_name)], expected)
            rows += [f"{group}\t{identifier}\t{label}\t{icon}" for identifier, label, icon in expected]
        if lua is not None:
            self.assertEqual(lua, rows)

    def test_cycles_wrap_round(self):
        layouts = eitr_choice_lists.ids(eitr_choice_lists.BAR_LAYOUTS)
        self.assertEqual(eitr_choice_lists.next_choice(eitr_choice_lists.BAR_LAYOUTS, layouts[-1]), layouts[0])
        self.assertEqual(eitr_choice_lists.next_choice(eitr_choice_lists.BAR_LAYOUTS, "missing"), layouts[0])
        self.assertEqual(eitr_choice_lists.label(eitr_choice_lists.UPDATE_CHANNELS, "testing"), "Testing")

    def test_invalid_rows_are_refused(self):
        path = ROOT / "tools/choice-lists.json"
        cases = [
            ("bar_layouts", lambda rows: rows.append(dict(rows[0]))),  # duplicate id
            ("bar_layouts", lambda rows: rows[0].update(icon="not-hex")),
            ("bar_appearances", lambda rows: rows[0].pop("description")),
            ("bar_appearances", lambda rows: rows[0].update(extra="field")),
            ("update_channels", lambda rows: rows[0].update(id="Stable!")),
            ("update_channels", lambda rows: rows[0].update(repository="")),
            ("bar_layouts", lambda rows: rows[0].update(keywords="Full")),
        ]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "choice-lists.json"
            for group, change in cases:
                broken = copy.deepcopy(self.catalog)
                change(broken[group])
                target.write_text(json.dumps(broken))
                with self.subTest(group=group), self.assertRaises(ValueError):
                    tool.load_catalog(target)
        tool.load_catalog(path)


if __name__ == "__main__":
    unittest.main()
