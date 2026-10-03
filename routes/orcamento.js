const fs = require('fs');
const path = require('path');

// Diretórios base
const BASE_DIR = path.resolve(__dirname, '..');
const TEMPLATES_ORCAMENTO_DIR = path.resolve(BASE_DIR, 'templates_orcamento');
const PRESTADORES_FILE = path.resolve(TEMPLATES_ORCAMENTO_DIR, 'prestadores.json');

/**
 * Função utilitária para ler o catálogo de prestadores
 */
async function lerCatalogoPrestadores() {
    try {
        if (!fs.existsSync(PRESTADORES_FILE)) {
            return [];
        }
        const data = await fs.promises.readFile(PRESTADORES_FILE, 'utf-8');
        return JSON.parse(data);
    } catch (err) {
        console.error('[Catálogo] Erro ao ler prestadores.json:', err);
        return [];
    }
}

/**
 * Função utilitária para salvar o catálogo de prestadores
 */
async function salvarCatalogoPrestadores(lista) {
    if (!fs.existsSync(TEMPLATES_ORCAMENTO_DIR)) {
        await fs.promises.mkdir(TEMPLATES_ORCAMENTO_DIR, { recursive: true });
    }
    await fs.promises.writeFile(PRESTADORES_FILE, JSON.stringify(lista, null, 2), 'utf-8');
}

/**
 * Exclusão cirúrgica e segura de modelo de prestador
 * @param {string} id - ID único do prestador
 */
async function excluirModeloPrestador(id) {
    if (!id || typeof id !== 'string') {
        return { success: false, status: 400, mensagem: 'ID do prestador inválido ou não informado.' };
    }

    const idNormalizado = id.trim().toLowerCase();

    // Blindagem de Código: Protege o modelo nativo/padrão do sistema contra remoção
    if (idNormalizado === 'padrao' || idNormalizado === 'default' || idNormalizado === 'sistema') {
        return {
            success: false,
            status: 403,
            mensagem: 'O modelo padrão nativo do sistema é protegido e não pode ser excluído.'
        };
    }

    // 1. Leia templates_orcamento/prestadores.json
    const prestadores = await lerCatalogoPrestadores();

    // 2. Localize o item correspondente pelo id
    const index = prestadores.findIndex(p => String(p.id).trim().toLowerCase() === idNormalizado);
    if (index === -1) {
        return { success: false, status: 404, mensagem: `Modelo com ID "${id}" não encontrado no catálogo.` };
    }

    const itemRemovido = prestadores[index];

    // Blindagem adicional caso o objeto tenha flag de proteção
    if (itemRemovido.padrao === true || (itemRemovido.nome && itemRemovido.nome.toLowerCase().includes('padrão'))) {
        return {
            success: false,
            status: 403,
            mensagem: 'Este modelo está configurado como padrão e não pode ser excluído.'
        };
    }

    // 3. Remova fisicamente o arquivo do disco usando fs.promises.unlink(caminhoArquivo) de forma segura
    const nomeArquivo = itemRemovido.arquivo ? path.basename(itemRemovido.arquivo) : (itemRemovido.caminho ? path.basename(itemRemovido.caminho) : null);

    if (nomeArquivo) {
        const caminhoArquivo = path.resolve(TEMPLATES_ORCAMENTO_DIR, nomeArquivo);

        // Blindagem contra Path Traversal: valida se o arquivo realmente reside dentro de templates_orcamento/
        const relativePath = path.relative(TEMPLATES_ORCAMENTO_DIR, caminhoArquivo);
        const dentroDaPasta = !relativePath.startsWith('..') && !path.isAbsolute(relativePath);

        if (!dentroDaPasta) {
            console.error(`[Segurança] Tentativa de exclusão fora do diretório permitido: ${caminhoArquivo}`);
            return {
                success: false,
                status: 403,
                mensagem: 'Violação de segurança: O arquivo informado reside fora da pasta templates_orcamento.'
            };
        }

        try {
            if (fs.existsSync(caminhoArquivo)) {
                await fs.promises.unlink(caminhoArquivo);
                console.log(`[Exclusão] Arquivo físico removido com sucesso: ${caminhoArquivo}`);
            } else {
                console.warn(`[Exclusão] Arquivo físico não encontrado em disco: ${caminhoArquivo}`);
            }
        } catch (err) {
            console.error(`[Exclusão] Falha ao remover arquivo físico: ${err.message}`);
            return {
                success: false,
                status: 500,
                mensagem: `Erro ao remover o arquivo físico do modelo: ${err.message}`
            };
        }
    }

    // 4. Remova o prestador do array no JSON e salve o arquivo prestadores.json atualizado
    prestadores.splice(index, 1);
    await salvarCatalogoPrestadores(prestadores);

    // 5. Retorne { success: true, mensagem: "Modelo removido com sucesso" }
    return {
        success: true,
        status: 200,
        mensagem: 'Modelo removido com sucesso'
    };
}

/**
 * Middleware Express / Router compatível
 */
function configurarRotasOrcamento(appOrRouter) {
    // GET /api/orcamento/modelos-prestadores
    appOrRouter.get('/api/orcamento/modelos-prestadores', async (req, res) => {
        try {
            const catalogo = await lerCatalogoPrestadores();
            res.json(catalogo);
        } catch (err) {
            res.status(500).json({ error: err.message });
        }
    });

    // DELETE /api/orcamento/modelo-prestador/:id
    appOrRouter.delete('/api/orcamento/modelo-prestador/:id', async (req, res) => {
        try {
            const { id } = req.params;
            const resultado = await excluirModeloPrestador(id);
            res.status(resultado.status).json({
                success: resultado.success,
                mensagem: resultado.mensagem
            });
        } catch (err) {
            res.status(500).json({
                success: false,
                mensagem: `Erro interno no servidor: ${err.message}`
            });
        }
    });
}

module.exports = {
    excluirModeloPrestador,
    lerCatalogoPrestadores,
    salvarCatalogoPrestadores,
    configurarRotasOrcamento,
    TEMPLATES_ORCAMENTO_DIR,
    PRESTADORES_FILE
};
