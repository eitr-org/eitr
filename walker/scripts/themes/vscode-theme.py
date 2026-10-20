#!/usr/bin/env python3
"""Read Eitr's vscode.json and set the VS Code color theme in settings.json.

VS Code's settings.json is JSONC.  Only the value of the requested top-level
key is replaced textually, so comments, trailing commas and formatting survive.

Usage:
  vscode-theme.py read THEME_JSON          print name, extension, vsix lines
  vscode-theme.py set SETTINGS_JSON NAME   set "workbench.colorTheme"
"""

import json
from pathlib import Path
import sys

THEME_KEY = "workbench.colorTheme"


def tokens(text):
    """Yield (kind, start, end) for JSONC tokens, skipping whitespace/comments."""
    index, length = 0, len(text)
    while index < length:
        char = text[index]
        if char.isspace():
            index += 1
        elif text.startswith("//", index):
            newline = text.find("\n", index)
            index = length if newline < 0 else newline + 1
        elif text.startswith("/*", index):
            close = text.find("*/", index + 2)
            if close < 0:
                raise ValueError("unterminated block comment")
            index = close + 2
        elif char == '"':
            end = index + 1
            while end < length and text[end] != '"':
                end += 2 if text[end] == "\\" else 1
            if end >= length:
                raise ValueError("unterminated string")
            yield "string", index, end + 1
            index = end + 1
        elif char in "{}[]:,":
            yield char, index, index + 1
            index += 1
        else:
            end = index
            while end < length and not text[end].isspace() and text[end] not in '{}[]:,"/':
                end += 1
            if end == index:
                raise ValueError(f"unexpected character at offset {index}")
            yield "literal", index, end
            index = end


def set_top_level_string(text, key, value):
    """Return text with the top-level key set to the JSON string value."""
    stream = list(tokens(text))
    if not stream or stream[0][0] != "{":
        raise ValueError("settings must be a JSON object")
    encoded = json.dumps(value, ensure_ascii=False)
    depth = 0
    for position, (kind, start, end) in enumerate(stream):
        if kind in "{[":
            depth += 1
        elif kind in "}]":
            depth -= 1
        elif (kind == "string" and depth == 1 and json.loads(text[start:end]) == key
              and position + 2 < len(stream) and stream[position + 1][0] == ":"):
            value_start = stream[position + 2][1]
            value_end, nested = value_start, 0
            for inner_kind, _, inner_end in stream[position + 2:]:
                if inner_kind in "{[":
                    nested += 1
                elif inner_kind in "}]":
                    if nested == 0:
                        break
                    nested -= 1
                elif inner_kind == "," and nested == 0:
                    break
                value_end = inner_end
            return text[:value_start] + encoded + text[value_end:]

    # Key absent: insert it as the first member, keeping existing members intact.
    opening = stream[0][2]
    separator = "," if stream[1][0] != "}" else ""
    return text[:opening] + f"\n  {json.dumps(key)}: {encoded}{separator}" + text[opening:]


def main(argv):
    if len(argv) == 3 and argv[1] == "read":
        data = json.loads(Path(argv[2]).read_text())
        for field in ("name", "extension", "vsix"):
            print(str(data.get(field, "")).replace("\n", " "))
        return 0
    if len(argv) == 4 and argv[1] == "set":
        path = Path(argv[2]).resolve()  # keep a symlinked settings.json linked
        text = path.read_text() if path.exists() and path.read_text().strip() else "{}\n"
        try:
            updated = set_top_level_string(text, THEME_KEY, argv[3])
        except ValueError as error:
            print(f"Could not parse VS Code settings: {error}", file=sys.stderr)
            return 1
        if updated != text:
            temporary = path.with_name(path.name + ".eitr-tmp")
            temporary.write_text(updated)
            temporary.replace(path)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
