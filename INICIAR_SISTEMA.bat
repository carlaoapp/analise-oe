@echo off
chcp 65001 >nul
title Analise O.E - Painel de Manutenção
color 0B

echo ================================================================
echo           SISTEMA ANALISE O.E - PAINEL DE MANUTENÇÃO
echo ================================================================
echo.

:: 1. Verifica se Python está instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [ERRO CRÍTICO] Python 3 não foi encontrado no PATH do sistema.
    echo Por favor, instale o Python em https://www.python.org/
    pause
    exit /b 1
)

:: 2. Identifica IP da rede local
for /f "tokens=14" %%a in ('ipconfig ^| findstr IPv4') do set IP=%%a

echo [*] Servidor Backend : http://localhost:8000
if not "%IP%"=="" echo [*] Acesso Rede Local: http://%IP%:8000
echo [*] Banco de Dados   : data\db.json
echo [*] WhatsApp Inbox   : data\whatsapp_inbox.json
echo.
echo Pressione Ctrl+C para encerrar o sistema quando desejar.
echo ================================================================
echo.

:: 3. Abre o navegador após 1.5s em segundo plano
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 1.5; Start-Process 'http://localhost:8000/'"

:: 4. Executa o servidor Python
cd /d "%~dp0"
python servidor.py
pause
