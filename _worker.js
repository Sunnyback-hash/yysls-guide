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
  // Exact match for defined SPA routes
  for (const r of SPA_ROUTES) {
    if (path === r || path.startsWith(r + '/')) return true;
  }
  // Match article detail routes
  if (path.startsWith('/article/') || path.startsWith('/articles/')) return true;
  // Match build detail routes
  if (path.startsWith('/build/')) return true;
  return false;
}

async function serveIndex(env) {
  try {
    const r = await env.ASSETS.fetch('/index.html');
    if (r.ok) return new Response(r.body, { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  } catch {}
  try {
    const r = await env.ASSETS.fetch('http://localhost/index.html');
    if (r.ok) return new Response(r.body, { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  } catch {}
  return new Response('<html><body><h1>燕云十六声攻略站</h1><script>location.href=\'/\'</script></body></html>', {
    status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' }
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 1) Static files with correct Content-Type
    const ct = CONTENT_TYPES[path];
    if (ct) {
      const assetUrl = new URL(path, url.origin);
      const asset = await env.ASSETS.fetch(assetUrl);
      if (asset.ok) {
        const h = new Headers(asset.headers);
        h.set('Content-Type', ct);
        return new Response(asset.body, { status: 200, headers: h });
      }
    }

    // 2) Market page: /stock → /market.html
    if (path === '/stock') {
      try {
        const asset = await env.ASSETS.fetch('/market.html');
        if (asset.ok) {
          const h = new Headers(asset.headers);
          h.set('Content-Type', 'text/html; charset=utf-8');
          return new Response(asset.body, { status: 200, headers: h });
        }
      } catch {}
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
