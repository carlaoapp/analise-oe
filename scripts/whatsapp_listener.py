#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Receptor e processador de mensagens e mídias do WhatsApp.
Responsável por:
1. Validar remetentes e grupos autorizados (Filtro de Segurança).
2. Extrair dados da O.S. via whatsapp_parser.py.
3. Salvar fisicamente fotos e vídeos recebidos em public/uploads/os_{numero_os}/.
4. Persistir a O.S. em data/db.json com status 'Pendente Orçamento'.
5. Manter cache rápido da última O.S. em data/whatsapp_ultima_os.json.
"""

import os
import sys
import json
import base64
import datetime
import re
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PUBLIC_DIR = BASE_DIR / "public"
UPLOADS_DIR = PUBLIC_DIR / "uploads"
CONFIG_FILE = DATA_DIR / "config_whatsapp.json"
ULTIMA_OS_FILE = DATA_DIR / "whatsapp_ultima_os.json"
DB_FILE = DATA_DIR / "db.json"

# Importa o parser
try:
    from scripts.whatsapp_parser import extrair_dados_whatsapp, eh_retorno_os, extrair_dados_retorno_colaborador
except ImportError:
    from whatsapp_parser import extrair_dados_whatsapp, eh_retorno_os, extrair_dados_retorno_colaborador


INBOX_FILE = DATA_DIR / "whatsapp_inbox.json"

def carregar_configuracao():
    """Carrega as regras de segurança e diretórios de data/config_whatsapp.json."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if "perfil_trabalho" not in cfg:
                    cfg["perfil_trabalho"] = "solo"
                return cfg
        except Exception:
            pass
    return {
        "perfil_trabalho": "solo",
        "modo_restrito": True,
        "exigir_os_ou_frota": True,
        "limite_video_mb": 50,
        "limite_foto_mb": 15,
        "download_midias_automatico": True,
        "diretorio_uploads": "public/uploads",
        "remetentes_autorizados": []
    }

def salvar_configuracao(nova_config: dict) -> bool:
    """Salva as configurações de segurança, perfil de trabalho e remetentes (com merge seguro)."""
    try:
        atual = carregar_configuracao()
        atual.update(nova_config)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(atual, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Erro] Falha ao salvar config_whatsapp.json: {e}", file=sys.stderr)
        return False

def normalizar_numero(num: str) -> str:
    """Extrai somente os dígitos de um número ou retorna ID limpo."""
    if not num:
        return ""
    limpo = re.sub(r'\D', '', str(num))
    return limpo if limpo else str(num).strip().lower()

def verificar_remetente_autorizado(remetente: str = "", grupo_id: str = "") -> tuple:
    """
    Verifica se o remetente ou grupo possui permissão de envio.
    Retorna (autorizado: bool, dados_contato: dict).
    """
    cfg = carregar_configuracao()
    if not cfg.get("modo_restrito", True):
        return True, {"nome": remetente or "Remetente Livre", "aceita_fotos": True, "aceita_videos": True}

    rems = cfg.get("remetentes_autorizados", [])
    rem_norm = normalizar_numero(remetente)
    grp_norm = str(grupo_id or "").strip().lower()

    for item in rems:
        if not item.get("ativo", True):
            continue
        tel_item = normalizar_numero(item.get("telefone") or item.get("identificador") or "")
        tipo = item.get("tipo", "contato")

        # Verifica correspondência de telefone do contato/mecânico/cliente
        if tipo != "grupo" and rem_norm and (rem_norm == tel_item or rem_norm.endswith(tel_item) or tel_item.endswith(rem_norm)):
            return True, item
        
        # Verifica correspondência de grupo
        if tipo == "grupo" and grp_norm and grp_norm == tel_item:
            return True, item

        # Verifica nome como fallback se remetente vier como nome
        nome_item = str(item.get("nome") or "").strip().lower()
        if nome_item and nome_item in str(remetente).strip().lower():
            return True, item

    return False, None

