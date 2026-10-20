"""System-locale selection and Eitr's single gettext domain for user messages."""
import argparse
from functools import lru_cache
import gettext
import json
import os
from pathlib import Path
import re
import string
import sys

from eitr_paths import code_root

DOMAIN = "eitr"
SOURCE = "en"


def mark(message):
    """Register display text whose English value is also a stable internal key."""
    return message


def normalize(value):
    value = value.strip().split(".", 1)[0].split("@", 1)[0].replace("-", "_")
    if value.upper() in {"", "C", "POSIX"}:
        return SOURCE
    if not re.fullmatch(r"[a-zA-Z]{2,3}(?:_[a-zA-Z]{2}|_[0-9]{3})?", value):
        return SOURCE
    parts = value.split("_")
    return parts[0].lower() + ("_" + parts[1].upper() if len(parts) > 1 else "")


def system_locale(environment=None):
    environment = os.environ if environment is None else environment
    return normalize(next((environment[key] for key in ("LC_ALL", "LC_MESSAGES", "LANG")
                           if environment.get(key, "").strip()), "en"))


def candidates(locale):
    normalized = normalize(locale)
    alias = "pt_BR" if normalized.split("_", 1)[0] == "pt" else normalized.split("_", 1)[0]
    return list(dict.fromkeys((normalized, alias, SOURCE)))


@lru_cache(maxsize=16)
def languages(root=None):
    try:
        return json.loads((code_root(root) / "i18n/languages.json").read_text())["languages"]
    except FileNotFoundError:
        return {"en": {"name": "English", "nativeName": "English"}}


def select_locale(environment=None, supported=None):
    supported = languages() if supported is None else supported
    return _select_locale(system_locale(environment), tuple(supported))


@lru_cache(maxsize=32)
def _select_locale(locale, supported):
    return next(candidate for candidate in candidates(locale) if candidate in supported)


@lru_cache(maxsize=16)
def _catalog(root, locale):
    return gettext.translation(DOMAIN, localedir=Path(root) / "i18n/locales",
                               languages=candidates(locale), fallback=True)


def translator(locale=None, root=None):
    root = code_root(root)
    selected = locale or select_locale(supported=languages(root))
    return _catalog(str(root), selected)


def tr(message, **values):
    translated = translator().gettext(message)
    return translated.format(**values) if values else translated


@lru_cache(maxsize=8)
def _rendered_patterns(root):
    filename = Path(root) / "i18n/catalogs/en/helpers.json"
    if not filename.is_file():
        return []
    patterns = []
    for source in json.loads(filename.read_text()):
        fields = []
        parts = []
        literal_length = 0
        try:
            for literal, field, specification, conversion in string.Formatter().parse(source):
                parts.append(re.escape(literal))
                literal_length += len(literal)
                if field is not None:
                    if not field.isidentifier() or specification or conversion:
                        break
                    parts.append("(?P=" + field + ")" if field in fields else "(?P<" + field + ">.*?)")
                    fields.append(field)
            else:
                if fields and literal_length > 2:
                    patterns.append((literal_length, source, re.compile("^" + "".join(parts) + "$", re.DOTALL)))
        except ValueError:
            continue
    return sorted(patterns, key=lambda entry: (-entry[0], entry[1]))


def rendered(message):
    """Localize a shell-expanded message without evaluating its captured values."""
    translated = tr(message)
    if translated != message:
        return translated
    for _, source, pattern in _rendered_patterns(str(code_root())):
        match = pattern.fullmatch(message)
        if match:
            return tr(source, **match.groupdict())
    return message


def ntr(singular, plural, count, **values):
    return translator().ngettext(singular, plural, count).format(count=count, **values)


def table(layer, locale=None, root=None):
    if layer not in {"qml", "menus", "handbook"}:
        raise ValueError("Unknown translation layer")
    root = code_root(root)
    merged = {}
    for candidate in reversed(candidates(locale or system_locale())):
        filename = root / "i18n/catalogs" / candidate / (layer + ".json")
        if filename.is_file():
            merged.update({key: value for key, value in json.loads(filename.read_text()).items()
                           if isinstance(value, str) and value})
    return merged


def metadata():
    supported = languages()
    locale = select_locale(supported=supported)
    return {"locale": locale, "systemLocale": system_locale(), **supported[locale]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--info", action="store_true")
    parser.add_argument("--locale", action="store_true")
    parser.add_argument("--table", choices=("qml", "menus", "handbook"))
    parser.add_argument("--plural")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("message", nargs="?")
    parser.add_argument("values", nargs="*")
    arguments = parser.parse_args(argv)
    if arguments.locale:
        print(select_locale())
    elif arguments.info:
        print(json.dumps(metadata(), ensure_ascii=False))
    elif arguments.table:
        print(json.dumps(table(arguments.table), ensure_ascii=False))
    elif arguments.message is not None:
        values = {}
        for value in arguments.values:
            name, separator, content = value.partition("=")
            if not separator or not name.isidentifier():
                parser.error("Message values must be named NAME=VALUE")
            values[name] = content
        if values:
            print(tr(arguments.message, **values), end="")
            return
        print(translator().ngettext(arguments.message, arguments.plural, arguments.count)
              if arguments.plural is not None else rendered(arguments.message), end="")
    else:
        parser.error("Supply a message, --info or --table")


if __name__ == "__main__":
    main()
