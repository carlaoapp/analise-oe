@echo off
title Enviar para o GitHub e Render - Analise O.E
chcp 65001 > nul
cd /d "%~dp0"
color 0A

echo ================================================================
echo       ENVIAR ATUALIZACOES PARA O GITHUB E NUVEM (RENDER)
echo                    SISTEMA ANALISE O.E
echo ================================================================
echo.

:: 1. Sincroniza public/ com a raiz para o GitHub Pages
echo [*] Sincronizando arquivos do app para publicacao...
xcopy /E /I /Y "public\*" "." > nul

:: 2. Identifica e adiciona todos os arquivos
echo [*] Mapeando arquivos...
git add -A

:: 3. Verifica se ha alteracoes para enviar
git status --porcelain > "%temp%\oe_git_status.txt"
set /p TEM_ALTERACOES=<"%temp%\oe_git_status.txt"

if "%TEM_ALTERACOES%"=="" (
    echo.
    echo ================================================================
    echo   TUDO ATUALIZADO! Nao ha nenhum arquivo modificado para subir.
    echo   Seu GitHub ja esta 100%% em dia com o seu computador!
    echo ================================================================
    echo.
    pause
    exit /b 0
)

:: 4. Cria o commit com data e hora
set "DATA_HORA=%date% as %time:~0,5%"
echo [*] Gravando alteracoes: %DATA_HORA%...
git commit -m "Atualizacao: %DATA_HORA%"

:: 5. Envia para o GitHub na branch main
echo [*] Enviando arquivos para o GitHub na nuvem...
echo.
git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo ================================================================
    echo   [SUCESSO TOTAL!]
    echo   Todos os arquivos foram enviados para o GitHub e Render!
    echo   Link Definitivo: https://carlaoapp.github.io/analise-oe/
    echo   Quem tem o app instalado vera a mensagem de atualizar na tela.
    echo ================================================================
) else (
    echo [!] Ocorreu um erro ao enviar para o GitHub. Verifique sua conexao.
)
echo.
pause