def salvar_midia_os(numero_os: str, nome_arquivo: str, conteudo_base64_ou_bytes, mime_type: str = "") -> str:
    """
    Salva fisicamente foto ou vídeo em public/uploads/os_{numero_os}/
    Retorna o caminho relativo web (ex: /uploads/os_141668/vid_20260911_090300.mp4).
    """
    if not numero_os:
        numero_os = "avulso_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    pasta_os = UPLOADS_DIR / f"os_{numero_os}"
    pasta_os.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_limpo = Path(nome_arquivo or "midia.mp4").name
    ext = Path(nome_limpo).suffix.lower()
    
    if not ext:
        if "video" in str(mime_type).lower():
            ext = ".mp4"
        else:
            ext = ".jpg"

    nome_final = f"{ts}_{Path(nome_limpo).stem}{ext}"
    destino = pasta_os / nome_final

    # Se for string Base64
    if isinstance(conteudo_base64_ou_bytes, str):
        raw_b64 = conteudo_base64_ou_bytes
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        file_bytes = base64.b64decode(raw_b64)
    else:
        file_bytes = conteudo_base64_ou_bytes

    with open(destino, "wb") as f:
        f.write(file_bytes)

    return f"/uploads/os_{numero_os}/{nome_final}"

def carregar_inbox(status_filtro: str = None) -> list:
    """Carrega as mensagens arquivadas na Caixa de Entrada."""
    if INBOX_FILE.exists():
        try:
            with open(INBOX_FILE, "r", encoding="utf-8") as f:
                itens = json.load(f)
                if status_filtro:
                    return [i for i in itens if i.get("status") == status_filtro]
                return itens
        except Exception:
            pass
    return []

import urllib.parse

def registrar_no_inbox(dados_os: dict, midias: list, remetente_info: dict, texto_original: str, tipo_registro: str = "nova_os", status_inicial: str = "pendente") -> dict:
    """Registra o chamado recebido na Caixa de Entrada WhatsApp."""
    INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
    inbox = carregar_inbox()

    num_os = dados_os.get("numero_os") or f"TEMP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    id_inbox = f"inbox_{num_os}_{datetime.datetime.now().strftime('%M%S')}"
    agora_iso = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    registro = {
        "id": id_inbox,
        "tipo_registro": tipo_registro,
        "timestamp": agora_iso,
        "remetente_nome": remetente_info.get("nome", "Desconhecido"),
        "remetente_numero": remetente_info.get("telefone", ""),
        "status": status_inicial,
        "mensagem_original": texto_original,
        "dados_extraidos": dados_os,
        "midias": midias
    }

    # Insere no topo da caixa de entrada
    inbox.insert(0, registro)

    try:
        with open(INBOX_FILE, "w", encoding="utf-8") as f:
            json.dump(inbox, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Erro] Falha ao salvar em whatsapp_inbox.json: {e}", file=sys.stderr)

    return registro

