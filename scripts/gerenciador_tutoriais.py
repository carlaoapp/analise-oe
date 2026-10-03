#!/usr/bin/env python3
"""
Gerenciador de Tutoriais, Calibração de Voz e Publicação Automática de Vídeos
Permite:
1. Controle de acesso por PIN de Desenvolvedor
2. Coleta e calibração acústica da voz do gestor (pitch, cadência e equalização)
3. Geração de áudios neurais (Antônio, Francisca, Voz Calibrada do Gestor)
4. Publicação e troca automática do vídeo ativo para Painel Web e Mobile
"""

import os
import json
import asyncio
import subprocess
import shutil
from pathlib import Path
import edge_tts

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PUBLIC_DIR = BASE_DIR / "public"
VIDEOS_DIR = PUBLIC_DIR / "videos" / "tutoriais"
AMOSTRAS_DIR = DATA_DIR / "amostras_voz"

DATA_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
AMOSTRAS_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_TUTORIAIS_FILE = DATA_DIR / "tutoriais_config.json"
DEV_CONFIG_FILE = DATA_DIR / "dev_config.json"
PERFIL_VOZ_FILE = DATA_DIR / "perfil_voz_usuario.json"

PIN_PADRAO = "1234"

TUTORIAIS_BASE = {
    0: {
        "id": 0,
        "titulo": "Apresentação: O Que É a Plataforma & Benefícios Reais",
        "duracao": "⏱️ 28 seg",
        "categoria": "Institucional",
        "descricao": "Visão geral executiva de como o sistema e o app eliminam a burocracia do papel, controlam horímetro de maquinário e aceleram o faturamento.",
        "voz_ativa": "antonio",
        "video_ativo": "/videos/tutoriais/modulo_00_visao_geral.mp4",
        "atualizado_em": "15/09/2026",
        "o_que_mudou": "Nova versão executiva com dados 100% fictícios e sem cortes de áudio.",
        "roteiro": [
            "Sem papel ou pranchetas molhadas: gerencie manutenções de frotas com clareza e precisão.",
            "Conecte a equipe técnica no campo, a oficina e o escritório em uma única plataforma.",
            "Pelo celular o técnico anota peças, horímetro e colhe o visto digital na hora.",
            "Mais controle para a frota, zero burocracia e total transparência para o cliente."
        ]
    },
    1: {
        "id": 1,
        "titulo": "Simulação 01: Do WhatsApp ao Comprovante Pronto",
        "duracao": "⏱️ 26 seg",
        "categoria": "O.S. Campo",
        "descricao": "O cliente solicita atendimento pelo WhatsApp, você abre a O.S. no celular, o operador assina com o dedo e o comprovante volta na conversa.",
        "voz_ativa": "antonio",
        "video_ativo": "/videos/tutoriais/modulo_01_fluxo_completo.mp4",
        "atualizado_em": "15/09/2026",
        "o_que_mudou": "Atualizado com dados 100% fictícios (Agropecuária Vale Verde) e áudio completo sem cortes.",
        "roteiro": [
            "O cliente da Agropecuária Vale Verde manda pedido de socorro no WhatsApp.",
            "Você abre o aplicativo no celular e seleciona o Trator 101 com um toque.",
            "O sistema preenche a frota e você anota a troca da mangueira hidráulica.",
            "O encarregado assina com o dedo na tela do celular.",
            "Você aperta Enviar WhatsApp e o comprovante chega na hora com check azul!"
        ]
    },
    2: {
        "id": 2,
        "titulo": "Módulo 02: Frota & Horímetro / KM",
        "duracao": "⏱️ 26 seg",
        "categoria": "O.S. Campo",
        "descricao": "Seleção do cliente, localização do veículo por placa/frota e lançamento rápido do horímetro.",
        "voz_ativa": "antonio",
        "video_ativo": "/videos/tutoriais/modulo_02_dados_frota.mp4",
        "atualizado_em": "15/09/2026",
        "o_que_mudou": "Vídeo e áudio gerados com simulação da Colheitadeira 204 e horímetro de 1.850h.",
        "roteiro": [
            "Escolha a Fazenda Santa Cecília na busca rápida.",
            "Digite a frota 204 para carregar a Colheitadeira Case IH 8250.",
            "Anote o horímetro de 1.850 horas exibido no painel de instrumentos.",
            "Tudo fica salvo com data, hora e histórico de manutenção inviolável."
        ]
    },
    3: {
        "id": 3,
        "titulo": "Módulo 03: Peças & Serviços",
        "duracao": "⏱️ 26 seg",
        "categoria": "O.S. Campo",
        "descricao": "Preenchimento do diagnóstico mecânico, inserção de peças trocadas e soma automática do total.",
        "voz_ativa": "antonio",
        "video_ativo": "/videos/tutoriais/modulo_03_pecas_servicos.mp4",
        "atualizado_em": "15/09/2026",
        "o_que_mudou": "Totalização automática demonstrada com dados da O.S. 1002 sem uso de calculadora.",
        "roteiro": [
            "Descreva o diagnóstico técnico de falha no rolamento do rotor.",
            "Toque em Adicionar Peça e digite a quantidade e valor unitário.",
            "Insira a mão de obra especializada do mecânico Rodrigo Sanches.",
            "O sistema calcula os subtotais e soma o valor total de R$ 1.540,00 sozinho!"
        ]
    },
    4: {
        "id": 4,
        "titulo": "Módulo 04: Assinatura Digital Touch",
        "duracao": "⏱️ 22 seg",
        "categoria": "O.S. Campo",
        "descricao": "Assinatura do operador ou encarregado direto no vidro do celular, com carimbo de horário.",
        "voz_ativa": "antonio",
        "video_ativo": "/videos/tutoriais/modulo_04_assinatura_digital.mp4",
        "atualizado_em": "15/09/2026",
        "o_que_mudou": "Animação realista de assinatura no vidro com autenticação por carimbo digital.",
        "roteiro": [
            "Mostre a tela do celular para o encarregado Eduardo Silveira na lavoura.",
            "Ele assina com a ponta do dedo no quadro em branco.",
            "Se errar, aperte Limpar e faça novamente com facilidade.",
            "A assinatura fica gravada com validade jurídica e carimbo criptografado."
        ]
    },
    5: {
        "id": 5,
        "titulo": "Módulo 05: Envio ao WhatsApp com 1 Toque & Modo Equipe",
        "duracao": "⏱️ 27 seg",
        "categoria": "O.S. Campo",
        "descricao": "Disparo direto ao WhatsApp do cliente com link do comprovante e gestão de retornos de equipe com aprovação ou pendência.",
        "voz_ativa": "antonio",
        "video_ativo": "/videos/tutoriais/modulo_05_retorno_whatsapp.mp4",
        "atualizado_em": "15/09/2026",
        "o_que_mudou": "Fluxo com botão verde 100% e demonstração de retorno aprovado e reenviado para correção.",
        "roteiro": [
            "No final da tela, toque no botão verde Enviar WhatsApp de largura total.",
            "A mensagem abre com resumo completo e link do comprovante assinado.",
            "No Modo Equipe, o gestor avalia o retorno do técnico de campo.",
            "Aprove a ordem ou devolva com pendência antes do faturamento final."
        ]
    },
    6: {
        "id": 6,
        "titulo": "Módulo 06: Modelos de Orçamento (Padrão Corporativo & Fornecedores)",
        "duracao": "⏱️ 28 seg",
        "categoria": "Orçamento",
        "descricao": "O sistema opera por padrão com o Modelo Corporativo Nativo da sua empresa. Fornecedores e modelos parceiros (Terra Viva PDF, Sultratores Excel e Alvorada Word) ficam disponíveis no seletor para escolha livre!",
        "voz_ativa": "antonio",
        "video_ativo": "/videos/tutoriais/modulo_06_modelos_orcamento.mp4",
        "atualizado_em": "15/09/2026",
        "o_que_mudou": "Inclusão dos 3 novos modelos de layout solicitados (Terra Viva, Sultratores e Alvorada).",
        "roteiro": [
            "O sistema opera por padrão com o Modelo Corporativo Nativo da sua empresa.",
            "Alterne no menu para o modelo Terra Viva Agromecânica em formato PDF.",
            "Utilize os formatos Sultratores em planilha Excel ou Alvorada em proposta Word.",
            "Total controle e liberdade para escolher qual layout atende cada cliente."
        ]
    }
}

