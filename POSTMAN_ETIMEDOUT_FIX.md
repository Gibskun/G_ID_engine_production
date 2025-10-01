# 🔧 POSTMAN ETIMEDOUT FIX GUIDE

## ✅ CONFIRMED: Your API is Working!

**Verified Working Endpoints**:
- ✅ `https://wecare.techconnect.co.id/gid/docs` - API Documentation (200 OK)
- ✅ `https://wecare.techconnect.co.id/gid/api/v1/health` - Health Check (200 OK)
- ✅ `  ` - Employee List (200 OK, 7504 records)
- ✅ `https://wecare.techconnect.co.id/gid/api/v1/pegawai/stats/summary` - Statistics (200 OK)

## 🔧 POSTMAN CONFIGURATION FIX

### Method 1: Postman Settings (MOST COMMON FIX)

1. **Open Postman Settings**:
   - File → Settings (or Postman → Preferences on Mac)
   - Or click the gear icon in top-right

2. **General Tab**:
   - ❌ **Turn OFF** "SSL certificate verification"
   - ✅ **Set** "Request timeout in ms" to **60000** (60 seconds)
   - ❌ **Turn OFF** "Automatically follow redirects"

3. **Proxy Tab**:
   - ❌ **Turn OFF** "Use the system proxy"
   - ❌ **Turn OFF** "Use a custom proxy configuration"

4. **Data Tab** (Optional but recommended):
   - Click **"Clear"** to clear cache
   - Restart Postman after clearing

### Method 2: Request-Level Configuration

In your specific request:

1. **Headers Tab**:
   - Remove all custom headers (let Postman auto-generate)
   - Do NOT manually add: User-Agent, Accept-Encoding, Connection, etc.

2. **Settings Tab** (in the request):
   - Set "Request timeout" to **60000ms**
   - ❌ Turn OFF "Follow original HTTP method"

### Method 3: Alternative Postman Versions

If settings don't work:

1. **Try Postman Desktop App**:
   - Download from: https://www.postman.com/downloads/
   - Desktop version often handles SSL/proxy better than web version

2. **Try Postman Agent** (for web version):
   - Install Postman Desktop Agent
   - Enable it in web Postman settings

### Method 4: Network/System Issues

1. **Windows Firewall**:
   ```powershell
   # Run as Administrator
   New-NetFirewallRule -DisplayName "Postman HTTPS" -Direction Outbound -Protocol TCP -RemotePort 443 -Action Allow
   ```

2. **Corporate Network/VPN**:
   - Try with VPN **OFF** if you're using one
   - Add `*.techconnect.co.id` to proxy bypass list
   - Contact IT about HTTPS access to external APIs

3. **DNS Issues**:
   ```powershell
   # Flush DNS cache
   ipconfig /flushdns
   ```

## 🧪 IMMEDIATE TEST STEPS

### Step 1: Test in Browser FIRST
Open these URLs in your browser:
- `https://wecare.techconnect.co.id/gid/docs`
- Click "Try it out" on any GET endpoint in Swagger UI

If Swagger UI works, the issue is definitely Postman configuration.

