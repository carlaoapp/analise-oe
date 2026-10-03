#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de Orçamento e Ordem de Serviço
Módulo responsável por:
1. Buscar dados de O.S. (do banco SQLite ou db.json)
2. Gerar PDF espelhado na folha física da oficina (ReportLab)
3. Gerar Excel estilizado com fórmulas (OpenPyXL)
"""

import os
import sys
import json
import datetime
from pathlib import Path
from copy import copy

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PUBLIC_DIR = BASE_DIR / "public"
DEFAULT_DB_FILE = DATA_DIR / "db.json"

STATUS_FINANCEIRO_ROTULOS = {
    "pendente_orcamento": "Pendente Orçamento",
    "aguardando_faturamento": "Aguardando Faturamento",
    "faturada": "Faturada",
    "cancelada": "Cancelada"
}

CONFIG_EMPRESA_FILE = DATA_DIR / "config_empresa.json"
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATE_INFO_FILE = TEMPLATES_DIR / "template_info.json"

def obter_template_ativo():
    """
    Retorna se há um template customizado ativo (.xlsx ou .html), seu nome e caminho.
    """
    if TEMPLATE_INFO_FILE.exists():
        try:
            with open(TEMPLATE_INFO_FILE, "r", encoding="utf-8") as f:
                info = json.load(f)
                if info.get("ativo"):
                    arq = TEMPLATES_DIR / info.get("arquivo_salvo", "")
                    if arq.exists():
                        return {
                            "ativo": True,
                            "tipo": info.get("tipo", "xlsx"),
                            "nome_arquivo": info.get("nome_original", arq.name),
                            "caminho": str(arq)
                        }
        except Exception:
            pass

    # Verifica também se algum modelo_usuario.* existe diretamente
    if TEMPLATES_DIR.exists():
        for arq in TEMPLATES_DIR.glob("modelo_usuario.*"):
            if arq.name != "template_info.json" and arq.is_file():
                t = arq.suffix.lower().replace(".", "")
                return {
                    "ativo": True,
                    "tipo": t,
                    "nome_arquivo": arq.name,
                    "caminho": str(arq)
                }

    return {"ativo": False, "tipo": "", "nome_arquivo": "", "caminho": ""}

def salvar_template_usuario(nome_arquivo, conteudo_base64):
    """
    Salva o arquivo modelo enviado pelo usuário em templates/ com nome padronizado
    (modelo_usuario.xlsx, .pdf, .html, .png, etc.) e registra no template_info.json.
    """
    import base64
    try:
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        nome_str = str(nome_arquivo or "").lower()
        
        # Suporte a múltiplos formatos: Word, Excel, PDF, HTML, e Imagens/Fotos
        ext = ".xlsx"
        for possivel_ext in [".docx", ".doc", ".xlsx", ".xls", ".pdf", ".html", ".htm", ".png", ".jpg", ".jpeg", ".webp"]:
            if nome_str.endswith(possivel_ext):
                ext = possivel_ext
                break
        
        # Remove arquivos anteriores de modelo_usuario para evitar conflitos de extensões
        for arq in TEMPLATES_DIR.glob("modelo_usuario.*"):
            if arq.is_file() and arq.name != "template_info.json":
                try:
                    arq.unlink()
                except Exception:
                    pass

        target_filename = f"modelo_usuario{ext}"
        target_path = TEMPLATES_DIR / target_filename
        
        raw_b64 = str(conteudo_base64 or "")
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
            
        file_bytes = base64.b64decode(raw_b64)
        with open(target_path, "wb") as f:
            f.write(file_bytes)
            
        tipo_str = ext.replace(".", "")
        info = {
            "ativo": True,
            "tipo": tipo_str,
            "nome_original": nome_arquivo,
            "arquivo_salvo": target_filename,
            "tamanho_bytes": len(file_bytes),
            "data_upload": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        with open(TEMPLATE_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
            
        return {
            "ok": True,
            "mensagem": f"Modelo '{nome_arquivo}' ({tipo_str.upper()}) anexado e ativado com sucesso!",
            "nome_arquivo": nome_arquivo,
            "tipo": tipo_str
        }
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro ao salvar modelo: {str(e)}"}

def remover_template_usuario():
    """
    Desativa o modelo customizado e retorna ao modelo padrão do sistema.
    """
    try:
        if TEMPLATE_INFO_FILE.exists():
            with open(TEMPLATE_INFO_FILE, "w", encoding="utf-8") as f:
                json.dump({"ativo": False}, f, ensure_ascii=False, indent=2)
        for arq in TEMPLATES_DIR.glob("modelo_usuario.*"):
            if arq.exists():
                try:
                    arq.unlink()
                except:
                    pass
        return {"ok": True, "mensagem": "Modelo personalizado removido. Utilizando modelo padrão."}
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro ao desativar modelo: {str(e)}"}

def obter_config_empresa():
    """
    Retorna a configuração cadastral da empresa (white-label).
    Se existir config_empresa.json salvo, carrega-o; caso contrário, retorna padrão neutro.
    """
    if CONFIG_EMPRESA_FILE.exists():
        try:
            with open(CONFIG_EMPRESA_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if isinstance(cfg, dict) and cfg.get("razao_social"):
                    return cfg
        except Exception:
            pass
    return {
        "razao_social": "[Nome da Sua Empresa]",
        "endereco": "[Endereço]",
        "cidade_uf_bairro": "[Cidade/UF]",
        "telefone": "[Telefone]",
        "cnpj": "[CNPJ]",
        "logo_base64": "",
        "modo_banner": False
    }

def salvar_config_empresa(dados):
    """
    Grava os dados cadastrais fixos da empresa em config_empresa.json.
    """
    try:
        CONFIG_EMPRESA_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(CONFIG_EMPRESA_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return {"ok": True, "mensagem": "Dados da empresa salvos com sucesso!"}
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro ao salvar dados da empresa: {str(e)}"}

def normalizar_status_financeiro(st):
    s = str(st or "").strip().lower()
    if "aguard" in s or "faturar" in s and "aguard" in s:
        return "aguardando_faturamento"
    elif "faturad" in s or s == "faturada":
        return "faturada"
    elif "pend" in s or "orc" in s:
        return "pendente_orcamento"
    return "pendente_orcamento"

def listar_os_para_orcamento(db_path=None, incluir_todas=False):
    """
    Retorna a lista de O.S. para a tela de orçamentos.
    Se incluir_todas=False, retorna apenas pendentes ('Pendente Orçamento' ou 'Aguardando Faturamento').
    Se incluir_todas=True, retorna todas as ordens (inclusive 'Faturada' e 'Cancelada') com detalhes enriquecidos.
    """
    db_file = Path(db_path) if db_path else DEFAULT_DB_FILE
    db_data = {"criticas": []}
    if db_file.exists():
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                db_data = json.load(f)
        except Exception as e:
            print(f"[Aviso] Erro ao ler db.json: {e}", file=sys.stderr)
            
    criticas = db_data.get("criticas", [])
    resultado = []
    vistos = set()
    
    for c in criticas:
        if c.get("tipo") and c.get("tipo") != "os":
            continue
            
        st_op = (c.get("status") or c.get("statusOS") or "").strip()
        st_fin = c.get("status_financeiro")
        if not st_fin:
            st_fin = "pendente_orcamento"
        else:
            st_fin = normalizar_status_financeiro(st_fin)
            
        if st_op.lower() in ["cancelada", "reprovado"]:
            st_fin = "cancelada"

        if not incluir_todas:
            # Exclui ordens canceladas e já faturadas no modo apenas pendentes
            if st_op.lower() in ["cancelada", "reprovado"] or st_fin in ["faturada", "cancelada"]:
                continue
            
        num_os = str(c.get("numeroOS") or c.get("id") or "").strip()
        if not num_os or num_os in vistos:
            continue
        vistos.add(num_os)
            
        # Cálculos de valores
        p_tot = float(c.get("pecasTotal") or 0.0)
        s_tot = 0.0
        if c.get("servicosItens"):
            s_tot = sum(float(i.get("valor") or 0.0) for i in c["servicosItens"])
        elif c.get("servicosFinal"):
            s_tot = float(c.get("servicosFinal") or 0.0)
        km_tot = float(c.get("valorKmTotal") or 0.0)
        total = float(c.get("totalGeral") or c.get("totalOS") or (p_tot + s_tot + km_tot) or 0.0)

        # Resumo de peças e serviços
        resumo_pecas = []
        if c.get("pecas"):
            resumo_pecas = [str(p.get("descricao") or p.get("produto") or "Peça") for p in c["pecas"][:3]]
        elif c.get("pecas_utilizadas"):
            resumo_pecas = [str(c["pecas_utilizadas"])]

        resumo_servicos = []
        if c.get("servicosItens"):
            resumo_servicos = [str(s.get("descricao") or s.get("servico") or "Serviço") for s in c["servicosItens"][:3]]
        elif c.get("servicos_executados"):
            resumo_servicos = [str(c["servicos_executados"])]
        elif c.get("observacoes"):
            resumo_servicos = [str(c["observacoes"])]
            
        resultado.append({
            "numero_os": num_os,
            "id": c.get("id") or num_os,
            "frota": c.get("frota") or c.get("veiculo") or c.get("placa") or "-",
            "equipamento": c.get("veiculo") or c.get("equipamento") or "-",
            "cliente": c.get("cliente") or c.get("nomeCliente") or "Cliente não informado",
            "fazenda": c.get("fazenda") or c.get("propriedade") or c.get("local") or "-",
            "data": c.get("dataOS") or (c.get("data", "")[:10] if c.get("data") else datetime.date.today().isoformat()),
            "status": st_op or "Finalizada",
            "status_operacional": st_op or "Finalizada",
            "status_financeiro": st_fin,
            "status_financeiro_rotulo": STATUS_FINANCEIRO_ROTULOS.get(st_fin, "Pendente Orçamento"),
            "pecas_total": p_tot,
            "servicos_total": s_tot,
            "resumo_pecas": ", ".join(resumo_pecas) if resumo_pecas else "Nenhuma peça informada",
            "resumo_servicos": ", ".join(resumo_servicos) if resumo_servicos else "Serviços gerais de manutenção",
            "total": total,
            "total_formatado": format_moeda_rs(total)
        })
        
    return resultado

def cancelar_os_registro(numero_os, motivo="Cancelada na Central de Orçamentos", db_path=None):
    """
    Cancela a O.S. no db.json, alterando status operacional e financeiro para 'cancelada'.
    """
    db_file = Path(db_path) if db_path else DEFAULT_DB_FILE
    if not db_file.exists():
        return {"ok": False, "mensagem": "Arquivo de banco de dados não encontrado."}
        
    try:
        with open(db_file, "r", encoding="utf-8") as f:
            db_data = json.load(f)
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro ao ler banco: {e}"}

    criticas = db_data.get("criticas", [])
    os_str = str(numero_os).strip()
    agora_iso = datetime.datetime.now().isoformat()
    encontrado = False

    for c in criticas:
        if str(c.get("numeroOS", "")).strip() == os_str or str(c.get("id", "")).strip() == os_str:
            c["status"] = "Cancelada"
            c["statusOS"] = "Cancelada"
            c["status_financeiro"] = "cancelada"
            c["status_financeiro_rotulo"] = "Cancelada"
            c["motivo_cancelamento"] = motivo
            c["data_cancelamento"] = agora_iso
            encontrado = True

    if encontrado:
        try:
            with open(db_file, "w", encoding="utf-8") as f:
                json.dump(db_data, f, ensure_ascii=False, indent=2)
            return {"ok": True, "mensagem": f"O.S. #{os_str} cancelada com sucesso!"}
        except Exception as e:
            return {"ok": False, "mensagem": f"Erro ao salvar cancelamento: {e}"}
    return {"ok": False, "mensagem": f"O.S. #{os_str} não encontrada."}

def excluir_os_registro(numero_os, db_path=None):
    """
    Remove permanentemente o registro da O.S. do db.json.
    """
    db_file = Path(db_path) if db_path else DEFAULT_DB_FILE
    if not db_file.exists():
        return {"ok": False, "mensagem": "Arquivo de banco de dados não encontrado."}
        
    try:
        with open(db_file, "r", encoding="utf-8") as f:
            db_data = json.load(f)
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro ao ler banco: {e}"}

    criticas = db_data.get("criticas", [])
    os_str = str(numero_os).strip()
    tam_antes = len(criticas)
    
    criticas_filtradas = [
        c for c in criticas
        if not (str(c.get("numeroOS", "")).strip() == os_str or str(c.get("id", "")).strip() == os_str)
    ]

    if len(criticas_filtradas) < tam_antes:
        db_data["criticas"] = criticas_filtradas
        try:
            with open(db_file, "w", encoding="utf-8") as f:
                json.dump(db_data, f, ensure_ascii=False, indent=2)
            return {"ok": True, "mensagem": f"O.S. #{os_str} excluída com sucesso!"}
        except Exception as e:
            return {"ok": False, "mensagem": f"Erro ao salvar banco após exclusão: {e}"}
    return {"ok": False, "mensagem": f"O.S. #{os_str} não encontrada para exclusão."}

def faturar_lote_os_registro(numeros_os, db_path=None):
    """
    Atualiza o status de múltiplas ordens de serviço para 'faturada' em uma única operação.
    """
    if not numeros_os or not isinstance(numeros_os, list):
        return {"ok": False, "mensagem": "Nenhuma O.S. informada para faturamento em lote."}
        
    sucessos = 0
    erros = []
    for num in numeros_os:
        r = atualizar_status_os(num, "faturada", db_path=db_path)
        if r.get("ok"):
            sucessos += 1
        else:
            erros.append(f"OS #{num}: {r.get('mensagem')}")

    return {
        "ok": sucessos > 0,
        "faturadas": sucessos,
        "total": len(numeros_os),
        "erros": erros,
        "mensagem": f"{sucessos} de {len(numeros_os)} O.S. foram faturadas com sucesso!"
    }

def atualizar_status_os(numero_os, novo_status, db_path=None):
    """
    Recebe o número da OS e altera seu status financeiro entre:
    - 'pendente_orcamento'
    - 'aguardando_faturamento'
    - 'faturada'
    Registra data/hora da alteração e persiste em db.json.
    """
    db_file = Path(db_path) if db_path else DEFAULT_DB_FILE
    if not db_file.exists():
        return {"ok": False, "mensagem": "Arquivo db.json não encontrado."}
        
    try:
        with open(db_file, "r", encoding="utf-8") as f:
            db_data = json.load(f)
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro ao ler banco: {e}"}
        
    criticas = db_data.get("criticas", [])
    os_str = str(numero_os).strip()
    status_norm = normalizar_status_financeiro(novo_status)
    rotulo = STATUS_FINANCEIRO_ROTULOS.get(status_norm, "Pendente Orçamento")
    agora_iso = datetime.datetime.now().isoformat()
    
    encontrado = False
    for c in criticas:
        if str(c.get("numeroOS", "")).strip() == os_str or str(c.get("id", "")).strip() == os_str:
            c["status_financeiro"] = status_norm
            c["status_financeiro_rotulo"] = rotulo
            c["status_financeiro_data"] = agora_iso
            
            if "historico_status_financeiro" not in c or not isinstance(c["historico_status_financeiro"], list):
                c["historico_status_financeiro"] = []
            c["historico_status_financeiro"].append({
                "status": status_norm,
                "rotulo": rotulo,
                "data": agora_iso
            })
            encontrado = True
            
    if not encontrado:
        novo_registro = {
            "id": os_str,
            "tipo": "os",
            "numeroOS": os_str,
            "data": agora_iso,
            "dataOS": agora_iso[:10],
            "status": "Finalizada",
            "statusOS": "Finalizada",
            "status_financeiro": status_norm,
            "status_financeiro_rotulo": rotulo,
            "status_financeiro_data": agora_iso,
            "historico_status_financeiro": [{
                "status": status_norm,
                "rotulo": rotulo,
                "data": agora_iso
            }]
        }
        criticas.insert(0, novo_registro)
        encontrado = True
        
    try:
        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
        return {
            "ok": True,
            "numero_os": os_str,
            "status": status_norm,
            "rotulo": rotulo,
            "data": agora_iso,
            "mensagem": f"Status financeiro da O.S. #{os_str} atualizado para '{rotulo}'."
        }
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro ao salvar db.json: {e}"}

def format_moeda(val):
    try:
        f = float(val)
        return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

def format_moeda_rs(val):
    return f"R$ {format_moeda(val)}"

def format_qtd(val):
    try:
        f = float(val)
        if f.is_integer():
            return f"{int(f):,d}".replace(",", ".") + ",00"
        return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "1,00"

def buscar_dados_os(numero_os, db_path=None):
    """
    Busca os dados completos da O.S. no arquivo db.json ou SQLite
    e retorna o dicionário pronto para uso no frontend e geração de relatórios.
    """
    db_file = Path(db_path) if db_path else DEFAULT_DB_FILE
    db_data = {"criticas": [], "clientes": [], "equipamentos": []}
    
    if db_file.exists():
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                db_data = json.load(f)
        except Exception as e:
            print(f"[Aviso] Erro ao ler db.json: {e}", file=sys.stderr)
            
    criticas = db_data.get("criticas", [])
    clientes = db_data.get("clientes", [])
    equipamentos = db_data.get("equipamentos", [])
    
    # Busca por numeroOS, id, ou frota
    os_str = str(numero_os).strip()
    match = None
    
    for c in criticas:
        if str(c.get("numeroOS", "")).strip() == os_str:
            match = c
            break
        if str(c.get("id", "")).strip() == os_str:
            match = c
            break
        if str(c.get("frota", "")).strip() == os_str:
            match = c
            break
            
    if not match:
        for c in criticas:
            if os_str.lower() in str(c.get("cliente", "")).lower() or os_str.lower() in str(c.get("equipamento", "")).lower():
                match = c
                break
                
    # Dados cadastrais da oficina (white-label carregado de config_empresa.json ou padrao neutro)
    empresa = obter_config_empresa()
    
    hoje = datetime.date.today()
    hora_agora = datetime.datetime.now().strftime("%H:%M:%S")
    data_hoje_str = hoje.strftime("%d/%m/%Y")
    
    if not match:
        # Retorna estrutura modelo limpa preenchivel
        return {
            "encontrado": False,
            "mensagem": f"O.S. '{numero_os}' não encontrada na base local.",
            "empresa": empresa,
            "orcamento": {
                "numero_orcamento": f"ORC-{int(datetime.datetime.now().timestamp())}",
                "numero_os": os_str,
                "frota": "",
                "data_emissao": data_hoje_str,
                "hora_emissao": hora_agora,
                "data_entrada": data_hoje_str,
                "data_entrega": data_hoje_str,
                "cliente_codigo": "",
                "cliente_nome": "",
                "cnpj_cpf": "",
                "ie_rg": "",
                "telefone": "",
                "contato": "",
                "endereco": "",
                "bairro": "",
                "cidade_uf": "",
                "cep": "",
                "hr_inicio": "08:00",
                "hr_final": "10:00",
                "hr_total": "02:00",
                "veiculo": "",
                "fabricante": "",
                "placa": "",
                "km_inicio": 0,
                "km_final": 0,
                "km_total": 0,
                "pecas": [],
                "subtotal_pecas": 0.0,
                "servicos": [],
                "subtotal_servicos": 0.0,
                "informacoes_cliente": "",
                "valor_pecas": 0.0,
                "valor_mao_obra": 0.0,
                "valor_terceiros": 0.0,
                "subtotal_geral": 0.0,
                "desconto_pecas": 0.0,
                "desconto_mao_obra": 0.0,
                "desconto_faturamento": 0.0,
                "valor_adiantamento": 0.0,
                "valor_a_receber": 0.0,
                "total_os": 0.0
            }
        }
        
    # Localiza dados estendidos do cliente se houver
    cliente_info = {}
    cli_nome = str(match.get("cliente", "")).strip()
    if cli_nome:
        for cl in clientes:
            if str(cl.get("nome", "")).strip().lower() == cli_nome.lower():
                cliente_info = cl
                break
                
    # Extrai e formata datas
    dt_os = match.get("dataOS") or match.get("data", "")
    data_formatada = data_hoje_str
    if dt_os:
        try:
            if "T" in str(dt_os):
                p = dt_os.split("T")[0].split("-")
                data_formatada = f"{p[2]}/{p[1]}/{p[0]}"
            elif "-" in str(dt_os):
                p = dt_os.split("-")
                data_formatada = f"{p[2]}/{p[1]}/{p[0]}"
        except:
            data_formatada = str(dt_os)
            
    # Horários
    hr_ini = "08:00"
    hr_fim = "10:00"
    hr_tot = "02:00"
    if match.get("dataInicio") and "T" in str(match.get("dataInicio")):
        try:
            hr_ini = match["dataInicio"].split("T")[1][:5]
        except: pass
    if match.get("dataFim") and "T" in str(match.get("dataFim")):
        try:
            hr_fim = match["dataFim"].split("T")[1][:5]
        except: pass

    # Peças
    pecas_raw = match.get("pecasItens", [])
    pecas = []
    subtotal_pecas = 0.0
    for idx, p in enumerate(pecas_raw, start=1):
        qtd = float(p.get("qtd") or 1)
        unit = float(p.get("valor") or 0)
        tot = float(p.get("subtotal") or (qtd * unit))
        subtotal_pecas += tot
        pecas.append({
            "codigo": str(p.get("codigo") or p.get("num") or idx),
            "produto": p.get("descricao") or p.get("produto") or "Peça Diversa",
            "obs": p.get("obs") or "",
            "qtd": qtd,
            "vr_unitario": unit,
            "vr_total": tot
        })
        
    # Serviços
    servicos_raw = match.get("servicosItens", [])
    servicos = []
    subtotal_servicos = 0.0
    for idx, s in enumerate(servicos_raw, start=1):
        qtd = float(s.get("qtd") or 1)
        unit = float(s.get("valor") or 0)
        tot = float(s.get("subtotal") or (qtd * unit))
        subtotal_servicos += tot
        servicos.append({
            "data": data_formatada,
            "servico": "MAO DE OBRA",
            "descricao": s.get("descricao") or "Serviço Mecânico / Elétrico",
            "obs": s.get("obs") or "",
            "qtd": qtd,
            "vr_unitario": unit,
            "vr_total": tot
        })
        
    # Se houver cobrança de KM rodado, adiciona como item de serviço conforme folha padrão
    km_tot = float(match.get("kmTotal") or 0)
    val_km = float(match.get("valorKm") or 0)
    val_km_tot = float(match.get("valorKmTotal") or (km_tot * val_km))
    if km_tot > 0 and val_km > 0:
        subtotal_servicos += val_km_tot
        servicos.append({
            "data": data_formatada,
            "servico": "KM RODADO",
            "descricao": f"{int(km_tot)}KM RODADOS DE DESLOCAMENTO TÉCNICO",
            "obs": "",
            "qtd": km_tot,
            "vr_unitario": val_km,
            "vr_total": val_km_tot
        })
        
    # Totais
    subtotal_geral = subtotal_pecas + subtotal_servicos
    desc_serv = float(match.get("servicosDesconto") or 0)
    total_geral = subtotal_geral - desc_serv
    
    diag_raw = match.get("observacoes") or match.get("problema") or (match.get("servicos") if isinstance(match.get("servicos"), str) else "") or match.get("informacoes_cliente") or ""
    obs_cliente = str(diag_raw).strip()
    if match.get("tecnico"):
        obs_cliente = f"TÉCNICO RESPONSÁVEL: {match.get('tecnico')}\n" + obs_cliente
        
    num_os = match.get("numeroOS") or match.get("id") or os_str
    
    return {
        "encontrado": True,
        "empresa": empresa,
        "orcamento": {
            "numero_orcamento": f"N° {str(num_os).zfill(6)}",
            "numero_os": str(num_os),
            "frota": str(match.get("frota") or ""),
            "data_emissao": data_hoje_str,
            "hora_emissao": hora_agora,
            "data_entrada": data_formatada,
            "data_entrega": data_formatada,
            "cliente_codigo": str(cliente_info.get("codigo") or ""),
            "cliente_nome": cli_nome or "",
            "cnpj_cpf": cliente_info.get("doc") or cliente_info.get("cpf") or match.get("cpf") or "",
            "ie_rg": cliente_info.get("rg") or cliente_info.get("ie") or "",
            "telefone": cliente_info.get("tel") or match.get("telefone") or "",
            "contato": cliente_info.get("contato") or "",
            "endereco": cliente_info.get("end") or match.get("localAtendimento") or "",
            "bairro": cliente_info.get("bairro") or "",
            "cidade_uf": cliente_info.get("cidade") or match.get("localAtendimento") or "",
            "cep": cliente_info.get("cep") or "",
            "hr_inicio": hr_ini,
            "hr_final": hr_fim,
            "hr_total": hr_tot,
            "veiculo": match.get("equipamento") or match.get("veiculo") or "",
            "fabricante": match.get("fabricante") or "",
            "placa": match.get("placa") or "",
            "km_inicio": float(match.get("kmInicial") or 0),
            "km_final": float(match.get("kmFinal") or 0),
            "km_total": km_tot,
            "pecas": pecas,
            "subtotal_pecas": subtotal_pecas,
            "servicos": servicos,
            "subtotal_servicos": subtotal_servicos,
            "informacoes_cliente": obs_cliente.strip(),
            "valor_pecas": subtotal_pecas,
            "valor_mao_obra": subtotal_servicos,
            "valor_terceiros": 0.0,
            "subtotal_geral": subtotal_geral,
            "desconto_pecas": 0.0,
            "desconto_mao_obra": desc_serv,
            "desconto_faturamento": 0.0,
            "valor_adiantamento": 0.0,
            "valor_a_receber": total_geral,
            "total_os": total_geral,
            "status_financeiro": match.get("status_financeiro") or "pendente_orcamento",
            "status_financeiro_rotulo": STATUS_FINANCEIRO_ROTULOS.get(match.get("status_financeiro") or "pendente_orcamento", "Pendente Orçamento")
        }
    }


def excel_to_pdf_reportlab(xlsx_path, pdf_path):
    """
    Renderiza uma planilha Excel (OpenPyXL) como PDF de alta fidelidade
    utilizando ReportLab, preservando larguras, fontes, cores de fundo,
    alinhamentos, bordas e células mescladas.
    """
    try:
        import openpyxl
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
    except ImportError as e:
        raise RuntimeError(f"Dependência ausente para conversão de planilha em PDF: {e}")

    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active

    max_r = ws.max_row
    max_c = ws.max_column
    if max_r < 1 or max_c < 1:
        raise ValueError("A planilha de modelo está vazia.")

    PAGE_W, PAGE_H = A4
    MARGIN = 20
    AVAILABLE_W = PAGE_W - (2 * MARGIN)

    # 1. Largura das colunas
    col_widths = []
    total_raw_w = 0
    for c in range(1, max_c + 1):
        col_letter = openpyxl.utils.get_column_letter(c)
        w = ws.column_dimensions[col_letter].width
        w_val = float(w) if w else 12.0
        col_widths.append(w_val)
        total_raw_w += w_val

    if total_raw_w <= 0:
        total_raw_w = max_c * 12.0
        col_widths = [12.0] * max_c

    scaled_widths = [(w / total_raw_w) * AVAILABLE_W for w in col_widths]

    styles = getSampleStyleSheet()
    table_data = []
    table_styles = [
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]

    for r in range(1, max_r + 1):
        row_cells = []
        for c in range(1, max_c + 1):
            cell = ws.cell(row=r, column=c)
            val = "" if cell.value is None else str(cell.value)
            
            is_bold = bool(cell.font and cell.font.bold)
            raw_size = int(cell.font.size) if (cell.font and cell.font.size) else 8
            font_size = min(max(raw_size - 1, 6), 13)
            
            align_code = 0 # Left
            if cell.alignment and cell.alignment.horizontal:
                h = cell.alignment.horizontal
                if h == 'center':
                    align_code = 1
                elif h == 'right':
                    align_code = 2

            p_style = ParagraphStyle(
                f'Cell_{r}_{c}',
                parent=styles['Normal'],
                fontName='Helvetica-Bold' if is_bold else 'Helvetica',
                fontSize=font_size,
                leading=font_size + 2,
                alignment=align_code,
                textColor=colors.black
            )
            safe_val = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
            row_cells.append(Paragraph(safe_val, p_style))

            if cell.fill and cell.fill.start_color and cell.fill.start_color.rgb:
                rgb_str = str(cell.fill.start_color.rgb)
                if len(rgb_str) == 8:
                    rgb_str = rgb_str[2:]
                if len(rgb_str) == 6 and rgb_str != "000000" and rgb_str.upper() != "FFFFFF":
                    try:
                        r_col = int(rgb_str[0:2], 16) / 255.0
                        g_col = int(rgb_str[2:4], 16) / 255.0
                        b_col = int(rgb_str[4:6], 16) / 255.0
                        table_styles.append(('BACKGROUND', (c-1, r-1), (c-1, r-1), colors.Color(r_col, g_col, b_col)))
                    except:
                        pass

            if cell.border:
                if cell.border.top and cell.border.top.style:
                    table_styles.append(('LINEABOVE', (c-1, r-1), (c-1, r-1), 0.5, colors.black))
                if cell.border.bottom and cell.border.bottom.style:
                    table_styles.append(('LINEBELOW', (c-1, r-1), (c-1, r-1), 0.5, colors.black))
                if cell.border.left and cell.border.left.style:
                    table_styles.append(('LINEBEFORE', (c-1, r-1), (c-1, r-1), 0.5, colors.black))
                if cell.border.right and cell.border.right.style:
                    table_styles.append(('LINEAFTER', (c-1, r-1), (c-1, r-1), 0.5, colors.black))

        table_data.append(row_cells)

    for rng in ws.merged_cells.ranges:
        sc, sr, ec, er = rng.min_col - 1, rng.min_row - 1, rng.max_col - 1, rng.max_row - 1
        table_styles.append(('SPAN', (sc, sr), (ec, er)))

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )

    t = Table(table_data, colWidths=scaled_widths)
    t.setStyle(TableStyle(table_styles))
    doc.build([t])
    return str(pdf_path)


def preencher_modelo_customizado(caminho_template, dados_orcamento, output_excel_path=None):
    """
    Motor de Injeção de Dados no modelo Excel (.xlsx) do usuário.
    Mapeia tags/placeholders dinâmicos, itera sobre itens de Peças e Mão de Obra
    inserindo dinamicamente as linhas sem quebrar fórmulas nativas ou estilos,
    e preenche células vazias com valores padrão seguros.
    """
    import openpyxl
    wb = openpyxl.load_workbook(caminho_template)
    ws = wb.active

    orc = dados_orcamento.get("orcamento", dados_orcamento)
    emp = dados_orcamento.get("empresa")
    if not emp or not emp.get("razao_social"):
        emp = obter_config_empresa()

    def _moeda(v):
        try:
            val = float(v or 0)
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"

    num_os = str(orc.get("numero_os") or "")
    num_orc = str(orc.get("numero_orcamento") or "")
    if num_orc and not num_orc.upper().startswith("N"):
        num_orc = f"N° {num_orc}"
    elif not num_orc and num_os:
        num_orc = f"N° {num_os.zfill(6)}"

    mapa_tags = {
        "{{NUMERO_OS}}": num_os,
        "{{OS}}": num_os,
        "{{NUMERO_ORCAMENTO}}": num_orc,
        "{{CLIENTE}}": str(orc.get("cliente_nome") or orc.get("cliente") or "-"),
        "{{NOME_CLIENTE}}": str(orc.get("cliente_nome") or orc.get("cliente") or "-"),
        "{{CNPJ_CPF}}": str(orc.get("cnpj_cpf") or orc.get("cpf_cnpj") or "-"),
        "{{CPF}}": str(orc.get("cnpj_cpf") or orc.get("cpf_cnpj") or "-"),
        "{{CNPJ}}": str(orc.get("cnpj_cpf") or orc.get("cpf_cnpj") or "-"),
        "{{DATA}}": str(orc.get("data_entrada") or orc.get("data_emissao") or orc.get("data") or datetime.date.today().strftime("%d/%m/%Y")),
        "{{DATA_ENTRADA}}": str(orc.get("data_entrada") or orc.get("data") or "-"),
        "{{DATA_ENTREGA}}": str(orc.get("data_entrega") or "-"),
        "{{DATA_EMISSAO}}": str(orc.get("data_emissao") or datetime.date.today().strftime("%d/%m/%Y")),
        "{{HORA_EMISSAO}}": str(orc.get("hora_emissao") or datetime.datetime.now().strftime("%H:%M:%S")),
        "{{FROTA}}": str(orc.get("frota") or "-"),
        "{{VEICULO}}": str(orc.get("veiculo") or orc.get("equipamento") or "-"),
        "{{EQUIPAMENTO}}": str(orc.get("veiculo") or orc.get("equipamento") or "-"),
        "{{FABRICANTE}}": str(orc.get("fabricante") or "-"),
        "{{PLACA}}": str(orc.get("placa") or "-"),
        "{{KM_INICIAL}}": str(orc.get("km_inicio") or orc.get("km_inicial") or "0"),
        "{{KM_FINAL}}": str(orc.get("km_final") or "0"),
        "{{KM_TOTAL}}": str(orc.get("km_total") or "0"),
        "{{HORAS_MOTOR}}": str(orc.get("hr_total") or orc.get("horas_motor") or "-"),
        "{{TELEFONE}}": str(orc.get("telefone") or "-"),
        "{{ENDERECO}}": str(orc.get("endereco") or "-"),
        "{{CIDADE_UF}}": str(orc.get("cidade_uf") or "-"),
        "{{CIDADE}}": str(orc.get("cidade_uf") or "-"),
        "{{BAIRRO}}": str(orc.get("bairro") or "-"),
        "{{CEP}}": str(orc.get("cep") or "-"),
        "{{PROBLEMA_TECNICO}}": str(orc.get("informacoes_cliente") or orc.get("observacoes") or "-"),
        "{{DIAGNOSTICO}}": str(orc.get("informacoes_cliente") or orc.get("observacoes") or "-"),
        "{{OBSERVACOES}}": str(orc.get("informacoes_cliente") or orc.get("observacoes") or "-"),
        "{{INFORMACOES_CLIENTE}}": str(orc.get("informacoes_cliente") or orc.get("observacoes") or "-"),
        "{{EMPRESA_NOME}}": str(emp.get("razao_social") or "[Sua Empresa]"),
        "{{RAZAO_SOCIAL}}": str(emp.get("razao_social") or "[Sua Empresa]"),
        "{{EMPRESA_CNPJ}}": str(emp.get("cnpj") or "-"),
        "{{EMPRESA_TELEFONE}}": str(emp.get("telefone") or "-"),
        "{{EMPRESA_ENDERECO}}": str(emp.get("endereco") or "-"),
        "{{EMPRESA_CIDADE}}": str(emp.get("cidade_uf_bairro") or "-"),
        "{{SUBTOTAL_PECAS}}": _moeda(orc.get("subtotal_pecas") or orc.get("valor_pecas")),
        "{{SUBTOTAL_SERVICOS}}": _moeda(orc.get("subtotal_servicos") or orc.get("valor_mao_obra")),
        "{{SUBTOTAL_GERAL}}": _moeda(orc.get("subtotal_geral") or (float(orc.get("subtotal_pecas") or 0) + float(orc.get("subtotal_servicos") or 0))),
        "{{DESCONTO_PECAS}}": _moeda(orc.get("desconto_pecas")),
        "{{DESCONTO_SERVICOS}}": _moeda(orc.get("desconto_mao_obra") or orc.get("desconto_servicos")),
        "{{DESCONTO_MAO_OBRA}}": _moeda(orc.get("desconto_mao_obra") or orc.get("desconto_servicos")),
        "{{DESCONTO_FATURAMENTO}}": _moeda(orc.get("desconto_faturamento")),
        "{{VALOR_ADIANTAMENTO}}": _moeda(orc.get("valor_adiantamento")),
        "{{VALOR_RECEBER}}": _moeda(orc.get("valor_a_receber") or orc.get("total_os")),
        "{{TOTAL_GERAL}}": _moeda(orc.get("total_os") or orc.get("valor_a_receber")),
        "{{TOTAL_OS}}": _moeda(orc.get("total_os") or orc.get("valor_a_receber"))
    }

    lista_pecas = []
    for p in orc.get("pecas", []):
        lista_pecas.append({
            "tipo": "PECA",
            "codigo": str(p.get("codigo") or "-"),
            "descricao": str(p.get("produto") or p.get("descricao") or "-"),
            "obs": str(p.get("obs") or ""),
            "qtd": float(p.get("qtd") or 1),
            "valor_unitario": float(p.get("vr_unitario") or p.get("valor") or 0),
            "valor_total": float(p.get("vr_total") or p.get("subtotal") or 0)
        })

    lista_servicos = []
    for s in orc.get("servicos", []):
        lista_servicos.append({
            "tipo": "SERVICO",
            "codigo": str(s.get("codigo") or s.get("data") or "-"),
            "descricao": str(s.get("descricao") or s.get("servico") or "-"),
            "obs": str(s.get("obs") or ""),
            "qtd": float(s.get("qtd") or 1),
            "valor_unitario": float(s.get("vr_unitario") or s.get("valor") or 0),
            "valor_total": float(s.get("vr_total") or s.get("subtotal") or 0)
        })

    itens_unificados = lista_pecas + lista_servicos

    def _injetar_itens_na_tabela(tags_gatilho, lista_dados):
        if not lista_dados:
            return
        row_idx = None
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                val = str(ws.cell(row=r, column=c).value or "")
                if any(tag in val for tag in tags_gatilho):
                    row_idx = r
                    break
            if row_idx:
                break

        if not row_idx:
            return

        row_template = []
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(row=row_idx, column=c)
            row_template.append({
                "col": c,
                "value": cell.value,
                "font": copy(cell.font),
                "fill": copy(cell.fill),
                "border": copy(cell.border),
                "alignment": copy(cell.alignment),
                "number_format": cell.number_format
            })

        if len(lista_dados) > 1:
            ws.insert_rows(row_idx + 1, amount=len(lista_dados) - 1)

        for i, item in enumerate(lista_dados):
            curr_r = row_idx + i
            for col_info in row_template:
                c = col_info["col"]
                new_cell = ws.cell(row=curr_r, column=c)
                val_tmpl = str(col_info["value"] or "")

                new_cell.font = copy(col_info["font"])
                new_cell.fill = copy(col_info["fill"])
                new_cell.border = copy(col_info["border"])
                new_cell.alignment = copy(col_info["alignment"])
                new_cell.number_format = col_info["number_format"]

                val_calc = val_tmpl
                val_calc = val_calc.replace("{{ITEM_CODIGO}}", item["codigo"]).replace("{{PECA_CODIGO}}", item["codigo"]).replace("{{SERVICO_CODIGO}}", item["codigo"])
                val_calc = val_calc.replace("{{ITEM_DESCRICAO}}", item["descricao"]).replace("{{PECA_DESCRICAO}}", item["descricao"]).replace("{{SERVICO_DESCRICAO}}", item["descricao"]).replace("{{MAO_DE_OBRA_DESCRICAO}}", item["descricao"])
                val_calc = val_calc.replace("{{ITEM_OBS}}", item["obs"]).replace("{{PECA_OBS}}", item["obs"]).replace("{{SERVICO_OBS}}", item["obs"])

                if "{{ITEM_QTD}}" in val_calc or "{{PECA_QTD}}" in val_calc or "{{SERVICO_QTD}}" in val_calc:
                    new_cell.value = item["qtd"]
                elif "{{ITEM_VALOR_UNITARIO}}" in val_calc or "{{PECA_VALOR_UNIT}}" in val_calc or "{{SERVICO_VALOR_UNIT}}" in val_calc or "{{ITEM_VR_UNITARIO}}" in val_calc:
                    new_cell.value = item["valor_unitario"]
                elif "{{ITEM_VALOR_TOTAL}}" in val_calc or "{{PECA_VALOR_TOTAL}}" in val_calc or "{{SERVICO_VALOR_TOTAL}}" in val_calc or "{{ITEM_VR_TOTAL}}" in val_calc:
                    new_cell.value = item["valor_total"]
                else:
                    new_cell.value = val_calc

    tem_pecas_especifico = False
    tem_servicos_especifico = False
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            val = str(ws.cell(row=r, column=c).value or "")
            if "{{PECA_" in val:
                tem_pecas_especifico = True
            if "{{SERVICO_" in val or "{{MAO_DE_OBRA_" in val:
                tem_servicos_especifico = True

    if tem_pecas_especifico or tem_servicos_especifico:
        if tem_pecas_especifico and lista_pecas:
            _injetar_itens_na_tabela(["{{PECA_"], lista_pecas)
        if tem_servicos_especifico and lista_servicos:
            _injetar_itens_na_tabela(["{{SERVICO_", "{{MAO_DE_OBRA_"], lista_servicos)
    else:
        if itens_unificados:
            _injetar_itens_na_tabela(["{{ITEM_"], itens_unificados)

    # Varredura para substituir todas as tags escalares
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(row=r, column=c)
            if cell.value and isinstance(cell.value, str):
                text = cell.value
                for tag, subst in mapa_tags.items():
                    if tag in text:
                        text = text.replace(tag, subst)
                if "{{" in text and "}}" in text:
                    import re
                    text = re.sub(r'\{\{[A-Z0-9_\-]+\}\}', '-', text)
                cell.value = text

    if not output_excel_path:
        pdf_dir = PUBLIC_DIR / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        output_excel_path = pdf_dir / f"Orcamento_{num_os or int(datetime.datetime.now().timestamp())}.xlsx"

    output_excel_path = Path(output_excel_path)
    output_excel_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output_excel_path))
    return str(output_excel_path)



def gerar_pdf(dados_orcamento, caminho_logo=None, output_path=None):
    """
    Gera PDF de alta fidelidade espelhando exatamente a folha da oficina
    utilizando ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
    except ImportError:
        raise RuntimeError("Biblioteca 'reportlab' não está instalada. Execute: pip install reportlab")

    if not output_path:
        pdf_dir = PUBLIC_DIR / "pdf"
        pdf_dir.mkdir(exist_ok=True)
        ts = int(datetime.datetime.now().timestamp())
        output_path = pdf_dir / f"Orcamento_{dados_orcamento.get('numero_os', ts)}.pdf"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Chaveamento Universal: Executa o preenchimento do modelo ativo do usuário (Word / Excel / PDF)
    tmpl = obter_template_ativo()
    if tmpl.get("ativo") and Path(tmpl.get("caminho", "")).exists():
        tipo = tmpl.get("tipo", "").lower()
        caminho_tmpl = str(tmpl["caminho"])
        
        # 1. Modelo em Word (.docx / .doc)
        if tipo in ["docx", "doc"]:
            try:
                from scripts.motor_documentos_universal import preencher_modelo_word, word_to_pdf_reportlab
                temp_docx = output_path.with_suffix(".temp.docx")
                preencher_modelo_word(caminho_tmpl, dados_orcamento, output_docx_path=str(temp_docx))
                word_to_pdf_reportlab(str(temp_docx), str(output_path))
                try:
                    temp_docx.unlink()
                except Exception:
                    pass
                return str(output_path)
            except Exception as e:
                print(f"[Aviso] Falha ao renderizar PDF a partir de Word: {e}. Executando fallback.", file=sys.stderr)

        # 2. Modelo em Excel (.xlsx / .xls)
        elif tipo in ["xlsx", "xls"]:
            try:
                temp_excel = output_path.with_suffix(".custom_temp.xlsx")
                preencher_modelo_customizado(caminho_tmpl, dados_orcamento, output_excel_path=str(temp_excel))
                excel_to_pdf_reportlab(str(temp_excel), str(output_path))
                try:
                    temp_excel.unlink()
                except Exception:
                    pass
                return str(output_path)
            except Exception as e:
                print(f"[Aviso] Falha ao renderizar PDF a partir de Excel: {e}. Executando fallback.", file=sys.stderr)

        # 3. Modelo em PDF (.pdf)
        elif tipo == "pdf":
            try:
                from scripts.motor_documentos_universal import preencher_modelo_pdf
                preencher_modelo_pdf(caminho_tmpl, dados_orcamento, output_pdf_path=str(output_path))
                return str(output_path)
            except Exception as e:
                print(f"[Aviso] Falha ao preencher PDF do modelo: {e}. Executando fallback.", file=sys.stderr)

    # Documento A4 com margens ajustadas de 8mm (22.6pt)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=18,
        bottomMargin=18
    )

    PAGE_W, PAGE_H = A4
    CONTENT_W = PAGE_W - 40 # 555.27 pt

    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle(
        'OrcNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=9.5,
        textColor=colors.black
    )
    style_bold = ParagraphStyle(
        'OrcBold',
        parent=style_normal,
        fontName='Helvetica-Bold'
    )
    style_small = ParagraphStyle(
        'OrcSmall',
        parent=style_normal,
        fontSize=7,
        leading=8.5
    )
    style_small_bold = ParagraphStyle(
        'OrcSmallBold',
        parent=style_bold,
        fontSize=7,
        leading=8.5
    )
    style_header_title = ParagraphStyle(
        'OrcHeaderTitle',
        parent=style_bold,
        fontSize=11,
        leading=13,
        alignment=1 # Center
    )

    story = []

    # 1. Topo: Data / Hora / Página
    data_emissao = dados_orcamento.get("data_emissao", datetime.date.today().strftime("%d/%m/%Y"))
    hora_emissao = dados_orcamento.get("hora_emissao", datetime.datetime.now().strftime("%H:%M:%S"))
    
    top_bar_data = [
        [
            Paragraph(f"Data: <b>{data_emissao}</b>&nbsp;&nbsp;&nbsp;Hora: <b>{hora_emissao}</b>", style_normal),
            Paragraph("Página: <b>1</b>", ParagraphStyle('RightPag', parent=style_normal, alignment=2))
        ]
    ]
    t_top_bar = Table(top_bar_data, colWidths=[CONTENT_W * 0.7, CONTENT_W * 0.3])
    t_top_bar.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_top_bar)
    story.append(Spacer(1, 2))

    # 2. Cabeçalho Principal (Empresa + Logo | Ordem de Serviço / Orçamento)
    empresa = dados_orcamento.get("empresa", {})
    if not empresa:
        empresa = {
            "razao_social": "AUTO CENTER MONTESSANI",
            "endereco": "RUA DANIEL DOS SANTOS VIAIS, 1021",
            "cidade_uf_bairro": "GUAIRAÇA - PR - CENTRO",
            "telefone": "(44)99113-8352",
            "cnpj": "27.140.558/0001-29"
        }

    # Busca logo
    logo_elem = Paragraph("<b>[ LOGO ]</b>", style_bold)
    logo_path = caminho_logo or (PUBLIC_DIR / "logo.jpg")
    if logo_path and Path(logo_path).exists():
        try:
            logo_elem = Image(str(logo_path), width=65, height=45)
        except:
            pass

    empresa_text = f"""<b>{empresa.get('razao_social', 'AUTO CENTER MONTESSANI')}</b><br/>
<font size="7">{empresa.get('endereco', 'RUA DANIEL DOS SANTOS VIAIS, 1021')}<br/>
{empresa.get('cidade_uf_bairro', 'GUAIRAÇA - PR - CENTRO')}<br/>
{empresa.get('telefone', '(44)99113-8352')}<br/>
{empresa.get('cnpj', '27.140.558/0001-29')}</font>"""

    col_empresa = [
        [logo_elem, Paragraph(empresa_text, style_normal)]
    ]
    t_empresa = Table(col_empresa, colWidths=[70, CONTENT_W * 0.58 - 70])
    t_empresa.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))

    num_orc = dados_orcamento.get("numero_orcamento") or f"N° {str(dados_orcamento.get('numero_os', '001.948')).zfill(6)}"
    frota = dados_orcamento.get("frota", "")
    num_os = dados_orcamento.get("numero_os", "")
    dt_entrada = dados_orcamento.get("data_entrada", data_emissao)
    dt_entrega = dados_orcamento.get("data_entrega", data_emissao)

    t_os_box = Table([
        [Paragraph(f"<b>ORDEM DE SERVIÇO / ORÇAMENTO</b><br/><b>{num_orc}</b>", style_header_title)],
        [Spacer(1, 4)],
        [Paragraph(f"<b>Frota:</b> {frota}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>OS Nº:</b> {num_os}<br/><b>Entrada:</b> {dt_entrada}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Entrega:</b> {dt_entrega}", style_normal)]
    ], colWidths=[CONTENT_W * 0.40])
    t_os_box.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    header_table_data = [
        [t_empresa, t_os_box]
    ]
    t_header = Table(header_table_data, colWidths=[CONTENT_W * 0.58, CONTENT_W * 0.42])
    t_header.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('LINEBEFORE', (1,0), (1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 4))

    # 3. Bloco do Cliente & Veículo
    cli_cod = dados_orcamento.get("cliente_codigo", "")
    cli_nome = dados_orcamento.get("cliente_nome", "")
    cli_str = f"<b>Cliente:</b> {cli_cod} - {cli_nome}" if cli_cod else f"<b>Cliente:</b> {cli_nome}"
    
    hr_ini = dados_orcamento.get("hr_inicio", "08:00")
    hr_fim = dados_orcamento.get("hr_final", "10:00")
    hr_tot = dados_orcamento.get("hr_total", "02:00")
    
    cnpj_cpf = dados_orcamento.get("cnpj_cpf", "")
    ie_rg = dados_orcamento.get("ie_rg", "")
    tel = dados_orcamento.get("telefone", "")
    contato = dados_orcamento.get("contato", "")
    endereco = dados_orcamento.get("endereco", "")
    cidade_uf = dados_orcamento.get("cidade_uf", "")
    cep = dados_orcamento.get("cep", "")
    bairro = dados_orcamento.get("bairro", "")
    veiculo = dados_orcamento.get("veiculo", "")
    fabricante = dados_orcamento.get("fabricante", "")
    placa = dados_orcamento.get("placa", "")
    km_ini = format_qtd(dados_orcamento.get("km_inicio", 0)).replace(",00", "")
    km_fim = format_qtd(dados_orcamento.get("km_final", 0)).replace(",00", "")
    km_tot = format_qtd(dados_orcamento.get("km_total", 0)).replace(",00", "")

    client_table_data = [
        [
            Paragraph(cli_str, style_normal),
            Paragraph(f"<b>Hr Inicio:</b> {hr_ini}&nbsp;&nbsp;&nbsp;<b>Hr Final:</b> {hr_fim}&nbsp;&nbsp;&nbsp;<b>Hr Total:</b> {hr_tot}", ParagraphStyle('Hr', parent=style_normal, alignment=2))
        ],
        [
            Paragraph(f"<b>CNPJ/CPF:</b> {cnpj_cpf}", style_normal),
            Paragraph(f"<b>IE/RG:</b> {ie_rg}", style_normal)
        ],
        [
            Paragraph(f"<b>Telefone:</b> {tel}", style_normal),
            Paragraph(f"<b>Contato:</b> {contato}", style_normal)
        ],
        [
            Paragraph(f"<b>Endereço:</b> {endereco}", style_normal),
            Paragraph(f"<b>Cidade/UF:</b> {cidade_uf}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>CEP:</b> {cep}", style_normal)
        ],
        [
            Paragraph(f"<b>Bairro:</b> {bairro}", style_normal),
            Paragraph("", style_normal)
        ],
        [
            Paragraph(f"<b>Veículo:</b> {veiculo}", style_normal),
            Paragraph(f"<b>Fabricante:</b> {fabricante}", style_normal)
        ],
        [
            Paragraph(f"<b>Placa:</b> {placa}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Km Inicio:</b> {km_ini}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Km Final:</b> {km_fim}", style_normal),
            Paragraph(f"<b>Km Total:</b> {km_tot}", ParagraphStyle('KmTot', parent=style_normal, alignment=2))
        ]
    ]

    t_client = Table(client_table_data, colWidths=[CONTENT_W * 0.55, CONTENT_W * 0.45])
    t_client.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_client)
    story.append(Spacer(1, 4))

    # 4. Seção: PEÇAS / PRODUTOS
    pecas_header = [
        [Paragraph("<b>PEÇAS / PRODUTOS</b>", style_bold), "", "", "", "", ""]
    ]
    pecas_cols = [
        [
            Paragraph("<b>Código</b>", style_small_bold),
            Paragraph("<b>Produto</b>", style_small_bold),
            Paragraph("<b>Obs.</b>", style_small_bold),
            Paragraph("<b>Qtde.</b>", ParagraphStyle('R1', parent=style_small_bold, alignment=2)),
            Paragraph("<b>Vr. Unitário</b>", ParagraphStyle('R2', parent=style_small_bold, alignment=2)),
            Paragraph("<b>Vr. Total</b>", ParagraphStyle('R3', parent=style_small_bold, alignment=2)),
        ]
    ]
    
    pecas_rows = []
    pecas_list = dados_orcamento.get("pecas", [])
    subtotal_pecas = float(dados_orcamento.get("subtotal_pecas") or dados_orcamento.get("valor_pecas") or 0.0)

    if pecas_list:
        for p in pecas_list:
            pecas_rows.append([
                Paragraph(str(p.get("codigo", "")), style_small),
                Paragraph(str(p.get("produto", "")), style_small),
                Paragraph(str(p.get("obs", "")), style_small),
                Paragraph(format_qtd(p.get("qtd", 1)), ParagraphStyle('RQ', parent=style_small, alignment=2)),
                Paragraph(format_moeda(p.get("vr_unitario", 0)), ParagraphStyle('RU', parent=style_small, alignment=2)),
                Paragraph(format_moeda(p.get("vr_total", 0)), ParagraphStyle('RT', parent=style_small, alignment=2)),
            ])
    else:
        pecas_rows.append([
            Paragraph("-", style_small),
            Paragraph("NENHUMA PEÇA REGISTRADA", style_small),
            Paragraph("", style_small),
            Paragraph("0,00", ParagraphStyle('RQ', parent=style_small, alignment=2)),
            Paragraph("0,00", ParagraphStyle('RU', parent=style_small, alignment=2)),
            Paragraph("0,00", ParagraphStyle('RT', parent=style_small, alignment=2)),
        ])

    pecas_subtotal_row = [
        [
            Paragraph("<b>Sub-Total</b>", style_bold),
            "", "", "", "",
            Paragraph(f"<b>R$ {format_moeda(subtotal_pecas)}</b>", ParagraphStyle('RSub', parent=style_bold, alignment=2))
        ]
    ]

    pecas_data = pecas_header + pecas_cols + pecas_rows + pecas_subtotal_row
    col_w_pecas = [45, 230, 80, 50, 75, 75.27]

    t_pecas = Table(pecas_data, colWidths=col_w_pecas)
    t_pecas.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('SPAN', (0,0), (5,0)),
        ('BACKGROUND', (0,0), (5,0), colors.HexColor("#EAEAEA")),
        ('BACKGROUND', (0,1), (5,1), colors.HexColor("#F2F2F2")),
        ('SPAN', (0, len(pecas_data)-1), (4, len(pecas_data)-1)),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEBELOW', (0,1), (-1,1), 0.5, colors.black),
        ('LINEABOVE', (0, len(pecas_data)-1), (-1, len(pecas_data)-1), 0.5, colors.black),
        ('INNERGRID', (0,1), (-1,-2), 0.25, colors.HexColor("#D0D0D0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_pecas)
    story.append(Spacer(1, 4))

    # 5. Seção: MÃO DE OBRA
    servicos_header = [
        [Paragraph("<b>MÃO DE OBRA</b>", style_bold), "", "", "", "", "", ""]
    ]
    servicos_cols = [
        [
            Paragraph("<b>Data</b>", style_small_bold),
            Paragraph("<b>Serviço</b>", style_small_bold),
            Paragraph("<b>Descrição</b>", style_small_bold),
            Paragraph("<b>Obs.</b>", style_small_bold),
            Paragraph("<b>Qtde.</b>", ParagraphStyle('R1', parent=style_small_bold, alignment=2)),
            Paragraph("<b>Vr. Unitário</b>", ParagraphStyle('R2', parent=style_small_bold, alignment=2)),
            Paragraph("<b>Vr. Total</b>", ParagraphStyle('R3', parent=style_small_bold, alignment=2)),
        ]
    ]

    servicos_rows = []
    servicos_list = dados_orcamento.get("servicos", [])
    subtotal_servicos = float(dados_orcamento.get("subtotal_servicos") or dados_orcamento.get("valor_mao_obra") or 0.0)

    if servicos_list:
        for s in servicos_list:
            servicos_rows.append([
                Paragraph(str(s.get("data", data_emissao)), style_small),
                Paragraph(str(s.get("servico", "MAO DE OBRA")), style_small),
                Paragraph(str(s.get("descricao", "")), style_small),
                Paragraph(str(s.get("obs", "")), style_small),
                Paragraph(format_qtd(s.get("qtd", 1)), ParagraphStyle('RQ', parent=style_small, alignment=2)),
                Paragraph(format_moeda(s.get("vr_unitario", 0)), ParagraphStyle('RU', parent=style_small, alignment=2)),
                Paragraph(format_moeda(s.get("vr_total", 0)), ParagraphStyle('RT', parent=style_small, alignment=2)),
            ])
    else:
        servicos_rows.append([
            Paragraph(data_emissao, style_small),
            Paragraph("MAO DE OBRA", style_small),
            Paragraph("SERVIÇOS TÉCNICOS EFETUADOS", style_small),
            Paragraph("", style_small),
            Paragraph("1,00", ParagraphStyle('RQ', parent=style_small, alignment=2)),
            Paragraph("0,00", ParagraphStyle('RU', parent=style_small, alignment=2)),
            Paragraph("0,00", ParagraphStyle('RT', parent=style_small, alignment=2)),
        ])

    servicos_subtotal_row = [
        [
            Paragraph("<b>Sub-Total</b>", style_bold),
            "", "", "", "", "",
            Paragraph(f"<b>R$ {format_moeda(subtotal_servicos)}</b>", ParagraphStyle('RSub', parent=style_bold, alignment=2))
        ]
    ]

    servicos_data = servicos_header + servicos_cols + servicos_rows + servicos_subtotal_row
    col_w_servicos = [52, 75, 175, 53, 50, 75, 75.27]

    t_servicos = Table(servicos_data, colWidths=col_w_servicos)
    t_servicos.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('SPAN', (0,0), (6,0)),
        ('BACKGROUND', (0,0), (6,0), colors.HexColor("#EAEAEA")),
        ('BACKGROUND', (0,1), (6,1), colors.HexColor("#F2F2F2")),
        ('SPAN', (0, len(servicos_data)-1), (5, len(servicos_data)-1)),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('LINEBELOW', (0,1), (-1,1), 0.5, colors.black),
        ('LINEABOVE', (0, len(servicos_data)-1), (-1, len(servicos_data)-1), 0.5, colors.black),
        ('INNERGRID', (0,1), (-1,-2), 0.25, colors.HexColor("#D0D0D0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_servicos)
    story.append(Spacer(1, 4))

    # 6. Seção: INFORMAÇÕES AO CLIENTE
    info_cli_text = dados_orcamento.get("informacoes_cliente") or "SERVIÇO REALIZADO CONFORME SOLICITAÇÃO E AUTORIZAÇÃO DO CLIENTE."
    info_data = [
        [Paragraph("<b>INFORMAÇÕES AO CLIENTE</b>", style_bold)],
        [Paragraph(info_cli_text.replace("\n", "<br/>"), style_small)]
    ]
    t_info = Table(info_data, colWidths=[CONTENT_W])
    t_info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#EAEAEA")),
        ('LINEBELOW', (0,0), (0,0), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 4))

    # 7. Resumo Financeiro & Assinaturas (Quadro Inferior)
    vl_pecas = float(dados_orcamento.get("valor_pecas", subtotal_pecas))
    vl_mo = float(dados_orcamento.get("valor_mao_obra", subtotal_servicos))
    vl_terc = float(dados_orcamento.get("valor_terceiros", 0.0))
    vl_subtotal = float(dados_orcamento.get("subtotal_geral", (vl_pecas + vl_mo + vl_terc)))
    desc_pecas = float(dados_orcamento.get("desconto_pecas", 0.0))
    desc_mo = float(dados_orcamento.get("desconto_mao_obra", 0.0))
    desc_fat = float(dados_orcamento.get("desconto_faturamento", 0.0))
    vl_adiant = float(dados_orcamento.get("valor_adiantamento", 0.0))
    vl_receber = float(dados_orcamento.get("valor_a_receber", (vl_subtotal - desc_pecas - desc_mo - desc_fat - vl_adiant)))
    total_os = float(dados_orcamento.get("total_os", vl_receber))

    fin_left_data = [
        [Paragraph("(+)VALOR DAS PEÇAS........................................:", style_small), Paragraph(format_moeda(vl_pecas), ParagraphStyle('FR', parent=style_small_bold, alignment=2))],
        [Paragraph("(+)VALOR DA MÃO-DE-OBRA...................................:", style_small), Paragraph(format_moeda(vl_mo), ParagraphStyle('FR', parent=style_small_bold, alignment=2))],
        [Paragraph("(+)VALOR DO SERVIÇO DE TERCEIRO...........................:", style_small), Paragraph(format_moeda(vl_terc), ParagraphStyle('FR', parent=style_small_bold, alignment=2))],
        [Paragraph("(=)SUB-TOTAL..............................................:", style_small_bold), Paragraph(format_moeda(vl_subtotal), ParagraphStyle('FR', parent=style_small_bold, alignment=2))],
        [Paragraph("(-) DESCONTO PEÇAS........................................:", style_small), Paragraph(format_moeda(desc_pecas), ParagraphStyle('FR', parent=style_small_bold, alignment=2))],
        [Paragraph("(-) DESCONTO MÃO-DE-OBRA..................................:", style_small), Paragraph(format_moeda(desc_mo), ParagraphStyle('FR', parent=style_small_bold, alignment=2))],
        [Paragraph("(-) DESCONTO FATURAMENTO..................................:", style_small), Paragraph(format_moeda(desc_fat), ParagraphStyle('FR', parent=style_small_bold, alignment=2))],
        [Paragraph("(-)VALOR ADIANTAMENTO.....................................:", style_small), Paragraph(format_moeda(vl_adiant), ParagraphStyle('FR', parent=style_small_bold, alignment=2))],
        [Paragraph("<b>(=)VALOR À RECEBER.......................................:</b>", style_bold), Paragraph(f"<b>{format_moeda(vl_receber)}</b>", ParagraphStyle('FRB', parent=style_bold, alignment=2))],
    ]
    t_fin_left = Table(fin_left_data, colWidths=[200, 65])
    t_fin_left.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))

    fin_right_text = f"""
<para align="center">
<font size="12"><b>TOTAL DA O.S.: &nbsp;&nbsp;&nbsp;&nbsp; R$ {format_moeda(total_os)}</b></font>
<br/><br/><br/><br/>
_____________________________________________
<br/>
<font size="8">Assinatura do Cliente / Responsável</font>
</para>
"""
    t_fin_right = Paragraph(fin_right_text, style_normal)

    bottom_box_data = [
        [t_fin_left, t_fin_right]
    ]
    t_bottom = Table(bottom_box_data, colWidths=[CONTENT_W * 0.52, CONTENT_W * 0.48])
    t_bottom.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(KeepTogether([t_bottom]))

    # Constrói o PDF
    doc.build(story)
    return str(output_path)


def gerar_excel(dados_orcamento, output_path=None):
    """
    Gera planilha Excel (.xlsx) altamente profissional e formatada
    com fórmulas dinâmicas para soma de totais, subtotais e descontos.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise RuntimeError("Biblioteca 'openpyxl' não está instalada. Execute: pip install openpyxl")

    if not output_path:
        pdf_dir = PUBLIC_DIR / "pdf"
        pdf_dir.mkdir(exist_ok=True)
        ts = int(datetime.datetime.now().timestamp())
        output_path = pdf_dir / f"Orcamento_{dados_orcamento.get('numero_os', ts)}.xlsx"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Chaveamento Universal: Se houver modelo Excel ativo, preenche na íntegra
    tmpl = obter_template_ativo()
    if tmpl.get("ativo") and tmpl.get("tipo") in ["xlsx", "xls"] and Path(tmpl.get("caminho", "")).exists():
        try:
            preencher_modelo_customizado(tmpl["caminho"], dados_orcamento, output_excel_path=str(output_path))
            return str(output_path)
        except Exception as e:
            print(f"[Aviso] Falha ao preencher modelo customizado no Excel: {e}. Executando fallback para o modelo padrão.", file=sys.stderr)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orçamento e O.S."
    ws.views.sheetView[0].showGridLines = True

    # Paleta de Estilos
    font_header_empresa = Font(name="Arial", size=11, bold=True, color="000000")
    font_empresa_sub = Font(name="Arial", size=8, color="333333")
    font_title_os = Font(name="Arial", size=12, bold=True, color="000000")
    font_section_title = Font(name="Arial", size=9, bold=True, color="000000")
    font_col_header = Font(name="Arial", size=8, bold=True, color="000000")
    font_cell = Font(name="Arial", size=8, color="000000")
    font_cell_bold = Font(name="Arial", size=8, bold=True, color="000000")
    font_total = Font(name="Arial", size=11, bold=True, color="000000")

    fill_section = PatternFill(start_color="EAEAEA", end_color="EAEAEA", fill_type="solid")
    fill_col = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
    fill_subtotal = PatternFill(start_color="F0F4F8", end_color="F0F4F8", fill_type="solid")

    thin_border_side = Side(style="thin", color="000000")
    thick_border_side = Side(style="medium", color="000000")
    double_border_side = Side(style="double", color="000000")

    border_box = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_bottom_only = Border(bottom=thin_border_side)

    # 1. Topo: Data / Hora / Página
    data_emissao = dados_orcamento.get("data_emissao", datetime.date.today().strftime("%d/%m/%Y"))
    hora_emissao = dados_orcamento.get("hora_emissao", datetime.datetime.now().strftime("%H:%M:%S"))
    ws.merge_cells("A1:D1")
    ws["A1"] = f"Data: {data_emissao}    Hora: {hora_emissao}"
    ws["A1"].font = font_cell_bold
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells("E1:G1")
    ws["E1"] = "Página: 1"
    ws["E1"].font = font_cell_bold
    ws["E1"].alignment = Alignment(horizontal="right", vertical="center")

    # 2. Cabeçalho Empresa e O.S.
    empresa = dados_orcamento.get("empresa", {})
    if not empresa:
        empresa = {
            "razao_social": "AUTO CENTER MONTESSANI",
            "endereco": "RUA DANIEL DOS SANTOS VIAIS, 1021",
            "cidade_uf_bairro": "GUAIRAÇA - PR - CENTRO",
            "telefone": "(44)99113-8352",
            "cnpj": "27.140.558/0001-29"
        }

    ws.merge_cells("A2:D2")
    ws["A2"] = empresa.get("razao_social", "AUTO CENTER MONTESSANI")
    ws["A2"].font = font_header_empresa

    ws.merge_cells("A3:D3")
    ws["A3"] = empresa.get("endereco", "")
    ws["A3"].font = font_empresa_sub

    ws.merge_cells("A4:D4")
    ws["A4"] = empresa.get("cidade_uf_bairro", "")
    ws["A4"].font = font_empresa_sub

    ws.merge_cells("A5:D5")
    ws["A5"] = f"Tel: {empresa.get('telefone', '')} | CNPJ: {empresa.get('cnpj', '')}"
    ws["A5"].font = font_empresa_sub

    num_orc = dados_orcamento.get("numero_orcamento") or f"N° {str(dados_orcamento.get('numero_os', '001.948')).zfill(6)}"
    ws.merge_cells("E2:G2")
    ws["E2"] = "ORDEM DE SERVIÇO / ORÇAMENTO"
    ws["E2"].font = font_title_os
    ws["E2"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("E3:G3")
    ws["E3"] = num_orc
    ws["E3"].font = font_title_os
    ws["E3"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("E4:G4")
    ws["E4"] = f"Frota: {dados_orcamento.get('frota', '')}          OS N°: {dados_orcamento.get('numero_os', '')}"
    ws["E4"].font = font_cell_bold
    ws["E4"].alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("E5:G5")
    ws["E5"] = f"Entrada: {dados_orcamento.get('data_entrada', data_emissao)}    Entrega: {dados_orcamento.get('data_entrega', data_emissao)}"
    ws["E5"].font = font_cell_bold
    ws["E5"].alignment = Alignment(horizontal="center", vertical="center")

    # Aplica borda ao cabeçalho (A2:G5)
    for r in range(2, 6):
        for c in range(1, 8):
            ws.cell(row=r, column=c).border = border_box

    # 3. Bloco do Cliente & Veículo
    row_idx = 7
    cli_str = f"Cliente: {dados_orcamento.get('cliente_codigo', '')} - {dados_orcamento.get('cliente_nome', '')}"
    hr_str = f"Hr Inicio: {dados_orcamento.get('hr_inicio', '08:00')}   Hr Final: {dados_orcamento.get('hr_final', '10:00')}   Hr Total: {dados_orcamento.get('hr_total', '02:00')}"
    
    ws.merge_cells(f"A{row_idx}:D{row_idx}")
    ws[f"A{row_idx}"] = cli_str
    ws[f"A{row_idx}"].font = font_cell_bold

    ws.merge_cells(f"E{row_idx}:G{row_idx}")
    ws[f"E{row_idx}"] = hr_str
    ws[f"E{row_idx}"].font = font_cell_bold
    ws[f"E{row_idx}"].alignment = Alignment(horizontal="right")

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:D{row_idx}")
    ws[f"A{row_idx}"] = f"CNPJ/CPF: {dados_orcamento.get('cnpj_cpf', '')}"
    ws[f"A{row_idx}"].font = font_cell

    ws.merge_cells(f"E{row_idx}:G{row_idx}")
    ws[f"E{row_idx}"] = f"IE/RG: {dados_orcamento.get('ie_rg', '')}"
    ws[f"E{row_idx}"].font = font_cell

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:D{row_idx}")
    ws[f"A{row_idx}"] = f"Telefone: {dados_orcamento.get('telefone', '')}"
    ws[f"A{row_idx}"].font = font_cell

    ws.merge_cells(f"E{row_idx}:G{row_idx}")
    ws[f"E{row_idx}"] = f"Contato: {dados_orcamento.get('contato', '')}"
    ws[f"E{row_idx}"].font = font_cell

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:D{row_idx}")
    ws[f"A{row_idx}"] = f"Endereço: {dados_orcamento.get('endereco', '')}"
    ws[f"A{row_idx}"].font = font_cell

    ws.merge_cells(f"E{row_idx}:G{row_idx}")
    ws[f"E{row_idx}"] = f"Cidade/UF: {dados_orcamento.get('cidade_uf', '')}    CEP: {dados_orcamento.get('cep', '')}"
    ws[f"E{row_idx}"].font = font_cell

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:D{row_idx}")
    ws[f"A{row_idx}"] = f"Bairro: {dados_orcamento.get('bairro', '')}"
    ws[f"A{row_idx}"].font = font_cell

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:D{row_idx}")
    ws[f"A{row_idx}"] = f"Veículo: {dados_orcamento.get('veiculo', '')}"
    ws[f"A{row_idx}"].font = font_cell

    ws.merge_cells(f"E{row_idx}:G{row_idx}")
    ws[f"E{row_idx}"] = f"Fabricante: {dados_orcamento.get('fabricante', '')}"
    ws[f"E{row_idx}"].font = font_cell

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:D{row_idx}")
    km_ini = format_qtd(dados_orcamento.get("km_inicio", 0)).replace(",00", "")
    km_fim = format_qtd(dados_orcamento.get("km_final", 0)).replace(",00", "")
    km_tot = format_qtd(dados_orcamento.get("km_total", 0)).replace(",00", "")
    ws[f"A{row_idx}"] = f"Placa: {dados_orcamento.get('placa', '')}    Km Inicio: {km_ini}    Km Final: {km_fim}"
    ws[f"A{row_idx}"].font = font_cell

    ws.merge_cells(f"E{row_idx}:G{row_idx}")
    ws[f"E{row_idx}"] = f"Km Total: {km_tot}"
    ws[f"E{row_idx}"].font = font_cell_bold
    ws[f"E{row_idx}"].alignment = Alignment(horizontal="right")

    for r in range(7, row_idx + 1):
        for c in range(1, 8):
            ws.cell(row=r, column=c).border = border_box

    # 4. Tabela de Peças / Produtos
    row_idx += 2
    ws.merge_cells(f"A{row_idx}:G{row_idx}")
    ws[f"A{row_idx}"] = "PEÇAS / PRODUTOS"
    ws[f"A{row_idx}"].font = font_section_title
    ws[f"A{row_idx}"].fill = fill_section

    row_idx += 1
    headers_pecas = ["Código", "Descrição do Produto", "Obs.", "Qtde.", "Vr. Unitário", "Vr. Total"]
    ws[f"A{row_idx}"] = "Código"
    ws.merge_cells(f"B{row_idx}:C{row_idx}")
    ws[f"B{row_idx}"] = "Descrição do Produto"
    ws[f"D{row_idx}"] = "Obs."
    ws[f"E{row_idx}"] = "Qtde."
    ws[f"F{row_idx}"] = "Vr. Unitário"
    ws[f"G{row_idx}"] = "Vr. Total"

    for c in range(1, 8):
        cell = ws.cell(row=row_idx, column=c)
        cell.font = font_col_header
        cell.fill = fill_col
        cell.border = border_box

    pecas_start_row = row_idx + 1
    pecas = dados_orcamento.get("pecas", [])
    if not pecas:
        pecas = [{"codigo": "-", "produto": "NENHUMA PEÇA REGISTRADA", "obs": "", "qtd": 0, "vr_unitario": 0, "vr_total": 0}]

    for p in pecas:
        row_idx += 1
        ws[f"A{row_idx}"] = str(p.get("codigo", ""))
        ws.merge_cells(f"B{row_idx}:C{row_idx}")
        ws[f"B{row_idx}"] = str(p.get("produto", ""))
        ws[f"D{row_idx}"] = str(p.get("obs", ""))
        ws[f"E{row_idx}"] = float(p.get("qtd", 1))
        ws[f"F{row_idx}"] = float(p.get("vr_unitario", 0))
        # Fórmula Excel: Qtde * Vr. Unitário
        ws[f"G{row_idx}"] = f"=E{row_idx}*F{row_idx}"

        for c in range(1, 8):
            cell = ws.cell(row=row_idx, column=c)
            cell.font = font_cell
            cell.border = border_box
        ws[f"E{row_idx}"].number_format = '#,##0.00'
        ws[f"F{row_idx}"].number_format = 'R$ #,##0.00'
        ws[f"G{row_idx}"].number_format = 'R$ #,##0.00'

    pecas_end_row = row_idx
    row_idx += 1
    ws.merge_cells(f"A{row_idx}:F{row_idx}")
    ws[f"A{row_idx}"] = "Sub-Total Peças"
    ws[f"A{row_idx}"].font = font_cell_bold
    ws[f"A{row_idx}"].alignment = Alignment(horizontal="right")
    ws[f"A{row_idx}"].fill = fill_subtotal

    # Fórmula de Soma das Peças
    ws[f"G{row_idx}"] = f"=SUM(G{pecas_start_row}:G{pecas_end_row})"
    ws[f"G{row_idx}"].font = font_cell_bold
    ws[f"G{row_idx}"].fill = fill_subtotal
    ws[f"G{row_idx}"].number_format = 'R$ #,##0.00'

    for c in range(1, 8):
        ws.cell(row=row_idx, column=c).border = border_box
    cell_subtotal_pecas = f"G{row_idx}"

    # 5. Tabela de Mão de Obra / Serviços
    row_idx += 2
    ws.merge_cells(f"A{row_idx}:G{row_idx}")
    ws[f"A{row_idx}"] = "MÃO DE OBRA / SERVIÇOS"
    ws[f"A{row_idx}"].font = font_section_title
    ws[f"A{row_idx}"].fill = fill_section

    row_idx += 1
    ws[f"A{row_idx}"] = "Data"
    ws[f"B{row_idx}"] = "Serviço"
    ws[f"C{row_idx}"] = "Descrição Detalhada"
    ws[f"D{row_idx}"] = "Obs."
    ws[f"E{row_idx}"] = "Qtde."
    ws[f"F{row_idx}"] = "Vr. Unitário"
    ws[f"G{row_idx}"] = "Vr. Total"

    for c in range(1, 8):
        cell = ws.cell(row=row_idx, column=c)
        cell.font = font_col_header
        cell.fill = fill_col
        cell.border = border_box

    servicos_start_row = row_idx + 1
    servicos = dados_orcamento.get("servicos", [])
    if not servicos:
        servicos = [{"data": data_emissao, "servico": "MAO DE OBRA", "descricao": "SERVIÇOS TÉCNICOS EFETUADOS", "obs": "", "qtd": 1, "vr_unitario": 0, "vr_total": 0}]

    for s in servicos:
        row_idx += 1
        ws[f"A{row_idx}"] = str(s.get("data", data_emissao))
        ws[f"B{row_idx}"] = str(s.get("servico", "MAO DE OBRA"))
        ws[f"C{row_idx}"] = str(s.get("descricao", ""))
        ws[f"D{row_idx}"] = str(s.get("obs", ""))
        ws[f"E{row_idx}"] = float(s.get("qtd", 1))
        ws[f"F{row_idx}"] = float(s.get("vr_unitario", 0))
        # Fórmula Excel: Qtde * Vr. Unitário
        ws[f"G{row_idx}"] = f"=E{row_idx}*F{row_idx}"

        for c in range(1, 8):
            cell = ws.cell(row=row_idx, column=c)
            cell.font = font_cell
            cell.border = border_box
        ws[f"E{row_idx}"].number_format = '#,##0.00'
        ws[f"F{row_idx}"].number_format = 'R$ #,##0.00'
        ws[f"G{row_idx}"].number_format = 'R$ #,##0.00'

    servicos_end_row = row_idx
    row_idx += 1
    ws.merge_cells(f"A{row_idx}:F{row_idx}")
    ws[f"A{row_idx}"] = "Sub-Total Mão de Obra"
    ws[f"A{row_idx}"].font = font_cell_bold
    ws[f"A{row_idx}"].alignment = Alignment(horizontal="right")
    ws[f"A{row_idx}"].fill = fill_subtotal

    # Fórmula de Soma dos Serviços
    ws[f"G{row_idx}"] = f"=SUM(G{servicos_start_row}:G{servicos_end_row})"
    ws[f"G{row_idx}"].font = font_cell_bold
    ws[f"G{row_idx}"].fill = fill_subtotal
    ws[f"G{row_idx}"].number_format = 'R$ #,##0.00'

    for c in range(1, 8):
        ws.cell(row=row_idx, column=c).border = border_box
    cell_subtotal_servicos = f"G{row_idx}"

    # 6. Informações ao Cliente
    row_idx += 2
    ws.merge_cells(f"A{row_idx}:G{row_idx}")
    ws[f"A{row_idx}"] = "INFORMAÇÕES AO CLIENTE / OBSERVAÇÕES"
    ws[f"A{row_idx}"].font = font_section_title
    ws[f"A{row_idx}"].fill = fill_section

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:G{row_idx+1}")
    info_text = dados_orcamento.get("informacoes_cliente") or "SERVIÇO REALIZADO CONFORME SOLICITAÇÃO E AUTORIZAÇÃO DO CLIENTE."
    ws[f"A{row_idx}"] = info_text
    ws[f"A{row_idx}"].font = font_cell
    ws[f"A{row_idx}"].alignment = Alignment(vertical="top", wrap_text=True)

    for r in range(row_idx - 1, row_idx + 2):
        for c in range(1, 8):
            ws.cell(row=r, column=c).border = border_box

    row_idx += 2

    # 7. Resumo Financeiro & Totais (Com Fórmulas de Soma e Subtração)
    fin_start = row_idx
    
    # Linha 1: Peças
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "(+) VALOR DAS PEÇAS"
    ws[f"D{row_idx}"] = f"={cell_subtotal_pecas}"
    ws[f"D{row_idx}"].number_format = 'R$ #,##0.00'
    cell_vl_pecas = f"D{row_idx}"

    # Bloco direito: TOTAL DA O.S.
    ws.merge_cells(f"E{row_idx}:G{row_idx+1}")
    ws[f"E{row_idx}"] = "TOTAL DA O.S."
    ws[f"E{row_idx}"].font = font_title_os
    ws[f"E{row_idx}"].alignment = Alignment(horizontal="center", vertical="center")
    ws[f"E{row_idx}"].fill = fill_section

    row_idx += 1
    # Linha 2: Mão de Obra
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "(+) VALOR DA MÃO-DE-OBRA"
    ws[f"D{row_idx}"] = f"={cell_subtotal_servicos}"
    ws[f"D{row_idx}"].number_format = 'R$ #,##0.00'
    cell_vl_mo = f"D{row_idx}"

    row_idx += 1
    # Linha 3: Serviços de Terceiros
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "(+) VALOR DO SERVIÇO DE TERCEIRO"
    ws[f"D{row_idx}"] = float(dados_orcamento.get("valor_terceiros", 0.0))
    ws[f"D{row_idx}"].number_format = 'R$ #,##0.00'
    cell_vl_terc = f"D{row_idx}"

    # Bloco direito: VALOR TOTAL FINAL (FÓRMULA)
    ws.merge_cells(f"E{row_idx}:G{row_idx+1}")

    row_idx += 1
    # Linha 4: Subtotal Geral
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "(=) SUB-TOTAL GERAL"
    ws[f"A{row_idx}"].font = font_cell_bold
    ws[f"D{row_idx}"] = f"=SUM({cell_vl_pecas}:{cell_vl_terc})"
    ws[f"D{row_idx}"].font = font_cell_bold
    ws[f"D{row_idx}"].number_format = 'R$ #,##0.00'
    cell_subtotal_geral = f"D{row_idx}"

    row_idx += 1
    # Linha 5: Descontos
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "(-) DESCONTO PEÇAS"
    ws[f"D{row_idx}"] = float(dados_orcamento.get("desconto_pecas", 0.0))
    ws[f"D{row_idx}"].number_format = 'R$ #,##0.00'
    cell_d_pecas = f"D{row_idx}"

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "(-) DESCONTO MÃO-DE-OBRA"
    ws[f"D{row_idx}"] = float(dados_orcamento.get("desconto_mao_obra", 0.0))
    ws[f"D{row_idx}"].number_format = 'R$ #,##0.00'
    cell_d_mo = f"D{row_idx}"

    row_idx += 1
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "(-) VALOR ADIANTAMENTO"
    ws[f"D{row_idx}"] = float(dados_orcamento.get("valor_adiantamento", 0.0))
    ws[f"D{row_idx}"].number_format = 'R$ #,##0.00'
    cell_adiant = f"D{row_idx}"

    row_idx += 1
    # Linha 8: VALOR A RECEBER
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    ws[f"A{row_idx}"] = "(=) VALOR A RECEBER / TOTAL"
    ws[f"A{row_idx}"].font = font_section_title
    ws[f"A{row_idx}"].fill = fill_section
    ws[f"D{row_idx}"] = f"={cell_subtotal_geral}-{cell_d_pecas}-{cell_d_mo}-{cell_adiant}"
    ws[f"D{row_idx}"].font = font_section_title
    ws[f"D{row_idx}"].fill = fill_section
    ws[f"D{row_idx}"].number_format = 'R$ #,##0.00'
    cell_final_total = f"D{row_idx}"

    # Atribui o total ao bloco da direita
    ws[f"E{fin_start+2}"] = f"={cell_final_total}"
    ws[f"E{fin_start+2}"].font = font_title_os
    ws[f"E{fin_start+2}"].alignment = Alignment(horizontal="center", vertical="center")
    ws[f"E{fin_start+2}"].number_format = 'R$ #,##0.00'

    # Bloco de Assinatura
    ws.merge_cells(f"E{row_idx-1}:G{row_idx}")
    ws[f"E{row_idx-1}"] = "______________________________\nAssinatura do Cliente / Responsável"
    ws[f"E{row_idx-1}"].font = font_cell
    ws[f"E{row_idx-1}"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for r in range(fin_start, row_idx + 1):
        for c in range(1, 8):
            ws.cell(row=r, column=c).border = border_box

    # Ajuste de Largura das Colunas
    column_widths = {
        "A": 14,
        "B": 22,
        "C": 35,
        "D": 15,
        "E": 12,
        "F": 15,
        "G": 16
    }
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    wb.save(str(output_path))
    return str(output_path)




def gerar_word(dados_orcamento, output_path=None):
    """
    Gera documento Word (.docx) preenchido a partir do modelo do usuário
    ou a partir do layout padrão do sistema.
    """
    from scripts.motor_documentos_universal import preencher_modelo_word
    
    if not output_path:
        pdf_dir = PUBLIC_DIR / "pdf"
        pdf_dir.mkdir(exist_ok=True)
        ts = int(datetime.datetime.now().timestamp())
        output_path = pdf_dir / f"Orcamento_{dados_orcamento.get('numero_os', ts)}.docx"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tmpl = obter_template_ativo()
    if tmpl.get("ativo") and tmpl.get("tipo") in ["docx", "doc"] and Path(tmpl.get("caminho", "")).exists():
        return preencher_modelo_word(tmpl["caminho"], dados_orcamento, output_docx_path=str(output_path))

    # Se não houver template Word do usuário, cria a partir do modelo padrão
    import docx
    doc = docx.Document()
    doc.add_heading(f"ORDEM DE SERVIÇO / ORÇAMENTO - OS Nº {dados_orcamento.get('numero_os', '')}", level=1)
    doc.add_paragraph(f"Cliente: {dados_orcamento.get('cliente_nome', '-')}")
    doc.add_paragraph(f"Veículo / Equipamento: {dados_orcamento.get('veiculo', '-')} | Frota: {dados_orcamento.get('frota', '-')}")
    doc.add_paragraph(f"Diagnóstico: {dados_orcamento.get('informacoes_cliente', '-')}")
    
    # Tabela
    pecas = dados_orcamento.get("pecas") or []
    servicos = dados_orcamento.get("servicos") or []
    table = doc.add_table(rows=1, cols=4)
    hdr = table.rows[0].cells
    hdr[0].text = "Código"
    hdr[1].text = "Descrição"
    hdr[2].text = "Qtd"
    hdr[3].text = "Valor Total"
    
    for p in pecas:
        r = table.add_row().cells
        r[0].text = str(p.get("codigo") or "-")
        r[1].text = str(p.get("produto") or "")
        r[2].text = str(p.get("qtd") or 0)
        r[3].text = f"R$ {float(p.get('vr_total') or 0):,.2f}"

    for s in servicos:
        r = table.add_row().cells
        r[0].text = "-"
        r[1].text = str(s.get("descricao") or s.get("servico") or "")
        r[2].text = str(s.get("qtd") or 0)
        r[3].text = f"R$ {float(s.get('vr_total') or 0):,.2f}"

    doc.add_paragraph(f"Total Geral da O.S.: R$ {float(dados_orcamento.get('total_os') or dados_orcamento.get('valor_a_receber') or 0):,.2f}")
    doc.save(str(output_path))
    return str(output_path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gerenciador de Orçamentos e Ordens de Serviço")
    parser.add_argument("--buscar", help="Número da OS para buscar")
    parser.add_argument("--pdf", help="Caminho do JSON com dados ou gera exemplo", action="store_true")
    parser.add_argument("--excel", help="Caminho do JSON com dados ou gera exemplo", action="store_true")
    parser.add_argument("--data", help="Arquivo JSON de entrada")
    parser.add_argument("--logo", help="Caminho do logotipo")
    parser.add_argument("--out", help="Arquivo de saída")
    args = parser.parse_args()

    if args.buscar:
        res = buscar_dados_os(args.buscar)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0)

    dados = None
    if args.data and Path(args.data).exists():
        with open(args.data, "r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        # Pega a primeira OS disponível ou dados padrão
        busca = buscar_dados_os("133774")
        dados = busca.get("orcamento", {})
        dados["empresa"] = busca.get("empresa", {})

    if args.pdf:
        out = gerar_pdf(dados, caminho_logo=args.logo, output_path=args.out)
        print(f"[OK] PDF gerado com sucesso: {out}")

    if args.excel:
        out = gerar_excel(dados, output_path=args.out)
        print(f"[OK] Excel gerado com sucesso: {out}")