def atualizar_status_inbox(id_ou_num_os: str, novo_status: str) -> bool:
    """Atualiza o status de um item do Inbox (ex: 'importada', 'descartada', 'aceito', 'recusado')."""
    if not INBOX_FILE.exists():
        return False
    try:
        with open(INBOX_FILE, "r", encoding="utf-8") as f:
            inbox = json.load(f)
        
        alterou = False
        for item in inbox:
            num = item.get("dados_extraidos", {}).get("numero_os")
            if item.get("id") == id_ou_num_os or str(num) == str(id_ou_num_os):
                item["status"] = novo_status
                item["data_atualizacao"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                alterou = True

        if alterou:
            with open(INBOX_FILE, "w", encoding="utf-8") as f:
                json.dump(inbox, f, ensure_ascii=False, indent=2)
        return alterou
    except Exception as e:
        print(f"[Erro] Falha ao atualizar inbox: {e}", file=sys.stderr)
        return False

def processar_mensagem_whatsapp(payload: dict) -> dict:
    """
    Ponto de entrada principal para mensagens recebidas via webhook/API.
    Aplica:
    1. Whitelist de remetentes autorizados.
    2. Identificação de retorno de O.S. de colaborador vs. Abertura de nova O.S.
    3. Respeito às regras de mídias do contato.
    4. Download físico e persistência em db.json e whatsapp_inbox.json.
    """
    texto = payload.get("text") or payload.get("texto") or ""
    remetente = payload.get("sender") or payload.get("remetente") or ""
    grupo_id = payload.get("group_id") or payload.get("grupo") or ""

    # 1. Filtro de Segurança / Whitelist
    autorizado, contato_info = verificar_remetente_autorizado(remetente, grupo_id)
    if not autorizado:
        return {
            "ok": False,
            "erro": f"Remetente '{remetente}' não está na lista de contatos autorizados. Mensagem rejeitada para manter a organização.",
            "bloqueado": True
        }

    info_rem = contato_info if contato_info else {"nome": remetente, "telefone": remetente}
    aceita_fotos = contato_info.get("aceita_fotos", True) if contato_info else True
    aceita_videos = contato_info.get("aceita_videos", True) if contato_info else True

    # =========================================================================
    # CENÁRIO A: É um RETORNO de Ordem de Serviço enviado pelo Colaborador
    # =========================================================================
    if eh_retorno_os(texto):
        dados_retorno = extrair_dados_retorno_colaborador(texto)
        num_os = dados_retorno.get("numero_os") or payload.get("numero_os") or ""
        
        # Salvamento físico das fotos e vídeos do retorno
        midias_salvas = []
        lista_midias = payload.get("media") or payload.get("midias") or []
        if isinstance(lista_midias, dict):
            lista_midias = [lista_midias]

        for m in lista_midias:
            nome_arq = m.get("filename") or m.get("name") or "midia.mp4"
            conteudo = m.get("content_base64") or m.get("base64") or m.get("data")
            mime = str(m.get("mimetype") or m.get("type") or "").lower()
            eh_video = "video" in mime or nome_arq.lower().endswith(('.mp4', '.mov', '.3gp'))

            if eh_video and not aceita_videos: continue
            if not eh_video and not aceita_fotos: continue

            if conteudo:
                try:
                    url_rel = salvar_midia_os(num_os, nome_arq, conteudo, mime)
                    midias_salvas.append({
                        "tipo": "video" if eh_video else "foto",
                        "nome_arquivo": nome_arq,
                        "url": url_rel,
                        "type": mime or ("video/mp4" if eh_video else "image/jpeg"),
                        "data": url_rel,
                        "origem": "retorno_campo"
                    })
                except Exception as e:
                    print(f"[Erro] Falha ao salvar mídia do retorno: {e}", file=sys.stderr)
            elif m.get("url"):
                midias_salvas.append({
                    "tipo": "video" if eh_video else "foto",
                    "nome_arquivo": nome_arq,
                    "url": m.get("url"),
                    "type": mime or ("video/mp4" if eh_video else "image/jpeg"),
                    "data": m.get("url"),
                    "origem": "retorno_campo"
                })

        agora_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        id_retorno = f"ret_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        retorno_registro = {
            "id": id_retorno,
            "data_retorno": agora_iso,
            "colaborador_nome": info_rem.get("nome", remetente),
            "colaborador_numero": info_rem.get("telefone", remetente),
            "status_retorno": "aguardando_analise",
            "status_execucao": dados_retorno.get("status_execucao"),
            "status_rotulo": dados_retorno.get("status_rotulo"),
            "km_final": dados_retorno.get("km_final"),
            "horimetro": dados_retorno.get("horimetro"),
            "servicos_executados": dados_retorno.get("servicos_executados"),
            "pecas_utilizadas": dados_retorno.get("pecas_utilizadas"),
            "observacoes": dados_retorno.get("observacoes"),
            "texto_original": texto,
            "midias": midias_salvas
        }

        # Atualiza a O.S. correspondente em data/db.json
        os_encontrada = False
        if DB_FILE.exists():
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    db = json.load(f)
                
                for item_os in db.get("criticas", []):
                    num_cad = str(item_os.get("numeroOS") or item_os.get("id") or "").strip()
                    if num_cad and (num_cad == str(num_os).strip()):
                        os_encontrada = True
                        item_os.setdefault("retornos_campo", [])
                        item_os["retornos_campo"].insert(0, retorno_registro)
                        item_os["tem_retorno_pendente"] = True
                        item_os["status_retorno"] = "aguardando_analise"
                        item_os["ultimo_retorno"] = retorno_registro
                        
                        # Anexa também mídias à galeria da OS
                        if midias_salvas:
                            item_os.setdefault("medias", [])
                            for ms in midias_salvas:
                                if not any(x.get("url") == ms.get("url") for x in item_os["medias"]):
                                    item_os["medias"].append(ms)
                        break
                
                if not os_encontrada and num_os:
                    # Se não existia no banco, registra de forma preliminar
                    nova_os = {
                        "id": str(num_os),
                        "numeroOS": str(num_os),
                        "tipo": "os",
                        "data": agora_iso,
                        "dataOS": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "status": "Aguardando Análise",
                        "statusOS": "Aguardando Análise",
                        "origem": "whatsapp_retorno",
                        "tecnico": info_rem.get("nome", remetente),
                        "tem_retorno_pendente": True,
                        "status_retorno": "aguardando_analise",
                        "retornos_campo": [retorno_registro],
                        "ultimo_retorno": retorno_registro,
                        "medias": midias_salvas
                    }
                    db.setdefault("criticas", []).insert(0, nova_os)

                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(db, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"[Erro] Falha ao persistir retorno na OS: {e}", file=sys.stderr)

        # Registra no Inbox com tipo retorno_os
        item_inbox = registrar_no_inbox(
            dados_os={"numero_os": num_os, **dados_retorno},
            midias=midias_salvas,
            remetente_info=info_rem,
            texto_original=texto,
            tipo_registro="retorno_os",
            status_inicial="aguardando_analise"
        )

        return {
            "ok": True,
            "tipo": "retorno_os",
            "mensagem": f"Retorno da O.S. #{num_os or 's/n'} registrado com sucesso e aguardando análise do gestor!",
            "numero_os": num_os,
            "dados_retorno": dados_retorno,
            "retorno": retorno_registro,
            "inbox_id": item_inbox.get("id"),
            "midias": midias_salvas
        }

    # =========================================================================
    # CENÁRIO B: Abertura de NOVA Ordem de Serviço (ou Solicitação)
    # =========================================================================
    template_remetente = (contato_info or {}).get("template_mensagem", None)
    dados_extraidos = extrair_dados_whatsapp(texto, template_remetente=template_remetente)
    num_os = dados_extraidos.get("numero_os")
    frota = dados_extraidos.get("frota")

    # Validação de conteúdo mínimo (Anti-bagunça)
    cfg = carregar_configuracao()
    if cfg.get("exigir_os_ou_frota", True) and not num_os and not frota:
        return {
            "ok": False,
            "erro": "A mensagem recebida não contém identificação de Frota nem de O.S. Descartada para evitar poluição do sistema.",
            "ignorado": True
        }

    # Salvamento físico das mídias
    midias_salvas = []
    lista_midias = payload.get("media") or payload.get("midias") or []
    if isinstance(lista_midias, dict):
        lista_midias = [lista_midias]

    for m in lista_midias:
        nome_arq = m.get("filename") or m.get("name") or "midia.mp4"
        conteudo = m.get("content_base64") or m.get("base64") or m.get("data")
        mime = str(m.get("mimetype") or m.get("type") or "").lower()
        eh_video = "video" in mime or nome_arq.lower().endswith(('.mp4', '.mov', '.3gp'))

        if eh_video and not aceita_videos:
            continue
        if not eh_video and not aceita_fotos:
            continue

        if conteudo:
            try:
                url_rel = salvar_midia_os(num_os, nome_arq, conteudo, mime)
                midias_salvas.append({
                    "tipo": "video" if eh_video else "foto",
                    "nome_arquivo": nome_arq,
                    "url": url_rel,
                    "type": mime or ("video/mp4" if eh_video else "image/jpeg"),
                    "data": url_rel
                })
            except Exception as e:
                print(f"[Erro] Falha ao salvar mídia {nome_arq}: {e}", file=sys.stderr)
        elif m.get("url"):
            midias_salvas.append({
                "tipo": "video" if eh_video else "foto",
                "nome_arquivo": nome_arq,
                "url": m.get("url"),
                "type": mime or ("video/mp4" if eh_video else "image/jpeg"),
                "data": m.get("url")
            })

    # Registro na Caixa de Entrada (Inbox)
    item_inbox = registrar_no_inbox(dados_extraidos, midias_salvas, info_rem, texto, tipo_registro="nova_os", status_inicial="pendente")

    # Atualização em cache da última OS
    registro_cache = dict(dados_extraidos)
    registro_cache["medias"] = midias_salvas
    registro_cache["data_recebimento"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registro_cache["inbox_id"] = item_inbox.get("id")
    try:
        with open(ULTIMA_OS_FILE, "w", encoding="utf-8") as f:
            json.dump(registro_cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return {
        "ok": True,
        "tipo": "nova_os",
        "mensagem": f"O.S. #{num_os or 's/n'} recebida e catalogada com sucesso na Caixa de Entrada!",
        "inbox_id": item_inbox.get("id"),
        "numero_os": num_os,
        "dados": dados_extraidos,
        "medias": midias_salvas
    }


def aceitar_retorno_os(numero_os: str, id_retorno: str = None, dados_ajuste: dict = None) -> dict:
    """
    Gestor aceita o retorno do colaborador:
    1. Atualiza o status do retorno para 'aceito'.
    2. Consolida os dados na O.S. em db.json (statusOS = 'Finalizada', KM, horímetro, serviços, mídias).
    3. Atualiza o status no Inbox.
    """
    if not DB_FILE.exists():
        return {"ok": False, "erro": "Banco de dados db.json não encontrado"}

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)

        num_str = str(numero_os).strip()
        os_encontrada = None
        for item in db.get("criticas", []):
            if str(item.get("numeroOS") or item.get("id")).strip() == num_str:
                os_encontrada = item
                break

        if not os_encontrada:
            return {"ok": False, "erro": f"O.S. #{numero_os} não encontrada no banco."}

        # Localiza o retorno
        retornos = os_encontrada.get("retornos_campo", [])
        retorno = None
        if id_retorno:
            retorno = next((r for r in retornos if r.get("id") == id_retorno), None)
        if not retorno and retornos:
            retorno = retornos[0]

        if not retorno:
            return {"ok": False, "erro": "Nenhum retorno de colaborador encontrado para esta O.S."}

        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        retorno["status_retorno"] = "aceito"
        retorno["data_analise"] = agora

        # Consolida dados na O.S.
        ajuste = dados_ajuste or {}
        novo_status = ajuste.get("statusOS") or "Finalizada"
        os_encontrada["statusOS"] = novo_status
        os_encontrada["status"] = novo_status
        os_encontrada["tem_retorno_pendente"] = False
        os_encontrada["status_retorno"] = "aceito"
        os_encontrada["data_aprovacao_retorno"] = agora

        if retorno.get("km_final"):
            try:
                os_encontrada["kmFinal"] = float(str(retorno.get("km_final")).replace(",", "."))
                km_ini = float(os_encontrada.get("kmInicial") or 0)
                if km_ini > 0 and os_encontrada["kmFinal"] >= km_ini:
                    os_encontrada["kmTotal"] = round(os_encontrada["kmFinal"] - km_ini, 2)
            except:
                pass

        if retorno.get("horimetro"):
            os_encontrada["horimetro"] = retorno.get("horimetro")

        # Adiciona observações e serviços executados
        serv_exec = retorno.get("servicos_executados") or ""
        obs_ret = retorno.get("observacoes") or ""
        texto_adicional = []
        if serv_exec:
            texto_adicional.append(f"[Serviços Realizados]: {serv_exec}")
        if obs_ret:
            texto_adicional.append(f"[Obs Campo]: {obs_ret}")

        if texto_adicional:
            obs_atual = os_encontrada.get("observacoes") or ""
            bloco_retorno = "\n".join(texto_adicional)
            if bloco_retorno not in obs_atual:
                os_encontrada["observacoes"] = f"{obs_atual}\n\n{bloco_retorno}".strip()

        # Adiciona mídias à galeria
        os_encontrada.setdefault("medias", [])
        for m in retorno.get("midias", []):
            if not any(x.get("url") == m.get("url") for x in os_encontrada["medias"]):
                os_encontrada["medias"].append(m)

        os_encontrada["ultimo_retorno"] = retorno

        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

        # Atualiza inbox
        atualizar_status_inbox(num_str, "aceito")

        return {
            "ok": True,
            "mensagem": f"Retorno da O.S. #{num_str} aceito com sucesso! Dados e mídias consolidados na O.S.",
            "os": os_encontrada
        }

    except Exception as e:
        return {"ok": False, "erro": str(e)}


def recusar_retorno_os(numero_os: str, id_retorno: str = None, justificativa: str = "") -> dict:
    """
    Gestor recusa o retorno do colaborador:
    1. Marca retorno como 'recusado' com a justificativa.
    2. Mantém a O.S. aberta e gera mensagem para envio ao colaborador no WhatsApp.
    """
    if not DB_FILE.exists():
        return {"ok": False, "erro": "Banco de dados db.json não encontrado"}

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)

        num_str = str(numero_os).strip()
        os_encontrada = None
        for item in db.get("criticas", []):
            if str(item.get("numeroOS") or item.get("id")).strip() == num_str:
                os_encontrada = item
                break

        if not os_encontrada:
            return {"ok": False, "erro": f"O.S. #{numero_os} não encontrada no banco."}

        retornos = os_encontrada.get("retornos_campo", [])
        retorno = None
        if id_retorno:
            retorno = next((r for r in retornos if r.get("id") == id_retorno), None)
        if not retorno and retornos:
            retorno = retornos[0]

        if not retorno:
            return {"ok": False, "erro": "Nenhum retorno encontrado para recusar."}

        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        retorno["status_retorno"] = "recusado"
        retorno["justificativa_recusa"] = justificativa
        retorno["data_recusa"] = agora

        os_encontrada["tem_retorno_pendente"] = False
        os_encontrada["status_retorno"] = "recusado"
        os_encontrada["ultimo_retorno"] = retorno

        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

        atualizar_status_inbox(num_str, "recusado")

        colaborador_nome = retorno.get("colaborador_nome") or "Colaborador"
        colaborador_tel = retorno.get("colaborador_numero") or ""

        # Monta texto de cobrança para WhatsApp
        msg_cobranca = (
            f"⚠️ *SOLICITAÇÃO DE CORREÇÃO - O.S. #{num_str}*\n\n"
            f"Olá *{colaborador_nome}*,\n"
            f"O retorno enviado para a O.S. #{num_str} foi analisado e precisa de correções.\n\n"
            f"📌 *Motivo / Ajuste necessário:*\n_{justificativa or 'Informações incompletas ou pendência de fotos/vídeos'}_\n\n"
            f"Por favor, revise o serviço e reenvie a mensagem no padrão:\n"
            f"*RETORNO OS: {num_str}*\n"
            f"Status: Concluído\n"
            f"KM Final: ...\n"
            f"Serviços Executados: ...\n"
            f"📸 + Fotos/Vídeos atualizados."
        )

        tel_clean = normalizar_numero(colaborador_tel)
        link_wa = f"https://wa.me/{tel_clean}?text={urllib.parse.quote(msg_cobranca)}" if tel_clean else f"https://wa.me/?text={urllib.parse.quote(msg_cobranca)}"

        return {
            "ok": True,
            "mensagem": f"Retorno da O.S. #{num_str} marcado como recusado.",
            "justificativa": justificativa,
            "texto_whatsapp": msg_cobranca,
            "link_whatsapp": link_wa,
            "colaborador_nome": colaborador_nome,
            "colaborador_numero": colaborador_tel
        }

    except Exception as e:
        return {"ok": False, "erro": str(e)}


