#!/usr/bin/env python3
"""
Gerador de Vídeo Tutorial: Módulo 06 - Modelos de Orçamento (Padrão Corporativo & Fornecedores)
Demonstração visual de 28s com narração neural ultra-humanizada e animações didáticas:
1. Padrão nativo do sistema selecionado por padrão.
2. Inserção do modelo de fornecedor como exemplo.
3. Disponibilização instantânea no seletor de modelos.
4. Total flexibilidade entre o padrão próprio e modelos anexados.
"""
import os
import sys
import asyncio
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "public" / "videos" / "tutoriais"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR = BASE_DIR / "scratch"
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

# 1. ROTEIRO ULTRA DIDÁTICO (PADRÃO 28 SEGUNDOS)
TEXTO_NARRACAO = (
    "Veja como é simples e flexível escolher o modelo de orçamento! "
    "O sistema já inicia sempre no Modelo Corporativo Nativo da sua empresa, pronto para faturamento. "
    "Se você precisar usar o padrão de um fornecedor, basta anexar o orçamento dele como exemplo. "
    "Na mesma hora, o fornecedor fica disponível na lista para você selecionar quando quiser!"
)

async def gerar_audio_neural(texto, arquivo_saida):
    import edge_tts
    comunicador = edge_tts.Communicate(texto, "pt-BR-AntonioNeural", rate="+2%", pitch="+0Hz")
    await comunicador.save(str(arquivo_saida))
    print(f"[OK] Áudio neural gerado com sucesso: {arquivo_saida}")

