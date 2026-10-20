import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from home_isolation import setUpModule, tearDownModule
import eitr_assistants
import eitr_collaboration as bridge
import eitr_paths


FAKE_CLI = """#!/usr/bin/python3
import json, os, sys
from pathlib import Path
identifier = Path(sys.argv[0]).name
store = Path(os.environ['FAKE_MCP_STORE']) / (identifier + '.json')
servers = json.loads(store.read_text()) if store.exists() else {}
arguments = sys.argv[1:]
if arguments[:1] != ['mcp']:
    sys.exit(98)
action, rest = arguments[1], arguments[2:]
positional, skip = [], False
for argument in rest:
    if argument == '--':
        break
    if skip:
        skip = False
    elif argument in ('-s', '-e', '--env'):
        skip = True
    elif not argument.startswith('-'):
        positional.append(argument)
name = positional[0]
if action == 'get':
    if name not in servers:
        sys.exit(1)
    print(json.dumps({'transport': servers[name]}))
elif action == 'add':
    if name in servers or os.environ.get('FAKE_MCP_FAIL'):
        sys.exit(1)
    separator = arguments.index('--')
    flag = '-e' if identifier == 'claude' else '--env'
    variable = arguments[arguments.index(flag) + 1].split('=', 1)
    servers[name] = {'command': arguments[separator + 1], 'args': arguments[separator + 2:], 'env': {variable[0]: variable[1]}}
elif action == 'remove':
    if name not in servers:
        sys.exit(1)
    del servers[name]
store.write_text(json.dumps(servers))
if identifier == 'claude':
    settings = Path(os.environ['HOME']) / '.claude.json'
    settings.write_text(json.dumps({'theme': 'dark', 'mcpServers': servers}))
"""


class CollaborationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.addCleanup(patch.stopall)
        patch.object(Path, 'home', return_value=self.home).start()
        patch.dict(os.environ, {'CODEX_HOME': str(self.home / '.codex'), 'HOME': str(self.home),
                              'CLAUDE_CONFIG_DIR': '', bridge.DEPTH: '', 'FAKE_MCP_STORE': str(self.home),
                              'FAKE_MCP_FAIL': '', 'PATH': str(self.home / 'bin')}).start()

    def sign_in(self, identifier):
        if identifier == 'claude':
            path = self.home / '.claude/.credentials.json'
            payload = {'claudeAiOauth': {'accessToken': 'fixture'}}
        else:
            path = self.home / '.codex/auth.json'
            payload = {'tokens': {'access_token': 'fixture'}}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
        binary = self.home / 'bin' / identifier
        binary.parent.mkdir(exist_ok=True)
        binary.write_text(FAKE_CLI)
        binary.chmod(0o755)
        return binary

    def request(self, method, **params):
        return bridge.dispatch({'jsonrpc': '2.0', 'id': 2, 'method': method, 'params': params})

    def test_installed_and_signed_in_only_and_hop_limit(self):
        self.assertEqual(self.request('tools/list')['result']['tools'], [])
        self.sign_in('claude')
        self.assertEqual([tool['name'] for tool in self.request('tools/list')['result']['tools']], ['ask_claude'])
        self.sign_in('codex')
        self.assertEqual(len(self.request('tools/list')['result']['tools']), 2)
        with patch.dict(os.environ, PATH=str(eitr_assistants.code('walker/assistants'))):
            self.assertEqual(bridge.connected(), {})
        with patch.dict(os.environ, {bridge.DEPTH: '1'}), patch.object(bridge.subprocess, 'Popen') as launch:
            self.assertEqual(self.request('tools/list')['result']['tools'], [])
            self.assertTrue(self.request('tools/call', name='ask_codex', arguments={'question':'review'})['result']['isError'])
            launch.assert_not_called()

    def test_protocol_and_invalid_arguments(self):
        self.assertIsNone(bridge.dispatch({'jsonrpc':'2.0', 'method':'notifications/initialized'}))
        self.assertEqual(self.request('initialize', protocolVersion='2025-03-26')['result']['protocolVersion'], '2025-03-26')
        self.assertEqual(self.request('missing')['error']['code'], -32601)
        self.assertEqual(bridge.dispatch([])['error']['code'], -32600)
        self.assertEqual(self.request('tools/call', name='ask_codex', arguments={'question':'', 'extra':1})['error']['code'], -32602)
        output = io.StringIO()
        bridge.serve(io.StringIO('{broken\n[]\n{"jsonrpc":"2.0","id":3,"method":"ping"}\n'), output)
        responses = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([response.get('error', {}).get('code') for response in responses], [-32700, -32600, None])
        self.assertEqual(responses[-1]['result'], {})

    def test_read_only_arguments_cwd_final_answer_and_depth(self):
        for identifier in bridge.LABELS:
            binary = self.sign_in(identifier)
            process = Mock(returncode=0)
            process.communicate.return_value = ('answer' if identifier == 'claude' else '\n'.join([
                json.dumps({'type':'item.completed', 'item':{'type':'reasoning', 'text':'private'}}),
                json.dumps({'type':'item.completed', 'item':{'type':'agent_message', 'text':'answer'}})]), '')
            with patch.object(bridge.subprocess, 'run') as notify, patch.object(bridge.subprocess, 'Popen', return_value=process) as launch:
                self.assertEqual(bridge.ask(identifier, '--dangerously-do-something'), 'answer')
                arguments = launch.call_args.args[0]
                self.assertEqual(arguments[0], str(binary))
                if identifier == 'claude':
                    self.assertIn('Read,Glob,Grep', arguments)
                    self.assertIn('plan', arguments)
                    self.assertIn('--strict-mcp-config', arguments)
                    self.assertEqual(arguments[-2:], ['--', '--dangerously-do-something'])
                else:
                    self.assertIn('read-only', arguments)
                    self.assertIn('approval_policy="never"', arguments)
                    self.assertIn('--ignore-user-config', arguments)
                    self.assertEqual(process.communicate.call_args.args[0], '--dangerously-do-something')
                self.assertEqual(launch.call_args.kwargs['env'][bridge.DEPTH], '1')
                self.assertEqual(launch.call_args.kwargs['cwd'], Path.cwd())
                self.assertTrue(launch.call_args.kwargs['start_new_session'])
                self.assertEqual(notify.call_args.args[0][0], 'notify-send')

    def test_timeout_kills_helper_process_group(self):
        self.sign_in('codex')
        process = Mock(pid=9876)
        process.communicate.side_effect = [subprocess.TimeoutExpired('mock', 180), ('', '')]
        with patch.object(bridge.subprocess, 'run'), patch.object(bridge.subprocess, 'Popen', return_value=process), patch.object(bridge.os, 'killpg') as kill:
            with self.assertRaisesRegex(ValueError, 'timed out'):
                bridge.ask('codex', 'review')
            kill.assert_called_once_with(9876, bridge.signal.SIGKILL)

    def servers(self, identifier):
        store = self.home / (identifier + '.json')
        return json.loads(store.read_text()) if store.exists() else {}

    def test_each_tool_registers_and_removes_only_its_own_entry(self):
        for identifier in bridge.LABELS:
            self.sign_in(identifier)
            (self.home / (identifier + '.json')).write_text(json.dumps({'other': {'command': 'mine'}}))
        self.assertEqual(bridge.enable(['claude', 'codex']), [])
        self.assertTrue(bridge.enabled())
        for identifier in bridge.LABELS:
            with self.subTest(identifier=identifier):
                self.assertEqual(self.servers(identifier)['assistants'], bridge.registration(identifier))
                self.assertEqual(self.servers(identifier)['other'], {'command': 'mine'})
                self.assertEqual(bridge.registered(identifier, bridge.executable(identifier)),
                                 bridge.registration(identifier))
        self.assertEqual(bridge.enable(['claude', 'codex']), [], 'enabling twice changes nothing')
        self.assertEqual(bridge.disable(), [])
        self.assertFalse(bridge.enabled())
        for identifier in bridge.LABELS:
            self.assertEqual(self.servers(identifier), {'other': {'command': 'mine'}})

    def test_an_existing_assistants_server_is_never_replaced(self):
        self.sign_in('codex')
        (self.home / 'codex.json').write_text(json.dumps({'assistants': {'command': 'mine', 'args': [], 'env': {}}}))
        self.assertTrue(bridge.enable(['codex']))
        self.assertEqual(self.servers('codex')['assistants']['command'], 'mine')
        self.assertFalse(bridge.enabled())

    def test_a_failed_registration_is_not_recorded(self):
        self.sign_in('claude')
        with patch.dict(os.environ, {'FAKE_MCP_FAIL': '1'}):
            self.assertTrue(bridge.enable(['claude']))
        self.assertFalse(bridge.enabled())

    def test_changed_managed_entry_is_not_removed(self):
        self.sign_in('codex')
        self.assertEqual(bridge.enable(['codex']), [])
        changed = dict(bridge.registration('codex'), command='custom')
        (self.home / 'codex.json').write_text(json.dumps({'assistants': changed}))
        self.assertTrue(bridge.disable())
        self.assertEqual(self.servers('codex')['assistants'], changed)

    def test_an_entry_removed_by_hand_just_clears_the_switch(self):
        self.sign_in('claude')
        self.assertEqual(bridge.enable(['claude']), [])
        (self.home / 'claude.json').write_text('{}')
        (self.home / '.claude.json').write_text('{}')
        self.assertEqual(bridge.disable(), [])
        self.assertFalse(bridge.enabled())

    def test_atomic_refuses_stale_snapshot(self):
        path = self.home / 'config'
        path.write_bytes(b'newer')
        with self.assertRaises(ValueError):
            bridge.atomic(path, b'old', b'overwrite')
        self.assertEqual(path.read_bytes(), b'newer')

    def test_confirmation_names_assistants_warns_of_limits_and_cancel_keeps_settings(self):
        self.sign_in('claude')
        self.sign_in('codex')
        script = Path(__file__).resolve().parents[1] / 'scripts/actions/assistant-collaboration.py'
        specification = importlib.util.spec_from_file_location('collaboration_action', script)
        action = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(action)
        real_run = subprocess.run
        for choice in ('Cancel', 'Confirm'):
            def walker_answers(command, *arguments, **options):
                if command[0].endswith('/walker'):
                    return Mock(returncode=0, stdout=choice)
                return real_run(command, *arguments, **options)
            with patch.object(action.subprocess, 'run', side_effect=walker_answers) as prompt:
                self.assertEqual(action.toggle(), 0)
                question = next(call.args[0][3] for call in prompt.call_args_list if call.args[0][0].endswith('/walker'))
                self.assertIn('Claude, Codex', question)
                self.assertIn('subscription', question)
                self.assertIn('limits', question)
                self.assertEqual(bridge.enabled(), choice == 'Confirm')
        with patch.object(action.subprocess, 'run', side_effect=real_run) as prompt:
            self.assertEqual(action.toggle(), 0)
            self.assertFalse(any(call.args[0][0].endswith('/walker') for call in prompt.call_args_list),
                             'turning it off asks nothing')
        self.assertFalse(bridge.enabled())

    def test_invalid_state_is_refused(self):
        record = bridge.record_path()
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text('{"version":2,"entries":[]}')
        with self.assertRaises(ValueError):
            bridge.disable()

    def test_packaged_layout_including_root_isolated_entrypoint(self):
        repository = Path(__file__).resolve().parents[2]
        root = self.home / 'usr/share/eitr'
        (root / 'lib').mkdir(parents=True)
        scripts = root / 'walker/scripts/actions'
        scripts.mkdir(parents=True)
        for source in (repository / 'distro/lib').glob('*.py'):
            shutil.copyfile(source, root / 'lib' / source.name)
        (root / 'software.json').write_bytes((repository / 'distro/software.json').read_bytes())
        entrypoint = scripts / 'assistant-collaboration.py'
        shutil.copyfile(repository / 'walker/scripts/actions/assistant-collaboration.py', entrypoint)
        with patch.object(eitr_paths, 'ROOT', root), patch.object(eitr_paths.os, 'geteuid', return_value=0):
            self.assertIn('codex', eitr_assistants.assistants())
            self.assertEqual(bridge.registration('codex')['args'][0], str(entrypoint))
        environment = dict(os.environ, HOME=str(self.home), PYTHONPATH='', EITR_CODE_ROOT=str(root))
        result = subprocess.run(['/usr/bin/python3', '-I', str(entrypoint), 'serve'],
                                input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n',
                                text=True, capture_output=True, env=environment, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['result']['serverInfo']['name'], 'assistants')