def gerar_texto_despacho_os(dados_os: dict, colaborador: dict = None) -> dict:
    """
    Gera texto padronizado com instruções para despachar a O.S. ao colaborador/mecânico.
    Estruturado em ordem lógica profissional, sem caracteres que corrompam no WhatsApp ou outros apps.
    """
    num_os = dados_os.get("numeroOS") or dados_os.get("numero_os") or dados_os.get("id") or "S/N"
    data_hora = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")

    colab_nome = (colaborador or {}).get("nome") or ""
    colab_funcao = (colaborador or {}).get("funcao") or (colaborador or {}).get("papel") or ""
    colab_ident = f"{colab_nome} ({colab_funcao})" if (colab_nome and colab_funcao and colab_funcao.lower() not in colab_nome.lower()) else (colab_nome or "Mecânico / Técnico Especialista")
    colab_tel = normalizar_numero((colaborador or {}).get("telefone") or (colaborador or {}).get("identificador") or "")

    frota = dados_os.get("frota") or "Não informado"
    veiculo = dados_os.get("veiculo") or dados_os.get("equipamento") or ""
    horimetro = dados_os.get("horimetro") or dados_os.get("km_inicial") or dados_os.get("horasMotor") or dados_os.get("km") or "Não informado"

    cliente = dados_os.get("cliente") or dados_os.get("solicitante") or "Não informado"
    fazenda = dados_os.get("localAtendimento") or dados_os.get("fazenda") or dados_os.get("local") or "Não informado"
    contato = dados_os.get("contato") or dados_os.get("telefone") or ""

    servicos = dados_os.get("observacoes") or dados_os.get("diagnostico") or dados_os.get("servico") or ""
    itens_serv = dados_os.get("servicosItens") or []
    if itens_serv:
        linhas_itens = []
        for s in itens_serv:
            desc = s.get("descricao") or s.get("servico") or ""
            if desc:
                linhas_itens.append(f"• {desc}")
        if linhas_itens:
            servicos = (servicos + "\n" + "\n".join(linhas_itens)).strip()
    if not servicos:
        servicos = "Conforme inspeção técnica no local."

    texto = (
        f"[ ORDEM DE SERVIÇO #{num_os} ]\n"
        f"• Data de Envio: {data_hora}\n"
        f"• Status: Despachada para Atendimento em Campo\n"
        f"----------------------------------------\n"
        f"MECÂNICO RESPONSÁVEL:\n"
        f"• {colab_ident}\n\n"
        f"EQUIPAMENTO / MÁQUINA:\n"
        f"• Frota: {frota}\n"
        f"• Modelo: {veiculo or 'Não informado'}\n"
        f"• Horímetro / KM: {horimetro}\n\n"
        f"LOCALIZAÇÃO & CONTATO:\n"
        f"• Cliente / Fazenda: {cliente}\n"
        f"• Local / Talhão: {fazenda}\n"
        + (f"• Contato: {contato}\n" if contato else "")
        + f"\nDIAGNÓSTICO & SERVIÇOS SOLICITADOS:\n"
        f"• {servicos}\n\n"
        f"----------------------------------------\n"
        f"INSTRUÇÕES DE RETORNO (OBRIGATÓRIO):\n"
        f"Ao concluir o atendimento, responda com:\n"
        f"1. Horímetro / KM Final\n"
        f"2. Serviços Executados e Peças Substituídas\n"
        f"3. Fotos e vídeos de comprovação do teste\n"
        f"4. Status: Concluído e Liberado (ou Pendência)\n"
        f"────────────────────────────────────────"
    )

    encoded_text = urllib.parse.quote(texto)
    link_wa = f"https://wa.me/{colab_tel}?text={encoded_text}" if colab_tel else f"https://wa.me/?text={encoded_text}"
    link_tg = f"https://t.me/share/url?text={encoded_text}"
    link_mail = f"mailto:?subject={urllib.parse.quote(f'ORDEM DE SERVIÇO #{num_os} - {frota}')}&body={encoded_text}"

    return {
        "ok": True,
        "numero_os": num_os,
        "texto_despacho": texto,
        "link_whatsapp": link_wa,
        "link_telegram": link_tg,
        "link_mailto": link_mail,
        "colaborador": colaborador or {}
    }


