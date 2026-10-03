import os
import sys
import re
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _format_moeda(v):
    try:
        val = float(v or 0)
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def _obter_mapa_tags(dados_orcamento):
    """
    Constrói dicionário unificado de tags/placeholders para preenchimento de Word, Excel e PDF.
    """
    orc = dados_orcamento.get("orcamento", dados_orcamento)
    emp = dados_orcamento.get("empresa", {})
    
    num_os = str(orc.get("numero_os") or "").replace("N°", "").replace("Nº", "").strip()
    num_orc = str(orc.get("numero_orcamento") or "").strip()
    if not num_orc and num_os:
        num_orc = f"N° {num_os.zfill(6)}"
    elif num_orc and not num_orc.upper().startswith("N"):
        num_orc = f"N° {num_orc}"

    cli_nome = str(orc.get("cliente_nome") or orc.get("cliente") or "-")
    cnpj_cpf = str(orc.get("cnpj_cpf") or orc.get("cpf_cnpj") or "-")
    tel = str(orc.get("telefone") or "-")
    end = str(orc.get("endereco") or "-")
    bairro = str(orc.get("bairro") or "-")
    cidade_uf = str(orc.get("cidade_uf") or "-")
    cep = str(orc.get("cep") or "-")
    
    veic = str(orc.get("veiculo") or orc.get("equipamento") or "-")
    fab = str(orc.get("fabricante") or "-")
    placa = str(orc.get("placa") or "-")
    frota = str(orc.get("frota") or "-")
    
    km_tot = str(orc.get("km_total") or orc.get("km") or "-")
    hr_tot = str(orc.get("hr_total") or orc.get("horimetro") or "-")
    
    dt_hoje = datetime.date.today().strftime("%d/%m/%Y")
    dt_ent = str(orc.get("data_entrada") or orc.get("data") or dt_hoje)
    dt_entg = str(orc.get("data_entrega") or "-")
    dt_emiss = str(orc.get("data_emissao") or dt_hoje)
    
    diag = str(orc.get("informacoes_cliente") or orc.get("diagnostico") or "-")
    
    vl_pecas = float(orc.get("valor_pecas") or orc.get("subtotal_pecas") or 0)
    vl_mo = float(orc.get("valor_mao_obra") or orc.get("subtotal_servicos") or 0)
    vl_terc = float(orc.get("valor_terceiros") or 0)
    vl_sub = float(orc.get("subtotal_geral") or (vl_pecas + vl_mo + vl_terc))
    desc_pecas = float(orc.get("desconto_pecas") or 0)
    desc_mo = float(orc.get("desconto_mao_obra") or 0)
    desc_fat = float(orc.get("desconto_faturamento") or 0)
    vl_adiant = float(orc.get("valor_adiantamento") or 0)
    vl_rec = float(orc.get("valor_a_receber") or orc.get("total_os") or max(0, vl_sub - desc_pecas - desc_mo - desc_fat - vl_adiant))
    
    return {
        # OS / Orçamento
        "{{NUMERO_OS}}": num_os,
        "{{OS}}": num_os,
        "{{NUMERO_ORCAMENTO}}": num_orc,
        "{{ORCAMENTO}}": num_orc,
        # Cliente
        "{{CLIENTE}}": cli_nome,
        "{{NOME_CLIENTE}}": cli_nome,
        "{{CNPJ_CPF}}": cnpj_cpf,
        "{{CPF}}": cnpj_cpf,
        "{{CNPJ}}": cnpj_cpf,
        "{{TELEFONE}}": tel,
        "{{CONTATO}}": str(orc.get("contato") or tel),
        "{{ENDERECO}}": end,
        "{{BAIRRO}}": bairro,
        "{{CIDADE}}": cidade_uf,
        "{{CIDADE_UF}}": cidade_uf,
        "{{CEP}}": cep,
        # Veículo / Equipamento
        "{{VEICULO}}": veic,
        "{{EQUIPAMENTO}}": veic,
        "{{FABRICANTE}}": fab,
        "{{MODELO}}": fab if fab != "-" else veic,
        "{{PLACA}}": placa,
        "{{FROTA}}": frota,
        "{{KM}}": km_tot,
        "{{KM_TOTAL}}": km_tot,
        "{{HORAS}}": hr_tot,
        "{{HORAS_MOTOR}}": hr_tot,
        "{{HORIMETRO}}": hr_tot,
        # Datas
        "{{DATA}}": dt_ent,
        "{{DATA_ENTRADA}}": dt_ent,
        "{{DATA_ENTREGA}}": dt_entg,
        "{{DATA_EMISSAO}}": dt_emiss,
        "{{HORA_EMISSAO}}": str(orc.get("hora_emissao") or datetime.datetime.now().strftime("%H:%M:%S")),
        # Diagnóstico / Problema Técnico
        "{{DIAGNOSTICO}}": diag,
        "{{PROBLEMA_TECNICO}}": diag,
        "{{OBSERVACOES}}": diag,
        # Financeiro
        "{{VALOR_PECAS}}": _format_moeda(vl_pecas),
        "{{VALOR_MAO_OBRA}}": _format_moeda(vl_mo),
        "{{VALOR_TERCEIROS}}": _format_moeda(vl_terc),
        "{{SUBTOTAL}}": _format_moeda(vl_sub),
        "{{DESCONTO_PECAS}}": _format_moeda(desc_pecas),
        "{{DESCONTO_MAO_OBRA}}": _format_moeda(desc_mo),
        "{{DESCONTO}}": _format_moeda(desc_pecas + desc_mo + desc_fat),
        "{{VALOR_ADIANTAMENTO}}": _format_moeda(vl_adiant),
        "{{VALOR_A_RECEBER}}": _format_moeda(vl_rec),
        "{{TOTAL}}": _format_moeda(vl_rec),
        "{{TOTAL_OS}}": _format_moeda(vl_rec),
        # Empresa
        "{{EMPRESA}}": str(emp.get("razao_social") or "OFICINA"),
        "{{EMPRESA_CNPJ}}": str(emp.get("cnpj") or "-"),
        "{{EMPRESA_TELEFONE}}": str(emp.get("telefone") or "-"),
        "{{EMPRESA_ENDERECO}}": str(emp.get("endereco") or "-"),
    }


