#!/usr/bin/env python3
"""Extract marked English messages and validate every translation catalog."""
import argparse
import ast
from collections import Counter
import json
import importlib.util
from pathlib import Path
import re
import shutil
import string
import subprocess
import sys
import tempfile
import tomllib
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ("qml", "menus", "handbook", "helpers")
LITERAL = r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''


def sort_key(title):
    return "".join(character for character in unicodedata.normalize("NFKD", title)
                   if not unicodedata.combining(character)).casefold()


def placeholders(message):
    qt = Counter(re.findall(r"%[1-9][0-9]*|%n", message))
    brace = Counter(field for _, field, _, _ in string.Formatter().parse(message) if field is not None)
    printf = Counter(re.findall(r"(?<![0-9])%(?:\([^)]+\))?[-+#0 ]*[0-9]*(?:\.[0-9]+)?[sdif]", message))
    return qt, brace, printf


def extract(root=ROOT):
    sources = {layer: {} for layer in LAYERS}

    def add(layer, message, path):
        if message and message != ">":
            sources[layer].setdefault(message, []).append(str(path.relative_to(root)))

    for path in sorted([*(root / "quickshell").rglob("*.qml"),
                        *(root / "distro/plugins/example").glob("*.qml")]):
        parts = path.relative_to(root).parts
        if "tests" in parts or "references" in parts or path.name.endswith("-preview.qml"):
            continue
        for match in re.finditer(r"\bI18n\.tr\(\s*(" + LITERAL + ")", path.read_text()):
            add("qml", ast.literal_eval(match[1]), path)
    for path in sorted((root / "elephant/menu-rows").glob("*.json")):
        for row in json.loads(path.read_text()):
            for field in ("text", "subtext"):
                add("menus", row.get(field), path)
    for path in sorted((root / "elephant/menus").glob("*.toml")):
        data = tomllib.loads(path.read_text())
        add("menus", data.get("name_pretty"), path)
        for row in data.get("entries", []):
            for field in ("text", "subtext"):
                add("menus", row.get(field), path)
    for path in sorted([*(root / "elephant").rglob("*.lua"),
                        *(root / "walker/scripts/menus").glob("*.lua")]):
        for match in re.finditer(r"\b(?:Text\s*=|Subtext\s*=|NamePretty\s*=|i18n\.(?:tr|mark)\()\s*(" + LITERAL + ")", path.read_text()):
            # Lua byte escapes belong to glyphs, never to translatable labels.
            if not re.search(r"\\[0-9]", match[1]):
                add("menus", ast.literal_eval(match[1]), path)
    book = root / "quickshell/desktop-bar/handbook/chapters.json"
    for chapter in json.loads(book.read_text()):
        for field in ("title", "summary"):
            add("handbook", chapter.get(field), book)
    shortcut_builder = root / "quickshell/desktop-bar/scripts/handbook-build.py"
    specification = importlib.util.spec_from_file_location("i18n_handbook_build", shortcut_builder)
    handbook_builder = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(handbook_builder)
    for message in handbook_builder.shortcut_messages():
        add("handbook", message, shortcut_builder)
    for directory in ("walker", "quickshell", "distro", "hypr", "fastfetch"):
        python_files = list((root / directory).rglob("*.py"))
        for entrypoints in (root / directory / "bin", root / directory / "archinstall"):
            for path in entrypoints.glob("*"):
                if path.is_file() and not path.suffix and "python3" in path.read_text().splitlines()[0]:
                    python_files.append(path)
        for path in sorted(set(python_files)):
            if path.is_relative_to(root / "distro/payload") or path.is_relative_to(root / "distro/repo"):
                continue
            # Folders inside the checkout only: a package build itself runs under src/.
            if set(path.relative_to(root).parts) & {"tests", "build", "out", "__pycache__", "references", "src", "pkg"}:
                continue
            syntax = ast.parse(path.read_text(), filename=str(path))
            imported = {alias.asname or alias.name: alias.name for node in ast.walk(syntax)
                        if isinstance(node, ast.ImportFrom) and node.module == "eitr_i18n"
                        for alias in node.names if alias.name in {"tr", "ntr", "mark"}}
            for node in ast.walk(syntax):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in imported:
                    for argument in node.args[:2 if imported[node.func.id] == "ntr" else 1]:
                        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                            add("menus" if node.func.id == "menu_mark" else "helpers", argument.value, path)
        for path in sorted((root / directory).rglob("*.sh")):
            if set(path.relative_to(root).parts) & {"tests", "build", "out", "references", "src", "pkg"}:
                continue
            for match in re.finditer(r"\beitr_gettext\s+(" + LITERAL + ")", path.read_text()):
                add("helpers", ast.literal_eval(match[1]), path)
    return {layer: {message: sorted(set(paths)) for message, paths in sorted(messages.items())}
            for layer, messages in sources.items()}


