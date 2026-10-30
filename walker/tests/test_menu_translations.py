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


@unittest.skipUnless(shutil.which("lua"), "Lua is required for live menu tests")
class LiveMenuTests(unittest.TestCase):
    def test_each_provider_preserves_browse_and_reuses_snapshot_across_lua_states(self):
        providers = [str(path) for path in sorted((ROOT / 'elephant/menus').glob('*.lua'))
                     if 'elephant/live-menu.lua' in path.read_text()
                     or 'cloud-navigation-entries.lua' in path.read_text()]
        decoded = {path.read_text(): json.loads(path.read_text())
                   for path in (ROOT / 'elephant/menu-rows').glob('*.json')}
        script = 'local decoded = ' + lua_value(decoded) + '\nlocal providers = ' + lua_value(providers) + '\n' + r'''
local root = os.getenv('EITR_CODE_ROOT')
local real_dofile, real_open = dofile, io.open
local states, encoded, calls = {}, {}, 0
local bypass = false
local indexed = {Text='Indexed child', Subtext='Child folder', Actions={open='safe-index-activation'}}
local function clone(value)
    if type(value) ~= 'table' then return value end
    local result = {}
    for key, item in pairs(value) do result[key] = clone(item) end
    return result
end
local function fingerprint(value)
    if type(value) ~= 'table' then return tostring(value) end
    local fields = {}
    for key, item in pairs(value) do fields[#fields+1] = tostring(key) .. '=' .. fingerprint(item) end
    table.sort(fields)
    return '{' .. table.concat(fields, '|') .. '}'
end
jsonEncode = function(value)
    encoded[#encoded+1] = clone(value)
    return 'encoded-' .. #encoded
end
jsonDecode = function(raw)
    local number = raw:match('^encoded%-(%d+)$')
    return clone(number and encoded[tonumber(number)] or decoded[raw] or {})
end
state = function() return states[Name] or {} end
setState = function(value) states[Name] = clone(value) end
lastMenuValue = function() return 'account-one' end
io.open = function(path, mode)
    if path:sub(1, #root) == root then return real_open(path, mode) end
    return nil
end
io.popen = function(command)
    calls = calls + 1
    local raw, lines = '', {}
    if command:find('git-accounts.py', 1, true) then
        raw='git-rows'
        decoded[raw]={{id='account-one', label='Account One', provider='github', folders={},
            searchActions={{label='Make Default', hint='Default identity', icon='git'}}}}
    elseif command:find('plugins.py', 1, true) then
        if command:find(' installed', 1, true) then
            raw='plugin-installed'
            decoded[raw]={{id='account-one',name='Plugin One',updateCount=1},
                {id='blocked-one',name='Blocked Plugin',blocked='policy',updateCount=1}}
        elseif command:find(' rows', 1, true) then
            raw='plugin-rows'
            decoded[raw]={{id='account-one',title='Plugin child action',description='Launch it',
                icon='plugin',index=0,official=true},
                {id='blocked-one',title='Blocked child action',description='Hidden',index=0}}
        end
    elseif command:find('ai-accounts.py', 1, true) then
        raw='ai-rows'
        decoded[raw]={supported=true,accounts={{id='account-one',label='AI One',current=true}}}
    elseif command:find('calendars.py', 1, true) then
        raw='calendars'
        decoded[raw]={{id='calendar-one',name='Calendar One',host='example.test'}}
    elseif command:find('webapps.py', 1, true) then
        raw='webapps'
        decoded[raw]={{id='app-one',name='Web One',url='https://example.test',path='/mock/web.desktop',icon='web'}}
    elseif command:find('keyboard-layout.py', 1, true) then
        lines = command:find('catalog-rows', 1, true) and {'us\t\tEnglish Test\t0'} or {'0\tEnglish Test\t1'}
    elseif command:find('navigation.py', 1, true) then
        raw='cloud-snapshot'
        decoded[raw]={entries={{Text='Service folder',SubMenu='aws-ec2',State={'submenu'}}},
            descendants={{parent='Service folder',entries={{Text='Cloud child action',Actions={open='bound-context'}}}}}}
    end
    return {read=function() return raw end, close=function() end,
        lines=function()
            local position=0
            return function() position=position+1; return lines[position] end
        end}
end
dofile = function(path)
    if path == root .. '/elephant/search-index-entries.lua' then
        return function() return {clone(indexed)} end
    end
    if bypass and path == root .. '/elephant/live-menu.lua' then
        return function(name, load) return load end
    end
    return real_dofile(path)
end
for _, provider in ipairs(providers) do
    bypass=true
    dofile(provider)
    local original_parent=Parent
    local expected=GetEntries('')
    bypass=false
    states={}
    dofile(provider)
    -- A cold query is safe: it must not load a provider just for typing.
    local before=calls
    assert(#GetEntries('cold') == 0 and calls == before, provider .. ': cold query ran a provider')
    local browse=GetEntries('')
    assert(fingerprint(browse) == fingerprint(expected), provider .. ': browse parity')
    local own_count=#browse
    before=calls
    -- Reload the entire provider to model Elephant's fresh VM per query.
    dofile(provider)
    local result=GetEntries('child')
    assert(calls == before, provider .. ': query ran a provider')
    assert(Parent == original_parent, provider .. ': parent changed')
    assert(#result >= own_count + 1, provider .. ': missing indexed child')
    assert(result[#result].Text == 'Indexed child', provider .. ': search adapter missing')
    for position=1,own_count do
        assert(fingerprint(result[position]) == fingerprint(browse[position]), provider .. ': query mutated own row')
    end
    local target, parent
    if Name == 'git-accounts' then target='Make Default'; parent='Account One'
    elseif Name == 'plugins-install' or Name == 'plugins' then target='Plugin child action'; parent='Plugin One'
    elseif Name == 'keyboard' then target='English Test'; parent='Add Layout'
    elseif provider:find('/aws-account.lua',1,true) then target='Cloud child action'; parent='Service folder' end
    if target then
        local found=false
        for _, entry in ipairs(result) do
            if entry.Text == target and entry.Subtext == parent then
                found=true
                assert(entry.Actions and entry.Actions.open, provider .. ': child has no bound action')
                if Name == 'git-accounts' or Name == 'plugins-install' then
                    assert(entry.Actions.open:find('account-one',1,true), provider .. ': missing context')
                    assert(entry.Value and entry.Value:find('account-one',1,true), provider .. ': ambiguous identity')
                end
            end
        end
        assert(found, provider .. ': missing live child ' .. target)
    end
    for _, entry in ipairs(result) do
        assert(entry.Text ~= 'Blocked child action', provider .. ': exposed a blocked plugin action')
    end
    dofile(provider)
    GetEntries('another query')
    assert(calls == before, provider .. ': subsequent query ran a provider')
end
'''
        with tempfile.TemporaryDirectory() as temporary:
            environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'),
                               HOME=temporary, XDG_CONFIG_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                               LC_ALL='C.UTF-8')
            result = subprocess.run(['lua', '-'], input=script, text=True, capture_output=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_context_changes_invalidate_without_running_loader(self):
        script = r'''
local root = os.getenv('EITR_CODE_ROOT')
local context, calls = 'first-account', 0
local adapter = dofile(root .. '/elephant/live-menu.lua')
local get = adapter('git-account', function()
    calls=calls+1
    return {{Text='Own', Actions={open='bound-first'}}},
        {{parent='Account', entries={{Text='Nested', Subtext='Original hint', Actions={open='bound-child'}}}}}
end, function() return context end)
assert(#get('cold query') == 0 and calls == 0)
assert(#get('') == 1 and calls == 1)
local found=false
for _, entry in ipairs(get('Nested')) do
    if entry.Text == 'Nested' then
        found=true
        assert(entry.Subtext == 'Account' and entry.Keywords[1] == 'Original hint')
    end
end
assert(found and calls == 1)
context='second-account'
assert(#get('Nested') == 0 and calls == 1)
assert(#get('') == 1 and calls == 2)
'''
        with tempfile.TemporaryDirectory() as temporary:
            environment = dict(os.environ, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'),
                               HOME=temporary, XDG_CONFIG_HOME=temporary, XDG_RUNTIME_DIR=temporary)
            result = subprocess.run(['lua', '-'], input=script, text=True, capture_output=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stderr)