def gerar_texto_conclusao_cliente(dados_os: dict, cliente_custom: dict = None) -> dict:
    """
    Gera texto padronizado de conclusão de O.S. para notificar o cliente final via WhatsApp, E-mail ou Compartilhar.
    """
    num_os = dados_os.get("numeroOS") or dados_os.get("numero_os") or dados_os.get("id") or "S/N"
    data_conclusao = dados_os.get("data_conclusao") or datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")

    cliente_nome = (cliente_custom or {}).get("nome") or dados_os.get("cliente") or dados_os.get("solicitante") or "Cliente"
    telefone_cliente = normalizar_numero((cliente_custom or {}).get("telefone") or dados_os.get("telefoneCliente") or dados_os.get("telefone") or "")

    frota = dados_os.get("frota") or "Não informado"
    veiculo = dados_os.get("veiculo") or dados_os.get("equipamento") or ""
    fazenda = dados_os.get("localAtendimento") or dados_os.get("fazenda") or dados_os.get("local") or "Não informado"
    km_final = dados_os.get("km_final") or dados_os.get("km") or dados_os.get("horimetro") or "Registrado em O.S."
    tecnico = dados_os.get("tecnico") or dados_os.get("responsavel") or "Técnico Especializado"

    servicos = dados_os.get("observacoes") or dados_os.get("diagnostico") or dados_os.get("servico") or ""
    itens_serv = dados_os.get("servicosItens") or []
    if itens_serv:
        linhas_itens = []
        for s in itens_serv:
            desc = s.get("descricao") or s.get("servico") or ""
            if desc:
                linhas_itens.append(f"• {desc}")
        if linhas_itens:
            servicos = ("\n".join(linhas_itens)).strip()
    if not servicos:
        servicos = "Revisão e manutenção técnica executada com sucesso."

    texto = (
        f"[ SERVIÇO CONCLUÍDO - O.S. #{num_os} ]\n\n"
        f"Olá {cliente_nome}, informamos que o atendimento ao seu equipamento foi concluído com sucesso!\n\n"
        f"DADOS DO ATENDIMENTO:\n"
        f"• Equipamento / Frota: {frota} {f'({veiculo})' if veiculo else ''}\n"
        f"• Local / Fazenda: {fazenda}\n"
        f"• KM / Horímetro Final: {km_final}\n"
        f"• Responsável Técnico: {tecnico}\n"
        f"• Conclusão: {data_conclusao}\n\n"
        f"SERVIÇOS REALIZADOS:\n"
        f"• {servicos}\n\n"
        f"----------------------------------------\n"
        f"Equipamento testado e liberado para operação!\n"
        f"Permanecemos à inteira disposição. Agradecemos a confiança!"
    )

    encoded_text = urllib.parse.quote(texto)
    link_wa = f"https://wa.me/{telefone_cliente}?text={encoded_text}" if telefone_cliente else f"https://wa.me/?text={encoded_text}"
    link_tg = f"https://t.me/share/url?text={encoded_text}"
    link_mail = f"mailto:?subject={urllib.parse.quote(f'CONCLUSÃO O.S. #{num_os} - {frota}')}&body={encoded_text}"

    return {
        "ok": True,
        "numero_os": num_os,
        "texto_conclusao": texto,
        "link_whatsapp": link_wa,
        "link_telegram": link_tg,
        "link_mailto": link_mail,
        "telefone_cliente": telefone_cliente,
        "cliente_nome": cliente_nome
    }