def criar_quadros_animacao(duracao_total=28, fps=15):
    total_quadros = int(duracao_total * fps)
    frames_dir = SCRATCH_DIR / "frames_mod06"
    frames_dir.mkdir(parents=True, exist_ok=True)

    COR_BG = (11, 15, 23)
    COR_CARD = (19, 27, 46)
    COR_CARD_BORDA = (30, 41, 59)
    COR_HEADER = (15, 23, 42)
    COR_AZUL = (56, 189, 248)
    COR_VERDE = (34, 197, 94)
    COR_AMARELO = (234, 179, 8)
    COR_TEXTO = (248, 250, 252)
    COR_MUTED = (148, 163, 184)
    COR_INPUT = (15, 23, 42)

    try:
        fonte_tit = ImageFont.truetype("arialbd.ttf", 26)
        fonte_sub = ImageFont.truetype("arial.ttf", 17)
        fonte_card_tit = ImageFont.truetype("arialbd.ttf", 20)
        fonte_texto = ImageFont.truetype("arial.ttf", 16)
        fonte_destaque = ImageFont.truetype("arialbd.ttf", 18)
        fonte_tag = ImageFont.truetype("arialbd.ttf", 14)
        fonte_legenda = ImageFont.truetype("arialbd.ttf", 20)
    except:
        fonte_tit = ImageFont.load_default()
        fonte_sub = fonte_tit
        fonte_card_tit = fonte_tit
        fonte_texto = fonte_tit
        fonte_destaque = fonte_tit
        fonte_tag = fonte_tit
        fonte_legenda = fonte_tit

    print(f"Gerando {total_quadros} quadros ({fps} fps)...")

    for i in range(total_quadros):
        t = i / fps
        img = Image.new("RGB", (1280, 720), COR_BG)
        draw = ImageDraw.Draw(img)

        # Barra Superior
        draw.rectangle([(0, 0), (1280, 70)], fill=COR_HEADER)
        draw.ellipse([(25, 15), (65, 55)], fill=(37, 99, 235))
        draw.text((37, 20), "📄", font=fonte_tit)
        draw.text((80, 16), "Sistema de Gestão & Orçamentos", fill=COR_TEXTO, font=fonte_card_tit)
        draw.text((80, 42), "Módulo de Orçamentos • Seleção Inteligente de Layouts", fill=COR_AZUL, font=fonte_sub)

        # Pill no Topo Direito
        draw.rounded_rectangle([(930, 18), (1240, 52)], radius=16, fill=(30, 41, 59), outline=COR_AZUL, width=1)
        draw.text((950, 25), "NOVO PROCESSO ATUALIZADO 🔔", fill=COR_AZUL, font=fonte_tag)

        # FASE 1: PADRÃO NATIVO DO SISTEMA (0s a 8s)
        if t < 8.0:
            legenda_texto = "1. O sistema opera por padrão com o Modelo Corporativo Nativo."
            passo_tag = "PASSO 1: Modelo Padrão Ativo"

            draw.rounded_rectangle([(80, 100), (1200, 620)], radius=16, fill=COR_CARD, outline=COR_CARD_BORDA, width=1)
            draw.text((120, 125), "Configuração de Layout do Orçamento", fill=COR_TEXTO, font=fonte_card_tit)
            draw.text((120, 155), "O padrão corporativo da sua empresa já vem pronto e ativo para faturamento.", fill=COR_MUTED, font=fonte_sub)

            draw.rounded_rectangle([(120, 200), (700, 430)], radius=12, fill=COR_INPUT, outline=(56, 189, 248), width=2)
            draw.text((150, 225), "Selecionar Modelo de Orçamento:", fill=COR_MUTED, font=fonte_texto)

            draw.rounded_rectangle([(150, 255), (670, 310)], radius=8, fill=(30, 41, 59), outline=COR_AZUL, width=1)
            draw.text((170, 275), "✓ [ Modelo Padrão do Sistema ]", fill=(56, 189, 248), font=fonte_destaque)
            draw.text((635, 275), "▼", fill=COR_AZUL, font=fonte_destaque)

            draw.rounded_rectangle([(150, 330), (670, 400)], radius=8, fill=(16, 185, 129), outline=COR_VERDE, width=1)
            draw.text((170, 345), "🛡️ Padrão Corporativo da Sua Empresa", fill=(0, 0, 0), font=fonte_destaque)
            draw.text((170, 370), "Cabeçalho oficial, logo, frota e cálculo automático.", fill=(15, 23, 42), font=fonte_sub)

            draw.rounded_rectangle([(740, 200), (1160, 580)], radius=12, fill=(15, 23, 42), outline=COR_CARD_BORDA, width=1)
            draw.rectangle([(760, 220), (1140, 275)], fill=(30, 41, 59))
            draw.text((780, 240), "OFICINA ESPECIALIZADA • ORÇAMENTO #001", fill=COR_TEXTO, font=fonte_destaque)
            draw.rectangle([(760, 295), (1140, 325)], fill=(24, 33, 47))
            draw.text((780, 305), "Cliente: Agropecuária Vale Verde  |  Frota: Trator 101", fill=COR_MUTED, font=fonte_sub)
            draw.rectangle([(760, 345), (1140, 490)], fill=(18, 26, 38))
            draw.text((780, 360), "Peças e Serviços Substituídos", fill=COR_AZUL, font=fonte_texto)
            draw.text((780, 395), "• Correia Dentada Dupla: R$ 450,00", fill=COR_TEXTO, font=fonte_sub)
            draw.text((780, 425), "• Filtro de Combustível: R$ 120,00", fill=COR_TEXTO, font=fonte_sub)
            draw.text((780, 455), "• Mão de Obra Especializada: R$ 380,00", fill=COR_TEXTO, font=fonte_sub)
            draw.rounded_rectangle([(760, 510), (1140, 555)], radius=6, fill=COR_VERDE)
            draw.text((880, 525), "TOTAL: R$ 950,00", fill=(0, 0, 0), font=fonte_destaque)

        # FASE 2: ANEXAR ORÇAMENTO DO FORNECEDOR COMO EXEMPLO (8s a 17s)
        elif t < 17.0:
            legenda_texto = "2. Para usar outro formato, anexe o orçamento do fornecedor como exemplo."
            passo_tag = "PASSO 2: Inserir Exemplo do Fornecedor"

            draw.rounded_rectangle([(80, 100), (1200, 620)], radius=16, fill=COR_CARD, outline=COR_CARD_BORDA, width=1)
            draw.text((120, 125), "Adicionar Modelo de Fornecedor", fill=COR_TEXTO, font=fonte_card_tit)
            draw.text((120, 155), "Fornecedores só entram na lista quando você inserir um orçamento exemplo.", fill=COR_MUTED, font=fonte_sub)

            draw.rounded_rectangle([(120, 200), (700, 580)], radius=12, fill=(15, 23, 42), outline=COR_AMARELO, width=2)
            draw.text((220, 240), "📤 ANEXAR ORÇAMENTO EXEMPLO", fill=COR_AMARELO, font=fonte_destaque)
            draw.text((170, 280), "Arraste aqui a foto ou PDF do orçamento do fornecedor", fill=COR_TEXTO, font=fonte_texto)
            draw.text((220, 310), "(Exemplo: Distribuidor, Concessionária, etc.)", fill=COR_MUTED, font=fonte_sub)

            draw.rounded_rectangle([(210, 355), (610, 415)], radius=8, fill=COR_AMARELO)
            draw.text((245, 375), "📁 Escolher Arquivo do Fornecedor", fill=(0, 0, 0), font=fonte_destaque)

            if t >= 11.5:
                draw.rounded_rectangle([(150, 450), (670, 540)], radius=8, fill=(30, 41, 59), outline=COR_VERDE, width=1)
                draw.text((170, 470), "✓ Arquivo: orcamento_fornecedor_exemplo.pdf", fill=COR_VERDE, font=fonte_destaque)
                draw.text((170, 500), "Layout catalogado! Fornecedor registrado com sucesso.", fill=COR_TEXTO, font=fonte_sub)

            draw.rounded_rectangle([(740, 200), (1160, 580)], radius=12, fill=(15, 23, 42), outline=COR_CARD_BORDA, width=1)
            draw.text((770, 230), "💡 Regra de Ouro do Sistema:", fill=COR_AZUL, font=fonte_destaque)
            draw.text((770, 270), "• O sistema não impõe modelos pré-fixados.", fill=COR_TEXTO, font=fonte_sub)
            draw.text((770, 310), "• O padrão fixo da OMC foi removido.", fill=COR_TEXTO, font=fonte_sub)
            draw.text((770, 350), "• Modelos de terceiros só aparecem sob demanda.", fill=COR_TEXTO, font=fonte_sub)
            draw.text((770, 390), "• Você tem controle 100% sobre quais layouts usar.", fill=COR_TEXTO, font=fonte_sub)
            draw.rounded_rectangle([(770, 460), (1130, 540)], radius=8, fill=(40, 35, 10), outline=COR_AMARELO, width=1)
            draw.text((790, 485), "Tudo limpo, organizado e sob seu comando!", fill=COR_AMARELO, font=fonte_destaque)

        # FASE 3: SELEÇÃO IMEDIATA NO DROPDOWN (17s a 24s)
        elif t < 24.0:
            legenda_texto = "3. Assim que anexado, o fornecedor aparece imediatamente para seleção!"
            passo_tag = "PASSO 3: Seleção Imediata no Catálogo"

            draw.rounded_rectangle([(80, 100), (1200, 620)], radius=16, fill=COR_CARD, outline=COR_CARD_BORDA, width=1)
            draw.text((120, 125), "Catálogo de Modelos Atualizado", fill=COR_TEXTO, font=fonte_card_tit)
            draw.text((120, 155), "O novo fornecedor já está disponível no menu de escolha.", fill=COR_MUTED, font=fonte_sub)

            draw.rounded_rectangle([(120, 200), (700, 580)], radius=12, fill=COR_INPUT, outline=COR_AZUL, width=2)
            draw.text((150, 225), "Selecionar Modelo de Orçamento:", fill=COR_MUTED, font=fonte_texto)

            draw.rounded_rectangle([(150, 255), (670, 315)], radius=8, fill=(30, 41, 59), outline=COR_CARD_BORDA, width=1)
            draw.text((170, 275), "• [ Modelo Padrão do Sistema ] (Oficina)", fill=COR_TEXTO, font=fonte_destaque)

            draw.rounded_rectangle([(150, 330), (670, 395)], radius=8, fill=(20, 50, 35), outline=COR_VERDE, width=2)
            draw.text((170, 355), "⭐ Fornecedor Recém-Inserido (Ativo)", fill=COR_VERDE, font=fonte_destaque)
            draw.text((580, 355), "NOVO ✓", fill=COR_VERDE, font=fonte_tag)

            draw.rounded_rectangle([(150, 410), (670, 470)], radius=8, fill=(30, 41, 59), outline=COR_CARD_BORDA, width=1)
            draw.text((170, 430), "+ Inserir Outro Fornecedor...", fill=COR_MUTED, font=fonte_destaque)

            draw.rounded_rectangle([(150, 490), (670, 550)], radius=8, fill=(20, 40, 60), outline=COR_AZUL, width=1)
            draw.text((170, 510), "💡 Clique no modelo desejado e o layout adapta na hora!", fill=COR_AZUL, font=fonte_sub)

            draw.rounded_rectangle([(740, 200), (1160, 580)], radius=12, fill=(15, 23, 42), outline=COR_CARD_BORDA, width=1)
            draw.rectangle([(760, 220), (1140, 275)], fill=(20, 50, 35))
            draw.text((780, 240), "LAYOUT: FORNECEDOR ESCOLHIDO", fill=COR_VERDE, font=fonte_destaque)
            draw.rectangle([(760, 295), (1140, 460)], fill=(18, 26, 38))
            draw.text((780, 315), "Grade de Peças com Código do Fabricante", fill=COR_TEXTO, font=fonte_texto)
            draw.text((780, 360), "Cod: 842103 - Correia Dupla Industrial", fill=COR_MUTED, font=fonte_sub)
            draw.text((780, 405), "Cod: 554109 - Filtro Primário Lavoura", fill=COR_MUTED, font=fonte_sub)
            draw.rounded_rectangle([(760, 490), (1140, 550)], radius=8, fill=COR_VERDE)
            draw.text((820, 510), "PDF GERADO NO PADRÃO ESCOLHIDO!", fill=(0, 0, 0), font=fonte_destaque)

        # FASE 4: RESUMO FINAL E LIBERDADE TOTAL (24s a 28s)
        else:
            legenda_texto = "4. Alterne livremente entre o padrão do sistema e qualquer fornecedor!"
            passo_tag = "CONCLUSÃO: Controle Total e Sem Amarras"

            draw.rounded_rectangle([(80, 100), (1200, 620)], radius=16, fill=COR_CARD, outline=COR_CARD_BORDA, width=1)
            draw.text((120, 125), "Resumo do Processo de Modelos", fill=COR_TEXTO, font=fonte_card_tit)

            draw.rounded_rectangle([(120, 180), (620, 370)], radius=12, fill=(15, 23, 42), outline=COR_AZUL, width=1)
            draw.text((150, 205), "1. Padrão Nativo do Sistema", fill=COR_AZUL, font=fonte_destaque)
            draw.text((150, 245), "• Sempre pronto e ativo por padrão.", fill=COR_TEXTO, font=fonte_sub)
            draw.text((150, 280), "• Identidade visual oficial da sua empresa.", fill=COR_TEXTO, font=fonte_sub)
            draw.text((150, 315), "• Cabeçalho automático com logo e dados.", fill=COR_TEXTO, font=fonte_sub)

            draw.rounded_rectangle([(660, 180), (1160, 370)], radius=12, fill=(15, 23, 42), outline=COR_VERDE, width=1)
            draw.text((690, 205), "2. Modelos de Fornecedores", fill=COR_VERDE, font=fonte_destaque)
            draw.text((690, 245), "• Só aparecem quando você anexar um exemplo.", fill=COR_TEXTO, font=fonte_sub)
            draw.text((690, 280), "• Sem nenhum modelo fixo imposto.", fill=COR_TEXTO, font=fonte_sub)
            draw.text((690, 315), "• Ficam salvos para reaproveitamento fácil.", fill=COR_TEXTO, font=fonte_sub)

            draw.rounded_rectangle([(120, 410), (1160, 580)], radius=12, fill=(20, 50, 35), outline=COR_VERDE, width=2)
            draw.text((360, 445), "✨ PROCESSO RÁPIDO, INTUITIVO E SEGURO!", fill=COR_VERDE, font=fonte_tit)
            draw.text((310, 500), "Orçamentos padronizados em poucos segundos para seus clientes.", fill=COR_TEXTO, font=fonte_destaque)

        draw.rounded_rectangle([(820, 120), (1180, 158)], radius=8, fill=(30, 41, 59), outline=COR_AZUL, width=1)
        draw.text((840, 132), passo_tag, fill=COR_AZUL, font=fonte_tag)

        # BARRA DE LEGENDA NÃO INTRUSIVA NO RODAPÉ
        box_leg_w = 880
        box_leg_h = 44
        box_leg_x = (1280 - box_leg_w) // 2
        box_leg_y = 650
        draw.rounded_rectangle([(box_leg_x, box_leg_y), (box_leg_x + box_leg_w, box_leg_y + box_leg_h)], radius=8, fill=(15, 23, 42), outline=(56, 189, 248), width=1)
        draw.text((box_leg_x + 24, box_leg_y + 10), legenda_texto, fill=COR_TEXTO, font=fonte_legenda)

        prog_total = (i / total_quadros)
        draw.line([(0, 718), (int(1280 * prog_total), 718)], fill=COR_AZUL, width=4)

        frame_path = frames_dir / f"frame_{i:04d}.png"
        img.save(frame_path)

    print("[OK] Todos os quadros de animação gerados com sucesso!")
    return frames_dir

def compilar_video_com_audio(frames_dir, audio_path, video_saida, duracao=28, fps=15):
    print(f"Renderizando vídeo final com FFmpeg em: {video_saida}...")
    cmd = [
        "ffmpeg", "-y",
        "-r", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(video_saida)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERRO] FFmpeg falhou:")
        print(res.stderr)
        raise RuntimeError("Erro ao renderizar MP4 via FFmpeg")
    print(f"[SUCESSO] Vídeo MP4 gerado com sucesso! Tamanho: {os.path.getsize(video_saida)} bytes")

async def main():
    audio_path = SCRATCH_DIR / "audio_modulo_06_modelos.mp3"
    video_saida = OUTPUT_DIR / "modulo_06_modelos_orcamento.mp4"

    await gerar_audio_neural(TEXTO_NARRACAO, audio_path)
    frames_dir = criar_quadros_animacao(duracao_total=28, fps=15)
    compilar_video_com_audio(frames_dir, audio_path, video_saida, duracao=28, fps=15)

if __name__ == "__main__":
    asyncio.run(main())
