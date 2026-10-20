#!/usr/bin/env python3
"""Build emojis.json, the picker's searchable list, from Unicode's own data.

  build-emojis.py EMOJI_TEST ANNOTATIONS DERIVED [--max-version 16.0]

EMOJI_TEST is https://unicode.org/Public/emoji/latest/emoji-test.txt; ANNOTATIONS
and DERIVED are CLDR's English keywords, annotations/en/annotations.json from the
cldr-annotations-full package and annotationsDerived/en/annotations.json from
cldr-annotations-derived-full (both on npm). All are Unicode-3.0 licensed
(see NOTICE). Only fully qualified emoji up to --max-version are kept, matching
what the Noto Color Emoji font in the package list can draw; skin tone and hair
variants are left out so each emoji appears once.
"""
import argparse
import json
from pathlib import Path
import re

LINE = re.compile(r"^([0-9A-F ]+?)\s*;\s*fully-qualified\s*#\s*\S+\s+E(\d+\.\d+)\s+(.+)$")
VARIANTS = {0x1F3FB, 0x1F3FC, 0x1F3FD, 0x1F3FE, 0x1F3FF, 0x1F9B0, 0x1F9B1, 0x1F9B2, 0x1F9B3}


def keywords(path, section):
    entries = json.loads(Path(path).read_text())[section]["annotations"]
    return {emoji.replace("️", ""): " ".join(value.get("tts", []) + value.get("default", []))
            for emoji, value in entries.items()}


def build(test_file, annotations, derived, max_version):
    words = keywords(derived, "annotationsDerived") | keywords(annotations, "annotations")
    result = []
    for line in Path(test_file).read_text().splitlines():
        match = LINE.match(line)
        if not match or float(match.group(2)) > max_version:
            continue
        points = [int(point, 16) for point in match.group(1).split()]
        if VARIANTS.intersection(points):
            continue
        emoji = "".join(map(chr, points))
        found = words.get(emoji.replace("️", ""), "")
        terms = []
        for word in (match.group(3) + " " + found).lower().replace(":", " ").split():
            if word not in terms:
                terms.append(word)
        result.append({"e": emoji, "k": " ".join(terms)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("emoji_test")
    parser.add_argument("annotations")
    parser.add_argument("derived")
    parser.add_argument("--max-version", type=float, default=16.0)
    arguments = parser.parse_args()
    emojis = build(arguments.emoji_test, arguments.annotations, arguments.derived, arguments.max_version)
    output = Path(__file__).with_name("emojis.json")
    output.write_text(json.dumps(emojis, separators=(",", ":")) + "\n")
    print(f"Wrote {len(emojis)} emoji to {output}")


if __name__ == "__main__":
    main()
