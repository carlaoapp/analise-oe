$desktopFolder = "$env:USERPROFILE\Desktop"
$zipName = "CriticaPro_Instalador_Ninja.zip"
$zipPath = Join-Path $desktopFolder $zipName
$sourceDir = "C:\Desenvolvimento\Projetos\Analise O.E"

$tempDir = Join-Path $env:TEMP "CriticaPro_Ninja"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copiar arquivos necessarios
Copy-Item (Join-Path $sourceDir "desktop_runner.cs") $tempDir -Force
Copy-Item (Join-Path $sourceDir "Sistema de Analises Orcamentos - Equip\icone-desktop.ico") $tempDir -Force

# Copiar a pasta public/desktop
$publicDirTemp = Join-Path $tempDir "public\desktop"
New-Item -ItemType Directory -Path $publicDirTemp -Force | Out-Null
Copy-Item (Join-Path $sourceDir "public\desktop\*") $publicDirTemp -Recurse -Force

# Criar script build_and_install.ps1
$ps1Path = Join-Path $tempDir "build_and_install.ps1"
$ps1Content = @'
 = System.Management.Automation.InvocationInfo.MyCommand.Path
 = Split-Path 
 = "C:\Users\NOTE\Desktop\CriticaPro - Computador"
 = Join-Path  "CriticaPro.exe"
 = Join-Path  "desktop_runner.cs"
 = Join-Path  "icone-desktop.ico"

# Localiza o compilador C#
 = @(
    "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
)
 =  | Where-Object { Test-Path  } | Select-Object -First 1

if (-not ) {
    [System.Windows.Forms.MessageBox]::Show("Nao foi possivel encontrar o compilador .NET nativo do Windows.", "Erro de Instalacao", 0, 16)
    exit
}

# Criar pasta no desktop
if (-not (Test-Path )) {
    New-Item -ItemType Directory -Force -Path  | Out-Null
}

 = @(
    "/target:winexe",
    "/optimize+",
    "/platform:anycpu",
    "/out:",
    "/win32icon:",
    "/reference:System.dll,System.Drawing.dll,System.Windows.Forms.dll,System.Web.Extensions.dll"
)

# Adicionar arquivos como recursos embutidos
 = Get-ChildItem -Path (Join-Path  "public\desktop") -File
foreach ( in ) {
     += "/resource:"",desktop."
}

 += """"

# Compilar direto no destino (evita Mark of the Web e SmartScreen)
 = Start-Process -FilePath  -ArgumentList  -NoNewWindow -Wait -PassThru

if (.ExitCode -eq 0 -and (Test-Path )) {
    # Criar atalho na area de trabalho
    =(New-Object -COM WScript.Shell).CreateShortcut("C:\Users\NOTE\Desktop\CriticaPro.lnk")
    .TargetPath=
    .WorkingDirectory=
    .Save()

    # Iniciar executavel
    Start-Process 
    
    [System.Windows.Forms.MessageBox]::Show("Sistema fabricado e instalado com sucesso no seu computador!", "CriticaPro Instalado", 0, 64)
} else {
    [System.Windows.Forms.MessageBox]::Show("Falha ao fabricar o executavel localmente.", "Erro", 0, 16)
}
'@

Set-Content -Path $ps1Path -Value $ps1Content -Encoding Ascii

# Criar o arquivo BAT amigavel (sem pedir admin)
$batPath = Join-Path $tempDir "Instalar_CriticaPro.bat"
$batContent = @'
@echo off
color 0B
echo =========================================================
echo       INSTALADOR NINJA - CRITICAPRO (COMPUTADOR)
echo =========================================================
echo.
echo Processando instalacao de forma segura pelo proprio Windows...
echo Isso burla a seguranca sem precisar de Administrador!
echo.
echo Aguarde um instante enquanto o sistema e fabricado...

powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0build_and_install.ps1"
'@

Set-Content -Path $batPath -Value $batContent -Encoding Ascii

# Compactar
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force

Remove-Item $tempDir -Recurse -Force

Write-Host "ZIP Ninja gerado em: $zipPath"
