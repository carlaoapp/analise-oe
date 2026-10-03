#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de extração inteligente de dados de Ordem de Serviço a partir
de mensagens de texto do WhatsApp da oficina/campo.

Suporta extração baseada em template específico do remetente (quando disponível)
com fallback automático para regex genérico.
"""

import re
import json


def limpar_prefixo_titulo(valor: str) -> str:
    """Remove prefixos comuns como 'Sr.', 'Sra.', etc."""
    if not valor:
        return ""
    val = re.sub(r'^(?:Sr\.?|Sra\.?|Dr\.?|Eng\.?)\s*', '', valor.strip(), flags=re.IGNORECASE)
    return val.strip()


def formatar_fazenda(nome_fazenda: str) -> str:
    """Padroniza o nome da fazenda ou local."""
    if not nome_fazenda:
        return ""
    limpo = nome_fazenda.strip()
    limpo = re.sub(r'^[:\-]\s*', '', limpo).strip()
    if not re.search(r'^(?:Fazenda|Sítio|Sitio|Estância|Estancia|Chácara|Chacara|Garagem|Oficina)\b', limpo, re.IGNORECASE):
        limpo = f"Fazenda {limpo}"
    return limpo.strip()


def _extrair_campos_por_template(texto: str, template: str) -> dict:
    """
    Tenta extrair campos da OS usando o template de mensagem do remetente.
    O template funciona como guia estrutural: cada linha não-vazia do template
    gera um padrão de busca que é aplicado à mensagem real.
    
    Retorna um dict com os campos encontrados (ou strings vazias para não encontrados).
    """
    resultado = {
        "frota": "", "numero_os": "", "fazenda": "",
        "solicitante": "", "responsavel": "", "diagnostico": ""
    }

    linhas_template = [l.strip() for l in template.splitlines() if l.strip()]
    linhas_msg = [l.strip() for l in texto.splitlines() if l.strip()]

    # Tenta identificar o padrão de cada linha do template e extrai da mensagem
    for linha_tpl in linhas_template:
        # Frota
        if re.search(r'\bfrota\b', linha_tpl, re.IGNORECASE):
            m = re.search(r'Frota\s*[:\-]?\s*(\S+)', texto, re.IGNORECASE)
            if m and not resultado["frota"]:
                resultado["frota"] = m.group(1).strip()

        # OS / O.S.
        elif re.search(r'\b(?:OS|O\.S\.)\b', linha_tpl, re.IGNORECASE):
            m = re.search(r'(?:OS|O\.S\.)\s*[:\-]?\s*(\d+)', texto, re.IGNORECASE)
            if m and not resultado["numero_os"]:
                resultado["numero_os"] = m.group(1).strip()

        # Solicitante
        elif re.search(r'\bsolicit', linha_tpl, re.IGNORECASE):
            m = re.search(r'Solicitado\s*(?:Sr\.?)?\s*[:\-]?\s*(.+)', texto, re.IGNORECASE)
            if m and not resultado["solicitante"]:
                resultado["solicitante"] = limpar_prefixo_titulo(m.group(1))

        # Responsável
        elif re.search(r'\brespons', linha_tpl, re.IGNORECASE):
            m = re.search(r'Respons[aá]vel\s*(?:Sr\.?)?\s*[:\-]?\s*(.+)', texto, re.IGNORECASE)
            if m and not resultado["responsavel"]:
                resultado["responsavel"] = limpar_prefixo_titulo(m.group(1))

        # Fazenda
        elif re.search(r'\bfazenda\b', linha_tpl, re.IGNORECASE):
            m = re.search(r'Fazenda\s*[:\-]?\s*(.+)', texto, re.IGNORECASE | re.MULTILINE)
            if m and not resultado["fazenda"]:
                resultado["fazenda"] = formatar_fazenda(m.group(1))

    # Diagnóstico: linhas que não foram identificadas como metadados
    linhas_diag = []
    for l in linhas_msg:
        if re.match(r'^Frota\s*[:\-]?\s*\S+', l, re.IGNORECASE): continue
        if re.match(r'^(?:OS|O\.S\.)\s*[:\-]?\s*\d+', l, re.IGNORECASE): continue
        if re.match(r'^Solicitado\s*(?:Sr\.?)?\s*[:\-]?\s*.+', l, re.IGNORECASE): continue
        if re.match(r'^Respons[aá]vel\s*(?:Sr\.?)?\s*[:\-]?\s*.+', l, re.IGNORECASE): continue
        if re.match(r'^Fazenda\s*[:\-]?\s*.+', l, re.IGNORECASE): continue
        if re.match(r'^[_\-\=\*\.\s]{3,}$', l): continue
        if re.match(r'^(?:Encaminhada|Mensagem Encaminhada)$', l, re.IGNORECASE): continue
        if re.search(r'[\U00010000-\U0010ffff]', l) and len(l) < 50: continue
        if re.search(r'^(?:Maur[ií]cio|Artur|Daniel|Gabriel|Delaine)\b.*(?:Manuten[cç][aã]o)?', l, re.IGNORECASE) and len(l) < 40: continue
        linhas_diag.append(l)

    resultado["diagnostico"] = "\n".join(linhas_diag).strip()
    return resultado


def extrair_dados_whatsapp(texto_mensagem: str, template_remetente: str = None) -> dict:
    """
    Recebe o texto bruto de uma mensagem do WhatsApp e extrai os campos da O.S.:
    - Frota
    - Nº da OS
    - Fazenda / Local
    - Solicitante / Cliente
    - Responsável / Técnico
    - Diagnóstico / Serviço detalhado

    Parâmetros:
        texto_mensagem: Texto da mensagem recebida
        template_remetente: (Opcional) Exemplo de mensagem cadastrado para este remetente.
                           Quando fornecido, é usado como guia de extração estrutural,
                           com fallback para regex genérico se campos não forem encontrados.
    """
    if not texto_mensagem or not isinstance(texto_mensagem, str):
        return {
            "frota": "", "numero_os": "", "fazenda": "", "local": "",
            "solicitante": "", "cliente": "", "responsavel": "",
            "tecnico": "", "diagnostico": "", "servico": "", "texto_original": ""
        }

    texto = texto_mensagem.strip()
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]

    frota = ""
    numero_os = ""
    fazenda = ""
    solicitante = ""
    responsavel = ""
    diagnostico = ""

    # --- Fase 1: Extração via template do remetente (quando disponível) ---
    if template_remetente and template_remetente.strip():
        campos_template = _extrair_campos_por_template(texto, template_remetente)
        frota = campos_template.get("frota", "")
        numero_os = campos_template.get("numero_os", "")
        fazenda = campos_template.get("fazenda", "")
        solicitante = campos_template.get("solicitante", "")
        responsavel = campos_template.get("responsavel", "")
        diagnostico = campos_template.get("diagnostico", "")

    # --- Fase 2: Fallback para regex genérico (campos não preenchidos pelo template) ---

    # Frota: Frota 5110 / Frota: 5814
    if not frota:
        match_frota = re.search(r'Frota\s*[:\-]?\s*(\d+)', texto, re.IGNORECASE)
        if match_frota:
            frota = match_frota.group(1).strip()

    # O.S.: OS 141668 / OS: 141875 / O.S. 141668
    if not numero_os:
        match_os = re.search(r'(?:OS|O\.S\.)\s*[:\-]?\s*(\d+)', texto, re.IGNORECASE)
        if match_os:
            numero_os = match_os.group(1).strip()

    # Solicitado / Solicitante
    if not solicitante:
        match_solic = re.search(r'Solicitado\s*(?:Sr\.?)?\s*[:\-]?\s*(.+)', texto, re.IGNORECASE)
        if match_solic:
            solicitante = limpar_prefixo_titulo(match_solic.group(1))

    # Responsável / Técnico
    if not responsavel:
        match_resp = re.search(r'Respons[aá]vel\s*(?:Sr\.?)?\s*[:\-]?\s*(.+)', texto, re.IGNORECASE)
        if match_resp:
            responsavel = limpar_prefixo_titulo(match_resp.group(1))

    # Local / Fazenda
    if not fazenda:
        # Caso A: linha explícita 'Fazenda: BELA MANHA'
        match_faz_linha = re.search(r'^\s*Fazenda\s*[:\-]?\s*(.+)', texto, re.IGNORECASE | re.MULTILINE)
        if match_faz_linha:
            fazenda = formatar_fazenda(match_faz_linha.group(1))
        else:
            # Caso B: Termo entre parênteses, ex: '(Fazenda Estrela)'
            match_faz_paren = re.search(r'\((?:Fazenda\s+)?([^)]+)\)', texto, re.IGNORECASE)
            if match_faz_paren:
                fazenda = formatar_fazenda(match_faz_paren.group(1))

    # Diagnóstico (fallback genérico)
    if not diagnostico:
        linhas_diagnostico = []
        for l in linhas:
            if re.match(r'^Frota\s*[:\-]?\s*\d+', l, re.IGNORECASE): continue
            if re.match(r'^(?:OS|O\.S\.)\s*[:\-]?\s*\d+', l, re.IGNORECASE): continue
            if re.match(r'^Solicitado\s*(?:Sr\.?)?\s*[:\-]?\s*.+', l, re.IGNORECASE): continue
            if re.match(r'^Respons[aá]vel\s*(?:Sr\.?)?\s*[:\-]?\s*.+', l, re.IGNORECASE): continue
            if re.match(r'^Fazenda\s*[:\-]?\s*.+', l, re.IGNORECASE): continue
            if re.match(r'^[_\-\=\*\.\s]{3,}$', l): continue
            if re.match(r'^(?:Encaminhada|Mensagem Encaminhada)$', l, re.IGNORECASE): continue
            if re.search(r'[\U00010000-\U0010ffff]', l) and len(l) < 50: continue
            if re.search(r'^(?:Maur[ií]cio|Artur|Daniel|Gabriel|Delaine)\b.*(?:Manuten[cç][aã]o)?', l, re.IGNORECASE) and len(l) < 40: continue
            linhas_diagnostico.append(l)
        diagnostico = "\n".join(linhas_diagnostico).strip()

    return {
        "frota": frota,
        "numero_os": numero_os,
        "fazenda": fazenda,
        "local": fazenda,
        "solicitante": solicitante,
        "cliente": solicitante,
        "responsavel": responsavel,
        "tecnico": responsavel,
        "diagnostico": diagnostico,
        "servico": diagnostico,
        "texto_original": texto
    }


def eh_retorno_os(texto_mensagem: str) -> bool:
    """
    Identifica se a mensagem recebida é um retorno de execução de Ordem de Serviço
    enviado por um colaborador ou técnico.
    
    Critérios de detecção:
    1. Menção explícita a 'RETORNO OS', 'RETORNO O.S.', 'RETORNO DE OS', 'RETORNO DA OS'
    2. OU menção a 'OS [num]' acompanhada de 'STATUS:', 'KM FINAL', 'HORÍMETRO',
       'SERVIÇO EXECUTADO', 'SERVICO REALIZADO' ou 'CONCLUIDO'.
    """
    if not texto_mensagem or not isinstance(texto_mensagem, str):
        return False

    t = texto_mensagem.strip().upper()
    
    # Marcador explícito forte
    if re.search(r'RETORNO\s+(?:DE\s+|DA\s+)?O\.?S\.?', t):
        return True

    # Padrão composto: tem número de OS e indicadores típicos de fechamento/retorno
    tem_os = bool(re.search(r'\b(?:OS|O\.S\.)\s*[:\-]?\s*\d+', t))
    tem_indicador_retorno = bool(re.search(
        r'\b(KM\s*FINAL|HOR[IÍ]METRO|SERVI[CÇ]O\s*(?:EXECUTADO|REALIZADO|CONCLU[IÍ]DO)|'
        r'RELAT[OÓ]RIO\s*DE\s*SERVI[CÇ]O|SERVI[CÇ]OS\s*EXECUTADOS|PE[CÇ]AS\s*UTILIZADAS|'
        r'STATUS\s*[:\-]?\s*(?:CONCLU[IÍ]D[OA]|FINALIZAD[OA]|PENDENTE))\b', t
    ))

    return tem_os and tem_indicador_retorno


def extrair_dados_retorno_colaborador(texto_mensagem: str) -> dict:
    """
    Extrai as informações estruturadas do retorno de campo do colaborador:
    - numero_os
    - status_execucao ('concluido', 'pendente', 'em_andamento')
    - status_rotulo ('Concluído', 'Pendente', etc)
    - km_final
    - horimetro
    - servicos_executados
    - pecas_utilizadas
    - observacoes
    - texto_original
    """
    if not texto_mensagem or not isinstance(texto_mensagem, str):
        return {
            "numero_os": "",
            "status_execucao": "concluido",
            "status_rotulo": "Concluído",
            "km_final": "",
            "horimetro": "",
            "servicos_executados": "",
            "pecas_utilizadas": "",
            "observacoes": "",
            "texto_original": ""
        }

    texto = texto_mensagem.strip()
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]

    # 1. Número da OS
    numero_os = ""
    # Primeiro tenta após RETORNO OS: 1234
    m_os = re.search(r'RETORNO\s+(?:DE\s+|DA\s+)?O\.?S\.?\s*[:\-]?\s*(\d+)', texto, re.IGNORECASE)
    if m_os:
        numero_os = m_os.group(1).strip()
    else:
        m_os2 = re.search(r'(?:OS|O\.S\.)\s*[:\-]?\s*(\d+)', texto, re.IGNORECASE)
        if m_os2:
            numero_os = m_os2.group(1).strip()

    # 2. Status informado pelo técnico
    status_execucao = "concluido"
    status_rotulo = "Concluído"
    m_st = re.search(r'Status\s*[:\-]?\s*([^\n\r]+)', texto, re.IGNORECASE)
    if m_st:
        st_raw = m_st.group(1).strip().lower()
        if any(k in st_raw for k in ["pendente", "incompleto", "aguardando"]):
            status_execucao = "pendente"
            status_rotulo = "Pendente"
        elif any(k in st_raw for k in ["andamento", "iniciado"]):
            status_execucao = "em_andamento"
            status_rotulo = "Em Andamento"
        elif any(k in st_raw for k in ["recusado", "cancelado"]):
            status_execucao = "cancelado"
            status_rotulo = "Cancelado"
        else:
            status_execucao = "concluido"
            status_rotulo = "Concluído"

    # 3. KM Final e Horímetro
    km_final = ""
    m_km = re.search(r'(?:KM\s*(?:Final|Atual)?|Kilometragem)\s*[:\-]?\s*([\d\.,]+)', texto, re.IGNORECASE)
    if m_km:
        km_final = m_km.group(1).replace('.', '').replace(',', '.').strip()

    horimetro = ""
    m_hor = re.search(r'Hor[ií]metro\s*[:\-]?\s*([\d\.,]+)', texto, re.IGNORECASE)
    if m_hor:
        horimetro = m_hor.group(1).replace('.', '').replace(',', '.').strip()

    # 4. Serviços Executados
    servicos_executados = ""
    m_serv = re.search(r'(?:Servi[cç]os?\s*(?:Executados?|Realizados?)?|Trabalho\s*Feito)\s*[:\-]?\s*(.+?)(?=(?:Pe[cç]as?|Obs|Observa[cç][oõ]es?|KM|Status|$))', texto, re.IGNORECASE | re.DOTALL)
    if m_serv:
        servicos_executados = m_serv.group(1).strip()

    # 5. Peças Utilizadas
    pecas_utilizadas = ""
    m_pecas = re.search(r'Pe[cç]as?\s*(?:Utilizadas?|Trocadas?)?\s*[:\-]?\s*(.+?)(?=(?:Obs|Observa[cç][oõ]es?|KM|Status|$))', texto, re.IGNORECASE | re.DOTALL)
    if m_pecas:
        pecas_utilizadas = m_pecas.group(1).strip()

    # 6. Observações
    observacoes = ""
    m_obs = re.search(r'Observa[cç][oõ]es?\s*[:\-]?\s*(.+?)$', texto, re.IGNORECASE | re.DOTALL)
    if m_obs:
        observacoes = m_obs.group(1).strip()

    # Se não capturou serviços executados por regex direto, compõe com as linhas que sobraram
    if not servicos_executados:
        linhas_restantes = []
        for l in linhas:
            if re.search(r'RETORNO\s+(?:DE\s+|DA\s+)?O\.?S\.?', l, re.IGNORECASE): continue
            if re.search(r'^(?:OS|O\.S\.)\s*[:\-]?\s*\d+', l, re.IGNORECASE): continue
            if re.search(r'^Status\s*[:\-]?\s*', l, re.IGNORECASE): continue
            if re.search(r'^(?:KM|Hor[ií]metro)\s*[:\-]?\s*', l, re.IGNORECASE): continue
            if re.match(r'^[_\-\=\*\.\s]{3,}$', l): continue
            linhas_restantes.append(l)
        if linhas_restantes:
            servicos_executados = "\n".join(linhas_restantes).strip()

    return {
        "numero_os": numero_os,
        "status_execucao": status_execucao,
        "status_rotulo": status_rotulo,
        "km_final": km_final,
        "horimetro": horimetro,
        "servicos_executados": servicos_executados,
        "pecas_utilizadas": pecas_utilizadas,
        "observacoes": observacoes,
        "texto_original": texto
    }



if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

    exemplo1 = """
    Maurício Manutenção 🍊🔧🧰⚙️🚜
    Encaminhada
    Frota 5110
    OS 141668
    Serviço de solda na chapa de fixação da estrutura próxima a roda traseira lado direito (Fazenda Estrela)
    Solicitado Sr. João Dubay
    Responsavel Sr. Mauricio
    """

    exemplo2 = """
    Artur
    Encaminhada
    Frota 5814
    OS 141875
    Verificar comando de acionamento da semeadora com mal funcionamento - (Fazenda Terra Branca)
    Solicitado Sr. Eder
    Responsável Sr. Arthur
    Fazenda: BELA MANHA
    ----------------------------
    """

    # Template cadastrado pelo remetente "Maurício"
    template_mauricio = """
    Frota 5110
    OS 141668
    Serviço de solda...
    Solicitado Sr. João
    Responsavel Sr. Mauricio
    """

    print("--- Exemplo 1 (sem template) ---")
    print(json.dumps(extrair_dados_whatsapp(exemplo1), indent=2, ensure_ascii=False))

    print("\n--- Exemplo 1 (com template do remetente) ---")
    print(json.dumps(extrair_dados_whatsapp(exemplo1, template_mauricio), indent=2, ensure_ascii=False))

    print("\n--- Exemplo 2 (sem template) ---")
    print(json.dumps(extrair_dados_whatsapp(exemplo2), indent=2, ensure_ascii=False))
