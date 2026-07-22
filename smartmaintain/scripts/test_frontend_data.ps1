# Script de Test - Flux de Données Frontend
# ==========================================

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Test Flux Données SmartMaintain        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Étape 1: Vérifier ML Service
Write-Host "📊 Étape 1: Vérification ML Service..." -ForegroundColor Yellow
$mlLogs = docker-compose logs ml --tail=100 | Select-String "Modèle.*chargé"
if ($mlLogs) {
    Write-Host "  ✅ $($mlLogs.Count) modèles chargés" -ForegroundColor Green
    $mlLogs | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
} else {
    Write-Host "  ⚠️  Aucun modèle visible dans logs" -ForegroundColor Yellow
    Write-Host "     Redémarrage ML service..." -ForegroundColor Gray
    docker-compose restart ml | Out-Null
    Start-Sleep -Seconds 5
}

# Étape 2: Tester Prédiction ML Direct
Write-Host "`n🧠 Étape 2: Test Prédiction ML Directe..." -ForegroundColor Yellow
try {
    $body = @{
        machine = "moteur"
        sensors = @{
            vibration = 0.5
            current = 12.0
        }
    } | ConvertTo-Json
    
    $prediction = Invoke-RestMethod -Uri "http://localhost:5002/api/ml/predict" `
                                    -Method POST `
                                    -Body $body `
                                    -ContentType "application/json" `
                                    -TimeoutSec 5
    
    Write-Host "  ✅ ML API répond" -ForegroundColor Green
    Write-Host "     Défaut: $($prediction.defect)" -ForegroundColor Gray
    Write-Host "     Score: $($prediction.defect_score)" -ForegroundColor Gray
    Write-Host "     Confidence: $($prediction.confidence)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ ML API erreur: $($_.Exception.Message)" -ForegroundColor Red
}

# Étape 3: Vérifier Redis Pub/Sub
Write-Host "`n📡 Étape 3: Écoute Redis (10 secondes)..." -ForegroundColor Yellow
Write-Host "     Appuyez sur Ctrl+C pour arrêter avant`n" -ForegroundColor Gray

$redisJob = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    $count = 0
    docker-compose exec redis redis-cli --csv PSUBSCRIBE '*' 2>&1 | ForEach-Object {
        if ($_ -match 'sensor_data|ml_predictions') {
            $count++
            Write-Output "[$count] $_"
        }
        if ($count -ge 5) { break }
    }
} -ArgumentList (Get-Location).Path

$timeout = 10
Wait-Job $redisJob -Timeout $timeout | Out-Null

$redisOutput = Receive-Job $redisJob
if ($redisOutput) {
    Write-Host "  ✅ Données Redis détectées:" -ForegroundColor Green
    $redisOutput | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
} else {
    Write-Host "  ⚠️  Pas de données Redis en 10 secondes" -ForegroundColor Yellow
    Write-Host "     Vérification IoT service..." -ForegroundColor Gray
    docker-compose logs iot --tail=20 | Select-String "publish|error" | ForEach-Object {
        Write-Host "     $_" -ForegroundColor Gray
    }
}
Remove-Job $redisJob -Force

# Étape 4: Tester WebSocket Gateway
Write-Host "`n🌐 Étape 4: Test Gateway WebSocket..." -ForegroundColor Yellow
try {
    $gatewayHealth = Invoke-RestMethod -Uri "http://localhost:5000/health" -TimeoutSec 3
    Write-Host "  ✅ Gateway accessible" -ForegroundColor Green
    $gatewayHealth.PSObject.Properties | ForEach-Object {
        $status = if ($_.Value -eq "ok") { "✅" } else { "❌" }
        Write-Host "     $status $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ❌ Gateway erreur: $($_.Exception.Message)" -ForegroundColor Red
}

# Étape 5: Vérifier Frontend
Write-Host "`n🎨 Étape 5: Vérification Frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing
    Write-Host "  ✅ Frontend accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Frontend erreur: $($_.Exception.Message)" -ForegroundColor Red
}

# Résumé
Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  RÉSUMÉ ET RECOMMANDATIONS               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📋 Checklist:" -ForegroundColor Yellow
Write-Host "   [ ] ML service répond aux prédictions" -ForegroundColor White
Write-Host "   [ ] Redis publie sensor_data toutes les 2s" -ForegroundColor White
Write-Host "   [ ] Gateway health check OK" -ForegroundColor White
Write-Host "   [ ] Frontend accessible sur :3000" -ForegroundColor White

Write-Host "`n🔧 Si problème persiste:" -ForegroundColor Yellow
Write-Host "   1. Ouvrir http://localhost:3000 dans navigateur" -ForegroundColor White
Write-Host "   2. Appuyer F12 (Console développeur)" -ForegroundColor White
Write-Host "   3. Onglet Console: Chercher erreurs en rouge" -ForegroundColor White
Write-Host "   4. Onglet Network: Filter 'WS' → Vérifier WebSocket" -ForegroundColor White
Write-Host "   5. Lire: TROUBLESHOOTING_FRONTEND.md" -ForegroundColor White

Write-Host "`n🚀 Reset rapide si nécessaire:" -ForegroundColor Yellow
Write-Host "   docker-compose restart iot ml alertes gateway" -ForegroundColor Gray
Write-Host "   Start-Sleep -Seconds 20" -ForegroundColor Gray
Write-Host "   Puis rafraîchir navigateur (Ctrl+F5)`n" -ForegroundColor Gray

Write-Host "✅ Diagnostic terminé!`n" -ForegroundColor Green
