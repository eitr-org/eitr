import assert from 'node:assert/strict';
import test from 'node:test';
import worker from '../index.js';

function database({ failure = false, stats = { total: 1234, since: '2026-10-01' } } = {}) {
  const calls = [];
  return {
    calls,
    prepare(sql) {
      calls.push(sql);
      return {
        bind(...values) {
          calls.push(values);
          return { run: async () => { if (failure) throw new Error('unavailable'); } };
        },
        first: async () => stats,
      };
    },
  };
}

for (const range of [null, 'bytes=0-', 'bytes=0-1023']) {
  test(`counts new ISO request with range ${range}`, async context => {
    const DB = database();
    const pending = [];
    const request = new Request('https://download.eitr.info/eitr-1.0.iso', {
      headers: range ? { Range: range } : {},
    });
    const origin = new Response('ISO', { status: 206, headers: { 'X-Origin': 'preserved' } });
    context.mock.method(globalThis, 'fetch', async forwarded => {
      assert.equal(forwarded, request);
      return origin;
    });
    const before = new Date().toISOString().slice(0, 10);
    assert.equal(await worker.fetch(request, { DB }, { waitUntil: promise => pending.push(promise) }), origin);
    await Promise.all(pending);
    assert.equal(pending.length, 1);
    assert.match(DB.calls[0], /ON CONFLICT\(day, file\) DO UPDATE SET count = count \+ 1/);
    assert.ok([before, new Date().toISOString().slice(0, 10)].includes(DB.calls[1][0]));
    assert.equal(DB.calls[1][1], 'eitr-1.0.iso');
  });
}

for (const [path, method, range] of [
  ['/eitr-1.iso', 'GET', 'bytes=100-'],
  ['/eitr-1.iso', 'GET', 'bytes=0-100,200-300'],
  ['/eitr-1.iso', 'GET', 'bytes=-500'],
  ['/eitr-1.iso', 'GET', 'invalid'],
  ['/eitr-1.iso', 'HEAD', null],
  ['/eitr-1.iso', 'POST', null],
  ['/repo/eitr-1.iso', 'GET', null],
  ['/repo-testing/pkg.tar.zst', 'GET', null],
  ['/eitr-1.iso.sha256', 'GET', null],
]) {
  test(`does not count ${method} ${path} ${range}`, async context => {
    const DB = database();
    context.mock.method(globalThis, 'fetch', async () => new Response('origin'));
    const response = await worker.fetch(new Request(`https://download.eitr.info${path}`, {
      method, headers: range ? { Range: range } : {},
    }), { DB }, { waitUntil: () => assert.fail('unexpected write') });
    assert.equal(await response.text(), 'origin');
    assert.deepEqual(DB.calls, []);
  });
}

test('failed or pending database never blocks the file', async context => {
  context.mock.method(globalThis, 'fetch', async () => new Response('ISO'));
  for (const [index, DB] of [database({ failure: true }), { prepare() { throw new Error('prepare failed'); } }, {
    prepare: () => ({ bind: () => ({ run: () => new Promise(() => {}) }) }),
  }].entries()) {
    const pending = [];
    const response = await worker.fetch(new Request('https://download.eitr.info/eitr-1.iso'),
      { DB }, { waitUntil: promise => pending.push(promise) });
    assert.equal(await response.text(), 'ISO');
    if (index < 2) {
      await Promise.all(pending);
    }
  }
});

for (const stats of [{ total: 1234, since: '2026-10-01' }, { total: 0, since: null }]) {
  test(`stats returns ${stats.total}`, async context => {
    context.mock.method(globalThis, 'fetch', () => assert.fail('stats must not fetch origin'));
    const DB = database({ stats });
    const response = await worker.fetch(new Request('https://download.eitr.info/stats.json'), { DB }, {});
    assert.deepEqual(await response.json(), stats);
    assert.equal(response.headers.get('Cache-Control'), 'public, max-age=300');
    assert.equal(response.headers.get('Access-Control-Allow-Origin'), 'https://eitr.info');
    assert.match(DB.calls[0], /SUM\(count\).*MIN\(day\)/);
  });
}

test('does not count a missing ISO', async context => {
  const DB = database();
  const pending = [];
  const request = new Request('https://download.eitr.info/eitr-missing.iso');
  const origin = new Response('Not found', { status: 404 });
  context.mock.method(globalThis, 'fetch', async () => origin);
  assert.equal(await worker.fetch(request, { DB }, { waitUntil: promise => pending.push(promise) }), origin);
  assert.equal(pending.length, 0);
  assert.equal(DB.calls.length, 0);
});

test('stats answer both site addresses', async () => {
  for (const origin of ['https://eitr.info', 'https://www.eitr.info']) {
    const request = new Request('https://download.eitr.info/stats.json', { headers: { Origin: origin } });
    const response = await worker.fetch(request, { DB: database() }, { waitUntil() {} });
    assert.equal(response.headers.get('Access-Control-Allow-Origin'), origin);
  }
  const other = new Request('https://download.eitr.info/stats.json', { headers: { Origin: 'https://example.com' } });
  const response = await worker.fetch(other, { DB: database() }, { waitUntil() {} });
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), 'https://eitr.info');
});
