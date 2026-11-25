// Сервис-воркер: игра работает без интернета.
// Страница игры — «сначала сеть» без кэша браузера (чтобы обновления приходили сразу), иконки — «сначала кэш».
// В офлайн-копию попадает только успешный ответ сервера.
const CACHE = 'neon-ronin-v6';
const FILES = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/icon-maskable-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES))); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))); self.clients.claim(); });
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const isPage = req.mode === 'navigate' || req.url.endsWith('/index.html');
  if (isPage) e.respondWith(fetch(req, { cache: 'no-cache' }).then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put('./index.html', copy)); } return r; }).catch(() => caches.match('./index.html'))); // мимо кэша браузера; ошибки (404 и т.п.) не сохраняем
  else e.respondWith(caches.match(req).then(r => r || fetch(req)));
});
