// CrossCurrent Hub - Service Worker
// Handles caching, push notifications, and offline support

const CACHE_NAME = 'crosscurrent-v2';
const OFFLINE_URL = '/';

// Install: cache essential assets
self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.add(OFFLINE_URL))
  );
});

// Activate: clean old caches and take control immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
      ),
      self.clients.claim(),
    ])
  );
});

// Fetch: network-first, fallback to cache
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/')) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request).then((r) => r || caches.match(OFFLINE_URL)))
  );
});

// Push notification handler — this is the critical piece for PWA mode
self.addEventListener('push', (event) => {
  let data = { title: 'CrossCurrent', body: 'New notification', url: '/', tag: 'crosscurrent' };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch {
      try {
        data.body = event.data.text();
      } catch {
        // fallback to defaults
      }
    }
  }

  const options = {
    body: data.body,
    icon: '/logo192.png',
    badge: '/logo192.png',
    tag: data.tag || 'crosscurrent',
    renotify: true,
    requireInteraction: false,
    vibrate: [200, 100, 200],
    data: { url: data.url || '/' },
    actions: [{ action: 'open', title: 'Open' }],
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

// Notification click: open or focus the app
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      // Try to focus an existing window
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      // No existing window — open a new one
      return self.clients.openWindow(url);
    })
  );
});
