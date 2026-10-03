#!/usr/bin/env python3
"""
Servidor HTTP com API de persistencia completa para Analise O.E
Persiste: criticas (OS), equipamentos, clientes, programacoes
Dados salvos em: data/db.json
"""
import http.server
import json
import os
import socket
import urllib.parse
import time
import re
import base64
import sys
from pathlib import Path

# Proteção para execução em segundo plano via pythonw.exe (onde stdout/stderr são None)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

BASE_DIR = Path(__file__).parent / "public"
DATA_FILE = Path(__file__).parent / "data" / "db.json"
DATA_FILE.parent.mkdir(exist_ok=True)
TEMPLATES_ORCAMENTO_DIR = Path(__file__).parent / "templates_orcamento"
PRESTADORES_FILE = TEMPLATES_ORCAMENTO_DIR / "prestadores.json"

def ler_catalogo_prestadores():
    if PRESTADORES_FILE.exists():
        try:
            with open(PRESTADORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def salvar_catalogo_prestadores(lista):
    TEMPLATES_ORCAMENTO_DIR.mkdir(parents=True, exist_ok=True)
    with open(PRESTADORES_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

PORT = int(os.environ.get("PORT", 8000))

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def load_db():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"criticas": [], "equipamentos": [], "clientes": [], "programacoes": []}

def save_db(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = http.server.SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map.update({
        ".apk": "application/vnd.android.package-archive",
        ".webmanifest": "application/manifest+json",
        ".json": "application/json",
        ".js": "application/javascript",
        ".ico": "image/x-icon"
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        return None

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/orcamento/modelos-prestadores":
            self.send_json(ler_catalogo_prestadores())
            return
        if path == "/api/empresa/config":
            try:
                from scripts.gerenciador_orcamento import obter_config_empresa
                self.send_json(obter_config_empresa())
            except Exception as e:
                self.send_json({"error": str(e), "ok": False}, 500)
            return
        if path in ("/api/orcamento/pendentes", "/api/orcamento/todas"):
            todas_param = (path == "/api/orcamento/todas") or (parsed.query and "todas=1" in parsed.query)
            try:
                from scripts.gerenciador_orcamento import listar_os_para_orcamento
                self.send_json(listar_os_para_orcamento(incluir_todas=todas_param))
            except Exception as e:
                self.send_json({"error": str(e), "ok": False}, 500)
            return
        if path.startswith("/api/orcamento/buscar"):
            num_os = path.replace("/api/orcamento/buscar/", "").strip() if path.startswith("/api/orcamento/buscar/") else ""
            if not num_os:
                qs = urllib.parse.parse_qs(parsed.query)
                num_os = qs.get("os", [""])[0]
            try:
                from scripts.gerenciador_orcamento import buscar_dados_os
                res = buscar_dados_os(num_os)
                self.send_json(res)
            except Exception as e:
                self.send_json({"error": str(e), "encontrado": False}, 500)
            return
        if path == "/api/orcamento/template-status":
            try:
                from scripts.gerenciador_orcamento import obter_template_ativo
                self.send_json(obter_template_ativo())
            except Exception as e:
                self.send_json({"ativo": False, "error": str(e)}, 500)
            return
        if path == "/api/data":
            self.send_json(load_db()["criticas"]); return
        if path == "/api/all":
            self.send_json(load_db()); return
        if path == "/api/equipamentos":
            self.send_json(load_db()["equipamentos"]); return
        if path == "/api/clientes":
            self.send_json(load_db()["clientes"]); return
        if path == "/api/programacoes":
            self.send_json(load_db()["programacoes"]); return
        if path == "/api/ip":
            self.send_json({"ip": get_local_ip(), "port": PORT}); return

        if path == "/api/whatsapp/config":
            try:
                from scripts.whatsapp_listener import carregar_configuracao
                self.send_json(carregar_configuracao())
            except Exception as e:
                self.send_json({"error": str(e), "ok": False}, 500)
            return

        if path == "/api/whatsapp/inbox":
            try:
                from scripts.whatsapp_listener import carregar_inbox
                qs = urllib.parse.parse_qs(parsed.query)
                st = qs.get("status", [None])[0]
                self.send_json(carregar_inbox(st))
            except Exception as e:
                self.send_json({"error": str(e), "ok": False}, 500)
            return

        if path == "/api/whatsapp/ultima-os":
            try:
                from scripts.whatsapp_listener import obter_ultima_os_whatsapp
                self.send_json(obter_ultima_os_whatsapp())
            except Exception as e:
                self.send_json({"error": str(e), "ok": False}, 500)
            return

        if path == "/api/tutoriais/publicados":
            try:
                import scripts.gerenciador_tutoriais as gt
                self.send_json(gt.obter_tutoriais_publicos())
            except Exception as e:
                self.send_json({"error": str(e), "ok": False}, 500)
            return

        if path == "/api/tutoriais/config-estudio":
            try:
                import scripts.gerenciador_tutoriais as gt
                self.send_json({
                    "tutoriais": gt.carregar_tutoriais_config(),
                    "perfil_voz": gt.carregar_perfil_voz(),
                    "vozes_disponiveis": [
                        {"id": "antonio", "nome": "Antônio (IA Masculina Corporativa)", "tipo": "neural"},
                        {"id": "francisca", "nome": "Francisca (IA Feminina Corporativa)", "tipo": "neural"},
                        {"id": "voz_gestor", "nome": "Voz do Gestor (Clonada/Calibrada)", "tipo": "clonada"}
                    ]
                })
            except Exception as e:
                self.send_json({"error": str(e), "ok": False}, 500)
            return

        if path == "/api/tutoriais/audios":
            audios_dir = Path(__file__).parent / "public" / "videos" / "tutoriais"
            arquivos = []
            if audios_dir.exists():
                for f in audios_dir.glob("user_audio_tema_*.*"):
                    arquivos.append({"arquivo": f.name, "tema": f.stem, "tamanho": f.stat().st_size})
            self.send_json({"ok": True, "audios": arquivos})
            return

        super().do_GET()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        body = self.read_body()
        db = load_db()

        if path == "/api/whatsapp/config":
            try:
                from scripts.whatsapp_listener import salvar_configuracao
                dados = body if isinstance(body, dict) else {}
                ok = salvar_configuracao(dados)
                self.send_json({"ok": ok})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path in ("/api/os/whatsapp/webhook", "/api/os/whatsapp/simular"):
            try:
                from scripts.whatsapp_listener import processar_mensagem_whatsapp
                dados = body if isinstance(body, dict) else {}
                res = processar_mensagem_whatsapp(dados)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/whatsapp/inbox/marcar-importada":
            try:
                from scripts.whatsapp_listener import atualizar_status_inbox
                dados = body if isinstance(body, dict) else {}
                id_item = dados.get("id") or dados.get("numero_os")
                ok = atualizar_status_inbox(id_item, "importada")
                self.send_json({"ok": ok})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/whatsapp/inbox/descartar":
            try:
                from scripts.whatsapp_listener import atualizar_status_inbox
                dados = body if isinstance(body, dict) else {}
                id_item = dados.get("id") or dados.get("numero_os")
                ok = atualizar_status_inbox(id_item, "descartada")
                self.send_json({"ok": ok})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/whatsapp/inbox/restaurar":
            try:
                from scripts.whatsapp_listener import atualizar_status_inbox
                dados = body if isinstance(body, dict) else {}
                id_item = dados.get("id") or dados.get("numero_os")
                ok = atualizar_status_inbox(id_item, "pendente")
                self.send_json({"ok": ok})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/os/despachar":
            try:
                from scripts.whatsapp_listener import gerar_texto_despacho_os
                dados = body if isinstance(body, dict) else {}
                dados_os = dados.get("dados_os") or dados.get("os") or dados
                colab = dados.get("colaborador") or {}
                res = gerar_texto_despacho_os(dados_os, colab)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/os/notificar-cliente":
            try:
                from scripts.whatsapp_listener import gerar_texto_conclusao_cliente
                dados = body if isinstance(body, dict) else {}
                dados_os = dados.get("dados_os") or dados.get("os") or dados
                cliente = dados.get("cliente") or {}
                res = gerar_texto_conclusao_cliente(dados_os, cliente)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/os/retorno/aceitar":
            try:
                from scripts.whatsapp_listener import aceitar_retorno_os
                dados = body if isinstance(body, dict) else {}
                num_os = dados.get("numero_os") or dados.get("numeroOS") or dados.get("id")
                id_ret = dados.get("id_retorno")
                ajuste = dados.get("dados_ajuste") or {}
                res = aceitar_retorno_os(num_os, id_ret, ajuste)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/os/retorno/recusar":
            try:
                from scripts.whatsapp_listener import recusar_retorno_os
                dados = body if isinstance(body, dict) else {}
                num_os = dados.get("numero_os") or dados.get("numeroOS") or dados.get("id")
                id_ret = dados.get("id_retorno")
                just = dados.get("justificativa", "")
                res = recusar_retorno_os(num_os, id_ret, just)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return


        if path == "/api/empresa/config":
            try:
                from scripts.gerenciador_orcamento import salvar_config_empresa
                res = salvar_config_empresa(body if isinstance(body, dict) else {})
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/status":
            try:
                from scripts.gerenciador_orcamento import atualizar_status_os
                dados = body if isinstance(body, dict) else {}
                num_os = dados.get("numero_os")
                novo_st = dados.get("status")
                res = atualizar_status_os(num_os, novo_st)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/cancelar":
            try:
                from scripts.gerenciador_orcamento import cancelar_os_registro
                dados = body if isinstance(body, dict) else {}
                num_os = dados.get("numero_os")
                motivo = dados.get("motivo", "Cancelada na Central de Orçamentos")
                res = cancelar_os_registro(num_os, motivo)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/excluir":
            try:
                from scripts.gerenciador_orcamento import excluir_os_registro
                dados = body if isinstance(body, dict) else {}
                num_os = dados.get("numero_os")
                res = excluir_os_registro(num_os)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/faturar-lote":
            try:
                from scripts.gerenciador_orcamento import faturar_lote_os_registro
                dados = body if isinstance(body, dict) else {}
                nums = dados.get("numeros_os", [])
                res = faturar_lote_os_registro(nums)
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/dev/auth":
            try:
                import scripts.gerenciador_tutoriais as gt
                dados = body if isinstance(body, dict) else {}
                pin_informado = str(dados.get("pin", "")).strip()
                pin_correto = gt.obter_pin_dev()
                if pin_informado == pin_correto:
                    self.send_json({"success": True, "token": "dev_session_authorized", "mensagem": "Acesso concedido ao Estúdio do Desenvolvedor."})
                else:
                    self.send_json({"success": False, "mensagem": "PIN de desenvolvedor incorreto."}, 401)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
            return

        if path == "/api/dev/alterar-pin":
            try:
                import scripts.gerenciador_tutoriais as gt
                dados = body if isinstance(body, dict) else {}
                pin_atual = str(dados.get("pin_atual", "")).strip()
                novo_pin = str(dados.get("novo_pin", "")).strip()
                if pin_atual != gt.obter_pin_dev():
                    self.send_json({"success": False, "mensagem": "PIN atual incorreto."}, 401)
                    return
                if len(novo_pin) < 4:
                    self.send_json({"success": False, "mensagem": "O novo PIN deve ter pelo menos 4 dígitos."}, 400)
                    return
                gt.definir_pin_dev(novo_pin)
                self.send_json({"success": True, "mensagem": "PIN de desenvolvedor alterado com sucesso!"})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
            return

        if path == "/api/tutoriais/calibrar-voz":
            try:
                import scripts.gerenciador_tutoriais as gt
                dados = body if isinstance(body, dict) else {}
                audio_b64 = dados.get("audio_base64", "")
                ext = dados.get("extensao", "webm")
                if not audio_b64:
                    self.send_json({"success": False, "mensagem": "Nenhum áudio de amostra enviado."}, 400)
                    return
                if "," in audio_b64:
                    audio_b64 = audio_b64.split(",", 1)[1]
                audio_bytes = base64.b64decode(audio_b64)
                
                amostra_nome = f"amostra_voz_{int(time.time())}.{ext}"
                amostra_path = Path(__file__).parent / "data" / "amostras_voz" / amostra_nome
                amostra_path.parent.mkdir(parents=True, exist_ok=True)
                with open(amostra_path, "wb") as f:
                    f.write(audio_bytes)
                
                perfil = gt.processar_calibracao_voz(str(amostra_path))
                self.send_json({"success": True, "mensagem": "Amostra analisada e voz do gestor calibrada com sucesso!", "perfil": perfil})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
            return

        if path == "/api/tutoriais/homologar-publicar":
            try:
                import scripts.gerenciador_tutoriais as gt
                dados = body if isinstance(body, dict) else {}
                tutorial_id = dados.get("tutorial_id", 0)
                voz_escolhida = dados.get("voz_escolhida", "antonio")
                res = gt.publicar_tutorial(tutorial_id, voz_escolhida)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
            return

        if path == "/api/tutoriais/salvar-audio":
            try:
                dados = body if isinstance(body, dict) else {}
                tema_id = dados.get("tema_id", 1)
                audio_b64 = dados.get("audio_base64", "")
                ext = dados.get("extensao", "webm")
                if not audio_b64:
                    self.send_json({"ok": False, "error": "Nenhum áudio enviado"}, 400)
                    return
                if "," in audio_b64:
                    audio_b64 = audio_b64.split(",", 1)[1]
                audio_bytes = base64.b64decode(audio_b64)
                nome_arq = f"user_audio_tema_{tema_id}.{ext}"
                dest_path = Path(__file__).parent / "public" / "videos" / "tutoriais" / nome_arq
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, "wb") as f:
                    f.write(audio_bytes)
                backup_path = Path(__file__).parent / "data" / "audios_tutoriais" / nome_arq
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                with open(backup_path, "wb") as f:
                    f.write(audio_bytes)
                url_audio = f"/videos/tutoriais/{nome_arq}?t={int(time.time())}"
                self.send_json({"ok": True, "url": url_audio, "tema_id": tema_id, "arquivo": nome_arq})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/pdf":
            try:
                import importlib
                import scripts.gerenciador_orcamento
                importlib.reload(scripts.gerenciador_orcamento)
                from scripts.gerenciador_orcamento import gerar_pdf
                dados = body if isinstance(body, dict) else {}
                caminho_logo = dados.pop("caminho_logo", None)
                logo_b64 = dados.pop("logo_base64", None)
                if logo_b64 and "," in str(logo_b64):
                    try:
                        logo_bytes = base64.b64decode(logo_b64.split(",", 1)[1])
                        temp_logo = BASE_DIR / "uploads" / "temp_logo.png"
                        temp_logo.parent.mkdir(exist_ok=True)
                        with open(temp_logo, "wb") as f:
                            f.write(logo_bytes)
                        caminho_logo = str(temp_logo)
                    except:
                        pass
                num_os = dados.get("numero_os") or int(time.time())
                pdf_filename = f"Orcamento_{num_os}.pdf"
                pdf_path = BASE_DIR / "pdf" / pdf_filename
                pdf_path.parent.mkdir(exist_ok=True)
                gerar_pdf(dados, caminho_logo=caminho_logo, output_path=str(pdf_path))
                local_ip = get_local_ip()
                self.send_json({
                    "ok": True,
                    "filename": pdf_filename,
                    "url": f"/pdf/{pdf_filename}",
                    "full_url": f"http://{local_ip}:{PORT}/pdf/{pdf_filename}"
                })
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/excel":
            try:
                import importlib
                import scripts.gerenciador_orcamento
                importlib.reload(scripts.gerenciador_orcamento)
                from scripts.gerenciador_orcamento import gerar_excel
                dados = body if isinstance(body, dict) else {}
                num_os = dados.get("numero_os") or int(time.time())
                excel_filename = f"Orcamento_{num_os}.xlsx"
                excel_path = BASE_DIR / "pdf" / excel_filename
                excel_path.parent.mkdir(exist_ok=True)
                gerar_excel(dados, output_path=str(excel_path))
                local_ip = get_local_ip()
                self.send_json({
                    "ok": True,
                    "filename": excel_filename,
                    "url": f"/pdf/{excel_filename}",
                    "full_url": f"http://{local_ip}:{PORT}/pdf/{excel_filename}"
                })
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/word":
            try:
                import importlib
                import scripts.gerenciador_orcamento
                importlib.reload(scripts.gerenciador_orcamento)
                from scripts.gerenciador_orcamento import gerar_word
                dados = body if isinstance(body, dict) else {}
                num_os = dados.get("numero_os") or int(time.time())
                word_filename = f"Orcamento_{num_os}.docx"
                word_path = BASE_DIR / "pdf" / word_filename
                word_path.parent.mkdir(exist_ok=True)
                gerar_word(dados, output_path=str(word_path))
                local_ip = get_local_ip()
                self.send_json({
                    "ok": True,
                    "filename": word_filename,
                    "url": f"/pdf/{word_filename}",
                    "full_url": f"http://{local_ip}:{PORT}/pdf/{word_filename}"
                })
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/upload-template":
            try:
                import importlib
                import scripts.gerenciador_orcamento
                importlib.reload(scripts.gerenciador_orcamento)
                from scripts.gerenciador_orcamento import salvar_template_usuario
                dados = body if isinstance(body, dict) else {}
                filename = dados.get("filename", "modelo_usuario.xlsx")
                content_base64 = dados.get("content_base64") or dados.get("data", "")
                res = salvar_template_usuario(filename, content_base64)

                try:
                    import re
                    clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(filename).stem).lower()
                    cat = ler_catalogo_prestadores()
                    ext = Path(filename).suffix.lower()
                    target_prest = TEMPLATES_ORCAMENTO_DIR / f"{clean_id}{ext}"
                    raw_b64 = str(content_base64 or "")
                    if "," in raw_b64:
                        raw_b64 = raw_b64.split(",", 1)[1]
                    with open(target_prest, "wb") as pf:
                        pf.write(base64.b64decode(raw_b64))

                    existente = next((p for p in cat if p.get("id") == clean_id), None)
                    if not existente:
                        cat.append({
                            "id": clean_id,
                            "nome": Path(filename).stem.replace("_", " ").title(),
                            "arquivo": f"{clean_id}{ext}",
                            "caminho": f"templates_orcamento/{clean_id}{ext}",
                            "tipo": ext.replace(".", ""),
                            "padrao": False,
                            "data_cadastro": time.strftime("%d/%m/%Y %H:%M:%S")
                        })
                        salvar_catalogo_prestadores(cat)
                except Exception as ce:
                    print(f"[Catalogo] Erro ao sincronizar com catalogo: {ce}")

                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/orcamento/selecionar-prestador":
            dados = body if isinstance(body, dict) else {}
            id_prestador = str(dados.get("id", "")).strip()
            if not id_prestador or id_prestador.lower() in ["padrao", "default", "sistema"]:
                try:
                    from scripts.gerenciador_orcamento import remover_template_usuario
                    remover_template_usuario()
                    self.send_json({"ok": True, "ativo": False, "mensagem": "Voltou ao modelo padrão"})
                except Exception as e:
                    self.send_json({"ok": False, "error": str(e)}, 500)
                return

            catalogo = ler_catalogo_prestadores()
            selecionado = next((p for p in catalogo if str(p.get("id", "")).lower() == id_prestador.lower()), None)
            if not selecionado:
                self.send_json({"ok": False, "mensagem": "Modelo não encontrado"}, 404)
                return

            nome_arq = selecionado.get("arquivo") or Path(selecionado.get("caminho", "")).name
            origem = TEMPLATES_ORCAMENTO_DIR / nome_arq
            if origem.exists():
                import shutil
                ext = origem.suffix
                destino = Path(__file__).parent / "templates" / f"modelo_usuario{ext}"
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origem, destino)
                info_path = destino.parent / "template_info.json"
                with open(info_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "ativo": True,
                        "tipo": ext.replace(".", ""),
                        "nome_original": selecionado.get("nome", nome_arq),
                        "arquivo_salvo": f"modelo_usuario{ext}",
                        "tamanho_bytes": destino.stat().st_size,
                        "data_upload": time.strftime("%d/%m/%Y %H:%M:%S")
                    }, f, ensure_ascii=False, indent=2)
                self.send_json({"ok": True, "ativo": True, "nome": selecionado.get("nome"), "mensagem": "Modelo ativado com sucesso"})
            else:
                self.send_json({"ok": False, "mensagem": "Arquivo físico não encontrado em templates_orcamento"}, 404)
            return

        if path == "/api/orcamento/remover-template":
            try:
                from scripts.gerenciador_orcamento import remover_template_usuario
                res = remover_template_usuario()
                self.send_json(res)
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/salvar_pdf":
            if isinstance(body, dict):
                filename = body.get("filename", f"OS_{int(time.time())}.pdf")
                safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
                if not safe_name.lower().endswith(".pdf"):
                    safe_name += ".pdf"
                data = body.get("data", "")
                if "," in data:
                    data = data.split(",", 1)[1]
                pdf_bytes = base64.b64decode(data)
                pdf_dir = BASE_DIR / "pdf"
                pdf_dir.mkdir(exist_ok=True)
                pdf_path = pdf_dir / safe_name
                with open(pdf_path, "wb") as f:
                    f.write(pdf_bytes)
                local_ip = get_local_ip()
                self.send_json({
                    "ok": True,
                    "filename": safe_name,
                    "url": f"/pdf/{safe_name}",
                    "full_url": f"http://{local_ip}:{PORT}/pdf/{safe_name}"
                })
                return
        if path == "/api/data":
            if isinstance(body, list):
                db["criticas"] = body; save_db(db); self.send_json({"ok": True})
            return
        if path == "/api/all":
            if isinstance(body, dict):
                for k in ["criticas","equipamentos","clientes","programacoes"]:
                    if k in body: db[k] = body[k]
                save_db(db); self.send_json({"ok": True})
            return
        if path == "/api/equipamentos":
            if isinstance(body, list):
                db["equipamentos"] = body; save_db(db); self.send_json({"ok": True})
            return
        if path == "/api/clientes":
            if isinstance(body, list):
                db["clientes"] = body; save_db(db); self.send_json({"ok": True})
            return
        if path == "/api/programacoes":
            if isinstance(body, list):
                db["programacoes"] = body; save_db(db); self.send_json({"ok": True})
            return
        self.send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/orcamento/modelo-prestador/"):
            id_prestador = urllib.parse.unquote(path.replace("/api/orcamento/modelo-prestador/", "")).strip()
            if not id_prestador:
                self.send_json({"success": False, "mensagem": "ID do modelo não informado"}, 400)
                return

            id_norm = id_prestador.lower()
            # Blindagem de Código: Protege o modelo nativo/padrão do sistema contra remoção
            if id_norm in ["padrao", "default", "sistema"]:
                self.send_json({"success": False, "mensagem": "O modelo padrão do sistema não pode ser excluído."}, 403)
                return

            # 1. Leia templates_orcamento/prestadores.json
            catalogo = ler_catalogo_prestadores()

            # 2. Localize o item correspondente pelo id
            idx = -1
            for i, p in enumerate(catalogo):
                if str(p.get("id", "")).strip().lower() == id_norm:
                    idx = i
                    break

            if idx == -1:
                self.send_json({"success": False, "mensagem": f"Modelo '{id_prestador}' não encontrado no catálogo."}, 404)
                return

            item = catalogo[idx]
            if item.get("padrao") is True or "padrão" in str(item.get("nome", "")).lower():
                self.send_json({"success": False, "mensagem": "Este modelo é padrão do sistema e não pode ser excluído."}, 403)
                return

            # 3. Remova fisicamente o arquivo do disco usando remoção segura
            nome_arq = item.get("arquivo") or item.get("caminho") or ""
            if nome_arq:
                nome_base = Path(nome_arq).name
                caminho_abs = (TEMPLATES_ORCAMENTO_DIR / nome_base).resolve()

                # Blindagem: Não permita a exclusão de arquivos fora da pasta templates_orcamento/
                try:
                    caminho_abs.relative_to(TEMPLATES_ORCAMENTO_DIR.resolve())
                except ValueError:
                    self.send_json({"success": False, "mensagem": "Acesso não autorizado ao caminho do arquivo."}, 403)
                    return

                try:
                    if caminho_abs.exists() and caminho_abs.is_file():
                        caminho_abs.unlink()
                        print(f"[Exclusao] Arquivo físico removido com sucesso: {caminho_abs}")
                except Exception as ex:
                    self.send_json({"success": False, "mensagem": f"Erro ao remover arquivo físico: {str(ex)}"}, 500)
                    return

            # Desativa template ativo se o modelo excluído for o que estava ativo
            try:
                from scripts.gerenciador_orcamento import obter_template_ativo, remover_template_usuario
                st = obter_template_ativo()
                if st.get("ativo"):
                    nome_ativo = str(st.get("nome_arquivo", "")).lower()
                    if (nome_arq and Path(nome_arq).name.lower() in nome_ativo) or id_norm in nome_ativo:
                        remover_template_usuario()
            except Exception:
                pass

            # 4. Remova o prestador do array no JSON e salve o arquivo prestadores.json atualizado
            catalogo.pop(idx)
            salvar_catalogo_prestadores(catalogo)

            # 5. Retorne { success: true, mensagem: "Modelo removido com sucesso" }
            self.send_json({"success": True, "mensagem": "Modelo removido com sucesso"}, 200)
            return

        self.send_json({"error": "not found"}, 404)

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"[OE] Painel Desktop : http://localhost:{PORT}/")
    print(f"[OE] Rede local     : http://{ip}:{PORT}/")
    print(f"[OE] Dados salvos em: {DATA_FILE}")
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OE] Servidor encerrado.")
