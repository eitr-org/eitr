from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SHOW_PANEL = ROOT / "scripts" / "show-panel.sh"


def show_panel_allowlist():
    text = SHOW_PANEL.read_text()
    match = re.search(r'case "\$\{1:-\}" in\s*\n\s*([a-z|]+)\)', text)
    if not match:
        raise AssertionError("show-panel.sh allowlist pattern not found")
    return set(match.group(1).split("|"))


def ipc_show_kinds():
    shell = (ROOT / "shell.qml").read_text()
    # The panels IPC forwards show() to the bar's showKind(), which holds the kind map.
    match = re.search(r"function showKind\(kind\) \{(.*?)\n\s*\}\n", shell, re.S)
    if not match:
        raise AssertionError("showKind() not found in shell.qml")
    body = match.group(1)
    mapping = re.search(r"var panels = \{(.*?)\};", body, re.S)
    if not mapping:
        raise AssertionError("panels kind map not found in shell.qml")
    kinds = set(re.findall(r"(\w+):\s*\w+", mapping.group(1)))
    kinds.update(re.findall(r'kind === "(\w+)"', body))
    return kinds


def show_panel_uses():
    sources = list((REPO / "elephant" / "menus").glob("*.toml")) + list((REPO / "elephant" / "menu-rows").glob("*.json"))
    sources += [path for path in (REPO / "walker").rglob("*") if path.is_file() and path.suffix in {".sh", ".py", ""}]
    uses = {}
    for path in sources:
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for kind in re.findall(r"show-panel\.sh\"?\s+([a-z]+)", text):
            uses.setdefault(kind, set()).add(str(path.relative_to(REPO)))
        for kind in re.findall(r"call -- panels show ([a-z]+)", text):
            uses.setdefault(kind, set()).add(str(path.relative_to(REPO)))
    return uses


class ShowPanelKindsTests(unittest.TestCase):
    def test_allowlist_matches_ipc_kinds(self):
        self.assertEqual(show_panel_allowlist(), ipc_show_kinds())

    def test_every_caller_uses_an_accepted_kind(self):
        accepted = show_panel_allowlist()
        uses = show_panel_uses()
        self.assertTrue(uses, "expected at least one show-panel caller")
        unknown = {kind: sorted(paths) for kind, paths in uses.items() if kind not in accepted}
        self.assertEqual(unknown, {})


if __name__ == "__main__":
    unittest.main()
