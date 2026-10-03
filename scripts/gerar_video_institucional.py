#!/usr/bin/env python3
"""
Gerador do Vídeo Explicativo Institucional (Apresentação da Plataforma & Benefícios)
Duração: ~30 segundos
Linguagem: Convincente, profissional, sem exageros ou promessas irreais.
Renderização: Edge-TTS (pt-BR-AntonioNeural) + Pillow + FFmpeg
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

TEXTO_INSTITUCIONAL = (
    "Gerenciar manutenções de máquinas e frotas pesadas não precisa depender de papel, pranchetas ou anotações perdidas. "
    "Nossa plataforma integra a oficina, a equipe técnica em campo e o cliente final em tempo real. "
    "Pelo aplicativo, o técnico registra o atendimento, controla peças, KM e horímetro, e coleta a assinatura digital na hora. "
    "No escritório, você acompanha os custos e envia orçamentos e comprovantes pelo WhatsApp com um clique. "
    "Mais controle para a frota, zero burocracia e total transparência para o cliente."
)

async def gerar_audio_institucional(texto, arquivo_saida):
    import edge_tts
    # Voz calma, executiva e profissional
    comunicador = edge_tts.Communicate(texto, "pt-BR-AntonioNeural", rate="+2%", pitch="-1Hz")
    await comunicador.save(str(arquivo_saida))
    print(f"[OK] Áudio institucional gerado: {arquivo_saida}")

def criar_quadros_institucionais(duracao_total=30, fps=15):
    total_quadros = int(duracao_total * fps)
    frames_dir = SCRATCH_DIR / "frames_institucional"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Paleta Corporativa Slate Dark
    COR_BG = (11, 15, 23)                # #0b0f17
    COR_CARD = (19, 27, 46)              # #131b2e
    COR_HEADER = (15, 23, 42)            # #0f172a
    COR_AZUL_ACCENT = (56, 189, 248)     # #38bdf8
    COR_VERDE_STATUS = (52, 211, 153)    # #34d399
    COR_AMBAR_ALERTA = (245, 158, 11)    # #f59e0b
    COR_TEXTO_BRANCO = (248, 250, 252)
    COR_TEXTO_MUTED = (148, 163, 184)

    try:
        fonte_hero = ImageFont.truetype("arialbd.ttf", 34)
        fonte_tit = ImageFont.truetype("arialbd.ttf", 26)
        fonte_sub = ImageFont.truetype("arial.ttf", 18)
        fonte_corpo = ImageFont.truetype("arial.ttf", 21)
        fonte_destaque = ImageFont.truetype("arialbd.ttf", 22)
        fonte_tag = ImageFont.truetype("arialbd.ttf", 13)
        fonte_legenda = ImageFont.truetype("arialbd.ttf", 20)
    except:
        fonte_hero = ImageFont.load_default()
        fonte_tit = fonte_hero
        fonte_sub = fonte_hero
        fonte_corpo = fonte_hero
        fonte_destaque = fonte_hero
        fonte_tag = fonte_hero
        fonte_legenda = fonte_hero

    print(f"Renderizando {total_quadros} quadros institucionais...")

    for i in range(total_quadros):
        t = i / fps

        img = Image.new("RGB", (1280, 720), COR_BG)
        draw = ImageDraw.Draw(img)

        # Barra Superior de Identidade Corporativa
        draw.rectangle([(0, 0), (1280, 70)], fill=COR_HEADER)
        draw.rounded_rectangle([(30, 16), (68, 54)], radius=8, fill=(56, 189, 248, 30), outline=COR_AZUL_ACCENT, width=1)
        draw.text((40, 20), "⚙️", font=fonte_tit)
        draw.text((80, 22), "PLATAFORMA DE GESTÃO DE MANUTENÇÃO & FROTAS", fill=COR_TEXTO_BRANCO, font=fonte_tit)

        draw.rounded_rectangle([(990, 18), (1250, 52)], radius=16, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        draw.text((1010, 26), "APRESENTAÇÃO EXECUTIVA", fill=COR_AZUL_ACCENT, font=fonte_tag)

        # CENA 1 (0s a 7.5s): O DESAFIO DA OPERAÇÃO TRADICIONAL
        if t < 7.5:
            draw.text((60, 105), "O Desafio Tradicional da Manutenção Pesada", fill=COR_TEXTO_BRANCO, font=fonte_hero)
            draw.text((60, 150), "Operações que dependem de formulários de papel enfrentam gargalos diários:", fill=COR_TEXTO_MUTED, font=fonte_sub)

            # 3 Cards de Dor Operacional
            cards_dor = [
                ("📋 Papéis & Pranchetas", "Anotações ilegíveis, fichas molhadas na lavoura ou perdidas no trânsito.", (239, 68, 68)),
                ("⏳ Lentidão no Fechamento", "Dias até a ordem física chegar da fazenda para o escritório faturar.", (245, 158, 11)),
                ("📉 Falta de Rastreabilidade", "Dificuldade para comprovar peças trocadas e histórico do horímetro.", (148, 163, 184))
            ]
            for idx, (c_tit, c_desc, c_cor) in enumerate(cards_dor):
                x = 60 + idx * 390
                draw.rounded_rectangle([(x, 195), (x + 370, 420)], radius=12, fill=COR_CARD, outline=(51, 65, 85), width=1)
                draw.rounded_rectangle([(x + 20, 215), (x + 350, 255)], radius=6, fill=(15, 23, 42), outline=c_cor, width=1)
                draw.text((x + 30, 224), c_tit, fill=c_cor, font=fonte_destaque)
                draw.text((x + 20, 280), c_desc[:38], fill=COR_TEXTO_BRANCO, font=fonte_corpo)
                draw.text((x + 20, 310), c_desc[38:80], fill=COR_TEXTO_BRANCO, font=fonte_corpo)
                draw.text((x + 20, 340), c_desc[80:], fill=COR_TEXTO_MUTED, font=fonte_sub)

            legenda_texto = "Sem papel ou anotações perdidas: gerencie frotas e manutenções com clareza."

        # CENA 2 (7.5s a 15.5s): A SOLUÇÃO INTEGRADA (CAMPO + ESCRITÓRIO)
        elif t < 15.5:
            draw.text((60, 105), "A Solução: Operação em Campo Conectada ao Painel", fill=COR_TEXTO_BRANCO, font=fonte_hero)
            draw.text((60, 150), "Um ecossistema moderno que liga quem está com a graxa na mão ao financeiro:", fill=COR_TEXTO_MUTED, font=fonte_sub)

            # Coluna 1: O Aplicativo de Campo
            draw.rounded_rectangle([(60, 195), (630, 450)], radius=12, fill=COR_CARD, outline=COR_AZUL_ACCENT, width=1)
            draw.rounded_rectangle([(80, 215), (320, 255)], radius=6, fill=(56, 189, 248, 25), outline=COR_AZUL_ACCENT, width=1)
            draw.text((95, 224), "📱 APLICATIVO EM CAMPO", fill=COR_AZUL_ACCENT, font=fonte_tag)
            draw.text((80, 275), "• Abertura rápida de chamados no celular", fill=COR_TEXTO_BRANCO, font=fonte_corpo)
            draw.text((80, 315), "• Controle de peças aplicadas e horímetro", fill=COR_TEXTO_BRANCO, font=fonte_corpo)
            draw.text((80, 355), "• Assinatura touch com validade jurídica", fill=COR_TEXTO_BRANCO, font=fonte_corpo)
            draw.text((80, 395), "• Funciona na lavoura, estrada ou oficina", fill=COR_TEXTO_MUTED, font=fonte_sub)

            # Coluna 2: O Painel de Gestão & Faturamento
            draw.rounded_rectangle([(650, 195), (1220, 450)], radius=12, fill=COR_CARD, outline=COR_VERDE_STATUS, width=1)
            draw.rounded_rectangle([(670, 215), (910, 255)], radius=6, fill=(52, 211, 153, 25), outline=COR_VERDE_STATUS, width=1)
            draw.text((685, 224), "🖥️ PAINEL DE CONTROLE", fill=COR_VERDE_STATUS, font=fonte_tag)
            draw.text((670, 275), "• Gestão de ordens abertas e faturamento", fill=COR_TEXTO_BRANCO, font=fonte_corpo)
            draw.text((670, 315), "• Cálculo automático de totais e margens", fill=COR_TEXTO_BRANCO, font=fonte_corpo)
            draw.text((670, 355), "• Geração de PDFs e planilhas inteligentes", fill=COR_TEXTO_BRANCO, font=fonte_corpo)
            draw.text((670, 395), "• Envio direto ao WhatsApp em 1 clique", fill=COR_TEXTO_MUTED, font=fonte_sub)

            legenda_texto = "Conecte a equipe técnica, a oficina e o cliente em uma única plataforma."

        # CENA 3 (15.5s a 23s): BENEFÍCIOS REAIS & SEGURANÇA
        elif t < 23.0:
            draw.text((60, 105), "Benefícios Concretos para o Seu Negócio", fill=COR_TEXTO_BRANCO, font=fonte_hero)
            draw.text((60, 150), "Sem promessas irreais: melhorias práticas que impactam o dia a dia da oficina:", fill=COR_TEXTO_MUTED, font=fonte_sub)

            beneficios = [
                ("⚡ Agilidade Real", "O atendimento é lançado no ato e o cliente recebe o comprovante em segundos.", COR_AZUL_ACCENT),
                ("🔒 Segurança Jurídica", "Assinatura touch do operador carimbada com data e hora invioláveis.", COR_VERDE_STATUS),
                ("💰 Faturamento sem Erros", "Fim de peças esquecidas ou cobranças contestadas por falta de registro.", COR_AMBAR_ALERTA),
                ("📲 Transparência no WhatsApp", "Comunicação profissional que transmite credibilidade imediata ao cliente.", (168, 85, 247))
            ]

            for idx, (b_tit, b_desc, b_cor) in enumerate(beneficios):
                row = idx // 2
                col = idx % 2
                bx = 60 + col * 590
                by = 195 + row * 125
                draw.rounded_rectangle([(bx, by), (bx + 570, by + 110)], radius=10, fill=COR_CARD, outline=(51, 65, 85), width=1)
                draw.text((bx + 20, by + 18), b_tit, fill=b_cor, font=fonte_destaque)
                draw.text((bx + 20, by + 52), b_desc[:46], fill=COR_TEXTO_BRANCO, font=fonte_corpo)
                draw.text((bx + 20, by + 78), b_desc[46:], fill=COR_TEXTO_MUTED, font=fonte_sub)

            legenda_texto = "Pelo celular o técnico anota peças e horímetro, e colhe o visto na hora."

        # CENA 4 (23s a 30s): RESULTADO FINAL E VISÃO EXECUTIVA
        else:
            draw.text((60, 105), "Mais Controle para Você, Total Confiança para o Cliente", fill=COR_TEXTO_BRANCO, font=fonte_hero)
            draw.text((60, 150), "A evolução natural da sua gestão de frotas e serviços mecânicos:", fill=COR_TEXTO_MUTED, font=fonte_sub)

            # Card Central Consolidado
            draw.rounded_rectangle([(60, 195), (1220, 460)], radius=14, fill=COR_CARD, outline=COR_AZUL_ACCENT, width=2)

            draw.text((100, 230), "✅ Redução drástica do retrabalho e perda de tempo", fill=COR_TEXTO_BRANCO, font=fonte_destaque)
            draw.text((100, 280), "✅ Histórico completo de cada máquina, trator ou caminhão", fill=COR_TEXTO_BRANCO, font=fonte_destaque)
            draw.text((100, 330), "✅ Envio profissional direto no WhatsApp com check azul", fill=(74, 222, 128), font=fonte_destaque)
            draw.text((100, 380), "✅ Faturamento ágil sem ruído de comunicação", fill=COR_TEXTO_BRANCO, font=fonte_destaque)

            # Badge Central Final
            draw.rounded_rectangle([(840, 240), (1170, 410)], radius=10, fill=(15, 23, 42), outline=COR_VERDE_STATUS, width=2)
            draw.text((875, 270), "GESTÃO EFICIENTE", fill=COR_VERDE_STATUS, font=fonte_tag)
            draw.text((865, 305), "Zero Papel", fill=COR_TEXTO_BRANCO, font=fonte_hero)
            draw.text((865, 350), "100% Digital", fill=COR_AZUL_ACCENT, font=fonte_destaque)

            legenda_texto = "Mais controle para a frota, zero burocracia e total transparência para o cliente."

        # Cápsula de Legenda Não Intrusiva
        box_leg_w = 840
        box_leg_h = 44
        box_leg_x = (1280 - box_leg_w) // 2
        box_leg_y = 650
        draw.rounded_rectangle([(box_leg_x, box_leg_y), (box_leg_x + box_leg_w, box_leg_y + box_leg_h)], radius=8, fill=(15, 23, 42), outline=COR_AZUL_ACCENT, width=1)
        draw.text((box_leg_x + 24, box_leg_y + 10), legenda_texto, fill=COR_TEXTO_BRANCO, font=fonte_legenda)

        # Barra de Progresso
        prog_total = (i / total_quadros)
        draw.line([(0, 718), (int(1280 * prog_total), 718)], fill=COR_VERDE_STATUS, width=4)

        frame_path = frames_dir / f"frame_{i:04d}.png"
        img.save(frame_path)

    print("[OK] Todos os quadros institucionais gerados!")
    return frames_dir

def compilar_video_institucional(frames_dir, audio_path, video_saida, fps=15):
    print(f"Compilando vídeo institucional em: {video_saida}...")
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
    print(f"[SUCESSO] Vídeo institucional gerado! Tamanho: {os.path.getsize(video_saida)} bytes")

async def main():
    audio_path = SCRATCH_DIR / "audio_institucional_30s.mp3"
    video_saida = OUTPUT_DIR / "modulo_00_visao_geral.mp4"

    await gerar_audio_institucional(TEXTO_INSTITUCIONAL, audio_path)
    frames_dir = criar_quadros_institucionais(duracao_total=28, fps=15)
    compilar_video_institucional(frames_dir, audio_path, video_saida, fps=15)

if __name__ == "__main__":
    asyncio.run(main())
