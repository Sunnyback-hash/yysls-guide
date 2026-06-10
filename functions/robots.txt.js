// Cloudflare Pages Function: serve robots.txt with correct Content-Type

export async function onRequest({ env, request }) {
  const url = new URL(request.url);
  const asset = await env.ASSETS.fetch(new Request(new URL('/robots.txt', url.origin)));
  const headers = new Headers(asset.headers);
  headers.set('Content-Type', 'text/plain; charset=utf-8');
  return new Response(asset.body, { status: asset.status, headers });
}