def render(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def gettext_source(messages, locale):
    """PO is an export of the canonical JSON; GNU msgfmt owns MO serialization."""
    def quote(value):
        escapes = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
        return '"' + ''.join(escapes.get(character, "\\%03o" % ord(character) if ord(character) < 32 else character)
                              for character in value) + '"'
    plural = "n > 1" if locale in {"fr", "pt_BR"} else "n != 1"
    header = "Project-Id-Version: Eitr\nContent-Type: text/plain; charset=UTF-8\nLanguage: " + locale + "\nPlural-Forms: nplurals=2; plural=(" + plural + ");\n"
    lines = ['msgid ""', 'msgstr ' + quote(header), '']
    for source, translated in sorted(messages.items()):
        lines.extend(['msgid ' + quote(source), 'msgstr ' + quote(translated), ''])
    return '\n'.join(lines)


def compile_gettext(messages, locale):
    if not shutil.which("msgfmt"):
        raise RuntimeError("GNU gettext (msgfmt) is required to build translation catalogs")
    source = gettext_source(messages, locale)
    with tempfile.TemporaryDirectory(prefix="eitr-gettext-") as temporary:
        po = Path(temporary) / "eitr.po"
        mo = Path(temporary) / "eitr.mo"
        po.write_text(source)
        subprocess.run(["msgfmt", "--check-format", "--no-hash", "-o", str(mo), str(po)],
                       check=True, capture_output=True, text=True)
        return source, mo.read_bytes()


def validate(catalog, sources):
    errors = []
    for message in sources:
        if message not in catalog or not isinstance(catalog[message], str) or not catalog[message]:
            errors.append("Missing translation: " + repr(message))
        else:
            try:
                if placeholders(message) != placeholders(catalog[message]):
                    errors.append("Placeholder mismatch: " + repr(message))
            except ValueError:
                errors.append("Invalid placeholder syntax: " + repr(message))
    for message in catalog.keys() - sources.keys():
        errors.append("Stale translation: " + repr(message))
    return errors


def english_catalog(previous, sources):
    messages = {message: message for message in previous if message in sources}
    messages.update({message: message for message in sources if message not in messages})
    return messages


def build(check=False, root=ROOT):
    sources = extract(root)
    outputs = {root / "i18n/sources.json": render(sources)}
    for layer in LAYERS:
        filename = root / "i18n/catalogs/en" / (layer + ".json")
        previous = json.loads(filename.read_text()) if filename.is_file() else {}
        outputs[filename] = render(english_catalog(previous, sources[layer]))
    errors = []
    for filename, contents in outputs.items():
        if check:
            if not filename.is_file() or filename.read_text() != contents:
                errors.append("Stale English catalog: " + str(filename.relative_to(root)))
        else:
            filename.parent.mkdir(parents=True, exist_ok=True)
            filename.write_text(contents)
    for locale in json.loads((root / "i18n/languages.json").read_text())["languages"]:
        for layer in LAYERS:
            filename = root / "i18n/catalogs" / locale / (layer + ".json")
            if not filename.is_file():
                errors.append("Missing catalog: " + str(filename.relative_to(root)))
                continue
            for error in validate(json.loads(filename.read_text()), sources[layer]):
                errors.append(locale + "/" + layer + ": " + error)
    language_data = json.loads((root / "i18n/languages.json").read_text())["languages"]
    language_lua = "return {\n" + "".join("    [" + json.dumps(locale) + "] = true,\n" for locale in language_data) + "}\n"
    output = root / "i18n/languages.lua"
    if check:
        if not output.is_file() or output.read_text() != language_lua:
            errors.append("Stale generated Lua languages")
    else:
        output.write_text(language_lua)
    bundles = {"languages": json.loads((root / "i18n/languages.json").read_text())["languages"], "qml": {}}
    for locale in bundles["languages"]:
        filename = root / "i18n/catalogs" / locale / "qml.json"
        if filename.is_file():
            bundles["qml"][locale] = json.loads(filename.read_text())
        helper_file = root / "i18n/catalogs" / locale / "helpers.json"
        if helper_file.is_file():
            po, mo = compile_gettext(json.loads(helper_file.read_text()), locale)
            for extension, contents in (("po", po.encode()), ("mo", mo)):
                output = root / "i18n/locales" / locale / "LC_MESSAGES" / ("eitr." + extension)
                if check:
                    if not output.is_file() or output.read_bytes() != contents:
                        errors.append("Stale gettext catalog: " + str(output.relative_to(root)))
                else:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(contents)
        menu_file = root / "i18n/catalogs" / locale / "menus.json"
        if menu_file.is_file():
            messages = json.loads(menu_file.read_text())
            quote = lambda value: json.dumps(value, ensure_ascii=False)
            rows = ["return {", "    messages = {"]
            rows.extend("        [" + quote(message) + "] = " + quote(value) + "," for message, value in sorted(messages.items()))
            rows.extend(["    },", "    sortKeys = {"])
            rows.extend("        [" + quote(value) + "] = " + quote(sort_key(value)) + "," for value in sorted(set(messages.values())))
            rows.extend(["    },", "    language = " + quote(bundles["languages"][locale]["nativeName"]), "}"])
            rendered = "\n".join(rows) + "\n"
            output = menu_file.with_suffix(".lua")
            if check:
                if not output.is_file() or output.read_text() != rendered:
                    errors.append("Stale generated menu catalog: " + locale)
            else:
                output.write_text(rendered)
    pending = {}
    for locale in bundles["languages"]:
        if locale == "en":
            continue
        helper_path = root / "i18n/catalogs" / locale / "helpers.json"
        if helper_path.is_file():
            pending[locale] = [source for source, translated in json.loads(helper_path.read_text()).items()
                               if source == translated]
    report = root / "i18n/pending-helpers.json"
    if check:
        if not report.is_file() or report.read_text() != render(pending):
            errors.append("Stale helper English-fallback report")
    else:
        report.write_text(render(pending))
    generated = ".pragma library\n\nvar languages = " + json.dumps(bundles["languages"], ensure_ascii=False, indent=2) + ";\nvar qml = " + json.dumps(bundles["qml"], ensure_ascii=False, indent=2) + ";\n"
    filename = root / "quickshell/Eitr/Catalogs.js"
    if check:
        if not filename.is_file() or filename.read_text() != generated:
            errors.append("Stale generated QML catalogs")
    else:
        filename.write_text(generated)
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    problems = build(check=arguments.check)
    if problems:
        sys.exit("\n".join(problems))
