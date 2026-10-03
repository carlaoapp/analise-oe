const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const { excluirModeloPrestador, lerCatalogoPrestadores } = require('./routes/orcamento.js');

const PORT = process.env.PORT || 8080;
const PUBLIC_DIR = path.join(__dirname, 'public');

const MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.pdf': 'application/pdf',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
};

const server = http.createServer(async (req, res) => {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;

    // Rota DELETE: /api/orcamento/modelo-prestador/:id
    if (req.method === 'DELETE' && pathname.startsWith('/api/orcamento/modelo-prestador/')) {
        const id = decodeURIComponent(pathname.replace('/api/orcamento/modelo-prestador/', '')).trim();
        const resultado = await excluirModeloPrestador(id);
        res.writeHead(resultado.status, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify({
            success: resultado.success,
            mensagem: resultado.mensagem
        }));
        return;
    }

    // Rota GET: /api/orcamento/modelos-prestadores
    if (req.method === 'GET' && pathname === '/api/orcamento/modelos-prestadores') {
        const catalogo = await lerCatalogoPrestadores();
        res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
        res.end(JSON.stringify(catalogo));
        return;
    }

    // Rotas WhatsApp
    if (req.method === 'GET' && pathname === '/api/whatsapp/config') {
        const configPath = path.join(__dirname, 'data', 'config_whatsapp.json');
        if (fs.existsSync(configPath)) {
            res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
            res.end(fs.readFileSync(configPath, 'utf-8'));
        } else {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ remetentes_autorizados: [] }));
        }
        return;
    }

    if (req.method === 'GET' && pathname === '/api/whatsapp/inbox') {
        const inboxPath = path.join(__dirname, 'data', 'whatsapp_inbox.json');
        if (fs.existsSync(inboxPath)) {
            try {
                let data = JSON.parse(fs.readFileSync(inboxPath, 'utf-8'));
                const statusFilter = parsedUrl.query.status;
                if (statusFilter) {
                    data = data.filter(i => i.status === statusFilter);
                }
                res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
                res.end(JSON.stringify(data));
            } catch (e) {
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: e.message }));
            }
        } else {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify([]));
        }
        return;
    }

    // Proxy Reverso para o Backend Python (porta 8000) para qualquer outra rota /api/
    if (pathname.startsWith('/api/')) {
        const proxyReq = http.request({
            hostname: '127.0.0.1',
            port: 8000,
            path: req.url,
            method: req.method,
            headers: {
                ...req.headers,
                host: '127.0.0.1:8000'
            }
        }, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res, { end: true });
        });

        proxyReq.on('error', (err) => {
            res.writeHead(503, { 'Content-Type': 'application/json; charset=utf-8' });
            res.end(JSON.stringify({
                error: 'O servidor Python principal (servidor.py na porta 8000) não está em execução.',
                detalhe: err.message,
                orientacao: 'Execute INICIAR_SISTEMA.bat ou "python servidor.py" para ativar todos os recursos.'
            }));
        });

        req.pipe(proxyReq, { end: true });
        return;
    }

    // Static files fallback
    let filePath = path.join(PUBLIC_DIR, pathname === '/' ? 'index.html' : pathname);
    fs.stat(filePath, (err, stats) => {
        if (err || !stats.isFile()) {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Arquivo não encontrado' }));
            return;
        }

        const ext = path.extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        fs.createReadStream(filePath).pipe(res);
    });
});

if (require.main === module) {
    server.listen(PORT, () => {
        console.log(`[Node.js] Servidor rodando em http://localhost:${PORT}`);
    });
}

module.exports = server;
