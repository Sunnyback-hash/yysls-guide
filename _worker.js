// SPA fallback for Cloudflare Workers with Assets
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Let the ASSETS runtime try to serve the file
    try {
      const response = await env.ASSETS.fetch(request);
      if (response.status === 404) {
        // SPA fallback - serve index.html for client-side routing
        return env.ASSETS.fetch(new Request(new URL('/index.html', url.origin)));
      }
      return response;
    } catch {
      // If ASSETS fetch throws, fall back to index.html
      return env.ASSETS.fetch(new Request(new URL('/index.html', url.origin)));
    }
  }
};