### Step 2: Create New Postman Request
1. Create **brand new** request (don't copy/paste)
2. Method: **GET**
3. URL: `https://wecare.techconnect.co.id/gid/api/v1/pegawai/`
4. Headers: **Leave empty** (remove all)
5. Body: **None**
6. Send request

### Step 3: Working PowerShell Alternative
Use this PowerShell command as alternative:
```powershell
# This command works perfectly:
Invoke-WebRequest -Uri "https://wecare.techconnect.co.id/gid/api/v1/pegawai/" -Method GET -TimeoutSec 30
```

## 🔄 ALTERNATIVE TOOLS

If Postman still doesn't work, try these:

### Thunder Client (VS Code Extension)
1. Install "Thunder Client" in VS Code
2. Create new request
3. Same URL: `https://wecare.techconnect.co.id/gid/api/v1/pegawai/`

### Insomnia REST Client
1. Download from: https://insomnia.rest/
2. Import your requests
3. Often handles SSL/proxy issues better

### curl (Command Line)
PowerShell equivalent:
```powershell
curl.exe -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/" -H "Accept: application/json"
```

## 📋 POSTMAN COLLECTION IMPORT

Complete Postman collection JSON with GET and POST methods:

```json
{
  "info": {
    "name": "Global ID API - Complete Collection",
    "description": "Complete REST API testing for Global ID Management System including GET and POST methods",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "https://wecare.techconnect.co.id/gid/api/v1"
    },
    {
      "key": "employee_id",
      "value": ""
    },
    {
      "key": "g_id",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "System Endpoints",
      "item": [
        {
          "name": "Health Check",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/health"
          }
        },
        {
          "name": "API Documentation",
          "request": {
            "method": "GET",
            "url": "https://wecare.techconnect.co.id/gid/docs"
          }
        }
      ]
    },
    {
      "name": "Employee Management",
      "item": [
        {
          "name": "Get All Employees",
          "request": {
            "method": "GET",
            "url": {
              "raw": "{{base_url}}/pegawai/?page=1&size=20",
              "host": ["{{base_url}}"],
              "path": ["pegawai", ""],
              "query": [
                {"key": "page", "value": "1"},
                {"key": "size", "value": "20"}
              ]
            }
          }
        },
        {
          "name": "Create Employee (POST)",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 201', function () {",
                  "    pm.response.to.have.status(201);",
                  "});",
                  "",
                  "pm.test('Response has success=true', function () {",
                  "    const jsonData = pm.response.json();",
                  "    pm.expect(jsonData.success).to.be.true;",
                  "});",
                  "",
                  "pm.test('Employee has ID and G_ID', function () {",
                  "    const jsonData = pm.response.json();",
                  "    pm.expect(jsonData.employee).to.have.property('id');",
                  "    pm.expect(jsonData.employee).to.have.property('g_id');",
                  "});",
                  "",
                  "if (pm.response.code === 201) {",
                  "    const response = pm.response.json();",
                  "    if (response.success && response.employee) {",
                  "        pm.collectionVariables.set('employee_id', response.employee.id);",
                  "        pm.collectionVariables.set('g_id', response.employee.g_id);",
                  "        console.log('Created Employee ID:', response.employee.id);",
                  "        console.log('Generated G_ID:', response.employee.g_id);",
                  "    }",
                  "}"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"name\": \"Test Employee Postman\",\n  \"personal_number\": \"TEST-{{$timestamp}}\",\n  \"no_ktp\": \"1111{{$timestamp}}\",\n  \"bod\": \"1990-01-01\"\n}"
            },
            "url": "{{base_url}}/pegawai/"
          }
        },
        {
          "name": "Get Employee by ID",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/pegawai/{{employee_id}}"
          }
        },
        {
          "name": "Employee Statistics",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/pegawai/stats/summary"
          }
        }
      ]
    }
  ]
}
```

## 🚨 COMMON MISTAKES TO AVOID

1. **❌ Don't use**: `https://wecare.techconnect.co.id/gid/api/v1/` (base URL only)
2. **✅ Always use**: `https://wecare.techconnect.co.id/gid/api/v1/pegawai/` (with endpoint)

3. **❌ Don't add these headers**:
   - User-Agent: PostmanRuntime/7.48.0
   - Accept-Encoding: gzip, deflate, br
   - Connection: keep-alive

4. **✅ Let Postman auto-generate headers**

## 📞 IF NOTHING WORKS

Your API is confirmed working. If Postman still fails:

1. **Use PowerShell**: Run `.\simple_api_test.ps1`
2. **Use Browser**: Test via Swagger UI at `/docs`
3. **Use Thunder Client**: VS Code extension alternative
4. **Contact Network Admin**: May be corporate firewall issue

## ✅ SUCCESS CONFIRMATION

You'll know it's working when you see:
```json
{
  "total_count": 7504,
  "page": 1,
  "size": 20,
  "total_pages": 376,
  "employees": [
    {
      "id": 7505,
      "name": "chatbot ai",
      "personal_number": "EMP-2025-0812",
      "no_ktp": "3211091876544678",
      "bod": "2000-11-11",
      "g_id": "G025DI06"
    }
  ]
}
```

**Your API is perfect! The issue is client-side configuration.** 🎉

---

## 📝 **POST METHOD: CREATE EMPLOYEE & GET G_ID**

### **Overview**
The POST method allows you to create new employee records and automatically generates a Global ID (G_ID) for each employee. This is the core functionality of the Global ID Management System.

### **📍 Endpoint Details**
- **Method**: `POST`
- **URL**: `https://wecare.techconnect.co.id/gid/api/v1/pegawai/`
- **Purpose**: Create new employee and automatically assign G_ID
- **Response**: Returns employee data including generated G_ID

### **📥 REQUEST FORMAT**

#### **Headers**
```
Content-Type: application/json
Accept: application/json
```

#### **Request Body (JSON)**
```json
{
  "name": "John Doe",
  "personal_number": "EMP001",
  "no_ktp": "1234567890123456",
  "bod": "1990-01-01"
}
```

#### **Field Requirements**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `name` | string | ✅ **Required** | Employee full name | 1-255 characters, cannot be empty |
| `personal_number` | string | ❌ Optional | Employee staff number | Max 15 characters |
| `no_ktp` | string | ✅ **Required** | Indonesian ID number | **Exactly 16 digits, must be unique** |
| `bod` | string | ❌ Optional | Birth date | Format: `YYYY-MM-DD` |

### **📤 RESPONSE FORMAT**

#### **✅ Success Response (201 Created)**
```json
{
  "success": true,
  "message": "Employee created successfully",
  "employee": {
    "id": 7506,
    "name": "John Doe",
    "personal_number": "EMP001",
    "no_ktp": "1234567890123456",
    "bod": "1990-01-01",
    "g_id": "G025DI07",
    "created_at": "2025-10-01T14:30:00.123456",
    "updated_at": "2025-10-01T14:30:00.123456",
    "deleted_at": null
  }
}
```

**🎯 Key Output Fields:**
- **`id`**: Auto-generated employee database ID
- **`g_id`**: **Auto-generated Global ID** (e.g., "G025DI07")
- **`created_at`**: Timestamp when employee was created
- **`success`**: Always `true` for successful operations

#### **❌ Error Response (422 Validation Error)**
```json
{
  "success": false,
  "error": "Validation error",
  "detail": "KTP number must be exactly 16 digits"
}
```

**Common Validation Errors:**
- `"KTP number must be exactly 16 digits"` - Invalid KTP format
- `"Name cannot be empty"` - Missing or empty name
- `"Personal number cannot exceed 15 characters"` - Personal number too long
- `"Employee with this KTP already exists"` - Duplicate KTP number

### **🧪 POSTMAN TEST SETUP**

#### **Step 1: Create POST Request**
1. Method: `POST`
2. URL: `https://wecare.techconnect.co.id/gid/api/v1/pegawai/`
3. Headers:
   ```
   Content-Type: application/json
   ```

#### **Step 2: Request Body**
In the **Body** tab, select **raw** and **JSON**:
```json
{
  "name": "Test Employee API",
  "personal_number": "TEST-20251001",
  "no_ktp": "1111222233334444",
  "bod": "1995-05-15"
}
```

#### **Step 3: Tests Script**
In the **Tests** tab, add this validation script:
```javascript
// Test response status
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

// Test response structure
pm.test("Response has success=true", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
});

// Test employee data
pm.test("Employee has ID and G_ID", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.employee).to.have.property('id');
    pm.expect(jsonData.employee).to.have.property('g_id');
    pm.expect(jsonData.employee.g_id).to.not.be.null;
});

// Save employee data for other tests
if (pm.response.code === 201) {
    const response = pm.response.json();
    if (response.success && response.employee) {
        pm.collectionVariables.set("employee_id", response.employee.id);
        pm.collectionVariables.set("g_id", response.employee.g_id);
        console.log("Created Employee ID:", response.employee.id);
        console.log("Generated G_ID:", response.employee.g_id);
    }
}
```

### **📋 TEST SCENARIOS**

#### **Scenario 1: Valid Employee Creation**
**Input:**
```json
{
  "name": "Alice Johnson",
  "personal_number": "EMP2025001",
  "no_ktp": "3201234567890123",
  "bod": "1985-12-25"
}
```

**Expected Output:**
- Status: `201 Created`
- `success`: `true`
- `employee.id`: Auto-generated number
- `employee.g_id`: Auto-generated (e.g., "G025DI08")

#### **Scenario 2: Minimal Required Data**
**Input:**
```json
{
  "name": "Bob Smith",
  "no_ktp": "3301234567890124"
}
```

**Expected Output:**
- Status: `201 Created`
- `personal_number`: `null`
- `bod`: `null`
- `g_id`: Auto-generated

#### **Scenario 3: Invalid KTP (Error Test)**
**Input:**
```json
{
  "name": "Invalid User",
  "no_ktp": "12345"
}
```

**Expected Output:**
- Status: `422 Unprocessable Entity`
- `success`: `false`
- `error`: "Validation error"
- `detail`: "KTP number must be exactly 16 digits"

#### **Scenario 4: Duplicate KTP (Error Test)**
**Input:** (Use same KTP as previous test)
```json
{
  "name": "Duplicate User",
  "no_ktp": "3201234567890123"
}
```

**Expected Output:**
- Status: `422 Unprocessable Entity`
- `success`: `false`
- Error about duplicate KTP

### **🔄 COMPLETE WORKFLOW TEST**

Test the full employee lifecycle:

1. **CREATE** employee (POST)
   ```
   POST /pegawai/
   Body: { "name": "Test User", "no_ktp": "1234567890123456" }
   ```

2. **VERIFY** creation (GET by ID)
   ```
   GET /pegawai/{{employee_id}}
   ```

3. **UPDATE** employee (PUT)
   ```
   PUT /pegawai/{{employee_id}}
   Body: { "name": "Updated Test User" }
   ```

4. **LIST** employees (GET all)
   ```
   GET /pegawai/?search=Test User
   ```

5. **DELETE** employee (DELETE)
   ```
   DELETE /pegawai/{{employee_id}}
   ```

### **🎯 EXPECTED SYSTEM BEHAVIOR**

When you POST a new employee:

1. **Input Validation**: System validates all fields
2. **Duplicate Check**: Ensures KTP number is unique
3. **Database Insert**: Creates employee record
4. **G_ID Generation**: Automatically generates unique Global ID
5. **Response**: Returns complete employee data with G_ID

**🔥 The G_ID is generated automatically - you don't need to provide it!**

### **💡 TIPS FOR TESTING**

1. **Use Unique KTP Numbers**: Generate different 16-digit numbers for each test
2. **Test Validation**: Try invalid data to ensure error handling works
3. **Save Variables**: Use Postman variables to store generated IDs
4. **Check G_ID Format**: Verify G_ID follows pattern (e.g., "G025DI##")
5. **Test Timestamps**: Verify created_at and updated_at are populated

### **🚀 PowerShell Test Command**

You can also test POST via PowerShell:
```powershell
$body = @{
    name = "PowerShell Test User"
    personal_number = "PS-TEST-001"
    no_ktp = "9999888877776666"
    bod = "1992-03-15"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://wecare.techconnect.co.id/gid/api/v1/pegawai/" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
```

This POST method is the **heart of your Global ID Management System** - it creates employees AND assigns them their unique Global IDs automatically! 🎉