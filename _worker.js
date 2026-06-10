// Cloudflare Pages Function — handles ALL requests.
// When _worker.js exists, Pages SPA fallback is bypassed entirely.
// This ensures sitemap.xml, robots.txt etc. get correct Content-Type.

const STATIC_ROUTES = {
  '/sitemap.xml':  { type: 'application/xml; charset=utf-8' },
  '/robots.txt':   { type: 'text/plain; charset=utf-8' },
  '/ads.txt':      { type: 'text/plain; charset=utf-8' },
  '/BingSiteAuth.xml': { type: 'application/xml; charset=utf-8' },
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 1) Crawler static files — serve from ASSETS with correct Content-Type
    const route = STATIC_ROUTES[path];
    if (route) {
      const asset = await env.ASSETS.fetch(new Request(new URL(path, url.origin)));
      if (asset.status !== 404) {
        const h = new Headers(asset.headers);
        h.set('Content-Type', route.type);
        return new Response(asset.body, { status: 200, headers: h });
      }
      // file not found → fall through to SPA
    }

    // 2) Clean URL: /market → /market.html
    if (path === '/market' || path === '/market/') {
      const asset = await env.ASSETS.fetch(new Request(new URL('/market.html', url.origin)));
      if (asset.ok) return asset;
    }

    // 3) Try static asset first
    try {
      const asset = await env.ASSETS.fetch(request);
      if (asset.ok) return asset;
    } catch { /* fall through */ }

    // 4) SPA fallback — everything else serves index.html
    const spa = await env.ASSETS.fetch(new Request(new URL('/index.html', url.origin)));
    return new Response(spa.body, {
      status: 200,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    });
  },
};
