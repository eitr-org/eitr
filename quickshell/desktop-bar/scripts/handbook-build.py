#!/usr/bin/env python3
"""Bundle the maintained Markdown sources for the offline, read-only handbook."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import markdown

ROOT = Path(__file__).resolve().parents[3]
BOOK = ROOT / "quickshell/desktop-bar/handbook"
sys.path.insert(0, str(ROOT / ("distro/lib" if (ROOT / "distro/lib").is_dir() else "lib")))
from eitr_i18n import languages, table


class Blocks(HTMLParser):
    """Keep top-level rich-text blocks small enough to render independently."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.depth = 0
        self.buffer = []
        self.blocks = []

    def flush(self):
        if self.buffer:
            self.blocks.append("".join(self.buffer))
            self.buffer = []

    def handle_starttag(self, tag, attrs):
        self.buffer.append(self.get_starttag_text())
        if tag not in ("br", "hr", "img", "wbr"):
            self.depth += 1
        elif not self.depth:
            self.flush()

    def handle_startendtag(self, tag, attrs):
        self.buffer.append(self.get_starttag_text())
        if not self.depth:
            self.flush()

    def handle_endtag(self, tag):
        self.buffer.append(f"</{tag}>")
        self.depth -= 1
        if not self.depth:
            self.flush()

    def handle_data(self, data):
        if self.depth:
            self.buffer.append(data)

    def handle_entityref(self, name):
        self.buffer.append("&" + name + ";")

    def handle_charref(self, name):
        self.buffer.append("&#" + name + ";")


def blocks(html):
    parser = Blocks()
    parser.feed(html)
    if parser.depth:
        raise ValueError("Unbalanced handbook HTML")
    return parser.blocks


def shortcuts():
    source = (ROOT / "walker/scripts/menus/shortcuts.sh").read_text()
    options = re.search(r'^options="(.*?)"$', source, re.MULTILINE | re.DOTALL)[1]
    lines = ["# Shortcuts", "", "Keyboard and mouse shortcuts share this reference. SUPER is the Windows/Command-logo key.", "",
             "Open this handbook with **SUPER + F1**. Search chapters with **Ctrl + F**, scroll with **Page Up/Page Down**; Escape closes it.", "",
             "## Keyboard", "", "Local hardware overrides may add bindings.", ""]
    for line in options.splitlines():
        if line.startswith("  "):
            key, description = re.split(r"\s{2,}", line.strip(), maxsplit=1)
            lines.append(f"| **{key}** | {description} |")
        else:
            lines.extend(["", "### " + line.split("  ", 1)[-1], "",
                          "| Shortcut | Action |", "| :--- | :--- |"])
    source = (ROOT / "walker/scripts/menus/mouse-gestures.sh").read_text()
    mouse = re.search(r'^options="(.*?)"$', source, re.MULTILINE | re.DOTALL)[1]
    lines.extend(["", "## Mouse", "", "Use empty desktop or bar space for desktop/bar gestures, not an application's content.", "",
                  "| Gesture | Action |", "| :--- | :--- |"])
    for line in mouse.splitlines():
        gesture, description = re.split(r"\s{2,}", line, maxsplit=1)
        lines.append(f"| **{gesture}** | {description} |")
    lines.extend(["| **SUPER + left drag on a window** | Move a floating window. |",
                  "| **SUPER + right drag on a window** | Resize a window. |",
                  "| **Click a bar icon** | Open/toggle its panel; outside click or Escape dismisses it. |",
                  "| **Right-click Idle Lock** | Toggle automatic locking. |"])
    return "\n".join(lines) + "\n"


def shortcut_parts(line):
    """Text cells only; binding sequences and Markdown table structure stay stable."""
    if line.startswith("|"):
        if re.fullmatch(r"[\s|:-]+", line):
            return []
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        return [cell.strip("*") for index, cell in enumerate(cells)
                if index > 0 or not re.search(r"\b(?:SUPER|Ctrl|Alt|Shift|CapsLock)\b", cell)]
    return [re.sub(r"^#+\s*", "", line)] if line.strip() else []


def shortcut_messages():
    return sorted({message for line in shortcuts().splitlines() for message in shortcut_parts(line)})