# =========================================================================
# 1. MOTOR WORD (.DOCX) COM PYTHON-DOCX
# =========================================================================
def preencher_modelo_word(caminho_template, dados_orcamento, output_docx_path=None):
    """
    Lê o arquivo Word (.docx) anexado pelo usuário, substitui placeholders dinâmicos
    nos parágrafos e células, e injeta as linhas de peças e serviços na tabela.
    """
    try:
        import docx
        from docx.shared import Pt, Inches, RGBColor
    except ImportError:
        raise RuntimeError("Biblioteca 'python-docx' não instalada.")

    if not output_docx_path:
        pdf_dir = BASE_DIR / "public" / "pdf"
        pdf_dir.mkdir(exist_ok=True)
        num_os = dados_orcamento.get("numero_os") or int(datetime.datetime.now().timestamp())
        output_docx_path = pdf_dir / f"Orcamento_{num_os}.docx"

    output_docx_path = Path(output_docx_path)
    output_docx_path.parent.mkdir(parents=True, exist_ok=True)

    doc = docx.Document(str(caminho_template))
    tags = _obter_mapa_tags(dados_orcamento)

    def _replace_text_in_paragraph(p):
        for tag, val in tags.items():
            if tag in p.text:
                # Substituição direta mantendo estilo básico
                p.text = p.text.replace(tag, val)
            # Suporte para tags sem chave dupla se estiver exatamente igual
            tag_sem_chaves = tag.replace("{{", "").replace("}}", "")
            if f"[{tag_sem_chaves}]" in p.text:
                p.text = p.text.replace(f"[{tag_sem_chaves}]", val)

    # 1. Substituir nos parágrafos normais
    for p in doc.paragraphs:
        _replace_text_in_paragraph(p)

    # 2. Processar tabelas: substituição de tags e injeção de itens
    tabela_itens = None
    for table in doc.tables:
        for row in table.rows:
            row_text = " ".join(cell.text for cell in row.cells).lower()
            if any(k in row_text for k in ["código", "codigo", "produto", "descrição", "descricao", "peça", "peças", "item"]):
                tabela_itens = table
                break
            for cell in row.cells:
                for p in cell.paragraphs:
                    _replace_text_in_paragraph(p)

    # 3. Injeção de itens na tabela encontrada
    pecas = dados_orcamento.get("pecas") or []
    servicos = dados_orcamento.get("servicos") or []
    todos_itens = []
    for p in pecas:
        todos_itens.append({
            "cod": str(p.get("codigo") or "-"),
            "desc": str(p.get("produto") or ""),
            "obs": str(p.get("obs") or ""),
            "uni": "UN",
            "qtd": float(p.get("qtd") or 0),
            "vr_unit": float(p.get("vr_unitario") or 0),
            "vr_total": float(p.get("vr_total") or (float(p.get("qtd") or 0) * float(p.get("vr_unitario") or 0)))
        })
    for s in servicos:
        desc = str(s.get("descricao") or s.get("servico") or "")
        if s.get("servico") and s.get("descricao") and s.get("servico") not in s.get("descricao"):
            desc = f"{s.get('servico')} - {desc}"
        uni = "KM" if "KM" in desc.upper() else "HR"
        todos_itens.append({
            "cod": "-",
            "desc": desc,
            "obs": str(s.get("obs") or ""),
            "uni": uni,
            "qtd": float(s.get("qtd") or 0),
            "vr_unit": float(s.get("vr_unitario") or 0),
            "vr_total": float(s.get("vr_total") or (float(s.get("qtd") or 0) * float(s.get("vr_unitario") or 0)))
        })

    if tabela_itens and len(todos_itens) > 0:
        # Procurar se há linha modelo/placeholder para itens
        header_row_idx = 0
        for idx, row in enumerate(tabela_itens.rows):
            row_text = " ".join(cell.text for cell in row.cells).lower()
            if any(k in row_text for k in ["descrição", "descricao", "produto", "item"]):
                header_row_idx = idx
                break

        num_cols = len(tabela_itens.columns)
        for item in todos_itens:
            new_row = tabela_itens.add_row()
            cells = new_row.cells
            if num_cols >= 6:
                cells[0].text = item["cod"]
                cells[1].text = item["desc"] + (f" ({item['obs']})" if item["obs"] else "")
                cells[2].text = item["uni"]
                cells[3].text = f"{item['qtd']:g}"
                cells[4].text = _format_moeda(item["vr_unit"])
                cells[5].text = _format_moeda(item["vr_total"])
            elif num_cols >= 5:
                cells[0].text = item["cod"]
                cells[1].text = item["desc"]
                cells[2].text = f"{item['qtd']:g}"
                cells[3].text = _format_moeda(item["vr_unit"])
                cells[4].text = _format_moeda(item["vr_total"])
            elif num_cols >= 4:
                cells[0].text = item["desc"]
                cells[1].text = f"{item['qtd']:g}"
                cells[2].text = _format_moeda(item["vr_unit"])
                cells[3].text = _format_moeda(item["vr_total"])

    # Salva o arquivo Word preenchido
    doc.save(str(output_docx_path))
    return str(output_docx_path)


