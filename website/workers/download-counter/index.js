const SITES = ['https://eitr.info', 'https://www.eitr.info'];

export default {
  async fetch(request, env, ctx) {
    const { pathname } = new URL(request.url);
    if (pathname === '/stats.json' && request.method === 'GET') {
      const stats = await env.DB.prepare(
        'SELECT COALESCE(SUM(count), 0) AS total, MIN(day) AS since FROM downloads'
      ).first();
      const origin = request.headers.get('Origin');
      return Response.json({ total: stats.total, since: stats.since }, {
        headers: {
          'Cache-Control': 'public, max-age=300',
          'Access-Control-Allow-Origin': SITES.includes(origin) ? origin : SITES[0],
          'Vary': 'Origin',
        },
      });
    }

    const range = request.headers.get('Range');
    const response = await fetch(request);
    // Only a successful start of a new download counts; a missing file or a resumed range does not.
    if (request.method === 'GET' && response.ok && /^\/eitr-[^/]+\.iso$/.test(pathname)
        && (range === null || /^bytes=0-\d*$/i.test(range))) {
      const day = new Date().toISOString().slice(0, 10);
      ctx.waitUntil(Promise.resolve().then(() => env.DB.prepare(
        'INSERT INTO downloads(day, file, count) VALUES (?, ?, 1) '
        + 'ON CONFLICT(day, file) DO UPDATE SET count = count + 1'
      ).bind(day, pathname.slice(1)).run()).catch(() => {}));
    }
    return response;
  },
};
