/**
 * WORKFLOW CONTROLLER - ESTEIRA OPERACIONAL UNIFICADA
 * Gerencia a esteira de manutenção:
 * 1. O.S. Campo (Referência/Recepção)
 * 2. Checklist de Entrada (Vistoria Flexível & Triagem)
 * 3. O.S. Interna (Oficina Mecânica com Pilha de 7 Botões)
 * 4. Orçamento Interno (Fechamento Comercial em tempo real)
 * 5. Checklist de Saída (Vistoria Comparativa & Trava Gatekeeper)
 */

(function(window) {
    'use strict';

    const STORAGE_KEY = 'esteira_operacional_unificada_v1';

    // Estado Padrão Inicial
    const estadoInicial = {
        osId: "1002",
        cliente: "Fazenda Santa Cecília Agronegócios",
        solicitante: "Eduardo Silveira (Encarregado)",
        telefone: "5544998220002",
        frota: "Frota 204",
        veiculo: "Colheitadeira Case IH 8250",
        horimetro: "1850",
        dataEntrada: new Date().toISOString().split('T')[0],
        tecnicoCampo: "Rodrigo Sanches",
        relatoCampo: "Ruído anormal no rotor de trilha e superaquecimento no mancal axial durante colheita de milho.",
        
        // Checklist de Entrada
        checkin: {
            status: "concluido", // pendente | andamento | concluido
            responsavel: "Carlos Mecânico (Oficina)",
            data: new Date().toISOString().split('T')[0],
            itens: [
                {
                    id: "item_1",
                    nome: "Rotor de Trilha e Mancal Axial",
                    categoria: "Transmissão / Colheita",
                    status: "avaria", // conforme | avaria | na
                    obs: "Rolamento autocompensador com folga excessiva e travamento parcial.",
                    aprovadoReparo: true,
                    medias: [
                        { id: "m1", tipo: "foto", url: "/img/placeholder_peca1.jpg", nota: "Folga radial no mancal" }
                    ]
                },
                {
                    id: "item_2",
                    nome: "Correia de Acionamento do Rotor",
                    categoria: "Transmissão",
                    status: "avaria",
                    obs: "Desgaste nos flancos e estiramento além do limite de tensão.",
                    aprovadoReparo: true,
                    medias: [
                        { id: "m2", tipo: "foto", url: "/img/placeholder_peca2.jpg", nota: "Desgaste nos flancos" }
                    ]
                },
                {
                    id: "item_3",
                    nome: "Circuito Hidráulico do Picador",
                    categoria: "Hidráulico",
                    status: "conforme",
                    obs: "Pressão normal de trabalho (190 bar), sem vazamentos.",
                    aprovadoReparo: false,
                    medias: []
                },
                {
                    id: "item_4",
                    nome: "Nível de Óleo do Motor e Filtros",
                    categoria: "Motor Diesel",
                    status: "conforme",
                    obs: "Nível na marca correta, sem contaminação.",
                    aprovadoReparo: false,
                    medias: []
                }
            ],
            assinatura: null
        },

        // O.S. Interna (Oficina)
        osInterna: {
            status: "andamento", // andamento | liberado | finalizada
            statusGatekeeper: "bloqueado", // bloqueado | liberado
            mecanicoLider: "Rodrigo Sanches",
            pecas: [
                { codigo: "ROL-8250", descricao: "Rolamento Autocompensador Case 8250", qtd: 1, unit: 890.00 },
                { codigo: "COR-3VX", descricao: "Jogo de Correias de Transmissão Gates", qtd: 1, unit: 350.00 },
                { codigo: "RET-90", descricao: "Retentor de Vedação Alta Temperatura", qtd: 2, unit: 75.00 }
            ],
            servicos: [
                { servico: "Desmontagem do Rotor e Extração do Mancal", mecanico: "Rodrigo Sanches", horas: 3.5, valorHora: 150.00 },
                { servico: "Alinhamento de Polias e Ajuste de Tensão de Correias", mecanico: "Rodrigo Sanches", horas: 2.0, valorHora: 150.00 }
            ],
            mediasOficina: [],
            assinatura: null,
            dataFinalizacao: null
        },

        // Orçamento Interno
        orcamento: {
            modeloAtivo: "padrao",
            statusFinanceiro: "aguardando_faturamento",
            desconto: 0.00
        },

        // Checklist de Saída
        checkout: {
            status: "pendente", // pendente | andamento | concluido
            responsavel: "Eduardo Silveira (Encarregado do Cliente)",
            data: new Date().toISOString().split('T')[0],
            itensComparativos: [
                {
                    itemEntradaId: "item_1",
                    nome: "Rotor de Trilha e Mancal Axial",
                    fotoEntrada: "/img/placeholder_peca1.jpg",
                    fotoSaida: null,
                    concluido: false
                },
                {
                    itemEntradaId: "item_2",
                    nome: "Correia de Acionamento do Rotor",
                    fotoEntrada: "/img/placeholder_peca2.jpg",
                    fotoSaida: null,
                    concluido: false
                }
            ],
            itensFuncionais: [
                { nome: "Teste de rotação do rotor em vazio", status: "conforme" },
                { nome: "Verificação de ruído e temperatura de mancal", status: "conforme" },
                { nome: "Recolhimento de peças velhas para descarte", status: "conforme" },
                { nome: "Limpeza da área de trabalho e cabine", status: "conforme" }
            ],
            assinatura: null
        }
    };

    class WorkflowManager {
        constructor() {
            this.state = this.carregarEstado();
            this.activePhotoEdit = null; // Para o micro-editor canvas
            this.canvasSigInstances = {};
        }

        carregarEstado() {
            try {
                const salvo = localStorage.getItem(STORAGE_KEY);
                if (salvo) {
                    return JSON.parse(salvo);
                }
            } catch (e) {
                console.warn("Erro ao carregar estado salvo, usando padrão:", e);
            }
            return JSON.parse(JSON.stringify(estadoInicial));
        }

        salvarEstado() {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state));
            } catch (e) {
                console.warn("Erro ao salvar no localStorage:", e);
            }
            this.emitirEvento('estado:atualizado', this.state);
        }

        resetarParaPadrao() {
            this.state = JSON.parse(JSON.stringify(estadoInicial));
            this.salvarEstado();
            this.renderizarTudo();
        }

        emitirEvento(nome, dados) {
            window.dispatchEvent(new CustomEvent(nome, { detail: dados }));
        }

        // =========================================================================
        // CÁLCULOS FINANCEIROS EM TEMPO REAL
        // =========================================================================
        calcularTotaisOficina() {
            const pecasTotal = this.state.osInterna.pecas.reduce((acc, p) => acc + (p.qtd * p.unit), 0);
            const servicosTotal = this.state.osInterna.servicos.reduce((acc, s) => acc + (s.horas * s.valorHora), 0);
            const totalGeral = pecasTotal + servicosTotal - (this.state.orcamento.desconto || 0);

            return {
                pecasTotal,
                servicosTotal,
                desconto: this.state.orcamento.desconto || 0,
                totalGeral
            };
        }

        formatarMoeda(val) {
            return (val || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        }

        // =========================================================================
        // TRIAGEM: TRANSFERIR ITENS APROVADOS DO CHECKIN PARA O.S. INTERNA
        // =========================================================================
        salvarCheckin() {
            const sig = this.obterAssinaturaDataUrl('canvasAssinaturaCheckin');
            if (sig) {
                this.state.checkin.assinatura = sig;
            }
            const itensAprovados = this.state.checkin.itens.filter(i => i.status === 'avaria');
            
            // Atualiza comparativo no checklist de saída
            this.state.checkout.itensComparativos = itensAprovados.map(it => {
                const primFoto = (it.medias && it.medias.length > 0) ? it.medias[0].url : null;
                const existente = (this.state.checkout.itensComparativos || []).find(c => c.itemEntradaId === it.id);
                return {
                    itemEntradaId: it.id,
                    nome: it.nome,
                    fotoEntrada: primFoto,
                    fotoSaida: existente ? existente.fotoSaida : null,
                    concluido: existente ? existente.concluido : false
                };
            });

            this.state.checkin.status = "concluido";
            this.salvarEstado();
            this.renderizarTudo();
            alert("Checklist de Entrada salvo com sucesso!\n\nAs avarias e fotos registradas foram sincronizadas para a Ordem Interna da oficina.");
        }

        transferirAprovadosParaOSInterna() {
            const itensAprovados = this.state.checkin.itens.filter(i => i.status === 'avaria' && i.aprovadoReparo);
            if (itensAprovados.length === 0) {
                alert("Nenhum item com avaria foi marcado como 'Aprovado para Reparo'.");
                return;
            }

            // Atualiza comparativo no checklist de saída
            this.state.checkout.itensComparativos = itensAprovados.map(it => {
                const primFoto = (it.medias && it.medias.length > 0) ? it.medias[0].url : null;
                const existente = (this.state.checkout.itensComparativos || []).find(c => c.itemEntradaId === it.id);
                return {
                    itemEntradaId: it.id,
                    nome: it.nome,
                    fotoEntrada: primFoto,
                    fotoSaida: existente ? existente.fotoSaida : null,
                    concluido: existente ? existente.concluido : false
                };
            });

            this.state.checkin.status = "concluido";
            this.state.osInterna.status = "andamento";
            this.salvarEstado();
            this.renderizarTudo();

            // Se estiver na esteira unificada, rola e expande
            if (document.getElementById('bloco-os-interna')) {
                this.expandirBloco('bloco-os-interna');
            } else {
                window.location.href = 'ordem_servico_interna.html';
            }
        }

        // =========================================================================
        // GATEKEEPER: LIBERAÇÃO DA O.S. INTERNA PELO CHECKLIST DE SAÍDA
        // =========================================================================
        verificarGatekeeper() {
            const checkoutAssinado = Boolean(this.state.checkout.assinatura);
            const statusLiberado = checkoutAssinado;

            if (statusLiberado) {
                this.state.osInterna.statusGatekeeper = "liberado";
            } else {
                this.state.osInterna.statusGatekeeper = "bloqueado";
            }

            return statusLiberado;
        }

        salvarCheckoutLibertador(assinaturaDataUrl) {
            this.state.checkout.assinatura = assinaturaDataUrl;
            this.state.checkout.status = "concluido";
            this.state.osInterna.statusGatekeeper = "liberado";
            this.state.osInterna.status = "liberado"; // Destrava Finalização!

            this.salvarEstado();
            this.renderizarTudo();

            alert("Checklist de Saída concluído e assinado com sucesso!\n\nA máquina foi liberada tecnicamente. A Ordem Interna da oficina foi destravada para encerramento!");
            
            // Se estiver na esteira, foca na O.S. Interna
            if (document.getElementById('bloco-os-interna')) {
                this.expandirBloco('bloco-os-interna');
            }
        }

        // =========================================================================
        // ACORDEÃO E EXPANSÃO DE BLOCOS
        // =========================================================================
        toggleBloco(blockId) {
            const el = document.getElementById(blockId);
            if (!el) return;
            el.classList.toggle('expanded');
        }

        expandirBloco(blockId) {
            const el = document.getElementById(blockId);
            if (!el) return;
            el.classList.add('expanded');
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        // =========================================================================
        // HUB MULTIMÍDIA & VALIDAÇÃO DE VÍDEO (MAX 30s / 25MB)
        // =========================================================================
        processarArquivoMidia(file, callback) {
            if (!file) return;

            const isVideo = file.type.startsWith('video/');
            const maxSize = 25 * 1024 * 1024; // 25 MB

            if (file.size > maxSize) {
                alert(`Arquivo excede o limite máximo permitido de 25 MB (${(file.size / (1024*1024)).toFixed(1)} MB).`);
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                const dataUrl = e.target.result;

                if (isVideo) {
                    // Valida duração de vídeo inline via elemento temporário
                    const tempVid = document.createElement('video');
                    tempVid.src = dataUrl;
                    tempVid.onloadedmetadata = () => {
                        if (tempVid.duration > 35) { // tolerância suave
                            alert(`Vídeo muito longo (${tempVid.duration.toFixed(0)}s). O limite de segurança para mídias de campo e oficina é de até 30 segundos.`);
                            return;
                        }
                        callback({
                            id: 'media_' + Date.now(),
                            tipo: 'video',
                            url: dataUrl,
                            duracao: tempVid.duration.toFixed(1) + 's',
                            nome: file.name
                        });
                    };
                } else {
                    callback({
                        id: 'media_' + Date.now(),
                        tipo: 'foto',
                        url: dataUrl,
                        nome: file.name
                    });
                }
            };
            reader.readAsDataURL(file);
        }

        // =========================================================================
        // MICRO-EDITOR CANVAS PARA FOTOS (MARCAÇÃO VERMELHA & NOTAS)
        // =========================================================================
        abrirMicroEditorFoto(itemOuMediaRef, mediaIndex, dataUrl) {
            this.activePhotoEdit = { ref: itemOuMediaRef, index: mediaIndex, url: dataUrl };
            const modal = document.getElementById('canvasEditorModal');
            const canvas = document.getElementById('canvasEditorStage');
            if (!modal || !canvas) return;

            const ctx = canvas.getContext('2d');
            const img = new Image();
            img.onload = () => {
                // Dimensões limitadas para viewport mobile
                const maxW = 420;
                const scale = Math.min(1, maxW / img.width);
                canvas.width = img.width * scale;
                canvas.height = img.height * scale;
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                this.setupCanvasDrawing(canvas, ctx);
                modal.classList.add('active');
            };
            img.src = dataUrl;
        }

        setupCanvasDrawing(canvas, ctx) {
            let drawing = false;
            ctx.strokeStyle = '#ef4444'; // Linha Vermelha de Destaque
            ctx.lineWidth = 4;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            const getPos = (e) => {
                const rect = canvas.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                return {
                    x: (clientX - rect.left) * (canvas.width / rect.width),
                    y: (clientY - rect.top) * (canvas.height / rect.height)
                };
            };

            canvas.onmousedown = canvas.ontouchstart = (e) => {
                e.preventDefault();
                drawing = true;
                const pos = getPos(e);
                ctx.beginPath();
                ctx.moveTo(pos.x, pos.y);
            };

            canvas.onmousemove = canvas.ontouchmove = (e) => {
                if (!drawing) return;
                e.preventDefault();
                const pos = getPos(e);
                ctx.lineTo(pos.x, pos.y);
                ctx.stroke();
            };

            canvas.onmouseup = canvas.ontouchend = () => {
                drawing = false;
            };
        }

        adicionarAnotacaoTextoCanvas(texto) {
            const canvas = document.getElementById('canvasEditorStage');
            if (!canvas || !texto) return;
            const ctx = canvas.getContext('2d');

            ctx.font = 'bold 16px Inter, sans-serif';
            ctx.fillStyle = '#ef4444';
            ctx.shadowColor = 'rgba(0,0,0,0.8)';
            ctx.shadowBlur = 4;
            ctx.fillText(texto, 20, 30);
            ctx.shadowBlur = 0;
        }

        salvarMicroEditorFoto() {
            const canvas = document.getElementById('canvasEditorStage');
            const modal = document.getElementById('canvasEditorModal');
            if (!canvas || !this.activePhotoEdit) return;

            const novoDataUrl = canvas.toDataURL('image/jpeg', 0.9);
            const { ref, index } = this.activePhotoEdit;

            if (ref && ref.medias && ref.medias[index]) {
                ref.medias[index].url = novoDataUrl;
                ref.medias[index].editado = true;
            } else if (Array.isArray(ref) && ref[index]) {
                ref[index].url = novoDataUrl;
                ref[index].editado = true;
            }

            this.salvarEstado();
            this.renderizarTudo();
            if (modal) modal.classList.remove('active');
            this.activePhotoEdit = null;
        }

        fecharMicroEditor() {
            const modal = document.getElementById('canvasEditorModal');
            if (modal) modal.classList.remove('active');
            this.activePhotoEdit = null;
        }

        // =========================================================================
        // ASSINATURAS TOUCH DIGITAIS (CANVAS)
        // =========================================================================
        inicializarCanvasAssinatura(canvasId) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;

            // Ajusta escala do display
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width || 340;
            canvas.height = rect.height || 140;

            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = '#0f172a'; // Tinta escura para canvas branco
            ctx.lineWidth = 2.5;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            let drawing = false;

            const getPos = (e) => {
                const r = canvas.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                return {
                    x: (clientX - r.left) * (canvas.width / r.width),
                    y: (clientY - r.top) * (canvas.height / r.height)
                };
            };

            canvas.onmousedown = canvas.ontouchstart = (e) => {
                e.preventDefault();
                drawing = true;
                const pos = getPos(e);
                ctx.beginPath();
                ctx.moveTo(pos.x, pos.y);
            };

            canvas.onmousemove = canvas.ontouchmove = (e) => {
                if (!drawing) return;
                e.preventDefault();
                const pos = getPos(e);
                ctx.lineTo(pos.x, pos.y);
                ctx.stroke();
            };

            canvas.onmouseup = canvas.ontouchend = () => {
                drawing = false;
            };

            this.canvasSigInstances[canvasId] = { canvas, ctx };
        }

        limparAssinatura(canvasId) {
            const inst = this.canvasSigInstances[canvasId];
            if (!inst) return;
            const { canvas, ctx } = inst;
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        obterAssinaturaDataUrl(canvasId) {
            const inst = this.canvasSigInstances[canvasId];
            if (!inst) return null;
            return inst.canvas.toDataURL('image/png');
        }

        // =========================================================================
        // EXPORTAÇÕES E WHATSAPP
        // =========================================================================
        exportarDocumento(formato, modulo) {
            const totais = this.calcularTotaisOficina();
            const resumo = `*Ordem de Serviço #${this.state.osId}*\n` +
                          `*Cliente:* ${this.state.cliente}\n` +
                          `*Equipamento:* ${this.state.veiculo} (${this.state.frota})\n` +
                          `*Horímetro:* ${this.state.horimetro} h\n` +
                          `*Total Peças:* ${this.formatarMoeda(totais.pecasTotal)}\n` +
                          `*Total Mão de Obra:* ${this.formatarMoeda(totais.servicosTotal)}\n` +
                          `*VALOR GERAL:* ${this.formatarMoeda(totais.totalGeral)}\n` +
                          `*Status:* ${this.state.osInterna.status.toUpperCase()}\n` +
                          `*Liberação Técnica:* ${this.state.osInterna.statusGatekeeper === 'liberado' ? 'LIBERADA ✓' : 'PENDENTE ⚠️'}`;

            if (formato === 'whatsapp') {
                const msg = encodeURIComponent(`Olá, segue a atualização da sua O.S.:\n\n${resumo}`);
                const url = `https://api.whatsapp.com/send?phone=${this.state.telefone}&text=${msg}`;
                window.open(url, '_blank');
            } else if (formato === 'copiar') {
                navigator.clipboard.writeText(resumo).then(() => {
                    alert("Resumo da O.S. copiado para a área de transferência com sucesso!");
                });
            } else if (formato === 'imprimir') {
                window.print();
            } else {
                alert(`Geração de ${formato.toUpperCase()} para o módulo [${modulo}] disparada com sucesso!\n\n${resumo}`);
            }
        }

        // =========================================================================
        // FINALIZAÇÃO DA O.S. INTERNA (CHECK DO GATEKEEPER)
        // =========================================================================
        finalizarOSInterna() {
            if (this.state.osInterna.statusGatekeeper !== 'liberado') {
                alert("TRAVA DE SEGURANÇA (GATEKEEPER ATIVO):\n\nA Ordem de Serviço Interna NÃO PODE ser finalizada antes da conclusão e assinatura digital do Checklist de Saída (Entrega Técnica)!");
                this.expandirBloco('bloco-checklist-saida');
                return;
            }

            this.state.osInterna.status = "finalizada";
            this.state.osInterna.dataFinalizacao = new Date().toLocaleString('pt-BR');
            this.salvarEstado();
            this.renderizarTudo();

            alert(`ORDEM DE SERVIÇO #${this.state.osId} FINALIZADA COM SUCESSO!\n\nEquipamento inspecionado na entrada, reparado na oficina, aprovado na vistoria de saída e liberado para o cliente.`);
        }

        // =========================================================================
        // RENDERIZAÇÃO CENTRAL DOS DADOS NA TELA
        // =========================================================================
        renderizarTudo() {
            this.renderizarCabecalhoGeral();
            this.renderizarBlocoCheckin();
            this.renderizarBlocoOSInterna();
            this.renderizarBlocoOrcamento();
            this.renderizarBlocoCheckout();
            this.renderizarSteppers();
        }

        renderizarCabecalhoGeral() {
            const els = {
                osId: document.querySelectorAll('.bind-os-id'),
                cliente: document.querySelectorAll('.bind-cliente'),
                frota: document.querySelectorAll('.bind-frota'),
                veiculo: document.querySelectorAll('.bind-veiculo'),
                horimetro: document.querySelectorAll('.bind-horimetro'),
                dataEntrada: document.querySelectorAll('.bind-data-entrada')
            };

            els.osId.forEach(el => el.textContent = '#' + this.state.osId);
            els.cliente.forEach(el => el.textContent = this.state.cliente);
            els.frota.forEach(el => el.textContent = this.state.frota);
            els.veiculo.forEach(el => el.textContent = this.state.veiculo);
            els.horimetro.forEach(el => el.textContent = this.state.horimetro + ' h');
            els.dataEntrada.forEach(el => el.textContent = this.state.dataEntrada);
        }

        renderizarSteppers() {
            const stCheckin = this.state.checkin.status;
            const stInterna = this.state.osInterna.status;
            const stCheckout = this.state.checkout.status;

            const updateStep = (num, status) => {
                const el = document.getElementById(`step-item-${num}`);
                const numEl = document.getElementById(`step-num-${num}`);
                if (!el || !numEl) return;
                el.className = 'progress-step-item';
                numEl.className = 'step-number';

                if (status === 'concluido' || status === 'finalizada' || status === 'liberado') {
                    el.classList.add('completed');
                    numEl.classList.add('completed');
                } else if (status === 'andamento') {
                    el.classList.add('active');
                    numEl.classList.add('active');
                }
            };

            updateStep(1, stCheckin);
            updateStep(2, stInterna);
            updateStep(3, this.state.orcamento.statusFinanceiro === 'faturada' ? 'concluido' : 'andamento');
            updateStep(4, stCheckout);
        }

        renderizarBlocoCheckin() {
            const badgeCheckin = document.getElementById('badgeCheckinStatus');
            if (badgeCheckin) {
                if (this.state.checkin.status === 'concluido') {
                    badgeCheckin.className = 'status-badge concluido';
                    badgeCheckin.textContent = 'CONCLUÍDO';
                } else {
                    badgeCheckin.className = 'status-badge pendente';
                    badgeCheckin.textContent = 'PENDENTE';
                }
            }

            const listEl = document.getElementById('checkinItensList');
            if (!listEl) return;

            listEl.innerHTML = '';
            this.state.checkin.itens.forEach((it, idx) => {
                const card = document.createElement('div');
                card.className = `checklist-item-card ${it.status === 'avaria' ? 'has-defect' : ''}`;

                let mediasHtml = '';
                if (it.medias && it.medias.length > 0) {
                    mediasHtml = `
                        <div class="media-preview-list">
                            ${it.medias.map((m, mIdx) => `
                                <div class="media-thumbnail-card" onclick="workflow.abrirMicroEditorFoto(workflow.state.checkin.itens[${idx}], ${mIdx}, '${m.url}')" title="Toque para abrir no micro-editor canvas">
                                    ${m.tipo === 'video' ? `<video src="${m.url}"></video><span class="badge-video"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> ${m.duracao || '30s'}</span>` : `<img src="${m.url}" alt="Avaria">`}
                                    <button type="button" class="btn-remove-media" onclick="event.stopPropagation(); workflow.removerMidiaCheckin(${idx}, ${mIdx})">✕</button>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }

                card.innerHTML = `
                    <div class="checklist-item-header">
                        <div class="checklist-item-meta-bar">
                            <span class="checklist-item-cat">${it.categoria}</span>
                            <div class="checklist-status-radios">
                                <button type="button" class="status-radio-label conforme ${it.status === 'conforme' ? 'active' : ''}" onclick="workflow.alterarStatusItemCheckin(${idx}, 'conforme')">OK</button>
                                <button type="button" class="status-radio-label avaria ${it.status === 'avaria' ? 'active' : ''}" onclick="workflow.alterarStatusItemCheckin(${idx}, 'avaria')">AVARIA</button>
                                <button type="button" class="status-radio-label na ${it.status === 'na' ? 'active' : ''}" onclick="workflow.alterarStatusItemCheckin(${idx}, 'na')">N/A</button>
                            </div>
                        </div>
                        <div class="checklist-item-title">${it.nome}</div>
                    </div>
                    ${it.obs ? `<div style="font-size:0.75rem; color:var(--txt-secondary);">${it.obs}</div>` : ''}
                    
                    <!-- Hub de mídias por item -->
                    <div class="media-hub-grid" style="margin-top: 4px;">
                        <label class="btn-media-capture">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
                            Câmera
                            <input type="file" accept="image/*" capture="environment" style="display:none;" onchange="workflow.adicionarMidiaItem(${idx}, this.files[0])">
                        </label>
                        <label class="btn-media-capture">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                            Galeria
                            <input type="file" accept="image/*" multiple style="display:none;" onchange="workflow.adicionarMidiaItem(${idx}, this.files[0])">
                        </label>
                        <label class="btn-media-capture">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
                            Gravar Vídeo
                            <input type="file" accept="video/*" capture="camcorder" style="display:none;" onchange="workflow.adicionarMidiaItem(${idx}, this.files[0])">
                        </label>
                        <label class="btn-media-capture">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M15 10l4.553-2.276A1 1 0 0 1 21 8.618v6.764a1 1 0 0 1-1.447.894L15 14v-4z"></path><rect x="3" y="6" width="12" height="12" rx="2"></rect></svg>
                            Anexar Vídeo
                            <input type="file" accept="video/*" style="display:none;" onchange="workflow.adicionarMidiaItem(${idx}, this.files[0])">
                        </label>
                    </div>

                    ${mediasHtml}

                    ${it.status === 'avaria' ? `
                        <div class="triage-approval-box">
                            <label class="triage-checkbox-label">
                                <input type="checkbox" ${it.aprovadoReparo ? 'checked' : ''} onchange="workflow.toggleAprovacaoItem(${idx}, this.checked)">
                                Aprovar para Reparo na O.S. Interna
                            </label>
                        </div>
                    ` : ''}
                `;
                listEl.appendChild(card);
            });
        }

        renderizarBlocoOSInterna() {
            // Tabela de Peças
            const pecasTbody = document.getElementById('tabelaPecasCorpo');
            if (pecasTbody) {
                pecasTbody.innerHTML = this.state.osInterna.pecas.map((p, idx) => `
                    <tr>
                        <td><code>${p.codigo}</code></td>
                        <td>${p.descricao}</td>
                        <td style="text-align:center;">${p.qtd}</td>
                        <td style="text-align:right;">${this.formatarMoeda(p.unit)}</td>
                        <td style="text-align:right; font-weight:700;">${this.formatarMoeda(p.qtd * p.unit)}</td>
                        <td style="text-align:center;"><button type="button" class="btn-tool" onclick="workflow.removerPeca(${idx})">✕</button></td>
                    </tr>
                `).join('');
            }

            // Tabela de Serviços / Mão de Obra
            const servTbody = document.getElementById('tabelaServicosCorpo');
            if (servTbody) {
                servTbody.innerHTML = this.state.osInterna.servicos.map((s, idx) => `
                    <tr>
                        <td>${s.servico}</td>
                        <td>${s.mecanico}</td>
                        <td style="text-align:center;">${s.horas}h</td>
                        <td style="text-align:right;">${this.formatarMoeda(s.valorHora)}</td>
                        <td style="text-align:right; font-weight:700;">${this.formatarMoeda(s.horas * s.valorHora)}</td>
                        <td style="text-align:center;"><button type="button" class="btn-tool" onclick="workflow.removerServico(${idx})">✕</button></td>
                    </tr>
                `).join('');
            }

            // Mídias da oficina
            const mediaOficinaEl = document.getElementById('mediasOficinaList');
            if (mediaOficinaEl) {
                mediaOficinaEl.innerHTML = (this.state.osInterna.mediasOficina || []).map((m, mIdx) => `
                    <div class="media-thumbnail-card" onclick="workflow.abrirMicroEditorFoto(workflow.state.osInterna.mediasOficina, ${mIdx}, '${m.url}')">
                        ${m.tipo === 'video' ? `<video src="${m.url}"></video><span class="badge-video"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> ${m.duracao || '30s'}</span>` : `<img src="${m.url}" alt="Oficina">`}
                        <button type="button" class="btn-remove-media" onclick="event.stopPropagation(); workflow.removerMidiaOficina(${mIdx})">✕</button>
                    </div>
                `).join('');
            }

            // Gatekeeper Status e Trava do Botão [Finalizar Ordem de Serviço]
            const btnFinalizar = document.getElementById('btnFinalizarOSInterna');
            const alertGatekeeper = document.getElementById('alertGatekeeperOS');
            const badgeInterna = document.getElementById('badgeStatusOSInterna');

            const isLiberado = this.verificarGatekeeper();

            if (btnFinalizar) {
                if (isLiberado) {
                    btnFinalizar.disabled = false;
                    btnFinalizar.classList.remove('is-locked');
                    btnFinalizar.title = "Equipamento liberado! Clique para finalizar a O.S.";
                } else {
                    btnFinalizar.disabled = true;
                    btnFinalizar.classList.add('is-locked');
                    btnFinalizar.title = "Finalização travada: aguardando conclusão e assinatura do Checklist de Saída";
                }
            }

            if (alertGatekeeper) {
                if (isLiberado) {
                    alertGatekeeper.className = 'gatekeeper-warning-box unlocked';
                    alertGatekeeper.innerHTML = `
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                        <div><b>LIBERAÇÃO TÉCNICA CONCLUÍDA:</b> O Checklist de Saída foi assinado. A O.S. Interna está liberada para encerramento!</div>
                    `;
                } else {
                    alertGatekeeper.className = 'gatekeeper-warning-box';
                    alertGatekeeper.innerHTML = `
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                        <div><b>TRAVA DE SEGURANÇA ATIVA:</b> O botão [Finalizar Ordem de Serviço] permanecerá bloqueado até que a vistoria de saída e a assinatura do cliente sejam salvas no Bloco 4.</div>
                    `;
                }
            }

            if (badgeInterna) {
                if (this.state.osInterna.status === 'finalizada') {
                    badgeInterna.className = 'status-badge concluido';
                    badgeInterna.textContent = 'FINALIZADA';
                } else if (isLiberado) {
                    badgeInterna.className = 'status-badge liberado';
                    badgeInterna.textContent = 'LIBERADO';
                } else {
                    badgeInterna.className = 'status-badge andamento';
                    badgeInterna.textContent = 'EM ANDAMENTO';
                }
            }
        }

        renderizarBlocoOrcamento() {
            const totais = this.calcularTotaisOficina();

            const elPecas = document.getElementById('orcPecasTotal');
            const elServicos = document.getElementById('orcServicosTotal');
            const elGeral = document.getElementById('orcTotalGeral');

            if (elPecas) elPecas.textContent = this.formatarMoeda(totais.pecasTotal);
            if (elServicos) elServicos.textContent = this.formatarMoeda(totais.servicosTotal);
            if (elGeral) elGeral.textContent = this.formatarMoeda(totais.totalGeral);

            const orcCorpo = document.getElementById('tabelaOrcamentoCorpo');
            if (orcCorpo) {
                let html = '';
                this.state.osInterna.pecas.forEach(p => {
                    html += `<tr>
                        <td><span style="font-size:10px; font-weight:700; color:var(--accent); background:rgba(37,99,235,0.15); padding:2px 6px; border-radius:4px;">PEÇA</span></td>
                        <td>${p.descricao}</td>
                        <td style="text-align:center;">${p.qtd}</td>
                        <td style="text-align:right; font-weight:700;">${this.formatarMoeda(p.qtd * p.unit)}</td>
                    </tr>`;
                });
                this.state.osInterna.servicos.forEach(s => {
                    html += `<tr>
                        <td><span style="font-size:10px; font-weight:700; color:#34d399; background:rgba(16,185,129,0.15); padding:2px 6px; border-radius:4px;">SERVIÇO</span></td>
                        <td>${s.servico} (${s.mecanico})</td>
                        <td style="text-align:center;">${s.horas}h</td>
                        <td style="text-align:right; font-weight:700;">${this.formatarMoeda(s.horas * s.valorHora)}</td>
                    </tr>`;
                });
                orcCorpo.innerHTML = html;
            }
        }

        renderizarBlocoCheckout() {
            const badgeCheckout = document.getElementById('badgeCheckoutStatus');
            if (badgeCheckout) {
                if (this.state.checkout.status === 'concluido') {
                    badgeCheckout.className = 'status-badge concluido';
                    badgeCheckout.textContent = 'CONCLUÍDO';
                } else {
                    badgeCheckout.className = 'status-badge pendente';
                    badgeCheckout.textContent = 'PENDENTE';
                }
            }

            const compList = document.getElementById('checkoutComparativoList');
            if (!compList) return;

            const itens = this.state.checkout.itensComparativos || [];
            if (itens.length === 0) {
                compList.innerHTML = `<div style="font-size:0.75rem; color:var(--txt-muted); text-align:center; padding:10px;">Nenhum item com avaria foi transferido da vistoria de entrada.</div>`;
                return;
            }

            compList.innerHTML = itens.map((c, idx) => `
                <div class="inner-card" style="margin-bottom:8px;">
                    <div style="font-size:0.82rem; font-weight:700; color:var(--txt-primary);">${c.nome}</div>
                    <div class="comparison-grid">
                        <div class="comparison-column">
                            <span class="comparison-column-header"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg> Entrada (Defeito)</span>
                            <div class="comparison-media-slot">
                                ${c.fotoEntrada ? `<img src="${c.fotoEntrada}" alt="Entrada">` : `<span style="font-size:0.65rem; color:var(--txt-muted);">Sem Foto</span>`}
                            </div>
                        </div>
                        <div class="comparison-column">
                            <span class="comparison-column-header" style="color:#34d399;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="20 6 9 17 4 12"></polyline></svg> Saída (Reparado)</span>
                            <div class="comparison-media-slot" id="slotSaida_${idx}" onclick="document.getElementById('inputFotoSaida_${idx}').click()" style="cursor:pointer;" title="Toque para capturar foto pós-reparo">
                                ${c.fotoSaida ? `<img src="${c.fotoSaida}" alt="Saída">` : `<span style="font-size:0.65rem; color:var(--accent); text-align:center;">+ Capturar<br>Pós-Reparo</span>`}
                            </div>
                            <input type="file" id="inputFotoSaida_${idx}" accept="image/*" capture="environment" style="display:none;" onchange="workflow.adicionarFotoSaidaComparativa(${idx}, this.files[0])">
                        </div>
                    </div>
                </div>
            `).join('');
        }

        // =========================================================================
        // MÉTODOS DE AÇÃO
        // =========================================================================
        alterarStatusItemCheckin(idx, status) {
            if (!this.state.checkin.itens[idx]) return;
            this.state.checkin.itens[idx].status = status;
            if (status === 'conforme' || status === 'na') {
                this.state.checkin.itens[idx].aprovadoReparo = false;
            } else if (status === 'avaria') {
                this.state.checkin.itens[idx].aprovadoReparo = true;
            }
            this.salvarEstado();
            this.renderizarBlocoCheckin();
        }

        toggleAprovacaoItem(idx, checked) {
            if (!this.state.checkin.itens[idx]) return;
            this.state.checkin.itens[idx].aprovadoReparo = checked;
            this.salvarEstado();
        }

        adicionarMidiaItem(idx, file) {
            if (!file) return;
            this.processarArquivoMidia(file, (mediaObj) => {
                if (!this.state.checkin.itens[idx].medias) {
                    this.state.checkin.itens[idx].medias = [];
                }
                this.state.checkin.itens[idx].medias.push(mediaObj);
                this.salvarEstado();
                this.renderizarBlocoCheckin();
            });
        }

        removerMidiaCheckin(itemIdx, mediaIdx) {
            if (this.state.checkin.itens[itemIdx] && this.state.checkin.itens[itemIdx].medias) {
                this.state.checkin.itens[itemIdx].medias.splice(mediaIdx, 1);
                this.salvarEstado();
                this.renderizarBlocoCheckin();
            }
        }

        adicionarMidiaOficina(file) {
            if (!file) return;
            this.processarArquivoMidia(file, (mediaObj) => {
                if (!this.state.osInterna.mediasOficina) {
                    this.state.osInterna.mediasOficina = [];
                }
                this.state.osInterna.mediasOficina.push(mediaObj);
                this.salvarEstado();
                this.renderizarBlocoOSInterna();
            });
        }

        removerMidiaOficina(mediaIdx) {
            if (this.state.osInterna.mediasOficina) {
                this.state.osInterna.mediasOficina.splice(mediaIdx, 1);
                this.salvarEstado();
                this.renderizarBlocoOSInterna();
            }
        }

        adicionarFotoSaidaComparativa(idx, file) {
            if (!file) return;
            this.processarArquivoMidia(file, (mediaObj) => {
                if (this.state.checkout.itensComparativos[idx]) {
                    this.state.checkout.itensComparativos[idx].fotoSaida = mediaObj.url;
                    this.state.checkout.itensComparativos[idx].concluido = true;
                    this.salvarEstado();
                    this.renderizarBlocoCheckout();
                }
            });
        }

        adicionarItemCheckinManual(nome, categoria, status, obs) {
            if (!nome) return;
            this.state.checkin.itens.push({
                id: 'item_' + Date.now(),
                nome: nome,
                categoria: categoria || 'Geral',
                status: status || 'conforme',
                obs: obs || '',
                aprovadoReparo: (status === 'avaria'),
                medias: []
            });
            this.salvarEstado();
            this.renderizarBlocoCheckin();
        }

        adicionarPeca(codigo, descricao, qtd, unit) {
            if (!descricao) return;
            this.state.osInterna.pecas.push({
                codigo: codigo || 'PEC-' + Math.floor(Math.random()*900 + 100),
                descricao: descricao,
                qtd: parseFloat(qtd) || 1,
                unit: parseFloat(unit) || 0.0
            });
            this.salvarEstado();
            this.renderizarBlocoOSInterna();
            this.renderizarBlocoOrcamento();
        }

        removerPeca(idx) {
            this.state.osInterna.pecas.splice(idx, 1);
            this.salvarEstado();
            this.renderizarBlocoOSInterna();
            this.renderizarBlocoOrcamento();
        }

        adicionarServico(servico, mecanico, horas, valorHora) {
            if (!servico) return;
            this.state.osInterna.servicos.push({
                servico: servico,
                mecanico: mecanico || this.state.osInterna.mecanicoLider,
                horas: parseFloat(horas) || 1,
                valorHora: parseFloat(valorHora) || 150.0
            });
            this.salvarEstado();
            this.renderizarBlocoOSInterna();
            this.renderizarBlocoOrcamento();
        }

        removerServico(idx) {
            this.state.osInterna.servicos.splice(idx, 1);
            this.salvarEstado();
            this.renderizarBlocoOSInterna();
            this.renderizarBlocoOrcamento();
        }
    }

    // Instancia singleton e anexa ao escopo global
    window.workflow = new WorkflowManager();

    // Inicialização ao carregar DOM
    document.addEventListener('DOMContentLoaded', () => {
        window.workflow.renderizarTudo();
        window.workflow.inicializarCanvasAssinatura('canvasAssinaturaCheckin');
        window.workflow.inicializarCanvasAssinatura('canvasAssinaturaOSInterna');
        window.workflow.inicializarCanvasAssinatura('canvasAssinaturaCheckout');
    });

})(window);