def word_to_pdf_reportlab(docx_path, pdf_path):
    """
    Converte o documento Word (.docx) preenchido em PDF via ReportLab estruturado,
    lendo parágrafos e tabelas do documento gerado.
    """
    import docx
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    doc_in = docx.Document(str(docx_path))
    pdf_out = Path(pdf_path)
    pdf_out.parent.mkdir(parents=True, exist_ok=True)

    doc_pdf = SimpleDocTemplate(
        str(pdf_out),
        pagesize=A4,
        leftMargin=24,
        rightMargin=24,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('WordP', fontName='Helvetica', fontSize=8.5, leading=11, textColor=colors.black)
    p_bold = ParagraphStyle('WordPB', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.black)

    elements = []
    PAGE_W, PAGE_H = A4
    CONTENT_W = PAGE_W - 48

    for p in doc_in.paragraphs:
        txt = p.text.strip()
        if txt:
            style_use = p_bold if len(txt) < 40 and txt.isupper() else p_style
            elements.append(Paragraph(txt, style_use))
            elements.append(Spacer(1, 3))

    for table in doc_in.tables:
        table_data = []
        for r_idx, row in enumerate(table.rows):
            row_data = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                s = p_bold if r_idx == 0 else p_style
                row_data.append(Paragraph(cell_text, s))
            table_data.append(row_data)

        if table_data:
            cols_count = len(table_data[0])
            col_w = CONTENT_W / max(1, cols_count)
            t = Table(table_data, colWidths=[col_w] * cols_count)
            t.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 1, colors.black),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F2F2F2')),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 6))

    if not elements:
        elements.append(Paragraph("Orçamento / Ordem de Serviço", p_bold))

    doc_pdf.build(elements)
    return str(pdf_out)


