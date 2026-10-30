"""Elephant menu definitions for the tests: TOML menus, and Lua menus (name,
parent and icon from the Lua file; rows from elephant/menu-rows/<name>.json when
the menu's rows are data)."""
from eitr_menu import rows as menu_rows
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[2]
MENUS = ROOT / "elephant/menus"
ROWS = ROOT / "elephant/menu-rows"


def load(name):
    toml = MENUS / f"{name}.toml"
    if toml.is_file():
        return tomllib.loads(toml.read_text())
    lua = (MENUS / f"{name}.lua").read_text()
    rows = ROWS / f"{name}.json"
    # Other Lua menus generate their rows; only their metadata is static.
    data = {"name": name, "entries": menu_rows(name) if rows.is_file() else []}
    for key, field in (("NamePretty", "name_pretty"), ("Parent", "parent"), ("Icon", "icon")):
        match = re.search(rf'^{key} = (?:i18n\.tr\()?"([^"]*)"', lua, re.M)
        if match:
            data[field] = match[1]
    return data


def static_menus():
    """{name: definition} for every menu whose rows are data."""
    names = [path.stem for path in MENUS.glob("*.toml")] + [path.stem for path in ROWS.glob("*.json")]
    return {name: load(name) for name in sorted(names)}
