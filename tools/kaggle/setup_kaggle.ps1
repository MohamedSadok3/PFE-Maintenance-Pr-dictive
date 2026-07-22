# Script PowerShell pour configurer Kaggle automatiquement
# =========================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$ApiKey = "KGAT_e61ac6c7270890a765eb0eb37ca0a931"
)

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  Configuration Kaggle CLI" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Créer le dossier .kaggle
$kaggleDir = "$env:USERPROFILE\.kaggle"
Write-Host "`n[1/4] Creation du dossier .kaggle..." -ForegroundColor Yellow

if (!(Test-Path $kaggleDir)) {
    New-Item -ItemType Directory -Force -Path $kaggleDir | Out-Null
    Write-Host "  ✅ Dossier cree: $kaggleDir" -ForegroundColor Green
} else {
    Write-Host "  ℹ️  Dossier existe deja" -ForegroundColor Gray
}

# 2. Créer le fichier kaggle.json
$kaggleFile = "$kaggleDir\kaggle.json"
Write-Host "`n[2/4] Creation du fichier kaggle.json..." -ForegroundColor Yellow

$config = @{
    username = $Username
    key = $ApiKey
} | ConvertTo-Json

$config | Out-File -FilePath $kaggleFile -Encoding UTF8 -Force

Write-Host "  ✅ Fichier cree: $kaggleFile" -ForegroundColor Green
Write-Host "  Username: $Username" -ForegroundColor Gray
Write-Host "  API Key: $($ApiKey.Substring(0,20))..." -ForegroundColor Gray

# 3. Installer kaggle CLI
Write-Host "`n[3/4] Installation de kaggle CLI..." -ForegroundColor Yellow

try {
    $kaggleVersion = kaggle --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ℹ️  Kaggle CLI deja installe: $kaggleVersion" -ForegroundColor Gray
    }
} catch {
    Write-Host "  Installation en cours..." -ForegroundColor Gray
    pip install kaggle --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Kaggle CLI installe avec succes!" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Erreur lors de l'installation" -ForegroundColor Red
        exit 1
    }
}

# 4. Tester la connexion
Write-Host "`n[4/4] Test de connexion a Kaggle..." -ForegroundColor Yellow

$testResult = kaggle datasets list --max-size 1 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Connexion reussie!" -ForegroundColor Green
} else {
    Write-Host "  ❌ Erreur de connexion" -ForegroundColor Red
    Write-Host "  Verifiez votre username et API key" -ForegroundColor Yellow
    Write-Host "`n  Error: $testResult" -ForegroundColor Red
    exit 1
}

# Résumé
Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  ✅ Configuration terminee!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host "`nCommandes disponibles:" -ForegroundColor Yellow
Write-Host "  kaggle datasets list -s 'bearing'     # Rechercher" -ForegroundColor Gray
Write-Host "  kaggle datasets download -d OWNER/NAME # Telecharger" -ForegroundColor Gray

Write-Host "`nExemples:" -ForegroundColor Yellow
Write-Host "  kaggle datasets download -d uciml/iris" -ForegroundColor Gray
Write-Host "  kaggle datasets download -d brjapon/cwru-bearing-datasets --unzip" -ForegroundColor Gray

Write-Host "`n"
