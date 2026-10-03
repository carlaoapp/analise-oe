const CACHE_NAME = 'critica-orcamento-v18';
const ASSETS_TO_CACHE = [
    '/mobile/index.html',
    '/mobile/manifest.json',
    '/mobile/html2pdf.bundle.min.js'
];

// Instalação: Cache dos arquivos estáticos
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
        .then(cache => cache.addAll(ASSETS_TO_CACHE))
        .then(() => self.skipWaiting())
    );
});

// Ativação: Limpeza de caches antigos
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

// Fetch: Intercepta requisições
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Se for requisição para a API (/api/...)
    if (url.pathname.startsWith('/api/')) {
        // Network-first (tenta rede, se falhar, não faz nada pois o frontend lida com o catch)
        event.respondWith(
            fetch(event.request).catch(() => {
                // Se offline, devolve um Response de erro claro
                return new Response(JSON.stringify({ error: 'offline' }), {
                    status: 503,
                    headers: { 'Content-Type': 'application/json' }
                });
            })
        );
        return;
    }

    // Estratégia Stale-While-Revalidate para garantir Modo Offline instantâneo + Atualizações em Background
    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            // 1. Dispara a requisição na rede no fundo (se possível)
            const fetchPromise = fetch(event.request).then(networkResponse => {
                // Só salva no cache requisições GET válidas (evita erro com POST ou extensões do Chrome)
                if (event.request.method === 'GET' && networkResponse && networkResponse.status === 200 && (event.request.url.startsWith('http') || event.request.url.startsWith('https'))) {
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, networkResponse.clone());
                    });
                }
                return networkResponse;
            }).catch(() => {
                // Silencia erros de rede (offline) no background
            });

            // 2. Retorna o Cache IMEDIATAMENTE se existir (garante o offline sem travamentos)
            if (cachedResponse) {
                return cachedResponse;
            }

            // 3. Se não tem no cache, espera a rede
            return fetchPromise.then(response => {
                if (response) return response;
                // 4. Se a rede falhar e não tem cache, devolve fallback
                const acceptHeader = event.request.headers.get('accept');
                if (event.request.mode === 'navigate' || (acceptHeader && acceptHeader.includes('text/html'))) {
                    return caches.match('/mobile/index.html');
                }
                return new Response('Offline');
            });
        })
    );
});
