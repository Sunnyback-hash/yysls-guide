// SPA fallback for Cloudflare Pages / Workers with Assets
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Diagnostic: confirm this Worker is in the request path
    const WORKER_TAG = 'x-cf-worker-active';

    // Route /market to market.html
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
