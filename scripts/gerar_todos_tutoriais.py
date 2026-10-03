#!/usr/bin/env python3
"""
Script Mestre: Gerador dos 7 Vídeos Tutoriais da Plataforma (Módulos 0 a 6)
Garante:
1. Zero cortes de áudio: duração do áudio medida via ffprobe + margem de conforto de 1.5s.
2. Dados 100% fictícios em todos os 7 módulos (Agropecuária Vale Verde, Fazenda Santa Cecília, etc.).
3. Novos modelos de orçamento no Módulo 06 (Padrão Corporativo, Terra Viva PDF, Sultratores Excel, Alvorada Word).
4. Renderização em MP4 H.264 / AAC de alta compatibilidade web e mobile.
5. Atualização automática do catálogo em data/tutoriais_config.json.
"""

import os
import sys
import json
import math
import asyncio
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "public" / "videos" / "tutoriais"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR = BASE_DIR / "scratch"
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = BASE_DIR / "data"

FPS = 15

# Cores Corporativas
C_BG = (11, 15, 23)           # #0b0f17
C_CARD = (19, 27, 46)         # #131b2e
C_HEADER = (15, 23, 42)       # #0f172a
C_AZUL = (56, 189, 248)       # #38bdf8
C_VERDE = (34, 197, 94)       # #22c55e
C_AMARELO = (234, 179, 8)     # #eab308
C_VERMELHO = (239, 68, 68)    # #ef4444
C_TEXTO = (248, 250, 252)     # #f8fafc
C_MUTED = (148, 163, 184)     # #94a3b8
C_BORDA = (30, 41, 59)        # #1e293b
C_INPUT = (15, 23, 42)

# Cores WhatsApp
C_WA_BG = (17, 27, 33)        # #111b21
C_WA_HEADER = (32, 44, 51)    # #202c33
C_WA_MSG_IN = (32, 44, 51)    # #202c33
C_WA_MSG_OUT = (0, 92, 75)    # #005c4b
C_WA_VERDE = (37, 211, 102)   # #25d366

def carregar_fontes():
    try:
        f_hero = ImageFont.truetype("arialbd.ttf", 32)
        f_tit = ImageFont.truetype("arialbd.ttf", 26)
        f_sub = ImageFont.truetype("arial.ttf", 18)
        f_card_tit = ImageFont.truetype("arialbd.ttf", 21)
        f_corpo = ImageFont.truetype("arial.ttf", 17)
        f_destaque = ImageFont.truetype("arialbd.ttf", 19)
        f_tag = ImageFont.truetype("arialbd.ttf", 13)
        f_legenda = ImageFont.truetype("arialbd.ttf", 19)
    except Exception:
        f_hero = ImageFont.load_default()
        f_tit = f_hero
        f_sub = f_hero
        f_card_tit = f_hero
        f_corpo = f_hero
        f_destaque = f_hero
        f_tag = f_hero
        f_legenda = f_hero
    return {
        "hero": f_hero,
        "tit": f_tit,
        "sub": f_sub,
        "card_tit": f_card_tit,
        "corpo": f_corpo,
        "destaque": f_destaque,
        "tag": f_tag,
        "legenda": f_legenda
    }

FONTS = carregar_fontes()

async def gerar_audio_tts(texto, arquivo_saida):
    import edge_tts
    # Comunicação em tom profissional brasileiro com clareza
    comunicador = edge_tts.Communicate(texto, "pt-BR-AntonioNeural", rate="+2%", pitch="-1Hz")
    await comunicador.save(str(arquivo_saida))
    print(f"[OK] Áudio neural gerado: {arquivo_saida.name}")

def obter_duracao_audio(arquivo_audio):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(arquivo_audio)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def desenhar_cabecalho(draw, titulo, categoria_tag, icone="⚙️"):
    draw.rectangle([(0, 0), (1280, 70)], fill=C_HEADER)
    draw.rounded_rectangle([(25, 14), (65, 54)], radius=8, fill=(56, 189, 248, 30), outline=C_AZUL, width=1)
    draw.text((34, 18), icone, font=FONTS["tit"])
    draw.text((80, 20), titulo, fill=C_TEXTO, font=FONTS["tit"])
    
    # Tag no canto direito
    tw = draw.textlength(categoria_tag, font=FONTS["tag"])
    bx = int(1250 - tw - 24)
    draw.rounded_rectangle([(bx, 18), (1250, 52)], radius=16, fill=C_BG, outline=C_AZUL, width=1)
    draw.text((bx + 12, 26), categoria_tag, fill=C_AZUL, font=FONTS["tag"])

def desenhar_barra_inferior(draw, progresso, legenda_texto):
    # Caixa da Legenda Inteligente
    box_w = 900
    box_h = 44
    box_x = (1280 - box_w) // 2
    box_y = 650
    draw.rounded_rectangle([(box_x, box_y), (box_x + box_w, box_y + box_h)], radius=8, fill=(15, 23, 42), outline=C_AZUL, width=1)
    draw.text((box_x + 20, box_y + 11), legenda_texto, fill=C_TEXTO, font=FONTS["legenda"])

    # Barra de Progresso
    draw.line([(0, 718), (int(1280 * progresso), 718)], fill=C_AZUL, width=4)

def compilar_video(frames_dir, audio_path, video_saida, duracao_total, fps=FPS):
    print(f"Compilando com FFmpeg: {video_saida.name} (Duração: {duracao_total:.2f}s)...")
    cmd = [
        "ffmpeg", "-y",
        "-r", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-i", str(audio_path),
        "-filter_complex", "[1:a]apad=pad_dur=2.0[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-t", f"{duracao_total:.2f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(video_saida)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERRO FFmpeg] {res.stderr}")
        raise RuntimeError(f"Falha ao compilar vídeo: {video_saida.name}")
    print(f"[SUCESSO] Vídeo gerado: {video_saida.name} ({os.path.getsize(video_saida)} bytes)")

# =========================================================================
# MÓDULO 00: Apresentação da Plataforma & Benefícios Reais
# =========================================================================
TEXTO_MOD00 = (
    "Gerenciar manutenções de máquinas e frotas pesadas não precisa depender de papel, pranchetas ou anotações perdidas. "
    "Nossa plataforma integra a oficina, a equipe técnica em campo e o cliente final em tempo real. "
    "Pelo aplicativo, o técnico registra o atendimento, controla peças, quilometragem e horímetro, e coleta a assinatura digital na hora. "
    "No escritório, você acompanha os custos e envia orçamentos e comprovantes pelo WhatsApp com um clique. "
    "Mais controle para a frota, zero burocracia e total transparência para o cliente."
)

