"""Account observation and mutation deadlines without a real account or bus."""
import asyncio
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, Mock, patch

from test_bar_data import broker_module


class AccountTests(unittest.IsolatedAsyncioTestCase):
    async def test_observe_refresh_and_zero_periodic_reads(self):
        result = {'path': None, 'initial': 'A', 'name': 'Astrid'}
        reader = Mock(return_value=result)
        broker = broker_module.Broker(lambda frame: None, reader=reader)
        try:
            broker.request(dict(v=1, op='subscribe', topic='account.picture', token='sheet'))
            await broker.states['account.picture']['task']
            self.assertEqual(broker.states['account.picture']['data'], result)
            self.assertEqual(broker_module.INTERVALS['account.picture'], float('inf'))
            broker.request(dict(v=1, op='unsubscribe', topic='account.picture', token='sheet'))
            broker.refresh('account.picture')
            self.assertEqual(reader.call_count, 1)
        finally:
            await broker.close()

    async def test_actions_json_and_no_replay(self):
        frames = []
        broker = broker_module.Broker(frames.append)
        process = Mock(returncode=0)
        process.communicate = AsyncMock(return_value=(b'{"ok": true, "result": {"path": null, "initial": "A", "name": "Astrid"}}', b''))
        try:
            with patch.object(broker_module.asyncio, 'create_subprocess_exec', AsyncMock(return_value=process)) as spawn:
                actions = [('browse', {}, []), ('browse', {'folder': '/mock/folder'}, ['/mock/folder']),
                           ('preview', {'source': '/mock/image'}, ['/mock/image']),
                           ('save', {'source': '/mock/image', 'x': 0, 'y': 0, 'size': 100}, ['/mock/image', '0', '0', '100']),
                           ('remove', {}, [])]
                for index, (name, args, extra) in enumerate(actions):
                    frame = dict(v=1, op='action', topic='account', id=f'{name}-{index}', name=name, args=args)
                    broker.request(frame)
                    await broker.account_action
                    self.assertFalse(frames[-1]['error'])
                    self.assertEqual(list(spawn.call_args.args[2:]), [name, *extra])
                    with self.assertRaises(ValueError):
                        broker.request(frame)
                self.assertEqual(spawn.call_count, 5)
                for name, args in [('choose', {}), ('browse', {'folder': 5}), ('preview', {})]:
                    with self.assertRaises(ValueError):
                        broker.request(dict(v=1, op='action', topic='account', id='bad-' + name, name=name, args=args))
        finally:
            await broker.close()

    async def test_timeout_kills_and_reaps(self):
        frames = []
        broker = broker_module.Broker(frames.append)
        process = Mock(returncode=None)
        process.communicate = AsyncMock(side_effect=TimeoutError)
        process.wait = AsyncMock()
        try:
            with patch.object(broker_module.asyncio, 'create_subprocess_exec', AsyncMock(return_value=process)):
                broker.request(dict(v=1, op='action', topic='account', id='save', name='remove', args={}))
                await broker.account_action
            process.kill.assert_called_once()
            process.wait.assert_awaited_once()
            self.assertEqual(frames[-1]['error'], 'outcome-unknown')
        finally:
            await broker.close()
