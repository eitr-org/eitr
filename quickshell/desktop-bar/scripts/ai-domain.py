"""Demand-owned AI adapter; account jobs use the broker's bounded pool."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import tempfile


class AiDomain:
    def __init__(self):
        spec = importlib.util.spec_from_file_location('ai_usage', Path(__file__).with_name('ai-usage.py'))
        self.backend = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.backend)
        self.cache = Path.home() / '.cache/desktop-ai-usage.json'

    def cached(self):
        try:
            data = json.loads(self.cache.read_text())
        except (OSError, ValueError):
            data = {}
        previous = {provider['name']: provider for provider in data.get('providers', [])}
        providers = {}
        self.accounts = self.backend.usage_accounts()
        for identifier, account in self.accounts:
            name = self.backend.LABELS[identifier]
            accounts = {entry.get('id'): entry for entry in previous.get(name, {}).get('accounts', [])}
            entry = dict(accounts.get(account['id'], {}))
            if entry.get('error') or not entry.get('windows'):
                continue
            entry.update(id=account['id'], label=account['label'])
            providers.setdefault(name, dict(name=name, accounts=[]))['accounts'].append(entry)
        data['providers'] = list(providers.values())
        return data

    def save(self, data):
        self.cache.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=self.cache.parent, prefix=self.cache.name)
        try:
            with os.fdopen(descriptor, 'w') as output:
                json.dump(data, output)
            os.replace(temporary, self.cache)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return data

    async def collect(self, executor, wanted, deadline):
        loop = asyncio.get_running_loop()
        accounts = self.accounts
        pending = iter(enumerate(accounts))
        results = {}

        async def lane():
            for index, (identifier, account) in pending:
                if not wanted() or loop.time() >= deadline:
                    return
                result = await loop.run_in_executor(executor, self.backend.collect_account, identifier, account)
                results[index] = (identifier, result)

        # Two active account jobs leave a pool slot for another domain. Closing
        # the last panel prevents queued accounts from reaching their providers.
        await asyncio.gather(lane(), lane())
        if not wanted():
            raise asyncio.CancelledError()
        if len(results) != len(accounts):
            raise TimeoutError()
        data = self.backend.group_results(results[index] for index in sorted(results))
        return await loop.run_in_executor(executor, self.save, data)
