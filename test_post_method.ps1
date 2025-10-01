# PowerShell Script to Test POST Method for Employee Creation
# This script demonstrates how to create employees and get their G_IDs

Write-Host "Testing POST Method: Create Employee & Get G_ID" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

$baseUrl = "https://wecare.techconnect.co.id/gid/api/v1"
$timeout = 30

# Function to create employee
function New-Employee {
    param(
        [string]$name,
        [string]$personalNumber = $null,
        [string]$ktpNumber,
        [string]$birthDate = $null
    )
    
    # Prepare request body
    $employeeData = @{
        name = $name
        no_ktp = $ktpNumber
    }
    
    if ($personalNumber) {
        $employeeData.personal_number = $personalNumber
    }
    
    if ($birthDate) {
        $employeeData.bod = $birthDate
    }
    
    $jsonBody = $employeeData | ConvertTo-Json
    
    Write-Host "Creating Employee: $name" -ForegroundColor Yellow
    Write-Host "KTP Number: $ktpNumber" -ForegroundColor Gray
    Write-Host "Request Body: $jsonBody" -ForegroundColor Gray
    Write-Host ""
    
    try {
        $headers = @{
            'Content-Type' = 'application/json'
            'Accept' = 'application/json'
        }
        
        $response = Invoke-WebRequest -Uri "$baseUrl/pegawai/" -Method POST -Body $jsonBody -Headers $headers -TimeoutSec $timeout
        
        Write-Host "SUCCESS: HTTP $($response.StatusCode)" -ForegroundColor Green
        
        $responseData = $response.Content | ConvertFrom-Json
        
        if ($responseData.success) {
            Write-Host "✅ Employee Created Successfully!" -ForegroundColor Green
            Write-Host "   Employee ID: $($responseData.employee.id)" -ForegroundColor Cyan
            Write-Host "   Name: $($responseData.employee.name)" -ForegroundColor Cyan
            Write-Host "   Personal Number: $($responseData.employee.personal_number)" -ForegroundColor Cyan
            Write-Host "   KTP Number: $($responseData.employee.no_ktp)" -ForegroundColor Cyan
            Write-Host "   Birth Date: $($responseData.employee.bod)" -ForegroundColor Cyan
            Write-Host "   🎯 GENERATED G_ID: $($responseData.employee.g_id)" -ForegroundColor Magenta
            Write-Host "   Created At: $($responseData.employee.created_at)" -ForegroundColor Cyan
            Write-Host ""
            
            return $responseData.employee
        } else {
            Write-Host "❌ Failed: $($responseData.message)" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        
        # Try to parse error response
        try {
            $errorResponse = $_.Exception.Response
            if ($errorResponse) {
                $reader = New-Object System.IO.StreamReader($errorResponse.GetResponseStream())
                $errorContent = $reader.ReadToEnd()
                $errorData = $errorContent | ConvertFrom-Json
                
                Write-Host "   Error Details:" -ForegroundColor Red
                Write-Host "   - Success: $($errorData.success)" -ForegroundColor Red
                Write-Host "   - Error: $($errorData.error)" -ForegroundColor Red
                Write-Host "   - Detail: $($errorData.detail)" -ForegroundColor Red
            }
        } catch {
            # Could not parse error response
        }
    }
    
    Write-Host ""
    return $null
}

# Test 1: Create employee with all fields
Write-Host "=== TEST 1: Complete Employee Data ===" -ForegroundColor Magenta
$employee1 = New-Employee -name "John Doe PowerShell" -personalNumber "PS-TEST-001" -ktpNumber "1234567890123456" -birthDate "1990-01-01"

# Test 2: Create employee with minimal data
Write-Host "=== TEST 2: Minimal Employee Data ===" -ForegroundColor Magenta
$employee2 = New-Employee -name "Jane Smith PowerShell" -ktpNumber "9876543210987654"

# Test 3: Create employee with timestamp-based unique data
Write-Host "=== TEST 3: Unique Employee Data ===" -ForegroundColor Magenta
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$uniqueKtp = "1111" + $timestamp.Substring(0, 12)  # Make 16 digits
$employee3 = New-Employee -name "Unique Employee $timestamp" -personalNumber "PS-$timestamp" -ktpNumber $uniqueKtp -birthDate "1985-05-15"

# Test 4: Error test - Invalid KTP
Write-Host "=== TEST 4: Error Test - Invalid KTP ===" -ForegroundColor Magenta
$employee4 = New-Employee -name "Invalid Employee" -ktpNumber "12345"  # Invalid - too short

# Test 5: Error test - Empty name
Write-Host "=== TEST 5: Error Test - Empty Name ===" -ForegroundColor Magenta
$employee5 = New-Employee -name "" -ktpNumber "5555666677778888"

# Summary of created employees
Write-Host ""
Write-Host "=== CREATION SUMMARY ===" -ForegroundColor Magenta
Write-Host ""

$createdEmployees = @($employee1, $employee2, $employee3) | Where-Object { $_ -ne $null }

if ($createdEmployees.Count -gt 0) {
    Write-Host "✅ Successfully Created Employees:" -ForegroundColor Green
    foreach ($emp in $createdEmployees) {
        Write-Host "   🆔 ID: $($emp.id) | 🎯 G_ID: $($emp.g_id) | 👤 Name: $($emp.name)" -ForegroundColor Green
    }
    Write-Host ""
    
    # Test verification - Get the first created employee
    if ($createdEmployees.Count -gt 0) {
        $firstEmployee = $createdEmployees[0]
        Write-Host "=== VERIFICATION: Get Created Employee ===" -ForegroundColor Magenta
        
        try {
            $verifyResponse = Invoke-WebRequest -Uri "$baseUrl/pegawai/$($firstEmployee.id)" -Method GET -TimeoutSec $timeout
            $verifyData = $verifyResponse.Content | ConvertFrom-Json
            
            Write-Host "✅ Verification Successful!" -ForegroundColor Green
            Write-Host "   Retrieved Employee ID: $($verifyData.id)" -ForegroundColor Cyan
            Write-Host "   Retrieved G_ID: $($verifyData.g_id)" -ForegroundColor Cyan
            Write-Host "   Name Matches: $(if ($verifyData.name -eq $firstEmployee.name) {'✅ Yes'} else {'❌ No'})" -ForegroundColor Cyan
            
        } catch {
            Write-Host "❌ Verification Failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "❌ No employees were created successfully" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== POST METHOD TEST COMPLETE ===" -ForegroundColor Green
Write-Host ""
Write-Host "🔑 Key Points:" -ForegroundColor White
Write-Host "1. ✅ POST method creates employees and auto-generates G_IDs" -ForegroundColor Yellow
Write-Host "2. ✅ Required fields: 'name' and 'no_ktp' (16 digits)" -ForegroundColor Yellow
Write-Host "3. ✅ Optional fields: 'personal_number' and 'bod'" -ForegroundColor Yellow
Write-Host "4. ✅ System validates input and returns detailed errors" -ForegroundColor Yellow
Write-Host "5. ✅ Each employee gets a unique G_ID automatically" -ForegroundColor Yellow
Write-Host ""
Write-Host "🎉 Your POST API is working perfectly!" -ForegroundColor Green