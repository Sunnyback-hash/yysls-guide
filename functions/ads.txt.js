// Cloudflare Pages Function: serve ads.txt with correct Content-Type

export async function onRequest({ env }) {
  const asset = await env.ASSETS.fetch(new Request(new URL('/ads.txt', 'https://placeholder')));
  const headers = new Headers(asset.headers);
  headers.set('Content-Type', 'text/plain; charset=utf-8');
  return new Response(asset.body, { status: asset.status, headers });
}
