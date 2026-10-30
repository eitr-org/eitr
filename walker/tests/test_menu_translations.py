import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def lua_value(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "nil"
    if isinstance(value, dict):
        return "{" + ",".join("[" + lua_value(key) + "]=" + lua_value(item) for key, item in value.items()) + "}"
    if isinstance(value, list):
        return "{" + ",".join(lua_value(item) for item in value) + "}"
    return str(value)


@unittest.skipUnless(shutil.which("lua"), "Lua is required for provider translation tests")
class MenuTranslationTests(unittest.TestCase):
    def test_plugin_authored_labels_remain_literal(self):
        script = r'''
local i18n = dofile(os.getenv("EITR_CODE_ROOT") .. "/elephant/i18n.lua")
local rows = i18n.entries({{Text="About", Subtext="Weather", Translate=false}, {Text="About", Subtext="Weather"}}, true)
assert(rows[1].Text == "About" and rows[1].Subtext == "Weather")
assert(rows[2].Text ~= "About" and rows[2].Subtext ~= "Weather")
'''
        environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"), LC_ALL="de_DE.UTF-8")
        result = subprocess.run(["lua", "-"], input=script, text=True, capture_output=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_named_values_are_not_interpreted_as_more_placeholders(self):
        script = 'local i18n = dofile(os.getenv("EITR_CODE_ROOT") .. "/elephant/i18n.lua")\n' + \
                 'assert(i18n.tr("{current} of {total}", {current="{total}", total="%1"}) == "{total} of %1")\n'
        environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT),
                           EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"))
        subprocess.run(["lua", "-"], input=script, text=True, env=environment, check=True)

    def test_every_menu_loads_in_each_locale_without_executing_actions(self):
        decoded = {path.read_text(): json.loads(path.read_text())
                   for path in (ROOT / "elephant/menu-rows").glob("*.json")}
        providers = [str(path) for path in sorted((ROOT / "elephant/menus").glob("*.lua"))]
        script = "local decoded = " + lua_value(decoded) + "\nlocal providers = " + lua_value(providers) + "\n" + r'''
io.popen = function(command)
    assert(not command:find("eitr_i18n.py", 1, true), "locale resolution must not spawn Python")
    return {read=function() return "" end, close=function() return true end,
        lines=function() return function() return nil end end}
end
jsonDecode = function(raw) return decoded[raw] or {} end
jsonEncode = function() return "[]" end
lastMenuValue = function() return "" end
state = function() return {} end
setState = function() end
for _, provider in ipairs(providers) do
    GetEntries = nil
    dofile(provider)
    assert(type(Name) == "string" and type(NamePretty) == "string", provider)
    assert(type(GetEntries) == "function", provider)
    local entries = GetEntries("")
    local i18n = dofile(os.getenv("EITR_CODE_ROOT") .. "/elephant/i18n.lua")
    assert(i18n.language() == os.getenv("EITR_EXPECTED_LANGUAGE"), "wrong locale: " .. i18n.language())
    assert(type(entries) == "table", provider)
    local fingerprints = {}
    for _, entry in ipairs(entries) do
        local actions = {}
        for action, command in pairs(entry.Actions or {}) do
            actions[#actions + 1] = action .. "=" .. command
        end
        table.sort(actions)
        fingerprints[#fingerprints + 1] = tostring(entry.Value or "") .. "|" .. tostring(entry.SubMenu or "") .. "|" .. tostring(entry.Icon or "") .. "|" .. table.concat(entry.State or {}, ",") .. "|" .. table.concat(actions, "|")
        if Name == "system" and entry.Text:find(" · ", 1, true) then
            local english = false
            for _, keyword in ipairs(entry.Keywords or {}) do if keyword == "Language" then english = true end end
            assert(english, "Language must retain its English search keyword")
        end
    end
    table.sort(fingerprints)
    print(Name .. "\t" .. #entries .. "\t" .. table.concat(fingerprints, "\t"))
end
'''
        outputs = []
        for locale, language in (("en_US.UTF-8", "English"), ("pt_BR.UTF-8", "Português (Brasil)"),
                                 ("es_ES.UTF-8", "Español"), ("de_DE.UTF-8", "Deutsch"),
                                 ("fr_FR.UTF-8", "Français"), ("pt_PT.UTF-8", "Português (Brasil)"),
                                 ("pt", "Português (Brasil)")):
            with self.subTest(locale=locale), tempfile.TemporaryDirectory() as temporary:
                fixture = Path(temporary) / "providers.lua"
                fixture.write_text(script)
                environment = dict(os.environ, LC_ALL="", LC_MESSAGES=locale,
                                   EITR_EXPECTED_LANGUAGE=language, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"),
                                   XDG_CONFIG_HOME=temporary, XDG_RUNTIME_DIR=temporary)
                result = subprocess.run(["lua", str(fixture)], env=environment, text=True,
                                        capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs.append(result.stdout)
        for output in outputs[1:]:
            self.assertEqual(output, outputs[0], "Localization must not change actions, values, icons or submenu routing")

    def test_cloud_setup_subtitle_and_search_follow_the_locale(self):
        script = r'''
io.popen = function()
    return {lines=function() return function() return nil end end, close=function() end}
end
local root = os.getenv("EITR_CODE_ROOT")
local factory = dofile(root .. "/elephant/cloud-context-entries.lua")
local i18n = dofile(root .. "/elephant/i18n.lua")
local expected = i18n.tr("Name it, then sign in")
assert(expected ~= "Name it, then sign in", "subtitle requires a translation")
local entries = factory("gcp", "cloud")()
assert(entries[1].Subtext == expected, "dynamic subtitle must be localized")
entries = i18n.entries(entries)
local keywords = ""
for _, entry in ipairs(entries) do
    if entry.Subtext == expected then keywords = table.concat(entry.Keywords, "|") end
end
assert(keywords:find(expected, 1, true), "translated subtitle must be searchable")
assert(keywords:find("Name it, then sign in", 1, true), "English subtitle must remain searchable")
assert(keywords:find("Add GCP Account", 1, true), "English title must remain searchable")
'''
        for locale in ("pt_BR", "es", "de", "fr"):
            with self.subTest(locale=locale), tempfile.TemporaryDirectory() as temporary:
                fixture = Path(temporary) / "cloud.lua"
                fixture.write_text(script)
                environment = dict(os.environ, LC_ALL="", LC_MESSAGES=locale,
                                   EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / "distro/lib"),
                                   XDG_CONFIG_HOME=temporary, XDG_RUNTIME_DIR=temporary)
                result = subprocess.run(["lua", str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_lua_uses_51_compatible_glyph_escapes(self):
        for path in (ROOT / "elephant").rglob("*.lua"):
            self.assertNotIn(r"\u{F00C}", path.read_text(), str(path))