def obter_ultima_os_whatsapp() -> dict:
    """Retorna os dados da última OS recebida via WhatsApp."""
    if ULTIMA_OS_FILE.exists():
        try:
            with open(ULTIMA_OS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Fallback: pesquisa a última no db.json marcada com origem 'whatsapp'
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
                criticas = db.get("criticas", [])
                for c in criticas:
                    if c.get("origem") == "whatsapp":
                        return {
                            "numero_os": c.get("numeroOS") or c.get("id"),
                            "frota": c.get("frota"),
                            "solicitante": c.get("cliente"),
                            "cliente": c.get("cliente"),
                            "fazenda": c.get("localAtendimento"),
                            "local": c.get("localAtendimento"),
                            "responsavel": c.get("tecnico"),
                            "tecnico": c.get("tecnico"),
                            "diagnostico": c.get("observacoes"),
                            "medias": c.get("medias", []),
                            "data_recebimento": c.get("data_importacao_whatsapp")
                        }
        except Exception:
            pass

    return {}

def buscar_os_whatsapp(numero_os: str) -> dict:
    """Busca os dados de uma O.S. específica recebida via WhatsApp."""
    num_str = str(numero_os or "").strip()
    if not num_str:
        return {}
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
                for c in db.get("criticas", []):
                    if str(c.get("numeroOS") or c.get("id")).strip() == num_str:
                        return {
                            "numero_os": c.get("numeroOS") or c.get("id"),
                            "frota": c.get("frota"),
                            "solicitante": c.get("cliente"),
                            "cliente": c.get("cliente"),
                            "fazenda": c.get("localAtendimento"),
                            "local": c.get("localAtendimento"),
                            "responsavel": c.get("tecnico"),
                            "tecnico": c.get("tecnico"),
                            "diagnostico": c.get("observacoes"),
                            "medias": c.get("medias", []),
                            "data_recebimento": c.get("data_importacao_whatsapp")
                        }
        except Exception:
            pass
    return {}

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

    # Demonstração rápida
    msg_teste = """
    Frota 5110
    OS 141668
    Serviço de solda na chapa de fixação da estrutura próxima a roda traseira lado direito (Fazenda Estrela)
    Solicitado Sr. João Dubay
    Responsavel Sr. Mauricio
    """
    res = processar_mensagem_whatsapp({
        "text": msg_teste,
        "sender": "554499999999",
        "media": [
            {
                "filename": "video_solda.mp4",
                "content_base64": base64.b64encode(b"SIMULACAO_VIDEO_BYTES_MP4").decode("ascii"),
                "mimetype": "video/mp4"
            }
        ]
    })
    print(json.dumps(res, indent=2, ensure_ascii=True))