def gerar_quadros_mod00(duracao_total):
    frames_dir = SCRATCH_DIR / "frames_mod00"
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_quadros = int(duracao_total * FPS)

    for i in range(total_quadros):
        t = i / FPS
        progresso = i / total_quadros
        img = Image.new("RGB", (1280, 720), C_BG)
        draw = ImageDraw.Draw(img)

        desenhar_cabecalho(draw, "PLATAFORMA DE GESTÃO DE MANUTENÇÃO & FROTAS", "APRESENTAÇÃO EXECUTIVA", "🚜")

        p = t / duracao_total
        if p < 0.25:
            legenda = "1. O modelo tradicional com papel causa perda de informações e atrasos."
            draw.text((60, 100), "O Desafio Tradicional da Manutenção Pesada", fill=C_TEXTO, font=FONTS["hero"])
            draw.text((60, 145), "Operações que dependem de formulários de papel enfrentam gargalos diários:", fill=C_MUTED, font=FONTS["sub"])

            cards = [
                ("📋 Papéis & Pranchetas", "Anotações ilegíveis, fichas molhadas na lavoura ou perdidas no trânsito.", C_VERMELHO),
                ("⏳ Lentidão no Fechamento", "Dias até a ordem física chegar da fazenda para o escritório faturar.", C_AMARELO),
                ("📉 Falta de Rastreabilidade", "Dificuldade para comprovar peças trocadas e histórico do horímetro.", C_MUTED)
            ]
            for idx, (ctit, cdesc, ccor) in enumerate(cards):
                x = 60 + idx * 390
                draw.rounded_rectangle([(x, 195), (x + 370, 420)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
                draw.rounded_rectangle([(x + 20, 215), (x + 350, 255)], radius=6, fill=C_INPUT, outline=ccor, width=1)
                draw.text((x + 30, 224), ctit, fill=ccor, font=FONTS["destaque"])
                draw.text((x + 25, 280), cdesc, fill=C_TEXTO, font=FONTS["corpo"])

        elif p < 0.55:
            legenda = "2. Conecte o técnico no campo, a oficina e o cliente em tempo real."
            draw.text((60, 100), "A Solução Integrada: Oficina, Campo & Cliente", fill=C_TEXTO, font=FONTS["hero"])
            draw.text((60, 145), "Comunicação contínua sem depender de papéis ou esperas:", fill=C_MUTED, font=FONTS["sub"])

            pilares = [
                ("📱 TÉCNICO NO CAMPO", "App mobile intuitivo\nLança peças, serviços e horímetro\nColeta visto no vidro do celular", C_VERDE),
                ("🏢 OFICINA & GESTÃO", "Painel web completo\nValidação de ordens e faturamento\nHistórico técnico por frota", C_AZUL),
                ("💬 CLIENTE FINAL", "Abertura ágil pelo WhatsApp\nComprovante assinado no ato\nTotal transparência e agilidade", C_AMARELO)
            ]
            for idx, (ptit, pdesc, pcor) in enumerate(pilares):
                x = 60 + idx * 390
                draw.rounded_rectangle([(x, 195), (x + 370, 440)], radius=12, fill=C_CARD, outline=pcor, width=2)
                draw.rectangle([(x, 195), (x + 370, 250)], fill=C_INPUT)
                draw.text((x + 25, 212), ptit, fill=pcor, font=FONTS["card_tit"])
                draw.text((x + 25, 275), pdesc, fill=C_TEXTO, font=FONTS["corpo"])

        elif p < 0.80:
            legenda = "3. Pelo celular o técnico anota peças, horímetro e colhe o visto digital."
            draw.text((60, 100), "Operação 100% Digital no Smartphone do Técnico", fill=C_TEXTO, font=FONTS["hero"])
            draw.text((60, 145), "Tudo funciona no campo, mesmo sem conexão permanente:", fill=C_MUTED, font=FONTS["sub"])

            draw.rounded_rectangle([(60, 190), (620, 580)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((90, 215), "Funcionalidades no Celular:", fill=C_AZUL, font=FONTS["card_tit"])
            itens_app = [
                "• Busca rápida de frotas e clientes cadastrados",
                "• Lançamento de peças com cálculo automático",
                "• Apontamento seguro de KM e Horímetro",
                "• Assinatura digital touch na tela do celular",
                "• Geração instantânea de comprovante PDF"
            ]
            for idx, it in enumerate(itens_app):
                draw.text((90, 265 + idx * 55), it, fill=C_TEXTO, font=FONTS["corpo"])

            draw.rounded_rectangle([(660, 190), (1220, 580)], radius=12, fill=C_INPUT, outline=C_VERDE, width=2)
            draw.text((690, 215), "Exemplo Real de Atendimento:", fill=C_VERDE, font=FONTS["card_tit"])
            draw.text((690, 265), "Cliente: Agropecuária Vale Verde Ltda.", fill=C_TEXTO, font=FONTS["destaque"])
            draw.text((690, 305), "Máquina: Trator Massey Ferguson 7719 • Frota 101", fill=C_MUTED, font=FONTS["sub"])
            draw.text((690, 345), "Serviço: Troca de mangueira hidráulica e óleo", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((690, 385), "Horímetro Aferido: 3.420 h", fill=C_AMARELO, font=FONTS["destaque"])
            draw.rounded_rectangle([(690, 440), (1190, 520)], radius=8, fill=(20, 50, 35), outline=C_VERDE, width=1)
            draw.text((710, 465), "✓ Assinado por Carlos Mendes • Pronto para Faturar", fill=C_VERDE, font=FONTS["destaque"])

        else:
            legenda = "4. Mais controle para a frota, zero burocracia e total transparência."
            draw.text((60, 100), "Resultados Comprovados para a Sua Oficina", fill=C_TEXTO, font=FONTS["hero"])
            draw.text((60, 145), "Benefícios imediatos desde o primeiro dia de uso:", fill=C_MUTED, font=FONTS["sub"])

            ganhos = [
                ("⚡ Faturamento 5x Mais Rápido", "Comprovante gerado na hora elimina a espera física de semanas.", C_VERDE),
                ("🛡️ Histórico Inviolável", "Cada ordem possui carimbo digital, horímetro e visto do operador.", C_AZUL),
                ("🤝 Fidelização do Produtor", "Transparência total com envio do relatório direto no WhatsApp.", C_AMARELO)
            ]
            for idx, (gtit, gdesc, gcor) in enumerate(ganhos):
                y = 195 + idx * 125
                draw.rounded_rectangle([(60, y), (1220, y + 105)], radius=12, fill=C_CARD, outline=gcor, width=1)
                draw.text((90, y + 20), gtit, fill=gcor, font=FONTS["card_tit"])
                draw.text((90, y + 58), gdesc, fill=C_TEXTO, font=FONTS["corpo"])

        desenhar_barra_inferior(draw, progresso, legenda)
        img.save(frames_dir / f"frame_{i:04d}.png")

    return frames_dir

# =========================================================================
# MÓDULO 01: Simulação 01: Do WhatsApp ao Comprovante Pronto (Modo Solo)
# =========================================================================
TEXTO_MOD01 = (
    "Olha só como é fácil! Primeiro, o cliente da Agropecuária Vale Verde solicita socorro mecânico no WhatsApp para o Trator cento e um. "
    "Você abre o aplicativo no celular, seleciona a máquina com um toque e anota o reparo da mangueira hidráulica. "
    "Agora, o encarregado assina com o dedo na tela do celular. "
    "Prontinho! Aperte o botão verde Enviar WhatsApp e o comprovante já chega na conversa na mesma hora com check azul!"
)

def gerar_quadros_mod01(duracao_total):
    frames_dir = SCRATCH_DIR / "frames_mod01"
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_quadros = int(duracao_total * FPS)

    for i in range(total_quadros):
        t = i / FPS
        progresso = i / total_quadros
        img = Image.new("RGB", (1280, 720), C_WA_BG)
        draw = ImageDraw.Draw(img)

        p = t / duracao_total
        if p < 0.28:
            legenda = "1. O cliente solicita atendimento direto pelo WhatsApp com o problema."
            draw.rectangle([(0, 0), (1280, 75)], fill=C_WA_HEADER)
            draw.ellipse([(30, 15), (75, 60)], fill=C_WA_VERDE)
            draw.text((45, 23), "🌾", font=FONTS["tit"])
            draw.text((90, 18), "Carlos Mendes • Agropecuária Vale Verde", fill=C_TEXTO, font=FONTS["tit"])
            draw.text((90, 46), "online • (44) 99811-0001", fill=C_MUTED, font=FONTS["sub"])

            draw.rounded_rectangle([(60, 130), (750, 310)], radius=12, fill=C_WA_MSG_IN)
            draw.text((85, 150), "Bom dia! Nosso Trator Massey 7719 (Frota 101)", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((85, 185), "estourou a mangueira hidráulica no Talhão 4.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((85, 220), "Consegue enviar socorro urgente para trocar?", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((660, 270), "08:15", fill=C_MUTED, font=FONTS["tag"])

            draw.rounded_rectangle([(60, 350), (1220, 520)], radius=12, fill=C_CARD, outline=C_AZUL, width=1)
            draw.text((90, 375), "⚡ Alerta Integrado na Oficina:", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((90, 420), "• Mensagem recebida automaticamente no Painel e App do Técnico", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((90, 455), "• O sistema já vincula o número ao cadastro da Agropecuária Vale Verde", fill=C_TEXTO, font=FONTS["corpo"])

        elif p < 0.58:
            legenda = "2. Você abre a O.S. no celular, seleciona a frota e lança o reparo."
            desenhar_cabecalho(draw, "APP MOBILE • ABERTURA DE O.S. DE CAMPO #1001", "MODO SOLO", "📱")

            draw.rounded_rectangle([(60, 95), (1220, 610)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((90, 120), "Cliente: Agropecuária Vale Verde Ltda.", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((90, 155), "Frota: Trator Massey Ferguson 7719 • Frota 101 • Horímetro: 3.420 h", fill=C_TEXTO, font=FONTS["destaque"])

            draw.rounded_rectangle([(90, 200), (1190, 310)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((110, 215), "Diagnóstico e Reparo Realizado:", fill=C_MUTED, font=FONTS["sub"])
            draw.text((110, 245), "Substituição da mangueira hidráulica de pressão R2 1/2\"", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((110, 275), "Completado nível do óleo hidráulico 68 e teste de carga no levante.", fill=C_TEXTO, font=FONTS["corpo"])

            draw.rounded_rectangle([(90, 335), (1190, 485)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((110, 350), "Peças & Serviços:", fill=C_MUTED, font=FONTS["sub"])
            draw.text((110, 385), "• 01x Mangueira R2 1/2\": R$ 380,00", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((110, 415), "• 20L Óleo Hidráulico 68: R$ 420,00", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((110, 445), "• Mão de Obra Mecânica de Campo: R$ 450,00", fill=C_TEXTO, font=FONTS["corpo"])

            draw.rounded_rectangle([(90, 510), (500, 575)], radius=8, fill=(20, 50, 35), outline=C_VERDE, width=1)
            draw.text((110, 530), "VALOR TOTAL: R$ 1.250,00", fill=C_VERDE, font=FONTS["destaque"])

        elif p < 0.78:
            legenda = "3. O operador ou gerente assina com o dedo na tela do celular."
            desenhar_cabecalho(draw, "APP MOBILE • ASSINATURA DIGITAL TOUCH", "VALIDAÇÃO", "✍️")

            draw.rounded_rectangle([(150, 95), (1130, 600)], radius=12, fill=C_CARD, outline=C_AZUL, width=2)
            draw.text((180, 120), "Assinatura do Responsável no Campo:", fill=C_TEXTO, font=FONTS["card_tit"])
            draw.text((180, 150), "Carlos Mendes (Gerente Agrícola - Agropecuária Vale Verde)", fill=C_MUTED, font=FONTS["sub"])

            draw.rounded_rectangle([(180, 190), (1100, 450)], radius=8, fill=(255, 255, 255))
            draw.line([(220, 400), (1060, 400)], fill=(200, 200, 200), width=2)
            draw.text((220, 410), "Assine acima com a ponta do dedo", fill=(160, 160, 160), font=FONTS["tag"])

            pontos = [
                (260, 360), (310, 300), (340, 380), (380, 290), (420, 370),
                (470, 350), (520, 370), (580, 340), (640, 370), (710, 330),
                (780, 370), (860, 360), (940, 350), (990, 370)
            ]
            draw.line(pontos, fill=(15, 23, 42), width=4)

            draw.rounded_rectangle([(180, 480), (380, 545)], radius=8, fill=(50, 20, 20), outline=C_VERMELHO, width=1)
            draw.text((230, 502), "🗑️ Limpar", fill=C_VERMELHO, font=FONTS["destaque"])

            draw.rounded_rectangle([(410, 480), (1100, 545)], radius=8, fill=C_VERDE)
            draw.text((560, 502), "✓ CONFIRMAR ASSINATURA & FECHAR", fill=(0, 0, 0), font=FONTS["hero"])

        else:
            legenda = "4. Aperte Enviar WhatsApp e o comprovante chega na mesma hora!"
            draw.rectangle([(0, 0), (1280, 75)], fill=C_WA_HEADER)
            draw.text((90, 22), "Carlos Mendes • Agropecuária Vale Verde", fill=C_TEXTO, font=FONTS["tit"])

            draw.rounded_rectangle([(480, 120), (1220, 500)], radius=12, fill=C_WA_MSG_OUT)
            draw.text((510, 145), "✓ O.S. #1001 CONCLUÍDA COM SUCESSO!", fill=C_WA_VERDE, font=FONTS["card_tit"])
            draw.text((510, 185), "Cliente: Agropecuária Vale Verde Ltda.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((510, 215), "Frota: Trator Massey Ferguson 7719 (Frota 101)", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((510, 245), "Serviço: Mangueira Hidráulica R2 + Óleo 68", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((510, 275), "Total: R$ 1.250,00  |  Horímetro: 3.420 h", fill=C_AMARELO, font=FONTS["destaque"])

            draw.rounded_rectangle([(510, 325), (1180, 435)], radius=8, fill=(17, 27, 33))
            draw.text((530, 345), "📄 COMPROVANTE_OS_1001_ASSINADO.PDF", fill=C_AZUL, font=FONTS["destaque"])
            draw.text((530, 385), "Assinado digitalmente por Carlos Mendes no campo", fill=C_MUTED, font=FONTS["sub"])
            draw.text((1130, 455), "09:40 ✓✓", fill=C_AZUL, font=FONTS["tag"])

        desenhar_barra_inferior(draw, progresso, legenda)
        img.save(frames_dir / f"frame_{i:04d}.png")

    return frames_dir

# =========================================================================
# MÓDULO 02: Frota & Horímetro / KM
# =========================================================================
TEXTO_MOD02 = (
    "No Módulo de Frota, registrar o maquinário leva poucos segundos. "
    "Selecione o cliente na busca rápida, como a Fazenda Santa Cecília. "
    "Digite o número da frota, como a Colheitadeira duzentos e quatro, e confira o modelo Case IH. "
    "Por fim, anote o horímetro exibido no painel de mil oitocentas e cinquenta horas. "
    "Todos os dados ficam salvos com data e hora exata para o histórico da manutenção."
)

def gerar_quadros_mod02(duracao_total):
    frames_dir = SCRATCH_DIR / "frames_mod02"
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_quadros = int(duracao_total * FPS)

    for i in range(total_quadros):
        t = i / FPS
        progresso = i / total_quadros
        img = Image.new("RGB", (1280, 720), C_BG)
        draw = ImageDraw.Draw(img)

        desenhar_cabecalho(draw, "MÓDULO 02: CADASTRO DE FROTA & HORÍMETRO", "O.S. CAMPO", "🔍")

        p = t / duracao_total
        if p < 0.28:
            legenda = "1. Escolha o cliente na lista de busca rápida com preenchimento instantâneo."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Passo 1: Selecionar o Cliente Solicitante", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rounded_rectangle([(110, 175), (1170, 245)], radius=8, fill=C_INPUT, outline=C_AZUL, width=2)
            draw.text((130, 195), "🔍 Fazenda Santa Cecília", fill=C_TEXTO, font=FONTS["destaque"])

            draw.rounded_rectangle([(110, 260), (1170, 480)], radius=8, fill=(15, 23, 42), outline=C_BORDA, width=1)
            clientes = [
                ("✓ Fazenda Santa Cecília Agronegócios", "CNPJ: 29.876.543/0001-12 • Solicitante: Eduardo Silveira", True),
                ("Agropecuária Vale Verde Ltda.", "CNPJ: 18.234.567/0001-89 • Solicitante: Carlos Mendes", False),
                ("Cerealista e Grãos São Pedro", "CNPJ: 34.112.233/0001-45 • Solicitante: Fernando Dias", False),
            ]
            for idx, (cnome, cinfo, sel) in enumerate(clientes):
                cy = 275 + idx * 65
                if sel:
                    draw.rounded_rectangle([(120, cy), (1160, cy + 55)], radius=6, fill=(20, 40, 65), outline=C_AZUL, width=1)
                    draw.text((140, cy + 10), cnome, fill=C_AZUL, font=FONTS["destaque"])
                    draw.text((140, cy + 32), cinfo, fill=C_MUTED, font=FONTS["tag"])
                else:
                    draw.text((140, cy + 10), cnome, fill=C_TEXTO, font=FONTS["corpo"])
                    draw.text((140, cy + 32), cinfo, fill=C_MUTED, font=FONTS["tag"])

        elif p < 0.58:
            legenda = "2. Digite a frota ou placa para carregar os dados técnicos da máquina."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Passo 2: Identificação do Veículo / Maquinário", fill=C_AZUL, font=FONTS["card_tit"])

            draw.text((110, 175), "Digite o Número da Frota ou Placa:", fill=C_MUTED, font=FONTS["sub"])
            draw.rounded_rectangle([(110, 210), (500, 275)], radius=8, fill=C_INPUT, outline=C_AZUL, width=2)
            draw.text((140, 228), "Frota: 204", fill=C_TEXTO, font=FONTS["hero"])

            draw.rounded_rectangle([(540, 210), (1170, 520)], radius=8, fill=C_INPUT, outline=C_VERDE, width=2)
            draw.text((570, 235), "MÁQUINA LOCALIZADA NO CADASTRO ✓", fill=C_VERDE, font=FONTS["destaque"])
            draw.text((570, 280), "Equipamento: Colheitadeira de Grãos", fill=C_TEXTO, font=FONTS["card_tit"])
            draw.text((570, 320), "Marca / Modelo: Case IH 8250 Axial-Flow", fill=C_MUTED, font=FONTS["sub"])
            draw.text((570, 360), "Ano de Fabricação: 2022  |  Chassi: JJC8250AX992", fill=C_MUTED, font=FONTS["sub"])
            draw.text((570, 400), "Último Atendimento: 12/08/2026 (Revisão Preventiva)", fill=C_MUTED, font=FONTS["sub"])
            draw.text((570, 440), "Mecânico Responsável: Rodrigo Sanches", fill=C_AZUL, font=FONTS["destaque"])

        elif p < 0.80:
            legenda = "3. Anote o horímetro ou quilometragem exibida no painel de instrumentos."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Passo 3: Apontamento do Horímetro Atual", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rounded_rectangle([(110, 180), (600, 450)], radius=12, fill=C_INPUT, outline=C_AMARELO, width=2)
            draw.text((140, 210), "Horímetro Painel (Horas Trabalhadas):", fill=C_MUTED, font=FONTS["sub"])
            draw.rounded_rectangle([(140, 250), (570, 340)], radius=8, fill=(30, 41, 59), outline=C_AMARELO, width=1)
            draw.text((200, 268), "1.850 h", fill=C_AMARELO, font=FONTS["hero"])
            draw.text((140, 370), "✓ Valor verificado pelo técnico no painel", fill=C_VERDE, font=FONTS["destaque"])

            draw.rounded_rectangle([(640, 180), (1170, 450)], radius=12, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((670, 210), "Histórico de Horímetro da Frota 204:", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((670, 260), "• Horímetro anterior: 1.730 h (Registrado em 12/08)", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((670, 300), "• Horas trabalhadas no ciclo: +120 horas", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((670, 340), "• Alerta preventivo: Próxima revisão em 2.000 h", fill=C_MUTED, font=FONTS["corpo"])
            draw.rounded_rectangle([(670, 385), (1130, 430)], radius=6, fill=(20, 50, 35))
            draw.text((690, 398), "Tudo em dia! Sem pendências de garantia.", fill=C_VERDE, font=FONTS["tag"])

        else:
            legenda = "4. Tudo fica gravado com data, hora e geolocalização para seu histórico."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_VERDE, width=2)
            draw.text((110, 125), "Dados da Frota Gravados com Sucesso!", fill=C_VERDE, font=FONTS["hero"])

            draw.rounded_rectangle([(110, 190), (1170, 480)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((140, 220), "Resumo do Registro de Campo:", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((140, 270), "• Cliente: Fazenda Santa Cecília Agronegócios", fill=C_TEXTO, font=FONTS["destaque"])
            draw.text((140, 310), "• Equipamento: Colheitadeira Case IH 8250 (Frota 204)", fill=C_TEXTO, font=FONTS["destaque"])
            draw.text((140, 350), "• Horímetro Aferido: 1.850 h  |  Data/Hora: 15/09/2026 às 10:15", fill=C_AMARELO, font=FONTS["destaque"])
            draw.text((140, 390), "• Mecânico Responsável: Rodrigo Sanches", fill=C_TEXTO, font=FONTS["destaque"])

        desenhar_barra_inferior(draw, progresso, legenda)
        img.save(frames_dir / f"frame_{i:04d}.png")

    return frames_dir

# =========================================================================
# MÓDULO 03: Peças & Serviços (Cálculo Automático)
# =========================================================================
TEXTO_MOD03 = (
    "O lançamento de peças e serviços é totalmente automático. "
    "Descreva o diagnóstico técnico, como a troca de rolamento do rotor na colheitadeira. "
    "Toque em Adicionar Peça, insira a quantidade e o valor unitário. "
    "Depois, inclua a mão de obra especializada do mecânico. "
    "O sistema calcula os subtotais e soma o valor final sozinho, sem você precisar de calculadora!"
)

def gerar_quadros_mod03(duracao_total):
    frames_dir = SCRATCH_DIR / "frames_mod03"
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_quadros = int(duracao_total * FPS)

    for i in range(total_quadros):
        t = i / FPS
        progresso = i / total_quadros
        img = Image.new("RGB", (1280, 720), C_BG)
        draw = ImageDraw.Draw(img)

        desenhar_cabecalho(draw, "MÓDULO 03: PEÇAS, SERVIÇOS & CÁLCULO AUTOMÁTICO", "O.S. CAMPO", "🔧")

        p = t / duracao_total
        if p < 0.28:
            legenda = "1. Descreva com clareza o diagnóstico técnico do equipamento."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Diagnóstico Técnico do Reparo:", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rounded_rectangle([(110, 170), (1170, 320)], radius=8, fill=C_INPUT, outline=C_AZUL, width=2)
            draw.text((135, 195), "Falha no rolamento autocompensador do rotor da colheitadeira Case IH 8250.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((135, 230), "Ruído excessivo e aquecimento acima do normal durante colheita de milho.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((135, 265), "Necessário desmontagem da correia de acionamento e substituição do mancal.", fill=C_MUTED, font=FONTS["corpo"])

            draw.rounded_rectangle([(110, 350), (1170, 480)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((135, 375), "💡 Vantagem do Laudo Digital:", fill=C_AMARELO, font=FONTS["destaque"])
            draw.text((135, 415), "• O texto fica arquivado na O.S. e sai impresso no orçamento do cliente.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((135, 445), "• Evita contestações futuras e comprova a necessidade técnica da troca.", fill=C_TEXTO, font=FONTS["corpo"])

        elif p < 0.58:
            legenda = "2. Adicione as peças utilizadas com código, quantidade e preço unitário."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Lançamento de Peças Substituídas:", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rectangle([(110, 170), (1170, 215)], fill=(30, 41, 59))
            draw.text((130, 185), "ITEM / DESCRIÇÃO DA PEÇA", fill=C_MUTED, font=FONTS["tag"])
            draw.text((700, 185), "QTD", fill=C_MUTED, font=FONTS["tag"])
            draw.text((820, 185), "UNITÁRIO", fill=C_MUTED, font=FONTS["tag"])
            draw.text((1020, 185), "SUBTOTAL", fill=C_MUTED, font=FONTS["tag"])

            draw.rectangle([(110, 220), (1170, 275)], fill=C_INPUT)
            draw.text((130, 235), "01. Rolamento Autocompensador 22218", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((710, 235), "1 un", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((820, 235), "R$ 890,00", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((1020, 235), "R$ 890,00", fill=C_VERDE, font=FONTS["destaque"])

            draw.rounded_rectangle([(110, 310), (450, 370)], radius=8, fill=C_AZUL)
            draw.text((140, 330), "+ Adicionar Nova Peça", fill=(0, 0, 0), font=FONTS["destaque"])

            draw.rounded_rectangle([(110, 400), (1170, 520)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((135, 425), "Controle de Estoque & Fornecedores:", fill=C_AZUL, font=FONTS["destaque"])
            draw.text((135, 465), "• O sistema calcula os subtotais na hora, multiplicando a quantidade pelo preço.", fill=C_TEXTO, font=FONTS["corpo"])

        elif p < 0.80:
            legenda = "3. Lance a mão de obra especializada da equipe técnica."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Lançamento de Mão de Obra e Serviços:", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rectangle([(110, 170), (1170, 215)], fill=(30, 41, 59))
            draw.text((130, 185), "SERVIÇO EXECUTADO", fill=C_MUTED, font=FONTS["tag"])
            draw.text((650, 185), "MECÂNICO", fill=C_MUTED, font=FONTS["tag"])
            draw.text((1020, 185), "VALOR MÃO DE OBRA", fill=C_MUTED, font=FONTS["tag"])

            draw.rectangle([(110, 220), (1170, 280)], fill=C_INPUT)
            draw.text((130, 240), "Serviço de Alinhamento e Montagem de Rotor", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((650, 240), "Rodrigo Sanches", fill=C_AZUL, font=FONTS["corpo"])
            draw.text((1020, 240), "R$ 650,00", fill=C_VERDE, font=FONTS["destaque"])

            draw.rounded_rectangle([(110, 310), (1170, 520)], radius=8, fill=(20, 40, 60), outline=C_AZUL, width=1)
            draw.text((135, 335), "⚡ Diferencial Modo Equipe:", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((135, 380), "• Vinculação direta do mecânico executante à ordem de serviço.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((135, 415), "• Produtividade da oficina e comissionamento calculados sem esforço manual.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((135, 450), "• Total segurança nas aprovações de ordens de serviço de campo.", fill=C_TEXTO, font=FONTS["corpo"])

        else:
            legenda = "4. Totalização automática com soma de peças e serviços sem calculadora!"
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_VERDE, width=2)
            draw.text((110, 125), "Resumo Financeiro da Ordem de Serviço #1002", fill=C_TEXTO, font=FONTS["hero"])

            draw.rounded_rectangle([(110, 190), (600, 360)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((135, 215), "Subtotal de Peças:", fill=C_MUTED, font=FONTS["sub"])
            draw.text((135, 255), "R$ 890,00", fill=C_TEXTO, font=FONTS["hero"])
            draw.text((135, 305), "1 peça lançada (Rolamento Autocompensador)", fill=C_MUTED, font=FONTS["tag"])

            draw.rounded_rectangle([(640, 190), (1170, 360)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((665, 215), "Subtotal de Mão de Obra:", fill=C_MUTED, font=FONTS["sub"])
            draw.text((665, 255), "R$ 650,00", fill=C_TEXTO, font=FONTS["hero"])
            draw.text((665, 305), "Serviço técnico especializado de campo", fill=C_MUTED, font=FONTS["tag"])

            draw.rounded_rectangle([(110, 390), (1170, 520)], radius=12, fill=(20, 50, 35), outline=C_VERDE, width=2)
            draw.text((150, 425), "VALOR TOTAL DA O.S.:", fill=C_VERDE, font=FONTS["hero"])
            draw.text((650, 420), "R$ 1.540,00", fill=C_TEXTO, font=FONTS["hero"])
            draw.text((150, 475), "Cálculo automático efetuado com sucesso ✓", fill=C_VERDE, font=FONTS["sub"])

        desenhar_barra_inferior(draw, progresso, legenda)
        img.save(frames_dir / f"frame_{i:04d}.png")

    return frames_dir

# =========================================================================
# MÓDULO 04: Assinatura Digital Touch no Vidro
# =========================================================================
TEXTO_MOD04 = (
    "Para validar o serviço na lavoura, use a Assinatura Digital Touch. "
    "Mostre a tela do celular para o encarregado no campo e ele assina diretamente com a ponta do dedo no quadro em branco. "
    "Se errar ou precisar refazer, basta tocar no botão Limpar. "
    "A assinatura fica gravada com validade jurídica, carimbo de horário e identificação do responsável."
)

def gerar_quadros_mod04(duracao_total):
    frames_dir = SCRATCH_DIR / "frames_mod04"
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_quadros = int(duracao_total * FPS)

    for i in range(total_quadros):
        t = i / FPS
        progresso = i / total_quadros
        img = Image.new("RGB", (1280, 720), C_BG)
        draw = ImageDraw.Draw(img)

        desenhar_cabecalho(draw, "MÓDULO 04: ASSINATURA DIGITAL TOUCH NO VIDRO", "O.S. CAMPO", "✍️")

        p = t / duracao_total
        if p < 0.28:
            legenda = "1. Apresente a tela do celular para o operador ou encarregado no campo."
            draw.rounded_rectangle([(120, 95), (1160, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((150, 120), "Validação da Manutenção no Campo:", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((150, 155), "Ordem de Serviço #1002 • Fazenda Santa Cecília Agronegócios", fill=C_MUTED, font=FONTS["sub"])

            draw.rounded_rectangle([(150, 200), (1130, 480)], radius=8, fill=(255, 255, 255))
            draw.line([(190, 430), (1090, 430)], fill=(200, 200, 200), width=2)
            draw.text((190, 440), "Assine com a ponta do dedo no quadro acima", fill=(150, 150, 150), font=FONTS["tag"])

            draw.rounded_rectangle([(150, 510), (1130, 565)], radius=8, fill=C_INPUT, outline=C_AZUL, width=1)
            draw.text((180, 528), "📱 Tela otimizada para toque capacitivo em qualquer smartphone ou tablet.", fill=C_AZUL, font=FONTS["sub"])

        elif p < 0.58:
            legenda = "2. O encarregado assina diretamente com a ponta do dedo no quadro branco."
            draw.rounded_rectangle([(120, 95), (1160, 600)], radius=12, fill=C_CARD, outline=C_AZUL, width=2)
            draw.text((150, 120), "Colhendo Visto Digital...", fill=C_VERDE, font=FONTS["card_tit"])

            draw.rounded_rectangle([(150, 180), (1130, 460)], radius=8, fill=(255, 255, 255))
            draw.line([(190, 410), (1090, 410)], fill=(200, 200, 200), width=2)

            pts_prog = int(14 * ((p - 0.28) / 0.30))
            pts_prog = max(2, min(14, pts_prog))
            pontos_totais = [
                (230, 360), (280, 280), (320, 390), (370, 290), (410, 360),
                (470, 340), (530, 380), (600, 320), (670, 370), (740, 310),
                (820, 360), (900, 340), (970, 370), (1030, 350)
            ]
            draw.line(pontos_totais[:pts_prog], fill=(15, 23, 42), width=4)

            cx, cy = pontos_totais[pts_prog - 1]
            draw.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=C_AZUL)

            draw.rounded_rectangle([(150, 490), (400, 555)], radius=8, fill=(50, 20, 20), outline=C_VERMELHO, width=1)
            draw.text((210, 512), "🗑️ Limpar", fill=C_VERMELHO, font=FONTS["destaque"])

            draw.rounded_rectangle([(430, 490), (1130, 555)], radius=8, fill=C_VERDE)
            draw.text((630, 512), "✓ Salvar Assinatura", fill=(0, 0, 0), font=FONTS["destaque"])

        elif p < 0.80:
            legenda = "3. Se errar, toque em Limpar e faça novamente com facilidade."
            draw.rounded_rectangle([(120, 95), (1160, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((150, 120), "Controle e Facilidade de Correção:", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rounded_rectangle([(150, 180), (600, 460)], radius=8, fill=C_INPUT, outline=C_VERMELHO, width=2)
            draw.text((180, 210), "Botão Limpar Imediato:", fill=C_VERMELHO, font=FONTS["card_tit"])
            draw.text((180, 260), "• O operador pode apagar com 1 toque se o traço", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((180, 290), "  sair imperfeito ou trêmulo no campo.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((180, 340), "• Permite refazer quantas vezes forem necessárias.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.rounded_rectangle([(180, 390), (430, 440)], radius=6, fill=(50, 20, 20), outline=C_VERMELHO, width=1)
            draw.text((230, 405), "🗑️ Limpar Tela", fill=C_VERMELHO, font=FONTS["destaque"])

            draw.rounded_rectangle([(640, 180), (1130, 460)], radius=8, fill=C_INPUT, outline=C_VERDE, width=2)
            draw.text((670, 210), "Botão Confirmar:", fill=C_VERDE, font=FONTS["card_tit"])
            draw.text((670, 260), "• Grava o visto criptografado no banco de dados.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((670, 290), "• Anexa automaticamente no cabeçalho do PDF.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.rounded_rectangle([(670, 390), (1050, 440)], radius=6, fill=C_VERDE)
            draw.text((750, 405), "✓ Confirmar Visto", fill=(0, 0, 0), font=FONTS["destaque"])

        else:
            legenda = "4. Assinatura gravada com carimbo de data, horário e validade jurídica."
            draw.rounded_rectangle([(120, 95), (1160, 600)], radius=12, fill=C_CARD, outline=C_VERDE, width=2)
            draw.text((150, 125), "Assinatura Digital Autenticada com Sucesso ✓", fill=C_VERDE, font=FONTS["hero"])

            draw.rounded_rectangle([(150, 190), (1130, 480)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((180, 220), "Certificado de Conformidade Operacional:", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((180, 270), "• Responsável: Eduardo Silveira (Encarregado de Frota)", fill=C_TEXTO, font=FONTS["destaque"])
            draw.text((180, 310), "• Empresa: Fazenda Santa Cecília Agronegócios", fill=C_TEXTO, font=FONTS["destaque"])
            draw.text((180, 350), "• Data e Hora: 15/09/2026 às 11:30:45", fill=C_AMARELO, font=FONTS["destaque"])
            draw.text((180, 390), "• Hash Digital: SHA256 e849cf29a8f... (Inviolável)", fill=C_MUTED, font=FONTS["corpo"])

        desenhar_barra_inferior(draw, progresso, legenda)
        img.save(frames_dir / f"frame_{i:04d}.png")

    return frames_dir

# =========================================================================
# MÓDULO 05: Envio ao WhatsApp com 1 Toque & Modo Equipe
# =========================================================================
TEXTO_MOD05 = (
    "No final da tela, toque no botão verde para enviar o comprovante ao cliente pelo WhatsApp com apenas um toque. "
    "A mensagem abre com o resumo completo e o link do documento assinado. "
    "Se sua oficina possui equipe de mecânicos, eles enviam o retorno do campo e o gestor pode revisar, solicitar ajustes ou aprovar na hora antes do faturamento final."
)

def gerar_quadros_mod05(duracao_total):
    frames_dir = SCRATCH_DIR / "frames_mod05"
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_quadros = int(duracao_total * FPS)

    for i in range(total_quadros):
        t = i / FPS
        progresso = i / total_quadros
        img = Image.new("RGB", (1280, 720), C_BG)
        draw = ImageDraw.Draw(img)

        desenhar_cabecalho(draw, "MÓDULO 05: ENVIO AO WHATSAPP & RETORNO DE EQUIPE", "GESTÃO & CAMPO", "📲")

        p = t / duracao_total
        if p < 0.30:
            legenda = "1. Toque no botão verde de 100% de largura para disparar o WhatsApp."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 125), "Finalização da O.S. no Aplicativo Mobile:", fill=C_TEXTO, font=FONTS["hero"])
            draw.text((110, 170), "Ordem de Serviço #1002 validada e pronta para envio:", fill=C_MUTED, font=FONTS["sub"])

            draw.rounded_rectangle([(110, 240), (1170, 360)], radius=16, fill=C_VERDE, outline=(255, 255, 255), width=2)
            draw.text((220, 275), "📲 ENVIAR COMPROVANTE VIA WHATSAPP (1 TOQUE)", fill=(0, 0, 0), font=FONTS["hero"])

            draw.rounded_rectangle([(110, 400), (1170, 520)], radius=8, fill=C_INPUT, outline=C_AZUL, width=1)
            draw.text((140, 425), "⚡ Disparo Inteligente:", fill=C_AZUL, font=FONTS["destaque"])
            draw.text((140, 465), "• O sistema busca o telefone do solicitante (Eduardo Silveira) e monta o link oficial.", fill=C_TEXTO, font=FONTS["corpo"])

        elif p < 0.58:
            legenda = "2. A mensagem abre completa no WhatsApp com resumo e link do PDF."
            draw.rectangle([(0, 70), (1280, 640)], fill=C_WA_BG)

            draw.rectangle([(0, 70), (1280, 140)], fill=C_WA_HEADER)
            draw.text((80, 90), "Eduardo Silveira • Fazenda Santa Cecília Agronegócios", fill=C_TEXTO, font=FONTS["tit"])

            draw.rounded_rectangle([(300, 170), (1200, 550)], radius=12, fill=C_WA_MSG_OUT)
            draw.text((330, 195), "Olá Eduardo Silveira! Seu atendimento foi finalizado.", fill=C_WA_VERDE, font=FONTS["card_tit"])
            draw.text((330, 240), "📋 ORDEM DE SERVIÇO: #1002 (CONCLUÍDA)", fill=C_TEXTO, font=FONTS["destaque"])
            draw.text((330, 275), "🚜 Equipamento: Colheitadeira Case IH 8250 (Frota 204)", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((330, 310), "⏱️ Horímetro Registrado: 1.850 h", fill=C_AMARELO, font=FONTS["corpo"])
            draw.text((330, 345), "💰 Total: R$ 1.540,00  |  Mecânico: Rodrigo Sanches", fill=C_TEXTO, font=FONTS["corpo"])

            draw.rounded_rectangle([(330, 395), (1160, 490)], radius=8, fill=(17, 27, 33))
            draw.text((350, 415), "📄 COMPROVANTE_OS_1002_ASSINADO.PDF", fill=C_AZUL, font=FONTS["destaque"])
            draw.text((350, 450), "Clique para baixar o comprovante oficial com visto digital", fill=C_MUTED, font=FONTS["tag"])
            draw.text((1110, 510), "11:32 ✓✓", fill=C_AZUL, font=FONTS["tag"])

        elif p < 0.80:
            legenda = "3. Modo Equipe: O mecânico envia o retorno e o gestor aprova ou devolve."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Gestão de Equipe & Controle de Retorno de Campo:", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rounded_rectangle([(110, 170), (1170, 360)], radius=8, fill=C_INPUT, outline=C_AMARELO, width=2)
            draw.text((135, 195), "O.S. #1003 • Pulverizador Jacto Uniport 3030 (Frota 308)", fill=C_TEXTO, font=FONTS["destaque"])
            draw.text((135, 230), "Mecânico: Marcos Vinicius  |  Cliente: Cerealista São Pedro", fill=C_MUTED, font=FONTS["sub"])
            draw.text((135, 270), "Status do Retorno: AGUARDANDO ANÁLISE DO GESTOR", fill=C_AMARELO, font=FONTS["destaque"])

            draw.rounded_rectangle([(135, 305), (550, 350)], radius=6, fill=C_VERDE)
            draw.text((200, 320), "✓ APROVAR RETORNO", fill=(0, 0, 0), font=FONTS["destaque"])

            draw.rounded_rectangle([(580, 305), (1050, 350)], radius=6, fill=(50, 20, 20), outline=C_VERMELHO, width=1)
            draw.text((610, 320), "⚠️ REENVIAR PARA CORREÇÃO (PENDÊNCIA)", fill=C_VERMELHO, font=FONTS["destaque"])

            draw.rounded_rectangle([(110, 385), (1170, 520)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((135, 410), "Se houver fotos faltando ou laudo incompleto:", fill=C_TEXTO, font=FONTS["destaque"])
            draw.text((135, 445), "• O gestor devolve a O.S. apontando a pendência (ex: falta de teste de pressão).", fill=C_MUTED, font=FONTS["corpo"])
            draw.text((135, 475), "• O mecânico refaz no campo e reenvia corrigida (ex: O.S. #1004 da Usina Alvorada).", fill=C_MUTED, font=FONTS["corpo"])

        else:
            legenda = "4. Retorno aprovado segue direto para faturamento e emissão de orçamento!"
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_VERDE, width=2)
            draw.text((110, 125), "Fluxo Operacional Concluído com Sucesso!", fill=C_VERDE, font=FONTS["hero"])

            draw.rounded_rectangle([(110, 190), (1170, 480)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((140, 220), "Integração Campo -> Oficina -> Financeiro:", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((140, 270), "✓ O.S. #1001 (Modo Solo) - Concluída e Faturada (R$ 1.250,00)", fill=C_VERDE, font=FONTS["destaque"])
            draw.text((140, 310), "✓ O.S. #1002 (Modo Equipe) - Retorno Aprovado (R$ 1.540,00)", fill=C_AZUL, font=FONTS["destaque"])
            draw.text((140, 350), "⏳ O.S. #1003 - Reenviada para Correção ao Técnico Marcos Vinicius", fill=C_AMARELO, font=FONTS["destaque"])
            draw.text((140, 390), "🔍 O.S. #1004 - Retornada da Correção pelo Técnico Lucas Biazon", fill=C_TEXTO, font=FONTS["destaque"])

        desenhar_barra_inferior(draw, progresso, legenda)
        img.save(frames_dir / f"frame_{i:04d}.png")

    return frames_dir

# =========================================================================
# MÓDULO 06: Modelos de Orçamento (Padrão Corporativo & Novos Fornecedores)
# =========================================================================
TEXTO_MOD06 = (
    "Veja como é simples e flexível escolher o modelo de orçamento! "
    "O sistema opera por padrão com o Modelo Corporativo Nativo da sua oficina, pronto para faturamento. "
    "Caso precise emitir no padrão de um parceiro, você conta com os modelos Terra Viva em PDF, Sultratores em planilha Excel e Alvorada em proposta Word. "
    "Basta escolher no menu e o layout se adapta imediatamente!"
)

def gerar_quadros_mod06(duracao_total):
    frames_dir = SCRATCH_DIR / "frames_mod06"
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_quadros = int(duracao_total * FPS)

    for i in range(total_quadros):
        t = i / FPS
        progresso = i / total_quadros
        img = Image.new("RGB", (1280, 720), C_BG)
        draw = ImageDraw.Draw(img)

        desenhar_cabecalho(draw, "MÓDULO 06: MODELOS DE ORÇAMENTO PERSONALIZADOS", "NOVO PROCESSO ATUALIZADO 🔔", "📄")

        p = t / duracao_total
        if p < 0.28:
            legenda = "1. O sistema opera por padrão com o Modelo Corporativo Nativo."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Seletor de Modelos de Orçamento:", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rounded_rectangle([(110, 170), (620, 230)], radius=8, fill=C_INPUT, outline=C_AZUL, width=2)
            draw.text((130, 188), "✓ [ Modelo Padrão do Sistema ]", fill=C_AZUL, font=FONTS["destaque"])
            draw.text((580, 188), "▼", fill=C_AZUL, font=FONTS["destaque"])

            draw.rounded_rectangle([(110, 245), (620, 520)], radius=8, fill=(15, 23, 42), outline=C_BORDA, width=1)
            modelos = [
                ("• [ Modelo Padrão do Sistema ] (Oficina Própria)", True, C_AZUL),
                ("• Terra Viva Agromecânica (Modelo PDF)", False, C_TEXTO),
                ("• Sultratores Manutenção (Modelo Excel)", False, C_TEXTO),
                ("• Alvorada Soluções Mecânicas (Modelo Word)", False, C_TEXTO),
            ]
            for idx, (mtit, sel, mcor) in enumerate(modelos):
                my = 260 + idx * 62
                if sel:
                    draw.rounded_rectangle([(120, my), (610, my + 50)], radius=6, fill=(20, 40, 65), outline=C_AZUL, width=1)
                    draw.text((135, my + 14), mtit, fill=mcor, font=FONTS["destaque"])
                else:
                    draw.text((135, my + 14), mtit, fill=mcor, font=FONTS["corpo"])

            draw.rounded_rectangle([(660, 170), (1170, 520)], radius=8, fill=C_INPUT, outline=C_VERDE, width=1)
            draw.text((690, 195), "PREVIEW: MODELO PADRÃO CORPORATIVO", fill=C_VERDE, font=FONTS["destaque"])
            draw.text((690, 240), "OFICINA DIESEL & AGRO MECÂNICA LTDA.", fill=C_TEXTO, font=FONTS["card_tit"])
            draw.text((690, 275), "CNPJ: 14.892.310/0001-44 • Paranavaí - PR", fill=C_MUTED, font=FONTS["tag"])
            draw.line([(690, 305), (1140, 305)], fill=C_BORDA, width=1)
            draw.text((690, 325), "Cliente: Agropecuária Vale Verde Ltda.", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((690, 355), "Frota 101 • Trator Massey Ferguson 7719", fill=C_MUTED, font=FONTS["corpo"])
            draw.text((690, 395), "Total Orçado: R$ 1.250,00", fill=C_AMARELO, font=FONTS["destaque"])

        elif p < 0.55:
            legenda = "2. Alterne para o Modelo Terra Viva Agromecânica (PDF Oficial)."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Modelo Selecionado: Terra Viva Agromecânica", fill=C_VERDE, font=FONTS["card_tit"])

            draw.rounded_rectangle([(110, 170), (620, 230)], radius=8, fill=(20, 50, 35), outline=C_VERDE, width=2)
            draw.text((130, 188), "✓ Terra Viva Agromecânica (Modelo PDF)", fill=C_VERDE, font=FONTS["destaque"])

            draw.rounded_rectangle([(110, 250), (1170, 530)], radius=8, fill=(255, 255, 255))
            draw.rectangle([(110, 250), (1170, 320)], fill=(34, 110, 60))
            draw.text((140, 265), "TERRA VIVA AGROMECÂNICA • ORÇAMENTO TÉCNICO", fill=(255, 255, 255), font=FONTS["card_tit"])
            draw.text((140, 295), "Estrutura padrão concessionária / revenda autorizada", fill=(220, 255, 230), font=FONTS["tag"])

            draw.text((140, 345), "Cliente: Fazenda Santa Cecília Agronegócios  |  O.S. #1002", fill=(15, 23, 42), font=FONTS["destaque"])
            draw.text((140, 385), "Máquina: Colheitadeira Case IH 8250 (Frota 204)  |  Horímetro: 1.850 h", fill=(60, 60, 60), font=FONTS["corpo"])
            draw.text((140, 425), "Subtotal Peças: R$ 890,00  |  Mão de Obra: R$ 650,00", fill=(60, 60, 60), font=FONTS["corpo"])
            draw.rounded_rectangle([(140, 465), (550, 510)], radius=6, fill=(34, 110, 60))
            draw.text((160, 478), "TOTAL PROPOSTA: R$ 1.540,00", fill=(255, 255, 255), font=FONTS["destaque"])

        elif p < 0.80:
            legenda = "3. Modelos em Planilha Excel (Sultratores) e Proposta Word (Alvorada)."
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_BORDA, width=1)
            draw.text((110, 120), "Outros Modelos Disponíveis no Dropdown:", fill=C_AZUL, font=FONTS["card_tit"])

            draw.rounded_rectangle([(110, 170), (620, 520)], radius=8, fill=C_INPUT, outline=C_VERDE, width=2)
            draw.text((135, 195), "📊 Sultratores Manutenção (Excel)", fill=C_VERDE, font=FONTS["card_tit"])
            draw.text((135, 235), "Grade estilo planilha eletrônica com colunas:", fill=C_MUTED, font=FONTS["sub"])
            draw.text((135, 275), "• Cód. Fornecedor | Descrição | Qtd | Un | Total", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((135, 315), "• Layout idêntico ao modelo de planilha fornecido", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((135, 355), "• Ideal para conciliação contábil de peças", fill=C_MUTED, font=FONTS["corpo"])
            draw.rounded_rectangle([(135, 430), (590, 490)], radius=6, fill=(20, 50, 35))
            draw.text((160, 448), "Formato Planilha Ativo ✓", fill=C_VERDE, font=FONTS["destaque"])

            draw.rounded_rectangle([(660, 170), (1170, 520)], radius=8, fill=C_INPUT, outline=C_AZUL, width=2)
            draw.text((685, 195), "📝 Alvorada Soluções (Word / Proposta)", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((685, 235), "Formato proposta comercial executiva:", fill=C_MUTED, font=FONTS["sub"])
            draw.text((685, 275), "• Termos de garantia, condições e prazos", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((685, 315), "• Apresentação visual limpa para diretoria", fill=C_TEXTO, font=FONTS["corpo"])
            draw.text((685, 355), "• Layout correspondente à imagem enviada", fill=C_MUTED, font=FONTS["corpo"])
            draw.rounded_rectangle([(685, 430), (1140, 490)], radius=6, fill=(20, 40, 65))
            draw.text((710, 448), "Formato Proposta Ativo ✓", fill=C_AZUL, font=FONTS["destaque"])

        else:
            legenda = "4. Total liberdade: use o padrão do sistema ou qualquer modelo parceiro!"
            draw.rounded_rectangle([(80, 95), (1200, 600)], radius=12, fill=C_CARD, outline=C_VERDE, width=2)
            draw.text((110, 125), "Catálogo de Modelos Completo & Sem Restrições", fill=C_TEXTO, font=FONTS["hero"])

            draw.rounded_rectangle([(110, 190), (1170, 480)], radius=8, fill=C_INPUT, outline=C_BORDA, width=1)
            draw.text((140, 220), "Modelos Homologados no Sistema:", fill=C_AZUL, font=FONTS["card_tit"])
            draw.text((140, 270), "1. Modelo Padrão do Sistema (Oficina Diesel & Agro Mecânica)", fill=C_AZUL, font=FONTS["destaque"])
            draw.text((140, 310), "2. Terra Viva Agromecânica (Modelo PDF)", fill=C_VERDE, font=FONTS["destaque"])
            draw.text((140, 350), "3. Sultratores Manutenção & Peças (Modelo Planilha Excel)", fill=C_AMARELO, font=FONTS["destaque"])
            draw.text((140, 390), "4. Alvorada Soluções Mecânicas (Modelo Word / Proposta)", fill=C_TEXTO, font=FONTS["destaque"])

        desenhar_barra_inferior(draw, progresso, legenda)
        img.save(frames_dir / f"frame_{i:04d}.png")

    return frames_dir

# =========================================================================
# CONFIGURAÇÃO DOS 7 MÓDULOS
# =========================================================================
MODULOS = [
    {
        "id": 0,
        "nome": "modulo_00_visao_geral",
        "titulo": "Apresentação: O Que É a Plataforma & Benefícios Reais",
        "categoria": "Institucional",
        "descricao": "Visão geral executiva de como o sistema e o app eliminam a burocracia do papel, controlam horímetro de maquinário e aceleram o faturamento.",
        "texto": TEXTO_MOD00,
        "gerador_quadros": gerar_quadros_mod00,
        "roteiro": [
            "Sem papel ou pranchetas molhadas: gerencie manutenções de frotas com clareza e precisão.",
            "Conecte a equipe técnica no campo, a oficina e o escritório em uma única plataforma.",
            "Pelo celular o técnico anota peças, horímetro e colhe o visto digital na hora.",
            "Mais controle para a frota, zero burocracia e total transparência para o cliente."
        ],
        "o_que_mudou": "Nova versão executiva com dados 100% fictícios e sem cortes de áudio."
    },
    {
        "id": 1,
        "nome": "modulo_01_fluxo_completo",
        "titulo": "Simulação 01: Do WhatsApp ao Comprovante Pronto",
        "categoria": "O.S. Campo",
        "descricao": "O cliente solicita atendimento pelo WhatsApp, você abre a O.S. no celular, o operador assina com o dedo e o comprovante volta na conversa.",
        "texto": TEXTO_MOD01,
        "gerador_quadros": gerar_quadros_mod01,
        "roteiro": [
            "O cliente da Agropecuária Vale Verde manda pedido de socorro no WhatsApp.",
            "Você abre o aplicativo no celular e seleciona o Trator 101 com um toque.",
            "O sistema preenche a frota e você anota a troca da mangueira hidráulica.",
            "O encarregado assina com o dedo na tela do celular.",
            "Você aperta Enviar WhatsApp e o comprovante chega na hora com check azul!"
        ],
        "o_que_mudou": "Atualizado com dados 100% fictícios (Agropecuária Vale Verde) e áudio completo sem cortes."
    },
    {
        "id": 2,
        "nome": "modulo_02_dados_frota",
        "titulo": "Módulo 02: Frota & Horímetro / KM",
        "categoria": "O.S. Campo",
        "descricao": "Seleção do cliente, localização do veículo por placa/frota e lançamento rápido do horímetro.",
        "texto": TEXTO_MOD02,
        "gerador_quadros": gerar_quadros_mod02,
        "roteiro": [
            "Escolha a Fazenda Santa Cecília na busca rápida.",
            "Digite a frota 204 para carregar a Colheitadeira Case IH 8250.",
            "Anote o horímetro de 1.850 horas exibido no painel de instrumentos.",
            "Tudo fica salvo com data, hora e histórico de manutenção inviolável."
        ],
        "o_que_mudou": "Vídeo e áudio gerados com simulação da Colheitadeira 204 e horímetro de 1.850h."
    },
    {
        "id": 3,
        "nome": "modulo_03_pecas_servicos",
        "titulo": "Módulo 03: Peças & Serviços",
        "categoria": "O.S. Campo",
        "descricao": "Preenchimento do diagnóstico mecânico, inserção de peças trocadas e soma automática do total.",
        "texto": TEXTO_MOD03,
        "gerador_quadros": gerar_quadros_mod03,
        "roteiro": [
            "Descreva o diagnóstico técnico de falha no rolamento do rotor.",
            "Toque em Adicionar Peça e digite a quantidade e valor unitário.",
            "Insira a mão de obra especializada do mecânico Rodrigo Sanches.",
            "O sistema calcula os subtotais e soma o valor total de R$ 1.540,00 sozinho!"
        ],
        "o_que_mudou": "Totalização automática demonstrada com dados da O.S. 1002 sem uso de calculadora."
    },
    {
        "id": 4,
        "nome": "modulo_04_assinatura_digital",
        "titulo": "Módulo 04: Assinatura Digital Touch",
        "categoria": "O.S. Campo",
        "descricao": "Assinatura do operador ou encarregado direto no vidro do celular, com carimbo de horário.",
        "texto": TEXTO_MOD04,
        "gerador_quadros": gerar_quadros_mod04,
        "roteiro": [
            "Mostre a tela do celular para o encarregado Eduardo Silveira na lavoura.",
            "Ele assina com a ponta do dedo no quadro em branco.",
            "Se errar, aperte Limpar e faça novamente com facilidade.",
            "A assinatura fica gravada com validade jurídica e carimbo criptografado."
        ],
        "o_que_mudou": "Animação realista de assinatura no vidro com autenticação por carimbo digital."
    },
    {
        "id": 5,
        "nome": "modulo_05_retorno_whatsapp",
        "titulo": "Módulo 05: Envio ao WhatsApp com 1 Toque & Modo Equipe",
        "categoria": "O.S. Campo",
        "descricao": "Disparo direto ao WhatsApp do cliente com link do comprovante e gestão de retornos de equipe com aprovação ou pendência.",
        "texto": TEXTO_MOD05,
        "gerador_quadros": gerar_quadros_mod05,
        "roteiro": [
            "No final da tela, toque no botão verde Enviar WhatsApp de largura total.",
            "A mensagem abre com resumo completo e link do comprovante assinado.",
            "No Modo Equipe, o gestor avalia o retorno do técnico de campo.",
            "Aprove a ordem ou devolva com pendência antes do faturamento final."
        ],
        "o_que_mudou": "Fluxo com botão verde 100% e demonstração de retorno aprovado e reenviado para correção."
    },
    {
        "id": 6,
        "nome": "modulo_06_modelos_orcamento",
        "titulo": "Módulo 06: Modelos de Orçamento (Padrão Corporativo & Fornecedores)",
        "categoria": "Orçamento",
        "descricao": "O sistema opera por padrão com o Modelo Corporativo Nativo da sua empresa. Fornecedores e modelos parceiros (Terra Viva PDF, Sultratores Excel e Alvorada Word) ficam disponíveis no seletor para escolha livre!",
        "texto": TEXTO_MOD06,
        "gerador_quadros": gerar_quadros_mod06,
        "roteiro": [
            "O sistema opera por padrão com o Modelo Corporativo Nativo da sua empresa.",
            "Alterne no menu para o modelo Terra Viva Agromecânica em formato PDF.",
            "Utilize os formatos Sultratores em planilha Excel ou Alvorada em proposta Word.",
            "Total controle e liberdade para escolher qual layout atende cada cliente."
        ],
        "o_que_mudou": "Inclusão dos 3 novos modelos de layout solicitados (Terra Viva, Sultratores e Alvorada)."
    }
]

async def processar_modulo(mod):
    mod_id = mod["id"]
    nome = mod["nome"]
    texto = mod["texto"]
    print(f"\n==================================================")
    print(f"PROCESSANDO MÓDULO {mod_id:02d}: {mod['titulo']}")
    print(f"==================================================")

    audio_path = SCRATCH_DIR / f"audio_{nome}.mp3"
    video_saida = OUTPUT_DIR / f"{nome}.mp4"

    # 1. Gerar áudio
    await gerar_audio_tts(texto, audio_path)

    # 2. Medir tempo real exato do áudio com ffprobe
    duracao_audio = obter_duracao_audio(audio_path)
    # Adicionamos 1.5s de margem de conforto/respiro no final para NUNCA cortar
    duracao_total = duracao_audio + 1.5
    print(f"[TEMPO] Áudio: {duracao_audio:.2f}s | Vídeo Total com margem: {duracao_total:.2f}s")

    # 3. Gerar quadros
    frames_dir = mod["gerador_quadros"](duracao_total)

    # 4. Compilar com FFmpeg
    compilar_video(frames_dir, audio_path, video_saida, duracao_total, fps=FPS)

    # 5. Atualizar metadados
    dur_seg = int(round(duracao_total))
    return {
        "id": mod_id,
        "titulo": mod["titulo"],
        "duracao": f"⏱️ {dur_seg} seg",
        "categoria": mod["categoria"],
        "descricao": mod["descricao"],
        "voz_ativa": "antonio",
        "video_ativo": f"/videos/tutoriais/{nome}.mp4",
        "atualizado_em": "15/09/2026",
        "o_que_mudou": mod["o_que_mudou"],
        "roteiro": mod["roteiro"]
    }

async def main():
    print("Iniciando geração em lote dos 7 vídeos tutoriais...")
    tutoriais_config = {}

    for mod in MODULOS:
        info = await processar_modulo(mod)
        tutoriais_config[str(mod["id"])] = info

    # Salvar tutoriais_config.json
    config_file = DATA_DIR / "tutoriais_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(tutoriais_config, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Configuração de tutoriais salva em: {config_file}")
    print("Todos os 7 vídeos tutoriais foram gerados com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
