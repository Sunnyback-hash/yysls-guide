// Cloudflare Workers + Assets 模式入口
// 处理SPA路由 + 静态文件Content-Type

const CONTENT_TYPES = {
  '/sitemap.xml':  'application/xml; charset=utf-8',
  '/robots.txt':   'text/plain; charset=utf-8',
  '/ads.txt':      'text/plain; charset=utf-8',
  '/BingSiteAuth.xml': 'application/xml; charset=utf-8',
};

const SPA_ROUTES = [
  '/newbie', '/articles', '/builds', '/build', '/maps', '/clues', '/shefu',
  '/equipment', '/pvp', '/events', '/tools', '/community', '/admin', '/dungeons',
];

function matchSpa(path) {
  for (const r of SPA_ROUTES) {
    if (path === r || path.startsWith(r + '/') || path.startsWith(r + '#')) return true;
  }
  return false;
}

function serveIndex(env) {
  return env.ASSETS.fetch('https://placeholder/index.html')
    .then(r => new Response(r.body, { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } }))
    .catch(() => new Response('Not Found', { status: 404 }));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 1) Static files with correct Content-Type
    const ct = CONTENT_TYPES[path];
    if (ct) {
      const asset = await env.ASSETS.fetch(request);
      if (asset.ok) {
        const h = new Headers(asset.headers);
        h.set('Content-Type', ct);
        return new Response(asset.body, { status: 200, headers: h });
      }
    }

    // 2) Clean URL: /market → /market.html
    if (path === '/market') {
      const asset = await env.ASSETS.fetch(new Request(new URL('/market.html', url.origin)));
      if (asset.ok) return asset;
    }

    // 3) SPA routes: serve index.html
    if (matchSpa(path)) {
      return serveIndex(env);
    }

    // 4) Default: try static asset (catch-all for existing files)
    try {
      const asset = await env.ASSETS.fetch(request);
      if (asset.ok) return asset;
    } catch {}

    // 5) Fallback: index.html for everything else
    return serveIndex(env);
  },
};
