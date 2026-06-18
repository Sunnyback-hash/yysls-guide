// Cloudflare Worker — SPA + Content-Type
export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    const CT = {'/sitemap.xml':'application/xml','/robots.txt':'text/plain','/ads.txt':'text/plain'}[path];
    if (CT) {
      const a = await env.ASSETS.fetch(path);
      if (a.ok) {
        const h = new Headers(a.headers); h.set('Content-Type', CT+'; charset=utf-8');
        return new Response(a.body, { status: 200, headers: h });
      }
    }
    const i = await env.ASSETS.fetch('/');
    return new Response(i.body, { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }
};
