// SPA fallback for Cloudflare Pages / Workers with Assets
// NOTE: When _worker.js exists, _redirects is NOT processed by CF Pages.
// All routing (including sitemap/robots/crawler files) must be handled here.

const STATIC_CONTENT_TYPES = {
  '/sitemap.xml':  'application/xml',
  '/robots.txt':   'text/plain; charset=utf-8',
  '/ads.txt':      'text/plain; charset=utf-8',
  '/BingSiteAuth.xml': 'application/xml',
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Diagnostic: confirm this Worker is in the request path
    const WORKER_TAG = 'x-cf-worker-active';

    // Serve crawler/static files with explicit Content-Type
    const contentType = STATIC_CONTENT_TYPES[path];
    if (contentType) {
      const r = await env.ASSETS.fetch(new Request(new URL(path, url.origin)));
      if (r.status !== 404) {
        const h = new Headers(r.headers);
        h.set('Content-Type', contentType);
        h.set(WORKER_TAG, 'true');
        return new Response(r.body, { status: r.status, headers: h });
      }
      // Fall through to SPA if 404
    }

    // Route /market to market.html (clean URL)
    if (path === '/market' || path === '/market/') {
      const r = await env.ASSETS.fetch(new Request(new URL('/market.html', url.origin)));
      const h = new Headers(r.headers);
      h.set(WORKER_TAG, 'true');
      return new Response(r.body, { status: r.status, headers: h });
    }

    // Try serving the file from ASSETS
    try {
      const response = await env.ASSETS.fetch(request);

      if (response.status === 404) {
        // SPA fallback - serve index.html for client-side routing
        const r = await env.ASSETS.fetch(new Request(new URL('/index.html', url.origin)));
        const h = new Headers(r.headers);
        h.set(WORKER_TAG, 'true');
        return new Response(r.body, { status: r.status, headers: h });
      }

      const headers = new Headers(response.headers);
      headers.set(WORKER_TAG, 'true');
      return new Response(response.body, { status: response.status, headers });
    } catch {
      const r = await env.ASSETS.fetch(new Request(new URL('/index.html', url.origin)));
      const h = new Headers(r.headers);
      h.set(WORKER_TAG, 'true');
      return new Response(r.body, { status: r.status, headers: h });
    }
  }
};
