/* Offline app shell for GitHub Pages or static hosting. */
const CACHE_NAME = 'aunjai-pwa-v1';
const APP_ROOT = new URL('./', self.registration.scope);
const PRECACHE = [APP_ROOT.href, new URL('./manifest.webmanifest', APP_ROOT).href, new URL('./icons/icon-192.png', APP_ROOT).href, new URL('./icons/icon-512.png', APP_ROOT).href];
self.addEventListener('install', (event) => { event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE))); self.skipWaiting(); });
self.addEventListener('activate', (event) => { event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key.startsWith('aunjai-pwa-') && key !== CACHE_NAME).map((key) => caches.delete(key)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', (event) => {
  const request = event.request, url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).then((response) => { if (response.ok) { const copy = response.clone(); caches.open(CACHE_NAME).then((cache) => cache.put(APP_ROOT.href, copy)); } return response; }).catch(async () => (await caches.match(request)) || (await caches.match(APP_ROOT.href))));
    return;
  }
  event.respondWith(caches.match(request).then((cached) => { if (cached) return cached; return fetch(request).then((response) => { if (response.ok) { const copy = response.clone(); caches.open(CACHE_NAME).then((cache) => cache.put(request, copy)); } return response; }); }));
});
