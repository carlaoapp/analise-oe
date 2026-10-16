<#
  LANCAR NOVA VERSAO - ANALISE O.E
  Uso: powershell -ExecutionPolicy Bypass -File .\release.ps1 -Version 1.0.1 [-Message "o que mudou"]

  Faz tudo sozinho:
   1. Atualiza o numero da versao em js/update.js, version.json e sw.js
   2. Copia public/ para a raiz (GitHub Pages)
   3. Commit + push na branch main do GitHub
   Depois do push, quem tem o app instalado ve na tela: "Atualizacao Disponivel [Atualizar Agora]".
#>
param(
  [Parameter(Mandatory = $true)][string]$Version,
  [string]$Message = ""
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "Versao invalida '$Version'. Use o formato 1.0.1" }

$current = (Get-Content "public\version.json" -Raw | ConvertFrom-Json).version
if ($current -eq $Version) { throw "A versao $Version ja e a atual. Informe um numero maior." }
Write-Host "Versao atual: $current  ->  Nova versao: $Version"

$files = @("public\js\update.js", "public\version.json", "public\sw.js")
foreach ($f in $files) {
  $text = [IO.File]::ReadAllText((Resolve-Path $f))
  if ($text.Contains($current)) {
    [IO.File]::WriteAllText((Resolve-Path $f), $text.Replace($current, $Version), (New-Object Text.UTF8Encoding($false)))
    Write-Host "  atualizado: $f"
  }
}

Copy-Item -Path "public\*" -Destination "." -Recurse -Force
Write-Host "  public/ sincronizado com a raiz para o GitHub Pages"

$msg = "v$Version"
if ($Message) { $msg += ": $Message" }
git add -A
git commit -m "$msg"
$prevEA = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
git push origin main
$ErrorActionPreference = $prevEA
Write-Host "Versao $Version publicada com sucesso! O GitHub Pages e o Render atualizam sozinhos na nuvem."
