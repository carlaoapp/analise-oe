@echo off
echo =======================================================
echo     SERVIDOR LOCAL - PAINEL DE MANUTENCAO
echo =======================================================
echo.
echo Iniciando servidor na rede local...
echo Para acessar do seu CELULAR ou outro COMPUTADOR, digite o link abaixo no navegador:
echo.

:: Pegar IP local
for /f "tokens=14" %%a in ('ipconfig ^| findstr IPv4') do set IP=%%a

echo    Link: http://%IP%:8000
echo.
echo Para fechar o servidor, feche esta janela.
echo.
cd /d "%~dp0"
python servidor.py
