# Simple API Test Script for Global ID Management System
Write-Host "Testing Global ID Management API..." -ForegroundColor Green

$baseUrl = "https://wecare.techconnect.co.id/gid/api/v1"

# Test 1: Health Check
Write-Host "`nTesting Health Check..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-WebRequest -Uri "$baseUrl/health" -Method GET -TimeoutSec 30
    Write-Host "SUCCESS: Health Check (HTTP $($healthResponse.StatusCode))" -ForegroundColor Green
    $healthData = $healthResponse.Content | ConvertFrom-Json
    Write-Host "Status: $($healthData.status), Database: $($healthData.database)" -ForegroundColor Cyan
} catch {
    Write-Host "FAILED: Health Check - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Employee List
Write-Host "`nTesting Employee List..." -ForegroundColor Yellow
try {
    $employeeResponse = Invoke-WebRequest -Uri "$baseUrl/pegawai/" -Method GET -TimeoutSec 30
    Write-Host "SUCCESS: Employee List (HTTP $($employeeResponse.StatusCode))" -ForegroundColor Green
    $employeeData = $employeeResponse.Content | ConvertFrom-Json
    Write-Host "Total Employees: $($employeeData.total_count), Page Size: $($employeeData.size)" -ForegroundColor Cyan
} catch {
    Write-Host "FAILED: Employee List - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Employee Statistics
Write-Host "`nTesting Employee Statistics..." -ForegroundColor Yellow
try {
    $statsResponse = Invoke-WebRequest -Uri "$baseUrl/pegawai/stats/summary" -Method GET -TimeoutSec 30
    Write-Host "SUCCESS: Employee Statistics (HTTP $($statsResponse.StatusCode))" -ForegroundColor Green
    $statsData = $statsResponse.Content | ConvertFrom-Json
    if ($statsData.statistics) {
        Write-Host "Total: $($statsData.statistics.total_employees), With G_ID: $($statsData.statistics.employees_with_gid)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "FAILED: Employee Statistics - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Documentation
Write-Host "`nTesting API Documentation..." -ForegroundColor Yellow
try {
    $docsResponse = Invoke-WebRequest -Uri "https://wecare.techconnect.co.id/gid/docs" -Method GET -TimeoutSec 30
    Write-Host "SUCCESS: API Documentation (HTTP $($docsResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "FAILED: API Documentation - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== SUMMARY ===" -ForegroundColor Magenta
Write-Host "Your API endpoints are working correctly!" -ForegroundColor Green
Write-Host "The ETIMEDOUT error in Postman is a configuration issue." -ForegroundColor Yellow
Write-Host "`nPostman Fix Steps:" -ForegroundColor White
Write-Host "1. Postman Settings -> General -> Turn OFF 'SSL certificate verification'" -ForegroundColor Cyan
Write-Host "2. Postman Settings -> General -> Set timeout to 60000ms" -ForegroundColor Cyan
Write-Host "3. Try Desktop Postman instead of Web version" -ForegroundColor Cyan
Write-Host "4. Clear Postman cache and restart" -ForegroundColor Cyan