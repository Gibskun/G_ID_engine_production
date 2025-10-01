# Project Cleanup Script for G_ID_engine_production
# This script removes unnecessary files while preserving important system files

Write-Host "🧹 Starting Project Cleanup..." -ForegroundColor Green

$projectPath = "C:\Folder Project\G_ID_engine_production"

# 1. Remove Virtual Environment (CRITICAL - Should not be in source control)
$venvPath = "$projectPath\venv"
if (Test-Path $venvPath) {
    Write-Host "📁 Removing virtual environment directory..." -ForegroundColor Yellow
    Remove-Item $venvPath -Recurse -Force
    Write-Host "✅ Virtual environment removed" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No virtual environment found" -ForegroundColor Cyan
}

# 2. Remove Python Cache Files
Write-Host "🗑️  Removing Python cache files..." -ForegroundColor Yellow
Get-ChildItem $projectPath -Recurse -Directory -Name "__pycache__" | ForEach-Object {
    $cachePath = "$projectPath\$_"
    Remove-Item $cachePath -Recurse -Force
    Write-Host "   Removed: $_" -ForegroundColor Gray
}

Get-ChildItem $projectPath -Recurse -Filter "*.pyc" | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "   Removed: $($_.Name)" -ForegroundColor Gray
}
Write-Host "✅ Python cache files removed" -ForegroundColor Green

# 3. Remove Duplicate Data Generators (Keep Ultra Version)
$filesToRemove = @(
    "dummy_data_generator.py",
    "scripts\generate_dummy_data.py"
)

foreach ($file in $filesToRemove) {
    $filePath = "$projectPath\$file"
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        Write-Host "✅ Removed duplicate: $file" -ForegroundColor Green
    }
}

# 4. Remove Basic Table Creation Script (Keep SQLAlchemy version)
$basicTableScript = "$projectPath\create_tables_first_time.py"
if (Test-Path $basicTableScript) {
    Remove-Item $basicTableScript -Force
    Write-Host "✅ Removed basic table creation script" -ForegroundColor Green
}

# 5. Remove Test/Debug Files
$testFiles = @(
    "test_dashboard_fix.py",
    "optimize_dashboard.py"
)

foreach ($file in $testFiles) {
    $filePath = "$projectPath\$file"
    if (Test-Path $filePath) {
        Remove-Item $filePath -Force
        Write-Host "✅ Removed test/debug file: $file" -ForegroundColor Green
    }
}

# 6. Archive log file if it's large (>1MB)
$logFile = "$projectPath\gid_system.log"
if (Test-Path $logFile) {
    $logSize = (Get-Item $logFile).Length
    if ($logSize -gt 1MB) {
        $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $archivedLog = "$projectPath\gid_system_$timestamp.log"
        Move-Item $logFile $archivedLog
        Write-Host "📦 Archived large log file to: gid_system_$timestamp.log" -ForegroundColor Yellow
    }
}

# 7. Remove sample data files if they exist and are large
$sampleFiles = @(
    "sample_data_large.csv",
    "sample_data_medium.csv", 
    "sample_data_small.csv"
)

foreach ($file in $sampleFiles) {
    $filePath = "$projectPath\$file"
    if (Test-Path $filePath) {
        $fileSize = (Get-Item $filePath).Length
        if ($fileSize -gt 100KB) {
            Remove-Item $filePath -Force
            Write-Host "✅ Removed large sample file: $file" -ForegroundColor Green
        }
    }
}

# 8. Calculate space saved
Write-Host "📊 Calculating space saved..." -ForegroundColor Yellow
$currentSize = (Get-ChildItem $projectPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
$sizeMB = [math]::Round($currentSize / 1MB, 2)
Write-Host "📁 Current project size: $sizeMB MB" -ForegroundColor Cyan

Write-Host "🎉 Cleanup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary of important files PRESERVED:" -ForegroundColor Cyan
Write-Host "   ✅ main.py - Main application" -ForegroundColor White
Write-Host "   ✅ requirements.txt - Dependencies" -ForegroundColor White
Write-Host "   ✅ .env - Configuration" -ForegroundColor White
Write-Host "   ✅ app/ - Application code" -ForegroundColor White
Write-Host "   ✅ templates/ - Web templates" -ForegroundColor White
Write-Host "   ✅ static/ - Static files" -ForegroundColor White
Write-Host "   ✅ ultra_dummy_generator.py - Advanced data generator" -ForegroundColor White
Write-Host "   ✅ create_tables_sqlalchemy.py - Modern table creation" -ForegroundColor White
Write-Host "   ✅ All documentation (.md files)" -ForegroundColor White
Write-Host "   ✅ Production scripts (.sh, .bat)" -ForegroundColor White
Write-Host ""
Write-Host "🗑️  Files REMOVED:" -ForegroundColor Red
Write-Host "   ❌ venv/ - Virtual environment (should be recreated)" -ForegroundColor White
Write-Host "   ❌ __pycache__/ - Python cache directories" -ForegroundColor White
Write-Host "   ❌ *.pyc - Compiled Python files" -ForegroundColor White
Write-Host "   ❌ Duplicate data generators" -ForegroundColor White
Write-Host "   ❌ Basic table creation script" -ForegroundColor White
Write-Host "   ❌ Test/debug files" -ForegroundColor White
Write-Host "   ❌ Large sample data files" -ForegroundColor White