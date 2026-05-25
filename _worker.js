export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    try {
      const response = await env.ASSETS.fetch(request);
      if (response.status !== 404) return response;
    } catch (e) {}
    
    return env.ASSETS.fetch(new URL('/index.html', url.origin));
  }
};
