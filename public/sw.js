const CACHE_NAME = 'analise-oe-v24';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/ordem_servico_campo.html',
    '/orcamento.html',
    '/checklist_fluxo.html',
    '/historico.html',
    '/downloads/index.html',
    '/manifest.json',
    '/favicon.png',
    '/icon-192.png',
    '/icon-512.png',
    '/icon.png'
];

// Instalação do Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS_TO_CACHE))
            .then(() => self.skipWaiting())
    );
});

// Ativação e limpeza de versões antigas do cache
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Interceptação de requisições de rede
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Requisições para API (/api/...) são SEMPRE Network-first
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                return new Response(JSON.stringify({ error: 'offline', offline: true }), {
                    status: 503,
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
        return;
    }

    // Navegações de página (HTML): Network-first com fallback para cache
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
                    return response;
                })
                .catch(() => caches.match(event.request).then(cached => cached || caches.match('/index.html')))
        );
        return;
    }

    // Arquivos estáticos (imagens, scripts, CSS): Cache-first com revalidação
    event.respondWith(
        caches.match(event.request).then(cached => {
            if (cached) {
                // Atualiza em background
                fetch(event.request).then(response => {
                    if (response && response.status === 200) {
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, response));
                    }
                }).catch(() => {});
                return cached;
            }
            return fetch(event.request).then(response => {
                if (response && response.status === 200 && event.request.method === 'GET') {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
                }
                return response;
            });
        })
    );
});
