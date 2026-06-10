// Cloudflare Pages Function: serve BingSiteAuth.xml with correct Content-Type

export async function onRequest({ env, request }) {
  const url = new URL(request.url);
  const asset = await env.ASSETS.fetch(new Request(new URL('/BingSiteAuth.xml', url.origin)));
  const headers = new Headers(asset.headers);
  headers.set('Content-Type', 'application/xml; charset=utf-8');
  return new Response(asset.body, { status: asset.status, headers });
}
