$desktopFolder = "$env:USERPROFILE\Desktop"
$zipName = "Instalador_Painel_Manutencao.zip"
$zipPath = Join-Path $desktopFolder $zipName
$exePath = "C:\Desenvolvimento\Projetos\Analise O.E\PainelDeManutencao.exe"

$tempDir = Join-Path $env:TEMP "PainelManutencao_Instalador"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir | Out-Null

Copy-Item $exePath $tempDir -Force

$batPath = Join-Path $tempDir "Instalar_Sistema.bat"
$batContent = @'
@echo off
color 0B
echo =========================================================
echo       INSTALACAO PAINEL DE MANUTENCAO - COMPUTADOR
echo =========================================================
echo.

echo 1. Criando pasta do sistema no seu perfil...
if not exist "%USERPROFILE%\Desktop\Painel de Manutencao" mkdir "%USERPROFILE%\Desktop\Painel de Manutencao"

echo 2. Copiando arquivos...
copy /Y "%~dp0PainelDeManutencao.exe" "%USERPROFILE%\Desktop\Painel de Manutencao\PainelDeManutencao.exe" >nul

echo 3. Liberando arquivo...
powershell -Command "Unblock-File -Path '%USERPROFILE%\Desktop\Painel de Manutencao\PainelDeManutencao.exe' -ErrorAction SilentlyContinue"

echo 4. Criando atalho na Area de Trabalho...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\Painel de Manutenção.lnk');$s.TargetPath='%USERPROFILE%\Desktop\Painel de Manutencao\PainelDeManutencao.exe';$s.WorkingDirectory='%USERPROFILE%\Desktop\Painel de Manutencao';$s.Save()"

echo.
echo =========================================================
echo   INSTALACAO CONCLUIDA!
echo =========================================================
echo Atalho criado na Area de Trabalho.
echo Iniciando o sistema agora...
timeout /t 2 >nul
start "" "%USERPROFILE%\Desktop\Painel de Manutencao\PainelDeManutencao.exe"
'@

Set-Content -Path $batPath -Value $batContent -Encoding Ascii

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force
Remove-Item $tempDir -Recurse -Force

Write-Host "Instalador gerado em: $zipPath"
