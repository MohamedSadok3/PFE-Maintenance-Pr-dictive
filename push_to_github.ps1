# Script Push vers GitHub - SmartMaintain
# Auteur: Mohamed Sadok
# Date: 22 Juillet 2026

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🚀 PUSH SMARTMAINTAIN VERS GITHUB                   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Étape 1: Demander username GitHub
Write-Host "📝 Configuration`n" -ForegroundColor Yellow
$username = Read-Host "Entrer votre nom d'utilisateur GitHub"

if ([string]::IsNullOrWhiteSpace($username)) {
    Write-Host "❌ Nom d'utilisateur requis!" -ForegroundColor Red
    exit 1
}

# Étape 2: Vérifier que nous sommes dans le bon répertoire
$currentDir = Get-Location
if (-not (Test-Path "README.md") -or -not (Test-Path "smartmaintain")) {
    Write-Host "❌ Veuillez exécuter ce script depuis: c:\Users\Mohamed Sadok\Desktop\PFE Maintenance prédictive" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Répertoire correct: $currentDir" -ForegroundColor Green

# Étape 3: Vérifier statut Git
Write-Host "`n📊 Vérification statut Git...`n" -ForegroundColor Yellow
$gitStatus = git status --short
if ($gitStatus) {
    Write-Host "⚠️ Fichiers non commités détectés:" -ForegroundColor Yellow
    git status --short
    $commit = Read-Host "`nVoulez-vous les commiter maintenant? (o/n)"
    if ($commit -eq "o") {
        git add .
        $message = Read-Host "Message du commit"
        git commit -m $message
        Write-Host "✅ Commit créé" -ForegroundColor Green
    }
}

# Étape 4: Vérifier si remote existe déjà
Write-Host "`n🔗 Configuration remote...`n" -ForegroundColor Yellow
$remotes = git remote
if ($remotes -contains "origin") {
    Write-Host "⚠️ Remote 'origin' existe déjà" -ForegroundColor Yellow
    $currentOrigin = git remote get-url origin
    Write-Host "Remote actuel: $currentOrigin" -ForegroundColor Cyan
    
    $replace = Read-Host "Voulez-vous le remplacer? (o/n)"
    if ($replace -eq "o") {
        git remote remove origin
        Write-Host "✅ Remote 'origin' supprimé" -ForegroundColor Green
    } else {
        Write-Host "❌ Opération annulée" -ForegroundColor Red
        exit 0
    }
}

# Étape 5: Ajouter remote
$repoUrl = "https://github.com/$username/smartmaintain.git"
Write-Host "🔗 Ajout remote: $repoUrl" -ForegroundColor Cyan
git remote add origin $repoUrl

# Vérifier
$verifyRemote = git remote get-url origin
Write-Host "✅ Remote configuré: $verifyRemote`n" -ForegroundColor Green

# Étape 6: Renommer branche en 'main'
Write-Host "🔄 Renommage branche en 'main'..." -ForegroundColor Yellow
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    git branch -M main
    Write-Host "✅ Branche renommée: $currentBranch → main`n" -ForegroundColor Green
} else {
    Write-Host "✅ Branche déjà nommée 'main'`n" -ForegroundColor Green
}

# Étape 7: Confirmation avant push
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║     ⚠️  PRÊT À POUSSER VERS GITHUB                      ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Yellow

Write-Host "Repository: $repoUrl" -ForegroundColor Cyan
Write-Host "Branche:    main" -ForegroundColor Cyan

# Compter fichiers et commits
$fileCount = (git ls-files).Count
$commitCount = (git rev-list --count HEAD)
Write-Host "Fichiers:   $fileCount" -ForegroundColor Cyan
Write-Host "Commits:    $commitCount`n" -ForegroundColor Cyan

$confirm = Read-Host "Confirmer push vers GitHub? (o/n)"
if ($confirm -ne "o") {
    Write-Host "`n❌ Push annulé" -ForegroundColor Red
    exit 0
}

# Étape 8: Push vers GitHub
Write-Host "`n🚀 Push en cours...`n" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Gray

try {
    git push -u origin main
    
    Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Gray
    Write-Host "`n✅ PUSH RÉUSSI!" -ForegroundColor Green
    Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║     🎉 PROJET DISPONIBLE SUR GITHUB                     ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
    
    Write-Host "🌐 URL Repository:" -ForegroundColor Cyan
    Write-Host "   https://github.com/$username/smartmaintain`n" -ForegroundColor White
    
    Write-Host "📋 Prochaines étapes suggérées:`n" -ForegroundColor Yellow
    Write-Host "   1. Aller sur https://github.com/$username/smartmaintain"
    Write-Host "   2. Vérifier que tous les fichiers sont présents"
    Write-Host "   3. Ajouter une description dans 'About'"
    Write-Host "   4. Ajouter topics: machine-learning, predictive-maintenance, xgboost"
    Write-Host "   5. (Optionnel) Ajouter LICENSE et contribuer guidelines`n"
    
    # Demander si ouvrir dans navigateur
    $openBrowser = Read-Host "Voulez-vous ouvrir le repository dans votre navigateur? (o/n)"
    if ($openBrowser -eq "o") {
        Start-Process "https://github.com/$username/smartmaintain"
    }
    
} catch {
    Write-Host "`n❌ ERREUR lors du push!" -ForegroundColor Red
    Write-Host "Erreur: $_`n" -ForegroundColor Red
    
    Write-Host "💡 Solutions possibles:`n" -ForegroundColor Yellow
    Write-Host "1. Vérifier que le repository existe sur GitHub:"
    Write-Host "   → https://github.com/$username/smartmaintain`n"
    
    Write-Host "2. Si erreur d'authentification:"
    Write-Host "   → Utiliser Personal Access Token (pas mot de passe)"
    Write-Host "   → Générer token: https://github.com/settings/tokens`n"
    
    Write-Host "3. Vérifier connexion Internet`n"
    
    Write-Host "4. Consulter: GITHUB_PUSH_INSTRUCTIONS.md`n"
    
    exit 1
}

Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
Write-Host "Script terminé avec succès! 🎉`n" -ForegroundColor Green
