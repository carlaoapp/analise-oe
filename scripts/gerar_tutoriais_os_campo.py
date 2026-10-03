#!/usr/bin/env python3
"""
Gerador de Vídeos Tutoriais Operacionais de 30 Segundos (Ultra Intuitivos)
Módulo Alvo: Abertura de O.S. Campo (Simulação WhatsApp -> App -> Retorno WhatsApp)
Gera áudio neural via Edge-TTS e renderiza o vídeo via Pillow + FFmpeg.
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

# 1. ROTEIRO ULTRA DIDÁTICO (PADRÃO 30 SEGUNDOS - NÍVEL CRIANÇA)
TEXTO_NARRACAO = (
    "Olha só como é fácil! Primeiro, o cliente avisa no WhatsApp que o trator parou na fazenda. "
    "Aí você abre o aplicativo no celular, escolhe o trator na lista e anota o reparo feito. "
    "Agora, o operador assina com o dedo na tela do celular. "
    "Prontinho! Aperte o botão verde e o comprovante já chega na conversa do WhatsApp na mesma hora!"
)

async def gerar_audio_neural(texto, arquivo_saida):
    import edge_tts
    # Voz ultra-humanizada masculina brasileira
    comunicador = edge_tts.Communicate(texto, "pt-BR-AntonioNeural", rate="+3%", pitch="+0Hz")
    await comunicador.save(str(arquivo_saida))
    print(f"[OK] Áudio neural gerado com sucesso: {arquivo_saida}")

def criar_quadros_animacao(duracao_total=30, fps=15):
    total_quadros = int(duracao_total * fps)
    frames_dir = SCRATCH_DIR / "frames_os_campo"
    frames_dir.mkdir(parents=True, exist_ok=True)

    COR_BG_WHATSAPP = (17, 27, 33)       # #111b21
    COR_HEADER_WA = (32, 44, 51)         # #202c33
    COR_MSG_RECEBIDA = (32, 44, 51)      # #202c33
    COR_MSG_ENVIADA = (0, 92, 75)        # #005c4b
    COR_BG_APP = (11, 15, 23)            # #0b0f17
    COR_CARD_APP = (19, 27, 46)          # #131b2e
    COR_TEXTO_BRANCO = (248, 250, 252)
    COR_TEXTO_MUTED = (148, 163, 184)
    COR_VERDE_WA = (37, 211, 102)        # #25d366
    COR_AZUL_ACCENT = (56, 189, 248)     # #38bdf8
    COR_AMARELO_ALERTA = (245, 158, 11)

    try:
        fonte_tit = ImageFont.truetype("arialbd.ttf", 28)
        fonte_sub = ImageFont.truetype("arial.ttf", 18)
        fonte_msg = ImageFont.truetype("arial.ttf", 20)
        fonte_destaque = ImageFont.truetype("arialbd.ttf", 22)
        fonte_tag = ImageFont.truetype("arialbd.ttf", 14)
        fonte_legenda = ImageFont.truetype("arialbd.ttf", 20)
    except:
        fonte_tit = ImageFont.load_default()
        fonte_sub = fonte_tit
        fonte_msg = fonte_tit
        fonte_destaque = fonte_tit
        fonte_tag = fonte_tit
        fonte_legenda = fonte_tit

    print(f"Gerando {total_quadros} quadros de animação ({fps} fps)...")

    for i in range(total_quadros):
        t = i / fps

        img = Image.new("RGB", (1280, 720), COR_BG_APP)
        draw = ImageDraw.Draw(img)

        # FASE 1: WHATSAPP - CHAMADO RECEBIDO (0s a 8s)
        if t < 8.0:
            draw.rectangle([(0, 0), (1280, 720)], fill=COR_BG_WHATSAPP)
            draw.rectangle([(0, 0), (1280, 75)], fill=COR_HEADER_WA)
            draw.ellipse([(30, 15), (75, 60)], fill=(74, 222, 128))
            draw.text((45, 23), "🚜", font=fonte_tit)
            draw.text((95, 18), "Agropecuária Vale Verde - Carlos Mendes", fill=COR_TEXTO_BRANCO, font=fonte_destaque)
            draw.text((95, 45), "Online agora • WhatsApp Business", fill=COR_VERDE_WA, font=fonte_sub)

            draw.rounded_rectangle([(980, 20), (1250, 55)], radius=18, fill=(30, 41, 59), outline=COR_AZUL_ACCENT, width=1)
            draw.text((1000, 27), "PASSO 1: Chamado Chegou", fill=COR_AZUL_ACCENT, font=fonte_tag)

            y_msg = 120
            prog_slide = min(1.0, t / 1.2)
            alpha_x = int(50 + (1.0 - prog_slide) * 40)
            
            draw.rounded_rectangle([(alpha_x, y_msg), (alpha_x + 580, y_msg + 140)], radius=12, fill=COR_MSG_RECEBIDA)
            draw.text((alpha_x + 20, y_msg + 15), "🚨 SOCORRO MECÂNICO URGENTE", fill=COR_AMARELO_ALERTA, font=fonte_destaque)
            draw.text((alpha_x + 20, y_msg + 50), "Bom dia equipe! O Trator Frota 327 parou", fill=COR_TEXTO_BRANCO, font=fonte_msg)
            draw.text((alpha_x + 20, y_msg + 75), "no Talhão 4 por rompimento da correia.", fill=COR_TEXTO_BRANCO, font=fonte_msg)
            draw.text((alpha_x + 20, y_msg + 105), "Podem vir atender agora por favor?", fill=COR_TEXTO_MUTED, font=fonte_sub)
            draw.text((alpha_x + 510, y_msg + 112), "08:14", fill=(100, 116, 139), font=fonte_tag)

            legenda_texto = "1. O cliente manda aviso no WhatsApp com a frota e problema."

        # FASE 2: APP DE CAMPO - PREENCHIMENTO INTUITIVO (8s a 16s)
        elif t < 16.0:
            t_fase = t - 8.0
            draw.rectangle([(0, 0), (1280, 720)], fill=(15, 23, 42))
            draw.rectangle([(0, 0), (1280, 70)], fill=(30, 41, 59))
            draw.text((40, 20), "⚡ Abertura de O.S. Campo - Manutenção Rápida", fill=COR_TEXTO_BRANCO, font=fonte_destaque)
            draw.rounded_rectangle([(960, 18), (1240, 52)], radius=16, fill=(16, 185, 129), outline=(52, 211, 153), width=1)
            draw.text((980, 25), "PASSO 2: Abertura Direta", fill=(255, 255, 255), font=fonte_tag)

            draw.rounded_rectangle([(40, 95), (620, 340)], radius=10, fill=COR_CARD_APP, outline=(51, 65, 85), width=1)
            draw.text((60, 110), "IDENTIFICAÇÃO DO EQUIPAMENTO", fill=COR_AZUL_ACCENT, font=fonte_tag)
            
            draw.text((60, 140), "Cliente:", fill=COR_TEXTO_MUTED, font=fonte_sub)
            draw.rounded_rectangle([(60, 165), (600, 205)], radius=6, fill=(15, 23, 42), outline=(56, 189, 248) if t_fase > 1.0 else (51, 65, 85))
            draw.text((75, 175), "Agropecuária Vale Verde Ltda.", fill=COR_TEXTO_BRANCO, font=fonte_msg)

            draw.text((60, 220), "Frota / Veículo:", fill=COR_TEXTO_MUTED, font=fonte_sub)
            draw.rounded_rectangle([(60, 245), (600, 285)], radius=6, fill=(15, 23, 42), outline=(52, 211, 153) if t_fase > 2.5 else (51, 65, 85))
            draw.text((75, 255), "Frota 327 - Trator John Deere 7230J", fill=(74, 222, 128), font=fonte_destaque)

            draw.text((60, 300), "Horímetro Atual: 4.820 h", fill=COR_TEXTO_BRANCO, font=fonte_sub)

            draw.rounded_rectangle([(650, 95), (1240, 340)], radius=10, fill=COR_CARD_APP, outline=(51, 65, 85), width=1)
            draw.text((670, 110), "SERVIÇOS & PEÇAS APLICADAS", fill=COR_AZUL_ACCENT, font=fonte_tag)

            draw.rounded_rectangle([(670, 140), (1220, 195)], radius=6, fill=(15, 23, 42), outline=(51, 65, 85))
            draw.text((685, 155), "🔧 Troca da correia do alternador e tensor", fill=COR_TEXTO_BRANCO, font=fonte_msg)

            draw.rounded_rectangle([(670, 210), (1220, 265)], radius=6, fill=(15, 23, 42), outline=(51, 65, 85))
            draw.text((685, 225), "📦 01x Correia Poly-V Gates Premium - R$ 185,00", fill=(74, 222, 128), font=fonte_msg)

            draw.text((670, 295), "Total dos Serviços + Peças: R$ 465,00", fill=COR_AMARELO_ALERTA, font=fonte_destaque)

            draw.rounded_rectangle([(40, 360), (1240, 420)], radius=8, fill=(2, 132, 199), outline=COR_AZUL_ACCENT, width=2)
            draw.text((500, 378), "✓ Salvar & Coletar Assinatura", fill=COR_TEXTO_BRANCO, font=fonte_destaque)

            prog_click = (t_fase / 8.0)
            cur_x = int(300 + prog_click * 300)
            cur_y = int(200 + prog_click * 180)
            draw.ellipse([(cur_x - 12, cur_y - 12), (cur_x + 12, cur_y + 12)], fill=(239, 68, 68), outline=COR_TEXTO_BRANCO, width=2)

            legenda_texto = "2. No celular você escolhe o trator, marca o reparo e calcula tudo."

        # FASE 3: ASSINATURA DIGITAL NA TELA TOUCH (16s a 22s)
        elif t < 22.0:
            t_fase = t - 16.0
            draw.rectangle([(0, 0), (1280, 720)], fill=(15, 23, 42))
            draw.rectangle([(0, 0), (1280, 70)], fill=(30, 41, 59))
            draw.text((40, 20), "✍️ Assinatura Digital do Cliente & Operador", fill=COR_TEXTO_BRANCO, font=fonte_destaque)
            draw.rounded_rectangle([(960, 18), (1240, 52)], radius=16, fill=(16, 185, 129), outline=(52, 211, 153), width=1)
            draw.text((980, 25), "PASSO 3: Visto com o Dedo", fill=(255, 255, 255), font=fonte_tag)

            draw.rounded_rectangle([(240, 110), (1040, 390)], radius=12, fill=(255, 255, 255), outline=(56, 189, 248), width=3)
            draw.text((260, 125), "Assine com o dedo ou caneta touch no quadro abaixo:", fill=(100, 116, 139), font=fonte_sub)

            draw.line([(280, 330), (1000, 330)], fill=(203, 213, 225), width=2)
            draw.text((280, 340), "Rogério Guimarães (Encarregado de Operações)", fill=(71, 85, 105), font=fonte_sub)

            prog_assin = min(1.0, t_fase / 4.0)
            pontos_assin = [
                (320, 270), (360, 230), (410, 280), (450, 220), (500, 260),
                (560, 210), (620, 290), (690, 240), (760, 280), (840, 230), (920, 270)
            ]
            qtd_pts = max(2, int(len(pontos_assin) * prog_assin))
            pts_desenhar = pontos_assin[:qtd_pts]
            if len(pts_desenhar) >= 2:
                for idx in range(len(pts_desenhar) - 1):
                    draw.line([pts_desenhar[idx], pts_desenhar[idx+1]], fill=(15, 23, 42), width=5)

            if prog_assin > 0.8:
                draw.rounded_rectangle([(780, 130), (1010, 175)], radius=6, fill=(220, 252, 231), outline=(34, 197, 94), width=2)
                draw.text((795, 142), "✓ ASSINATURA VÁLIDA", fill=(22, 101, 52), font=fonte_destaque)

            draw.rounded_rectangle([(240, 420), (1040, 480)], radius=8, fill=COR_VERDE_WA, outline=(255, 255, 255), width=1)
            draw.text((490, 438), "🚀 Enviar Comprovante ao WhatsApp", fill=(17, 27, 33), font=fonte_destaque)

            legenda_texto = "3. O operador passa o dedo na tela e assina sem papel."

        # FASE 4: RETORNO AUTOMÁTICO AO WHATSAPP (22s a 30s)
        else:
            t_fase = t - 22.0
            draw.rectangle([(0, 0), (1280, 720)], fill=COR_BG_WHATSAPP)
            draw.rectangle([(0, 0), (1280, 75)], fill=COR_HEADER_WA)
            draw.ellipse([(30, 15), (75, 60)], fill=(74, 222, 128))
            draw.text((45, 23), "🚜", font=fonte_tit)
            draw.text((95, 18), "Agropecuária Vale Verde - Carlos Mendes", fill=COR_TEXTO_BRANCO, font=fonte_destaque)
            draw.text((95, 45), "Online • Resumo Enviado com Sucesso", fill=COR_VERDE_WA, font=fonte_sub)

            draw.rounded_rectangle([(960, 20), (1250, 55)], radius=18, fill=(6, 78, 59), outline=(52, 211, 153), width=1)
            draw.text((980, 27), "PASSO 4: Comprovante Entregue ✓✓", fill=(52, 211, 153), font=fonte_tag)

            y_ret = 120
            draw.rounded_rectangle([(580, y_ret), (1240, y_ret + 300)], radius=12, fill=COR_MSG_ENVIADA)
            draw.text((610, y_ret + 15), "✅ ORDEM DE SERVIÇO CONCLUÍDA!", fill=(74, 222, 128), font=fonte_destaque)
            draw.text((610, y_ret + 50), "O.S. Nº 133774 • Frota 327 (John Deere)", fill=COR_TEXTO_BRANCO, font=fonte_msg)
            draw.text((610, y_ret + 80), "Serviço: Troca correia Poly-V e tensor realizada.", fill=COR_TEXTO_BRANCO, font=fonte_sub)
            draw.text((610, y_ret + 110), "Status: Máquina liberada e testada no campo.", fill=COR_TEXTO_BRANCO, font=fonte_sub)
            
            draw.rounded_rectangle([(610, y_ret + 145), (1210, y_ret + 225)], radius=8, fill=(18, 30, 36), outline=(38, 54, 64), width=1)
            draw.text((630, y_ret + 160), "📄 Comprovante_OS_133774.pdf", fill=COR_TEXTO_BRANCO, font=fonte_destaque)
            draw.text((630, y_ret + 190), "1 Página • 248 KB • Assinatura Digital anexada", fill=COR_TEXTO_MUTED, font=fonte_tag)

            draw.text((610, y_ret + 245), "Assinado por: Rogério Guimarães", fill=(147, 197, 253), font=fonte_sub)
            draw.text((1150, y_ret + 265), "08:42 ✓✓", fill=(56, 189, 248), font=fonte_destaque)

            legenda_texto = "4. O comprovante chega no WhatsApp na mesma hora com check azul!"

        box_leg_w = 780
        box_leg_h = 44
        box_leg_x = (1280 - box_leg_w) // 2
        box_leg_y = 650
        draw.rounded_rectangle([(box_leg_x, box_leg_y), (box_leg_x + box_leg_w, box_leg_y + box_leg_h)], radius=8, fill=(15, 23, 42), outline=(56, 189, 248), width=1)
        draw.text((box_leg_x + 24, box_leg_y + 10), legenda_texto, fill=COR_TEXTO_BRANCO, font=fonte_legenda)

        prog_total = (i / total_quadros)
        draw.line([(0, 718), (int(1280 * prog_total), 718)], fill=COR_AZUL_ACCENT, width=4)

        frame_path = frames_dir / f"frame_{i:04d}.png"
        img.save(frame_path)

    print("[OK] Todos os quadros de animação gerados com sucesso!")
    return frames_dir

def compilar_video_com_audio(frames_dir, audio_path, video_saida, duracao=30, fps=15):
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
    audio_path = SCRATCH_DIR / "audio_modulo_01_30s.mp3"
    video_saida = OUTPUT_DIR / "modulo_01_fluxo_completo.mp4"

    await gerar_audio_neural(TEXTO_NARRACAO, audio_path)
    frames_dir = criar_quadros_animacao(duracao_total=30, fps=15)
    compilar_video_com_audio(frames_dir, audio_path, video_saida, duracao=30, fps=15)

if __name__ == "__main__":
    asyncio.run(main())