# =========================================================================
# 2. MOTOR EXCEL (.XLSX) COM OPENPYXL
# =========================================================================
def preencher_modelo_excel(caminho_template, dados_orcamento, output_excel_path=None):
    """
    Preenche modelo de planilha Excel (.xlsx) mapeando tags, preenchendo tabelas
    e preservando fórmulas.
    """
    import openpyxl
    if not output_excel_path:
        pdf_dir = BASE_DIR / "public" / "pdf"
        pdf_dir.mkdir(exist_ok=True)
        num_os = dados_orcamento.get("numero_os") or int(datetime.datetime.now().timestamp())
        output_excel_path = pdf_dir / f"Orcamento_{num_os}.xlsx"

    output_excel_path = Path(output_excel_path)
    output_excel_path.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.load_workbook(str(caminho_template))
    ws = wb.active
    tags = _obter_mapa_tags(dados_orcamento)

    # Substituição de tags nas células
    for row in ws.iter_rows():
        for cell in row:
            if cell.value and isinstance(cell.value, str):
                v = cell.value
                for tag, val in tags.items():
                    if tag in v:
                        v = v.replace(tag, str(val))
                cell.value = v

    wb.save(str(output_excel_path))
    return str(output_excel_path)


# =========================================================================
# 3. MOTOR PDF (.PDF) COM PYMUPDF (FITZ) E REPORTLAB
# =========================================================================
def preencher_modelo_pdf(caminho_template, dados_orcamento, output_pdf_path=None):
    """
    Preenche modelo PDF anexado preservando a folha original e adicionando os dados.
    """
    import fitz
    if not output_pdf_path:
        pdf_dir = BASE_DIR / "public" / "pdf"
        pdf_dir.mkdir(exist_ok=True)
        num_os = dados_orcamento.get("numero_os") or int(datetime.datetime.now().timestamp())
        output_pdf_path = pdf_dir / f"Orcamento_{num_os}.pdf"

    output_pdf_path = Path(output_pdf_path)
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(caminho_template))
    tags = _obter_mapa_tags(dados_orcamento)

    # Verifica se há campos de formulário (AcroForms)
    tem_widgets = False
    for page in doc:
        for widget in page.widgets():
            tem_widgets = True
            name = (widget.field_name or "").upper()
            for tag, val in tags.items():
                tag_clean = tag.replace("{{", "").replace("}}", "")
                if tag_clean in name:
                    widget.field_value = str(val)
                    widget.update()

    if not tem_widgets and len(doc) > 0:
        # Substituição visual / overlay nas páginas
        for page in doc:
            for tag, val in tags.items():
                rects = page.search_for(tag)
                for rect in rects:
                    # Redesenha com texto preenchido sobre a tag
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_text((rect.x0, rect.y1 - 2), str(val), fontsize=9, fontname="helv", color=(0, 0, 0))

    doc.save(str(output_pdf_path))
    return str(output_pdf_path)
