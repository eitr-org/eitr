"""Isolated regressions for query hot paths; never contact the desktop."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


class WalkerSpeedTests(unittest.TestCase):
    def lua(self, source, **environment):
        result = subprocess.run(['lua', '-'], input=source, text=True, capture_output=True,
                                env=dict(os.environ, EITR_CODE_ROOT=str(ROOT),
                                         EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'), **environment))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_policy_snapshot_is_shared_and_fail_closed(self):
        for mode in ['missing', 'malformed', 'scalar', 'restricted']:
            with self.subTest(mode=mode):
                self.lua(r'''
local opens, decodes = 0, 0
local mode = os.getenv('POLICY_MODE')
io.open = function(path)
    assert(path == '/etc/eitr/policies.json')
    opens = opens + 1
    if mode == 'missing' then return nil end
    return {read=function() return 'policy' end, close=function() end}
end
jsonDecode = function()
    decodes = decodes + 1
    if mode == 'malformed' then error('invalid json') end
    if mode == 'scalar' then return false end
    return {gaming=false, update_channel='stable'}
end
local source = os.getenv('EITR_CODE_ROOT') .. '/elephant/policies.lua'
local policies = dofile(source)
for iteration=1,20 do
    assert(dofile(source) == policies)
    assert(policies.allowed('gaming') == (mode == 'missing'))
    assert(policies.allowed('update_channel') == (mode == 'missing'))
    assert(policies.allowed('sharing') == (mode == 'missing' or mode == 'restricted'))
    assert(policies.row({SubMenu='gaming'}, 'main') == (mode == 'missing'))
end
assert(opens == 1)
assert(decodes == (mode == 'missing' and 0 or 1))
''', POLICY_MODE=mode)

    def test_english_sort_matches_full_catalog_for_all_messages(self):
        self.lua(r'''
local root = os.getenv('EITR_CODE_ROOT')
local full = dofile(root .. '/i18n/catalogs/en/menus.lua')
local exceptions = dofile(root .. '/i18n/catalogs/en/menu-sort-exceptions.lua')
local expected, entries = {}, {}
for title, translated in pairs(full.messages) do
    assert(title == translated)
    assert((exceptions[title] or title:lower()) == full.sortKeys[title])
    table.insert(expected, title)
    table.insert(entries, {Text=title, Value=title})
end
table.sort(expected, function(left, right)
    local left_key, right_key = full.sortKeys[left], full.sortKeys[right]
    if left_key == right_key then return left < right end
    return left_key < right_key
end)
local original = dofile
dofile = function(path)
    assert(not path:match('/en/menus.lua$'), 'English full catalog loaded')
    return original(path)
end
local i18n = dofile(root .. '/elephant/i18n.lua')
entries = i18n.entries(entries)
for index, entry in ipairs(entries) do assert(entry.Text == expected[index]) end
assert(i18n.language() == 'English')
''', LC_ALL='en_US.UTF-8')

    def test_apps_single_scan_retains_precedence_actions_and_parent(self):
        self.lua(r'''
local root, home = os.getenv('EITR_CODE_ROOT'), os.getenv('HOME')
local original = dofile
dofile = function(path)
    if path:match('/elephant/i18n.lua$') then
        return {tr=function(value) return value end, entries=function(value) return value end,
            language=function() return 'English' end}
    end
    return original(path)
end
local scans = 0
local user = home .. '/.local/share/applications/'
local system = '/usr/share/applications/'
local paths = {system .. 'same.desktop', user .. 'same.desktop',
    system .. 'fallback.desktop', user .. 'fallback.desktop'}
io.popen = function(command)
    scans = scans + 1
    assert(not command:find('|', 1, true))
    return {lines=function()
        local index=0
        return function() index=index+1; return paths[index] end
    end, close=function() end}
end
io.open = function(path)
    local name = path == user .. 'same.desktop' and 'Chosen' or 'Other'
    local rows = {'[Desktop Entry]', 'Type=Application', 'Name=' .. name, 'Exec=app'}
    if path == user .. 'fallback.desktop' then table.insert(rows, 'Hidden=true') end
    return {lines=function()
        local index=0
        return function() index=index+1; return rows[index] end
    end, close=function() end}
end
dofile(root .. '/elephant/menus/apps.lua')
local entries = GetEntries('')
assert(scans == 1 and #entries == 2 and Parent == 'main')
assert(entries[1].Value == user .. 'same.desktop')
assert(entries[2].Value == system .. 'fallback.desktop')
assert(entries[1].Actions.open:find('--desktop', 1, true))
assert(entries[1].Actions.app_uninstall:find(' uninstall ', 1, true))
''')

    def test_wrapper_executes_before_background_prepare_finishes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, body in {
                'systemctl': 'exit 0',
                'python3': 'touch "$TEST_ROOT/started"; while [ ! -f "$TEST_ROOT/release" ]; do sleep .01; done; touch "$TEST_ROOT/done"',
                'real-walker': 'if [ "$*" = "-m menus:main" ]; then while [ ! -f "$TEST_ROOT/started" ]; do sleep .01; done; fi; [ ! -f "$TEST_ROOT/done" ] || exit 9; touch "$TEST_ROOT/release"',
            }.items():
                path = root / name
                path.write_text('#!/bin/sh\n' + body + '\n')
                path.chmod(0o755)
            wrapper = root / 'wrapper'
            wrapper.write_text((ROOT / 'walker/bin/walker').read_text().replace('/usr/bin/walker', str(root / 'real-walker')))
            index = root / 'run/eitr-search/index.json'
            index.parent.mkdir(parents=True)
            index.write_text('{}')
            environment = dict(os.environ, TEST_ROOT=directory, EITR_CODE_ROOT=directory, XDG_RUNTIME_DIR=str(root / 'run'),
                               PATH=directory + os.pathsep + os.environ['PATH'])
            for menu in ['apps', 'clipboard', 'main']:
                result = subprocess.run(['bash', str(wrapper), '-m', 'menus:' + menu],
                                        env=environment, capture_output=True, timeout=3)
                self.assertEqual(result.returncode, 0, result.stderr)
                if menu != 'main':
                    self.assertFalse((root / 'started').exists())
                    (root / 'release').unlink()
            import time
            deadline = time.monotonic() + 3
            while not (root / 'done').exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue((root / 'done').exists())

    def test_wrapper_builds_a_missing_index_before_opening(self):
        # Without an index a search typed at once would find nothing, so it is built first.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, body in {'systemctl': 'exit 0', 'python3': 'touch "$TEST_ROOT/prepared"',
                               'real-walker': '[ -f "$TEST_ROOT/prepared" ] || exit 9'}.items():
                path = root / name
                path.write_text('#!/bin/sh\n' + body + '\n')
                path.chmod(0o755)
            wrapper = root / 'wrapper'
            wrapper.write_text((ROOT / 'walker/bin/walker').read_text().replace('/usr/bin/walker', str(root / 'real-walker')))
            environment = dict(os.environ, TEST_ROOT=directory, EITR_CODE_ROOT=directory, XDG_RUNTIME_DIR=str(root / 'run'),
                               PATH=directory + os.pathsep + os.environ['PATH'])
            result = subprocess.run(['bash', str(wrapper), '-m', 'menus:main'], env=environment, capture_output=True, timeout=3)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_readiness_does_not_refresh_and_exhaustion_fails(self):
        specification = importlib.util.spec_from_file_location('ready_search', ROOT / 'walker/scripts/menus/search-index.py')
        search = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(search)
        with patch.object(search.subprocess, 'run') as query, patch.object(search, 'refresh') as refresh:
            query.return_value.returncode = 0
            search.ready(attempts=1, delay=0)
            refresh.assert_not_called()
            query.return_value.returncode = 1
            with self.assertRaises(ValueError):
                search.ready(attempts=1, delay=0)
            refresh.assert_not_called()

    def test_refresh_lock_prevents_a_second_query(self):
        import fcntl
        specification = importlib.util.spec_from_file_location('speed_search', ROOT / 'walker/scripts/menus/search-index.py')
        search = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(search)
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            with (runtime / 'refresh.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with patch.object(search, 'RUNTIME', runtime), patch.object(search.subprocess, 'run') as query:
                    search.refresh()
                query.assert_not_called()


if __name__ == '__main__':
    unittest.main()
