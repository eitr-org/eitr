"""Portable preferences, validation, compositor projections and inert CLI summaries."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import eitr_keybinds as keys
import eitr_window_rules as rules

ROOT = Path(__file__).resolve().parents[3]


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.config = Path(self.folder.name)
        environment = patch.dict(os.environ, XDG_CONFIG_HOME=str(self.config), XDG_DATA_HOME=str(self.config / 'data'), XDG_DATA_DIRS=str(self.config / 'system'))
        environment.start()
        self.addCleanup(environment.stop)

    def test_normalization_and_validation(self):
        self.assertEqual(keys.normalize('shift + super + enter'), 'SUPER + SHIFT + RETURN')
        self.assertEqual(keys.normalize('ctrl + super + /'), 'SUPER + CTRL + SLASH')
        for invalid in ('SUPER + SUPER + E', 'SUPER +', 'BOGUS', 'SUPER + E;bad'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                keys.normalize(invalid)

    def test_clash_swap_disable_reset_and_projection(self):
        with self.assertRaisesRegex(ValueError, 'is used by'):
            keys.change('set', 'SUPER + E', 'SUPER + T')
        keys.change('set', 'SUPER + E', 'SUPER + T', swap=True)
        self.assertEqual(keys.load()['SUPER + T'], 'SUPER + E')
        keys.change('disable', 'SUPER + E')
        self.assertIsNone(keys.load()['SUPER + E'])
        subprocess.run(['luac', '-p', str(self.config / 'hypr/keybinds.lua')], check=True)
        keys.change('reset-all')
        self.assertFalse((self.config / 'hypr/keybinds.lua').exists())
        keys.change('set', 'SUPER + E', 'SUPER + SHIFT + E')
        keys.change('reset', 'SUPER + E')
        self.assertEqual(keys.load(), {})
        for default, target in [('SUPER + M', 'SUPER + SHIFT + E'), ('SUPER + E', 'SUPER + M'), ('D', 'SUPER + SHIFT + E')]:
            with self.assertRaises(ValueError):
                keys.change('set', default, target)

    def test_lua_resolver_and_all_real_bindings(self):
        keys.change('set', 'SUPER + E', 'SUPER + SHIFT + E')
        keys.change('disable', 'SUPER + P')
        source = (ROOT / 'hypr/hyprland.lua').read_text()
        block = source.split('-- Launchers and app helpers', 1)[1].split('-- Windows And Workspaces', 1)[0]
        fixture = '''local bound = {}
local stub = setmetatable({}, {__index = function(self, key) return self end, __call = function() return {} end})
hl = {dsp = stub, bind = function(key) bound[#bound+1] = key end}
local paths = {config = CONFIG, code = function(path) return path end}
local bind_key = dofile("hypr/keybind-overrides.lua")(paths).bind
local mainMod, terminal, appLaunch, fileManager, hyprScriptsDir, actionsDir, menusDir = "SUPER", "", "", "", "", "", ""
local window_layout = {layout = "scrolling"}
local function workspace_action() return {} end
BLOCK
for _, key in ipairs(bound) do print(key) end
'''.replace('CONFIG', json.dumps(str(self.config))).replace('BLOCK', block)
        result = subprocess.run(['lua', '-'], input=fixture, text=True, capture_output=True, cwd=ROOT, check=True)
        bound = [keys.normalize(key) if 'mouse' not in key and not key.startswith('switch:') else key for key in result.stdout.splitlines()]
        self.assertIn('SUPER + SHIFT + E', bound)
        self.assertNotIn('SUPER + E', bound)
        self.assertNotIn('SUPER + P', bound)
        self.assertEqual(bound.count('SUPER + T'), 2)
        self.assertIn('SUPER + mouse:272', bound)
        self.assertIn('switch:on:Lid Switch', bound)
        catalogue = {entry['default'] for entry in keys.catalogue()}
        self.assertTrue({keys.normalize(key) for key in bound if 'mouse' not in key and not key.startswith('switch:')} - {'SUPER + SHIFT + E'} <= catalogue)

    def test_rules_validation_and_exact_lua(self):
        rule = {'class': 'org.app+[x]', 'title': 'A "title"', 'float': True, 'workspace': 'special:notes', 'size': '80% 600', 'opacity': .8}
        self.assertEqual(rules.validate(rule), rule)
        rules.save([rule])
        self.assertEqual(rules.load(), [rule])
        lua = rules.lua_projection([rule])
        self.assertIn('org\\\\.app\\\\+', lua)
        subprocess.run(['luac', '-p', str(self.config / 'hypr/window-rules.lua')], check=True)
        for field, value in [('class', ''), ('workspace', '11'), ('workspace', '1;exec'), ('size', '0 100'), ('size', '101% 20'), ('opacity', .1), ('opacity', True), ('float', 'true'), ('opacity', float('nan'))]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                rules.validate({**rule, field: value})
        rules.save([])
        self.assertFalse((self.config / 'hypr/window-rules.lua').exists())

    def test_rule_commands_reload_only_after_valid_writes(self):
        rule = {"class": "example", "float": True}
        with patch.object(rules.subprocess, 'run') as reload:
            rules.main(['add', json.dumps(rule)])
            self.assertEqual(rules.load(), [rule])
            rules.main(['update', '0', json.dumps({**rule, 'workspace': '3'})])
            self.assertEqual(rules.load()[0]['workspace'], '3')
            with self.assertRaises(ValueError):
                rules.main(['update', '0', json.dumps({**rule, 'opacity': 0})])
            self.assertEqual(reload.call_count, 2)
            rules.main(['remove', '0'])
            self.assertEqual(reload.call_count, 3)
            self.assertEqual(reload.call_args.args[0], ['hyprctl', 'reload'])
        self.assertFalse((self.config / 'hypr/window-rules.lua').exists())

    def test_personal_rules_loader_uses_defaults_for_broken_files(self):
        rules.save([{'class': 'example.app', 'float': True, 'workspace': '3'}])
        source = (ROOT / 'hypr/hyprland.lua').read_text().split('local personal_rules = ', 1)[1]
        fixture = 'local paths = {config = ' + json.dumps(str(self.config)) + '}\n'
        fixture += 'hl = {window_rule = function(rule) print(rule.match.class, rule.workspace) end}\nlocal personal_rules = ' + source
        result = subprocess.run(['lua', '-'], input=fixture, capture_output=True, text=True, check=True)
        self.assertIn(r'^(example\.app)$', result.stdout)
        (self.config / 'hypr/window-rules.lua').write_text('broken lua!')
        result = subprocess.run(['lua', '-'], input=fixture, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, '')

    def test_apps_and_summary_without_compositor(self):
        applications = self.config / 'data/applications'
        applications.mkdir(parents=True)
        (applications / 'test.desktop').write_text('[Desktop Entry]\nName=Example\nStartupWMClass=example.app\nIcon=example\n')
        # Without StartupWMClass the class is the desktop file name, as Wayland apps report it.
        (applications / 'org.example.Viewer.desktop').write_text('[Desktop Entry]\nName=Viewer\nIcon=viewer\n')
        with patch.object(rules.subprocess, 'run', side_effect=FileNotFoundError), \
                patch.dict(os.environ, {'XDG_DATA_DIRS': str(self.config / 'none')}):
            summary = rules.summary()
        self.assertEqual([(app['class'], app['icon']) for app in summary['apps']],
                         [('example.app', 'example'), ('org.example.Viewer', 'viewer')])
        self.assertEqual(summary['rules'], [])
        self.assertTrue(keys.summary()['items'])
        for script in ('keybinds', 'window-rules'):
            fakebin = self.config / 'bin'
            fakebin.mkdir(exist_ok=True)
            (fakebin / 'hyprctl').write_text('#!/bin/sh\nprintf "[]"\n')
            (fakebin / 'hyprctl').chmod(0o755)
            environment = dict(os.environ, PATH=str(fakebin) + ':' + os.environ['PATH'])
            result = subprocess.run(['python3', str(ROOT / 'quickshell/desktop-bar/scripts' / (script + '.py')), 'summary'], capture_output=True, text=True, env=environment, check=True)
            self.assertIsInstance(json.loads(result.stdout), dict)
