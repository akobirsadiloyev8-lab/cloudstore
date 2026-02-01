// Cloudstore Service Worker - PWA uchun
const CACHE_NAME = 'cloudstore-v1';
const OFFLINE_URL = '/offline/';

// Cache qilinadigan fayllar
const STATIC_ASSETS = [
    '/',
    '/static/blog/style.css',
    '/static/manifest.json',
    '/offline/',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Install event - cache yaratish
self.addEventListener('install', event => {
    console.log('[SW] Install');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - eski cache'larni o'chirish
self.addEventListener('activate', event => {
    console.log('[SW] Activate');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(cacheName => cacheName !== CACHE_NAME)
                    .map(cacheName => caches.delete(cacheName))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - so'rovlarni tutish
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);
    
    // API so'rovlarini cache qilmaslik
    if (url.pathname.startsWith('/api/') || 
        url.pathname.startsWith('/admin/') ||
        request.method !== 'GET') {
        return;
    }
    
    // Static fayllar uchun Cache First strategiyasi
    if (request.url.includes('/static/') || 
        request.url.includes('/media/') ||
        request.url.includes('.css') ||
        request.url.includes('.js') ||
        request.url.includes('.png') ||
        request.url.includes('.jpg')) {
        
        event.respondWith(
            caches.match(request)
                .then(cachedResponse => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    return fetch(request).then(response => {
                        if (response.ok) {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME).then(cache => {
                                cache.put(request, responseClone);
                            });
                        }
                        return response;
                    });
                })
        );
        return;
    }
    
    // HTML sahifalar uchun Network First strategiyasi
    event.respondWith(
        fetch(request)
            .then(response => {
                // Muvaffaqiyatli javobni cache qilish
                if (response.ok) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Offline bo'lsa, cache'dan olish
                return caches.match(request)
                    .then(cachedResponse => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // Offline sahifani ko'rsatish
                        if (request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }
                        return new Response('Offline', { status: 503 });
                    });
            })
    );
});

// Push notification
self.addEventListener('push', event => {
    console.log('[SW] Push received');
    
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Cloudstore';
    const options = {
        body: data.body || 'Yangi xabar!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/'
        },
        actions: [
            { action: 'open', title: 'Ochish' },
            { action: 'close', title: 'Yopish' }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click
self.addEventListener('notificationclick', event => {
    console.log('[SW] Notification clicked');
    event.notification.close();
    
    if (event.action === 'close') return;
    
    const urlToOpen = event.notification.data.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Agar ilova ochiq bo'lsa, unga fokus qilish
                for (const client of clientList) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Yangi oyna ochish
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Background sync - offline vaqtida saqlangan amallarni bajarish
self.addEventListener('sync', event => {
    console.log('[SW] Background sync:', event.tag);
    
    if (event.tag === 'sync-reading-progress') {
        event.waitUntil(syncReadingProgress());
    }
});

async function syncReadingProgress() {
    // IndexedDB'dan saqlangan progresslarni olish va serverga yuborish
    try {
        // Bu yerda IndexedDB bilan ishlash kodi bo'ladi
        console.log('[SW] Syncing reading progress...');
    } catch (error) {
        console.error('[SW] Sync failed:', error);
    }
}
