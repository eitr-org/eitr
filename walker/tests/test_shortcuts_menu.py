"""Pre-refactor fixtures exercise all fixed rows without querying the desktop."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import unittest
from unittest.mock import patch

from eitr_menu import definitions, rows, shortcut_reference, shortcut_options, shortcut_command
from test_menu_translations import lua_value

ROOT = Path(__file__).resolve().parents[2]
BASELINE = json.loads((Path(__file__).with_name('fixtures') / 'menu-parity.json').read_text())

SCRIPT = ROOT / "walker/scripts/menus/shortcuts.sh"


class ShortcutsMenuTests(unittest.TestCase):
    def test_each_row_resolves_its_exact_binding(self):
        for entry in shortcut_reference():
            if 'key' in entry:
                selection = '  ' + entry['key'].ljust(26) + entry['description']
                self.assertEqual(shortcut_command(selection), entry['command'])
                self.assertEqual(shortcut_command(selection.strip()), entry['command'])
        self.assertIsNone(shortcut_command('SUPER + Unknown  Unknown action'))


class AssistantShortcutTests(unittest.TestCase):
    def test_assistant_and_rotate_bindings(self):
        configuration = (SCRIPT.parents[3] / 'hypr/hyprland.lua').read_text()
        self.assertIn('mainMod .. " + A", hl.dsp.exec_cmd("python3 /usr/share/eitr/walker/scripts/actions/ai-assistant.py open")', configuration)
        self.assertIn('mainMod .. " + SHIFT + R", hl.dsp.layout("rotatesplit")', configuration)
        self.assertNotIn('mainMod .. " + ALT + A"', configuration)


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shell_tokens(command):
    for variable, value in (('$EITR_CODE_ROOT', '/usr/share/eitr'),
                            ('$MENUS_DIR', '/usr/share/eitr/walker/scripts/menus'),
                            ('$ACTIONS_DIR', '/usr/share/eitr/walker/scripts/actions')):
        command = command.replace(variable, value)
    return shlex.split(command)


class MenuParityTests(unittest.TestCase):
    def test_every_fixed_definition_and_parent_matches_baseline(self):
        self.assertEqual({name: data['entries'] for name, data in definitions().items()}, BASELINE['rows'])
        search = load_script('parity_search', 'walker/scripts/menus/search-index.py')
        self.assertEqual(search.parents(), BASELINE['parents'])
        action = load_script('parity_action', 'quickshell/desktop-bar/scripts/menu-action.py')
        for name, expected in BASELINE['rows'].items():
            self.assertEqual(action.rows(name), expected)
            self.assertEqual(rows(name), expected)

    def test_entire_fixed_search_snapshot_matches_baseline(self):
        search = load_script('parity_search', 'walker/scripts/menus/search-index.py')
        output = []
        for name, entries in BASELINE['rows'].items():
            for index, row in enumerate(entries):
                output.append(json.dumps({'item': dict(provider='menus:' + name,
                    identifier=name + ':' + str(index), text=row['text'],
                    subtext=row.get('subtext', ''), icon=row.get('icon', ''),
                    actions=list(row.get('actions', {})))}))
        with patch.object(search, 'system_batteries', return_value=[Path('/mock/BAT0')]):
            actual = search.snapshot('\n'.join(output), search.keyword_index(), search.parents(), search.definitions())
        self.assertEqual(actual, BASELINE['search'])

    def test_shell_reference_order_spacing_labels_and_actions_match_baseline(self):
        expected = BASELINE['shortcuts']
        self.assertEqual(shortcut_options(), '\n'.join(entry.get('heading', entry.get('line')) for entry in expected))
        for before, after in zip(expected, shortcut_reference(), strict=True):
            if 'key' in before:
                self.assertEqual(after['key'], before['key'])
                self.assertEqual(shell_tokens(after['command']), shell_tokens(before['command']))

    def test_reference_tracks_canonical_binding_and_action_changes(self):
        import eitr_menu
        changed = [dict(row) for row in rows('shortcuts')]
        target = next(row for row in changed if row['text'] == 'Search Apps')
        target['subtext'] = 'SUPER + NewBinding'
        target['actions'] = {'open': 'updated-command'}
        with patch.object(eitr_menu, 'rows', return_value=changed):
            entry = next(entry for entry in shortcut_reference() if entry.get('row') == 'Search Apps')
            self.assertEqual(entry['key'], 'SUPER + NewBinding')
            self.assertEqual(entry['command'], 'updated-command')

    def test_browse_projection_matches_old_adapter_in_every_locale(self):
        decoded = {path.read_text(): json.loads(path.read_text()) for path in (ROOT / 'elephant/menu-rows').glob('*.json')}
        script = 'local decoded = ' + lua_value(decoded) + '\n' + r'''
jsonDecode = function(raw) return decoded[raw] or {} end
io.popen = function() return {read=function() return "" end, close=function() end} end
local root = os.getenv("EITR_CODE_ROOT")
local project = dofile(root .. "/elephant/row-entry.lua")
local i18n = dofile(root .. "/elephant/i18n.lua")
local function fingerprint(value)
    if type(value) ~= "table" then return type(value) .. ":" .. tostring(value) end
    local parts = {}
    for key, item in pairs(value) do parts[#parts+1] = tostring(key) .. "=" .. fingerprint(item) end
    table.sort(parts)
    return "{" .. table.concat(parts, ";") .. "}"
end
for _, rows in pairs(decoded) do
    local before, after = {}, {}
    for _, row in ipairs(rows) do
        local submenu = row.subtext == ">"
        before[#before+1] = {Text=row.text, Subtext=not submenu and row.subtext or nil,
            State=submenu and {"submenu"} or nil, Keywords=row.keywords,
            Icon=row.icon, SubMenu=row.submenu, Actions=row.actions}
        local entry = project(row)
        entry.SubMenu = row.submenu
        entry.Actions = row.actions
        after[#after+1] = entry
    end
    assert(fingerprint(i18n.entries(before, false)) == fingerprint(i18n.entries(after, false)))
end
'''
        for locale in ('en', 'pt_BR', 'es', 'de', 'fr'):
            environment = dict(os.environ, LC_ALL=locale, EITR_CODE_ROOT=str(ROOT), EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'))
            result = subprocess.run(['lua', '-'], input=script, text=True, capture_output=True, env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
