# PowerShell script to test validation endpoints locally
# Run this on Windows to verify endpoints work

Write-Host "🔧 Testing G_ID Validation Endpoints Locally" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if server is running
$baseUrl = "http://127.0.0.1:8000"

Write-Host "`n1. Testing if server is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/docs" -Method GET -TimeoutSec 5
    Write-Host "✅ Server is running (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "❌ Server is not running or unreachable" -ForegroundColor Red
    Write-Host "Please start the server first with: python main.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n2. Testing validation status endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/validation-config/status" -Method GET
    $content = $response.Content | ConvertFrom-Json
    Write-Host "✅ Validation Status Endpoint Working!" -ForegroundColor Green
    Write-Host "Response: $($content | ConvertTo-Json -Depth 3)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Validation status endpoint failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n3. Testing validation toggle endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/validation-config/toggle-strict" -Method POST
    $content = $response.Content | ConvertFrom-Json
    Write-Host "✅ Validation Toggle Endpoint Working!" -ForegroundColor Green
    Write-Host "Response: $($content | ConvertTo-Json -Depth 3)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Validation toggle endpoint failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n4. Opening sync management page..." -ForegroundColor Yellow
Start-Process "$baseUrl/sync-management"

Write-Host "`n🎯 Testing complete!" -ForegroundColor Green
Write-Host "If all endpoints show ✅, the validation system is working correctly." -ForegroundColor Cyan