def localized_shortcuts(locale):
    if locale == "en":
        return shortcuts()
    messages = table("handbook", locale, ROOT)
    output = []
    for line in shortcuts().splitlines():
        if line.startswith("|") and not re.fullmatch(r"[\s|:-]+", line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            for index, cell in enumerate(cells):
                if index == 0 and re.search(r"\b(?:SUPER|Ctrl|Alt|Shift|CapsLock)\b", cell):
                    continue
                plain = cell.strip("*")
                translated = messages.get(plain, plain)
                cells[index] = "**" + translated + "**" if cell.startswith("**") else translated
            output.append("| " + " | ".join(cells) + " |")
        elif line.strip() and not line.startswith("|"):
            prefix = re.match(r"^#+\s*", line)
            plain = line[prefix.end():] if prefix else line
            output.append((prefix[0] if prefix else "") + messages.get(plain, plain))
        else:
            output.append(line)
    return "\n".join(output) + "\n"


def unnest_fences(text):
    """Python-Markdown cannot nest fenced code in list items; render those blocks at top level."""
    return re.sub(r"^( {1,4})(```.*?\n)(.*?)^\1```$",
                  lambda match: match[2] + re.sub(r"^" + match[1], "", match[3], flags=re.MULTILINE) + "```",
                  text, flags=re.MULTILINE | re.DOTALL)


def translation_source_problems(locale):
    """Flag changed English chapters independently of regenerated catalogs."""
    if locale == "en":
        return []
    folder = BOOK / "content" / locale
    manifest = folder / "source-hashes.json"
    hashes = json.loads(manifest.read_text()) if manifest.is_file() else {}
    problems = []
    definitions = json.loads((BOOK / "chapters.json").read_text())
    for chapter in definitions:
        if "source" not in chapter or not (folder / (chapter["id"] + ".md")).is_file():
            continue
        digest = hashlib.sha256((ROOT / chapter["source"]).read_bytes()).hexdigest()
        if hashes.get(chapter["id"]) != digest:
            problems.append(locale + "/" + chapter["id"])
    return problems


def build(locale="en"):
    if locale not in languages(ROOT):
        raise ValueError("Unsupported handbook locale")
    messages = table("handbook", locale, ROOT)
    definitions = json.loads((BOOK / "chapters.json").read_text())
    ids = {chapter["id"] for chapter in definitions}
    if len(ids) != len(definitions):
        raise ValueError("Duplicate handbook chapter")
    links = {Path(chapter["source"]).name: chapter["id"] for chapter in definitions if "source" in chapter}
    result = []
    for chapter in definitions:
        localized = BOOK / "content" / locale / (chapter["id"] + ".md")
        if chapter.get("generated") == "shortcuts":
            text = localized_shortcuts(locale)
        elif locale != "en" and localized.is_file():
            text = localized.read_text()
        else:
            text = (ROOT / chapter["source"]).read_text()
        for filename, chapter_id in links.items():
            text = text.replace("](" + filename + ")", "](handbook:" + chapter_id + ")")
        for target in re.findall(r"\]\(handbook:([^)#]+)", text):
            if target not in ids:
                raise ValueError(f"Unknown chapter link: {target}")
        if re.search(r"!\[[^\]]*\]\(https?://", text):
            raise ValueError("Handbook images must be local and offline")
        for figure in chapter.get("figures", []):
            path = (BOOK / figure["src"]).resolve()
            if not path.is_relative_to(BOOK.resolve()) or not path.is_file():
                raise ValueError(f"Missing or unsafe handbook image: {figure['src']}")
        html = markdown.markdown(unnest_fences(text), extensions=["tables", "fenced_code", "sane_lists"])
        metadata = {key: value for key, value in chapter.items() if key not in ("source", "generated")}
        for key in ("title", "summary"):
            if key in metadata:
                metadata[key] = messages.get(metadata[key], metadata[key])
        if locale != "en":
            metadata["sourceLocale"] = locale if localized.is_file() or chapter.get("generated") else "en"
        result.append({**metadata, "markdown": text, "blocks": blocks(html)})
    return json.dumps({"version": 1, "chapters": result}, ensure_ascii=False, indent=2) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--locale", choices=list(languages(ROOT)))
    args = parser.parse_args()
    stale = []
    source_changes = []
    for locale in [args.locale] if args.locale else languages(ROOT):
        rendered = build(locale)
        catalog = BOOK / "catalog.json" if locale == "en" else BOOK / "catalogs" / (locale + ".json")
        if args.check:
            source_changes.extend(translation_source_problems(locale))
            if not catalog.exists() or catalog.read_text() != rendered:
                stale.append(locale)
        else:
            catalog.parent.mkdir(parents=True, exist_ok=True)
            catalog.write_text(rendered)
    if source_changes:
        sys.exit("Handbook translations need source review: " + ", ".join(source_changes)
                 + "; translate the changed chapters before updating source-hashes.json")
    if stale:
        sys.exit("Handbook catalogs are stale: " + ", ".join(stale) + "; run python3 quickshell/desktop-bar/scripts/handbook-build.py")
