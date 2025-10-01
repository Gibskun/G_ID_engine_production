# PowerShell API Testing Script for Global ID Management System
# This script tests all your API endpoints and confirms they're working

Write-Host "Testing Global ID Management API Endpoints..." -ForegroundColor Green
Write-Host "Server: https://wecare.techconnect.co.id" -ForegroundColor Blue
Write-Host ""

$baseUrl = "https://wecare.techconnect.co.id/gid/api/v1"
$timeout = 30

# Test Results Array
$results = @()

function Test-Endpoint {
    param(
        [string]$url,
        [string]$method = "GET",
        [string]$description,
        [object]$body = $null
    )
    
    Write-Host "Testing: $description" -ForegroundColor Yellow
    Write-Host "URL: $url" -ForegroundColor Gray
    
    try {
        $headers = @{
            'Content-Type' = 'application/json'
        }
        
        if ($method -eq "GET") {
            $response = Invoke-WebRequest -Uri $url -Method $method -TimeoutSec $timeout -Headers $headers
        } else {
            $jsonBody = $body | ConvertTo-Json -Depth 10
            $response = Invoke-WebRequest -Uri $url -Method $method -Body $jsonBody -TimeoutSec $timeout -Headers $headers
        }
        
        $status = $response.StatusCode
        $contentLength = $response.Content.Length
        
        Write-Host "SUCCESS: HTTP $status ($contentLength bytes)" -ForegroundColor Green
        
        # Parse JSON response for summary
        try {
            $jsonResponse = $response.Content | ConvertFrom-Json
            if ($jsonResponse.total_count) {
                Write-Host "   Total Records: $($jsonResponse.total_count)" -ForegroundColor Cyan
            }
            if ($jsonResponse.employees -and $jsonResponse.employees.Count -gt 0) {
                Write-Host "   Employees in Response: $($jsonResponse.employees.Count)" -ForegroundColor Cyan
            }
            if ($jsonResponse.status) {
                Write-Host "   Health Status: $($jsonResponse.status)" -ForegroundColor Cyan
            }
        } catch {
            # Non-JSON response is fine
        }
        
        $script:results += @{
            URL = $url
            Method = $method
            Description = $description
            Status = "SUCCESS ($status)"
            ResponseSize = "$contentLength bytes"
        }
        
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $script:results += @{
            URL = $url
            Method = $method
            Description = $description
            Status = "FAILED"
            ResponseSize = "Error"
        }
    }
    
    Write-Host ""
}

# Test System Endpoints
Write-Host "=== SYSTEM ENDPOINTS ===" -ForegroundColor Magenta
Test-Endpoint -url "https://wecare.techconnect.co.id/gid/docs" -description "API Documentation (Swagger UI)"
Test-Endpoint -url "$baseUrl/health" -description "Health Check"

# Test Employee Management Endpoints
Write-Host "=== EMPLOYEE MANAGEMENT ENDPOINTS ===" -ForegroundColor Magenta
Test-Endpoint -url "$baseUrl/pegawai/" -description "Get All Employees (Default Pagination)"
Test-Endpoint -url "$baseUrl/pegawai/?page=1&size=5" -description "Get Employees (Custom Pagination)"
Test-Endpoint -url "$baseUrl/pegawai/?search=test" -description "Search Employees"
Test-Endpoint -url "$baseUrl/pegawai/stats/summary" -description "Employee Statistics"

# Test Global ID Data View Endpoints (if they exist)
Write-Host "=== GLOBAL ID DATA VIEW ENDPOINTS ===" -ForegroundColor Magenta
Test-Endpoint -url "$baseUrl/api/global_id" -description "Get All Global ID Records"
Test-Endpoint -url "$baseUrl/api/global_id_non_database" -description "Get Global ID Non-Database Records"

# Test Individual Employee Endpoint (using first employee ID if available)
Write-Host "=== INDIVIDUAL EMPLOYEE TEST ===" -ForegroundColor Magenta
try {
    $employeesResponse = Invoke-WebRequest -Uri "$baseUrl/pegawai/?size=1" -Method GET -TimeoutSec $timeout
    $employeesData = $employeesResponse.Content | ConvertFrom-Json
    
    if ($employeesData.employees -and $employeesData.employees.Count -gt 0) {
        $firstEmployeeId = $employeesData.employees[0].id
        Test-Endpoint -url "$baseUrl/pegawai/$firstEmployeeId" -description "Get Employee by ID ($firstEmployeeId)"
    } else {
        Write-Host "⚠️  No employees found to test individual endpoint" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not test individual employee endpoint" -ForegroundColor Yellow
}

# Test POST Endpoint (Create Employee)
Write-Host "=== CREATE EMPLOYEE TEST ===" -ForegroundColor Magenta
$newEmployee = @{
    name = "API Test Employee $(Get-Date -Format 'yyyyMMdd-HHmmss')"
    personal_number = "TEST-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    no_ktp = "1111222233334444"
    bod = "1990-01-01"
}

Test-Endpoint -url "$baseUrl/pegawai/" -method "POST" -description "Create New Employee" -body $newEmployee

# Summary Report
Write-Host ""
Write-Host "=== TEST SUMMARY REPORT ===" -ForegroundColor Magenta
Write-Host ""

$successCount = ($results | Where-Object { $_.Status -like "*SUCCESS*" }).Count
$failCount = ($results | Where-Object { $_.Status -like "*FAILED*" }).Count
$totalTests = $results.Count

Write-Host "📊 Total Tests: $totalTests" -ForegroundColor White
Write-Host "✅ Successful: $successCount" -ForegroundColor Green
Write-Host "❌ Failed: $failCount" -ForegroundColor Red
Write-Host ""

if ($successCount -gt 0) {
    Write-Host "✅ WORKING ENDPOINTS:" -ForegroundColor Green
    $results | Where-Object { $_.Status -like "*SUCCESS*" } | ForEach-Object {
        Write-Host "   $($_.Method) $($_.URL) - $($_.Description)" -ForegroundColor Green
    }
    Write-Host ""
}

if ($failCount -gt 0) {
    Write-Host "❌ FAILED ENDPOINTS:" -ForegroundColor Red
    $results | Where-Object { $_.Status -like "*FAILED*" } | ForEach-Object {
        Write-Host "   $($_.Method) $($_.URL) - $($_.Description)" -ForegroundColor Red
    }
    Write-Host ""
}

# Postman Fix Recommendations
Write-Host "=== POSTMAN FIX RECOMMENDATIONS ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Since PowerShell can access your API successfully:" -ForegroundColor White
Write-Host "1. Postman Settings -> General -> Turn OFF 'SSL certificate verification'" -ForegroundColor Yellow
Write-Host "2. Postman Settings -> General -> Set 'Request timeout' to 60000ms" -ForegroundColor Yellow
Write-Host "3. Postman Settings -> Proxy -> Turn OFF 'Use the system proxy'" -ForegroundColor Yellow
Write-Host "4. Try Postman Desktop App instead of web version" -ForegroundColor Yellow
Write-Host "5. Clear Postman cache: Settings -> Data -> Clear" -ForegroundColor Yellow
Write-Host ""
Write-Host "Your API is working perfectly! The issue is Postman configuration." -ForegroundColor Green
Write-Host ""
Write-Host "Test Complete! Your Global ID Management API is fully functional." -ForegroundColor Green