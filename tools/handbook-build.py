#!/usr/bin/env python3
"""Bundle the maintained Markdown sources for the offline, read-only handbook."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import markdown

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "quickshell/desktop-bar/handbook"
sys.path.insert(0, str(ROOT / ("distro/lib" if (ROOT / "distro/lib").is_dir() else "lib")))
from eitr_i18n import languages, table
from eitr_focus import shortcut_entries

# Live illustrations the reader draws in QML (quickshell/desktop-bar/figures/<Name>Figure.qml).
FIGURES = ("bar-anatomy", "bar-layouts", "control-center", "settings-window", "launcher", "window-style")


class Blocks(HTMLParser):
    """Keep top-level rich-text blocks small enough to render independently.

    Each block also records the welcome section (`<!-- eitr-welcome:NAME -->`) it sits in.
    A figure marker (`<!-- eitr-figure: NAME -->`) turns the paragraph after it into one
    `<figure data-figure="NAME"><figcaption>…</figcaption></figure>` block: the reader
    draws the named figure above that caption, the website shows the caption alone."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.depth = 0
        self.buffer = []
        self.blocks = []
        self.sections = []
        self.section = None
        self.figure = None

    def flush(self):
        if self.buffer:
            block = "".join(self.buffer)
            if self.figure:
                caption = re.fullmatch(r"<p>(.*)</p>", block.strip(), re.DOTALL)
                if not caption:
                    raise ValueError(f"The figure {self.figure} needs a caption paragraph right after its marker")
                block = f'<figure data-figure="{self.figure}"><figcaption>{caption[1].strip()}</figcaption></figure>'
                self.figure = None
            self.blocks.append(block)
            self.sections.append(self.section)
            self.buffer = []

    def handle_comment(self, data):
        figure = re.fullmatch(r"\s*eitr-figure:\s*([a-z-]+)\s*", data)
        if figure:
            if self.depth or self.figure:
                raise ValueError("Figure markers sit between top-level blocks, each before its caption")
            if figure[1] not in FIGURES:
                raise ValueError(f"Unknown handbook figure: {figure[1]}")
            self.figure = figure[1]
            return
        marker = re.fullmatch(r"\s*(/?)eitr-welcome:([a-z]+)\s*", data)
        if not marker:
            return
        if self.depth:
            raise ValueError("Welcome markers belong between top-level blocks")
        closing, name = marker[1] == "/", marker[2]
        if closing != (self.section == name) or (not closing and self.section):
            raise ValueError(f"Unbalanced welcome marker: {name}")
        self.section = None if closing else name

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


def parse_blocks(html):
    parser = Blocks()
    parser.feed(html)
    if parser.depth:
        raise ValueError("Unbalanced handbook HTML")
    if parser.section:
        raise ValueError(f"Unclosed welcome marker: {parser.section}")
    if parser.figure:
        raise ValueError(f"The figure {parser.figure} needs a caption paragraph right after its marker")
    return parser


def figures(blocks):
    """Figure names in block order."""
    return [match[1] for block in blocks if (match := re.match(r'<figure data-figure="([a-z-]+)">', block))]


def blocks(html):
    return parse_blocks(html).blocks


def inner(block, tag):
    match = re.fullmatch(rf"<{tag}>(.*)</{tag}>", block.strip(), re.DOTALL)
    if not match:
        raise ValueError(f"Expected <{tag}> in the welcome chapter: {block[:60]}")
    return match[1].strip()


def welcome(definition, parser):
    """The first-login welcome's reader layout, read from its own chapter text.

    chapters.json names each tour step and setup card in order (ids, Settings
    routes, icons); the chapter's marked sections give their translated words:
    an h2 title, optional intro paragraphs and one list of `**Title**: text` items.
    The reader draws these blocks itself and lists their indexes in `hidden`."""
    pieces, sections = parser.blocks, parser.sections
    if len(pieces) < 2 or not pieces[0].startswith("<h1>") or not pieces[1].startswith("<p>"):
        raise ValueError("The welcome chapter starts with its title and one lead paragraph")
    result = {"title": inner(pieces[0], "h1"), "lead": inner(pieces[1], "p"), "hidden": [0, 1]}
    for name, entries in definition.items():
        indexes = [index for index, section in enumerate(sections) if section == name]
        if not indexes or indexes != list(range(indexes[0], indexes[-1] + 1)):
            raise ValueError(f"The welcome needs one marked {name} section")
        marked = [pieces[index] for index in indexes]
        if len(marked) < 2 or not marked[0].startswith("<h2>") or not marked[-1].startswith("<ul>"):
            raise ValueError(f"The welcome {name} section is a heading, optional paragraphs and one list")
        items = re.findall(r"<li>(.*?)</li>", marked[-1], re.DOTALL)
        if len(items) != len(entries):
            raise ValueError(f"The welcome {name} list needs {len(entries)} items")
        parsed = []
        for entry, item in zip(entries, items):
            match = re.fullmatch(r"<strong>(.+?)</strong>\s*:\s*(.+)", item.strip(), re.DOTALL)
            if not match:
                raise ValueError(f"Welcome {name} items read **Title**: text: {item[:60]}")
            fields = entry if isinstance(entry, dict) else {"id": entry}
            parsed.append({**fields, "title": match[1], "text": match[2].strip()})
        result[name] = {"title": inner(marked[0], "h2"), "intro": " ".join(inner(block, "p") for block in marked[1:-1]),
                        "items": parsed}
        result["hidden"].extend(indexes)
    return result


def shortcuts():
    # The Handbook is built from this tree's shortcut source, not an installed copy.
    os.environ["EITR_CODE_ROOT"] = str(ROOT)
    from eitr_menu import shortcut_options
    options = shortcut_options()
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
    lines.extend(["", "### Focus mode", "", "These keys replace workspace controls while Focus is on. See the Focus chapter for recovery and monitor behavior.", "",
                  "| Shortcut | Action |", "| :--- | :--- |"])
    for entry in shortcut_entries():
        lines.append("| **" + entry["Subtext"] + "** | " + entry["Text"] + " |")
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
                  "| **Click Idle Lock** | Toggle automatic locking. |"])
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
        parsed = parse_blocks(html)
        if locale != "en" and localized.is_file() and "source" in chapter:
            english = parse_blocks(markdown.markdown(unnest_fences((ROOT / chapter["source"]).read_text()),
                                                     extensions=["tables", "fenced_code", "sane_lists"]))
            if figures(parsed.blocks) != figures(english.blocks):
                raise ValueError(f"{locale}/{chapter['id']} needs the English chapter's figures, in order")
        metadata = {key: value for key, value in chapter.items() if key not in ("source", "generated")}
        if "welcome" in chapter:
            metadata["welcome"] = welcome(chapter["welcome"], parsed)
        elif any(parsed.sections):
            raise ValueError(f"Welcome markers outside the welcome chapter: {chapter['id']}")
        for key in ("title", "summary", "group"):
            if key in metadata:
                metadata[key] = messages.get(metadata[key], metadata[key])
        if locale != "en":
            metadata["sourceLocale"] = locale if localized.is_file() or chapter.get("generated") else "en"
        result.append({**metadata, "markdown": text, "blocks": parsed.blocks})
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
        sys.exit("Handbook catalogs are stale: " + ", ".join(stale) + "; run python3 tools/handbook-build.py")
