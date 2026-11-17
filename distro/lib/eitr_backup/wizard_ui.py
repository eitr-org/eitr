"""Reusable curses checklist and review widgets for the Eitr backup wizard."""
import curses

from eitr_backup.sizes import format_size
from eitr_i18n import mark, tr
from eitr_terminal import read_key
from eitr_textwidth import cell_width, clip, wrap_text
from eitr_wizard import Back, Cancelled, Wizard


def build_app_package_items(apps_data, selected_map=None):
    items = []
    groups = [
        ("official", mark("Official packages"), apps_data.get("official", []), lambda item: (item, item, "")),
        ("aur", mark("AUR packages"), apps_data.get("aur", []), lambda item: (item, item, "")),
        ("flatpak", mark("Flatpak apps"), apps_data.get("flatpak", []), lambda item: (item, item, "")),
        ("plugins", mark("Plugins"), apps_data.get("plugins", []), lambda item: (item["id"], item.get("name") or item["id"], item.get("url", ""))),
        ("store", mark("Store items"), apps_data.get("store", []), lambda item: (f"{item['kind']}:{item['id']}", f"{item['kind']}: {item.get('name') or item['id']}", item.get("url", ""))),
    ]
    for source_key, group_label, entries, formatter in groups:
        wanted = None if selected_map is None else selected_map.get(source_key)
        for entry in entries:
            item_id, label, hint = formatter(entry)
            items.append({
                "id": item_id,
                "source": source_key,
                "label": label,
                "group": tr(group_label),
                "hint": hint,
                "selected": True if wanted is None else item_id in wanted,
            })
    return items


def selected_app_map(items):
    selected = {"official": [], "aur": [], "flatpak": [], "plugins": [], "store": []}
    for item in items:
        if item.get("selected"):
            selected[item["source"]].append(item["id"])
    return selected


def terminal_approve_item(kind, item, details):
    """Interactive terminal review prompt for plugins and Store items."""
    print()
    print(f"=== {tr('Review {kind}: {name}', kind=kind, name=item.get('name') or item.get('id'))} ===")
    if item.get("url"):
        print(f"  {tr('Source')}: {item['url']}")
    if item.get("commit"):
        print(f"  {tr('Commit')}: {item['commit'][:12]}")
    if isinstance(details, dict):
        if details.get("official") is False:
            print(f"  {tr('Notice: third-party repository (not reviewed by Eitr)')}")
        for flag in details.get("flags", []):
            print(f"  RISK: {flag}")
    print(tr("Approve installation? [y/N/Esc] "), end="", flush=True)
    while True:
        key = read_key()
        if key in ("y", "Y"):
            print("y")
            return True
        if key in ("n", "N", "\r", "\n", "\x1b", "\x03", ""):
            print("n")
            return False


def _item_matches(item, query):
    if not query:
        return True
    needle = query.casefold()
    haystack = " ".join(filter(None, (
        item.get("label", ""),
        item.get("id", ""),
        item.get("group", ""),
        item.get("hint", ""),
    ))).casefold()
    return needle in haystack


def _build_rows(items, query):
    rows = []
    last_group = None
    for item in items:
        if item.get("action"):
            rows.append(("item", item))
            continue
        if not _item_matches(item, query):
            continue
        group = item.get("group")
        if group and group != last_group:
            rows.append(("header", group))
            last_group = group
        rows.append(("item", item))
    return rows


def _next_selectable(rows, cursor, delta):
    if not rows:
        return 0
    pos = cursor
    while 0 <= pos + delta < len(rows):
        pos += delta
        if rows[pos][0] == "item":
            return pos
    return cursor