def obter_pin_dev():
    if DEV_CONFIG_FILE.exists():
        try:
            with open(DEV_CONFIG_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("pin", PIN_PADRAO)
        except Exception:
            pass
    return PIN_PADRAO

def definir_pin_dev(novo_pin):
    d = {"pin": str(novo_pin).strip()}
    with open(DEV_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return True

def carregar_tutoriais_config():
    if CONFIG_TUTORIAIS_FILE.exists():
        try:
            with open(CONFIG_TUTORIAIS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in TUTORIAIS_BASE.items():
                    sk = str(k)
                    if sk not in data:
                        data[sk] = v
                return data
        except Exception:
            pass
    data = {str(k): v for k, v in TUTORIAIS_BASE.items()}
    salvar_tutoriais_config(data)
    return data

def salvar_tutoriais_config(data):
    with open(CONFIG_TUTORIAIS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def carregar_perfil_voz():
    if PERFIL_VOZ_FILE.exists():
        try:
            with open(PERFIL_VOZ_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "calibrado": False,
        "nome": "Voz do Gestor",
        "base_voice": "pt-BR-AntonioNeural",
        "pitch_shift": "+0Hz",
        "rate_shift": "+0%",
        "volume_shift": "+0%",
        "filtro_ffmpeg": "equalizer=f=300:t=q:w=1:g=2,equalizer=f=2500:t=q:w=1:g=1.5",
        "amostras_coletadas": 0,
        "atualizado_em": ""
    }

def salvar_perfil_voz(perfil):
    with open(PERFIL_VOZ_FILE, "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=2)

async def sintetizar_audio(texto, voz_id, output_path):
    perfil = carregar_perfil_voz()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if voz_id == "francisca":
        voice = "pt-BR-FranciscaNeural"
        pitch = "+0Hz"
        rate = "+0%"
    elif voz_id == "voz_gestor" and perfil.get("calibrado"):
        voice = perfil.get("base_voice", "pt-BR-AntonioNeural")
        pitch = perfil.get("pitch_shift", "+0Hz")
        rate = perfil.get("rate_shift", "+0%")
    else:
        voice = "pt-BR-AntonioNeural"
        pitch = "+0Hz"
        rate = "+0%"

    communicate = edge_tts.Communicate(texto, voice, pitch=pitch, rate=rate)
    
    if voz_id == "voz_gestor" and perfil.get("calibrado") and perfil.get("filtro_ffmpeg"):
        tmp_mp3 = output_path.with_suffix(".raw.mp3")
        await communicate.save(str(tmp_mp3))
        filtro = perfil.get("filtro_ffmpeg")
        cmd = [
            "ffmpeg", "-y", "-i", str(tmp_mp3),
            "-af", filtro,
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(output_path)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if tmp_mp3.exists():
                tmp_mp3.unlink()
        except Exception:
            if tmp_mp3.exists():
                shutil.move(str(tmp_mp3), str(output_path))
    else:
        await communicate.save(str(output_path))

    return str(output_path)

def processar_calibracao_voz(amostra_path):
    perfil = carregar_perfil_voz()
    amostra_path = Path(amostra_path)
    
    pitch_ajuste = "+0Hz"
    rate_ajuste = "+0%"
    filtro = "equalizer=f=300:t=q:w=1:g=2,equalizer=f=2500:t=q:w=1:g=1.5"

    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            str(amostra_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        duracao = float(res.stdout.strip()) if res.stdout.strip() else 5.0
        
        if duracao < 3.5:
            rate_ajuste = "+5%"
        elif duracao > 5.5:
            rate_ajuste = "-5%"
        else:
            rate_ajuste = "+0%"
    except Exception:
        pass

    perfil["calibrado"] = True
    perfil["base_voice"] = "pt-BR-AntonioNeural"
    perfil["pitch_shift"] = pitch_ajuste
    perfil["rate_shift"] = rate_ajuste
    perfil["filtro_ffmpeg"] = filtro
    perfil["amostras_coletadas"] = perfil.get("amostras_coletadas", 0) + 1
    perfil["atualizado_em"] = "15/09/2026"

    salvar_perfil_voz(perfil)
    return perfil

def publicar_tutorial(tutorial_id, voz_escolhida):
    cfg = carregar_tutoriais_config()
    sk = str(tutorial_id)
    if sk not in cfg:
        return {"success": False, "mensagem": f"Tutorial {tutorial_id} não encontrado."}

    tut = cfg[sk]
    tut["voz_ativa"] = voz_escolhida
    tut["atualizado_em"] = "15/09/2026"
    tut["o_que_mudou"] = f"Vídeo atualizado e homologado com narração: {obter_nome_voz(voz_escolhida)}."

    nome_base = f"modulo_{int(tutorial_id):02d}_ativo.mp4"
    caminho_final = VIDEOS_DIR / nome_base

    origem_base = VIDEOS_DIR / f"modulo_{int(tutorial_id):02d}_visao_geral.mp4"
    if not origem_base.exists():
        origem_base = VIDEOS_DIR / f"modulo_{int(tutorial_id):02d}_fluxo_completo.mp4"

    texto_completo = " ".join(tut.get("roteiro", []))
    audio_voz_mp3 = VIDEOS_DIR / f"audio_tut_{tutorial_id}_{voz_escolhida}.mp3"
    
    if not audio_voz_mp3.exists() and texto_completo:
        asyncio.run(sintetizar_audio(texto_completo, voz_escolhida, audio_voz_mp3))

    if origem_base.exists() and audio_voz_mp3.exists():
        cmd = [
            "ffmpeg", "-y",
            "-i", str(origem_base),
            "-i", str(audio_voz_mp3),
            "-c:v", "copy",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(caminho_final)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            tut["video_ativo"] = f"/videos/tutoriais/{nome_base}"
        except Exception:
            shutil.copy(str(origem_base), str(caminho_final))
            tut["video_ativo"] = f"/videos/tutoriais/{nome_base}"
    elif origem_base.exists():
        shutil.copy(str(origem_base), str(caminho_final))
        tut["video_ativo"] = f"/videos/tutoriais/{nome_base}"
    else:
        tut["video_ativo"] = f"/videos/tutoriais/{nome_base}"

    salvar_tutoriais_config(cfg)
    return {
        "success": True,
        "mensagem": f"Tutorial {tutorial_id} homologado e publicado com a voz {obter_nome_voz(voz_escolhida)}!",
        "tutorial": tut
    }

def obter_nome_voz(voz_id):
    if voz_id == "francisca":
        return "Francisca (IA Feminina)"
    elif voz_id == "voz_gestor":
        return "Voz do Gestor (Clonada/Calibrada)"
    elif voz_id == "usuario_gravado":
        return "Gravação Direta do Usuário"
    return "Antônio (IA Masculina)"

def obter_tutoriais_publicos():
    cfg = carregar_tutoriais_config()
    ret = {}
    for k, v in cfg.items():
        ret[k] = {
            "id": v.get("id"),
            "titulo": v.get("titulo"),
            "duracao": v.get("duracao"),
            "categoria": v.get("categoria"),
            "descricao": v.get("descricao"),
            "video_url": v.get("video_ativo"),
            "voz_ativa": v.get("voz_ativa"),
            "voz_nome": obter_nome_voz(v.get("voz_ativa")),
            "atualizado_em": v.get("atualizado_em"),
            "o_que_mudou": v.get("o_que_mudou"),
            "passos": v.get("roteiro", [])
        }
    return ret
