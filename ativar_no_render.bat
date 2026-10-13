@echo off
title Ativacao no Render - Analise O.E
chcp 65001 > nul
cd /d "%~dp0"
color 0B

echo ================================================================
echo       ATIVACAO AUTOMATICA NO RENDER - ANALISE O.E
echo ================================================================
echo.
echo Abrindo o configurador automatico do Render (Blueprint)...
echo Como preparamos o arquivo render.yaml no seu GitHub,
echo todas as configuracoes serao preenchidas automaticamente.
echo.
echo Pressione qualquer tecla para abrir a tela de ativacao no navegador...
pause > nul

start "" "https://dashboard.render.com/blueprint/new?repo=https%%3A%%2F%%2Fgithub.com%%2Fcarlaoapp%%2Fanalise-oe"

echo.
echo [OK] Tela aberta no seu navegador!
echo Basta clicar no botao "Apply" ou "Criar" para o Render gerar seu link definitivo no ar.
echo.
pause