class BackupWizard(Wizard):
    """Backup/Restore wizard built on Eitr's shared SetupWizard layout."""

    def __init__(self, screen, title, steps):
        super().__init__(screen, steps)
        self.heading = title
        self.allow_back = True
        self.cancel_keys = ("\x1b", "\x03")

    def checklist(
        self,
        title,
        items,
        *,
        note="",
        size_monitor=None,
        add_folder_callback=None,
        require_one=False,
        allow_back=True,
    ):
        query = ""
        error = ""
        rows = _build_rows(items, query)
        cursor = _next_selectable(rows, -1, 1)

        try:
            while True:
                polling = bool(size_monitor and size_monitor.pending_count() > 0)
                self.screen.timeout(120 if polling else -1)

                help_parts = [tr("Space: toggle")]
                if add_folder_callback:
                    help_parts.append(tr("+: add folder"))
                help_parts.append(tr("Enter: next"))
                if allow_back:
                    help_parts.append(tr("Left: back"))
                help_parts.append(tr("Esc: cancel"))
                help_line = "  ".join(help_parts)

                y, x = self.frame(title, help_line)
                for paragraph in note.splitlines():
                    for line in wrap_text(paragraph, self.body_width):
                        self.text(y, x, line)
                        y += 1
                if note:
                    y += 1

                self.text(y, x, tr("Search: {query}", query=query) if query else tr("Type to search (Ctrl+A: toggle all)"), 1)
                y += 2

                rows = _build_rows(items, query)
                if rows and (cursor >= len(rows) or rows[cursor][0] != "item"):
                    cursor = _next_selectable(rows, -1, 1)

                bottom = getattr(self, "panel_bottom", self.screen.getmaxyx()[0] - 3)
                reserve = 4 if error else 3
                visible_count = max(2, bottom - y - reserve)
                start = max(0, min(cursor - visible_count + 1, max(0, len(rows) - visible_count)))

                if not rows:
                    self.text(y, x, tr("No matches"))
                else:
                    for idx, (kind, payload) in enumerate(rows[start:start + visible_count], start):
                        row_y = y + idx - start
                        if kind == "header":
                            self.text(row_y, x, f"— {payload} —", 2)
                            continue
                        selected_row = idx == cursor
                        style = 3 if selected_row else 1
                        if payload.get("action") == "add_folder":
                            line = f"  [+] {payload['label']}"
                            self.text(row_y, x, clip(line, self.body_width), style)
                            continue
                        mark_box = "[x]" if payload["selected"] else "[ ]"
                        right_text = ""
                        if size_monitor and payload.get("size_key"):
                            right_text = format_size(size_monitor.get(payload["size_key"]))
                        elif payload.get("size_bytes") is not None:
                            right_text = format_size(payload["size_bytes"])
                        elif payload.get("right"):
                            right_text = payload["right"]
                        left_text = f"{mark_box} {payload['label']}"
                        if right_text:
                            gap = max(2, self.body_width - cell_width(left_text) - cell_width(right_text))
                            max_left = max(12, self.body_width - cell_width(right_text) - 2)
                            left_text = clip(left_text, max_left)
                            gap = max(1, self.body_width - cell_width(left_text) - cell_width(right_text))
                            rendered = f"{left_text}{' ' * gap}{right_text}"
                        else:
                            rendered = left_text
                        self.text(row_y, x, clip(rendered, self.body_width), style)

                    if 0 <= cursor < len(rows) and rows[cursor][0] == "item":
                        hint = rows[cursor][1].get("hint", "")
                        if hint:
                            self.text(bottom - 2, x, clip(hint, self.body_width), 1)
                if error:
                    self.text(bottom - 1, x, clip(error, self.body_width), 2)

                self.screen.refresh()
                try:
                    key = self.screen.get_wch()
                except curses.error:
                    continue

                if key in self.cancel_keys:
                    raise Cancelled
                if allow_back and key in (curses.KEY_LEFT, "\t", curses.KEY_BTAB):
                    raise Back
                if key == curses.KEY_UP:
                    cursor = _next_selectable(rows, cursor, -1)
                    error = ""
                elif key == curses.KEY_DOWN:
                    cursor = _next_selectable(rows, cursor, 1)
                    error = ""
                elif key == " ":
                    error = ""
                    if 0 <= cursor < len(rows) and rows[cursor][0] == "item":
                        item = rows[cursor][1]
                        if item.get("action") == "add_folder" and add_folder_callback:
                            self.screen.timeout(-1)
                            added, err = add_folder_callback()
                            if err:
                                error = err
                            elif added:
                                rows = _build_rows(items, query)
                        elif not item.get("action"):
                            item["selected"] = not item["selected"]
                elif key == "\x01":
                    selectable = [payload for kind, payload in rows if kind == "item" and not payload.get("action")]
                    target_state = not all(entry["selected"] for entry in selectable)
                    for entry in selectable:
                        entry["selected"] = target_state
                    error = ""
                elif key == "+" and add_folder_callback and not query:
                    self.screen.timeout(-1)
                    added, err = add_folder_callback()
                    if err:
                        error = err
                    elif added:
                        rows = _build_rows(items, query)
                elif key in ("\n", "\r", curses.KEY_ENTER):
                    if 0 <= cursor < len(rows) and rows[cursor][0] == "item" and rows[cursor][1].get("action") == "add_folder" and add_folder_callback:
                        self.screen.timeout(-1)
                        added, err = add_folder_callback()
                        if err:
                            error = err
                        elif added:
                            rows = _build_rows(items, query)
                        continue
                    if require_one and not any(item["selected"] for item in items if not item.get("action")):
                        error = tr("Select at least one option to continue.")
                        continue
                    return items
                elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                    query = query[:-1]
                    cursor = _next_selectable(_build_rows(items, query), -1, 1)
                elif isinstance(key, str) and key.isprintable():
                    query += key
                    cursor = _next_selectable(_build_rows(items, query), -1, 1)
        finally:
            self.screen.timeout(-1)

    def review_screen(self, title, sections, *, confirm_label=None):
        """Show wrapped review sections without writing anything before Enter confirms."""
        def build_lines(with_gaps):
            out = []
            for heading, body_lines in sections:
                out.append((2, heading))
                for entry in body_lines:
                    for wrapped in wrap_text(entry, max(20, self.body_width - 2)) or [""]:
                        out.append((1, "  " + wrapped))
                if with_gaps:
                    out.append((1, ""))
            return out

        offset = 0
        while True:
            y, x = self.frame(title, tr("Enter: confirm  Left: back  PgUp/PgDn: scroll  Esc: cancel"))
            bottom = getattr(self, "panel_bottom", self.screen.getmaxyx()[0] - 3)
            visible = max(2, bottom - y - 3)
            lines = build_lines(with_gaps=True)
            if len(lines) > visible:
                lines = build_lines(with_gaps=False)
            offset = max(0, min(offset, max(0, len(lines) - visible)))
            for idx, (style, text_line) in enumerate(lines[offset:offset + visible]):
                self.text(y + idx, x, clip(text_line, self.body_width), style)
            prompt = confirm_label or tr("Enter: start now  ·  Nothing is written until you confirm")
            self.text(bottom - 2, x, clip(prompt, self.body_width), 2)
            self.screen.refresh()

            key = self.screen.get_wch()
            if key in self.cancel_keys:
                raise Cancelled
            if key in (curses.KEY_LEFT, "\t", curses.KEY_BTAB):
                raise Back
            if key in (curses.KEY_UP, curses.KEY_PPAGE):
                step = visible if key == curses.KEY_PPAGE else 1
                offset = max(0, offset - step)
            elif key in (curses.KEY_DOWN, curses.KEY_NPAGE):
                step = visible if key == curses.KEY_NPAGE else 1
                offset = min(max(0, len(lines) - visible), offset + step)
            elif key in ("\n", "\r", curses.KEY_ENTER):
                return True
