# 📮 Complete Postman Testing Guide for Global ID REST API

## 🚀 **Server Information**

### Local Development:
- **Base URL**: `http://localhost:8001/api/v1`
- **API Documentation**: `http://localhost:8001/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8001/redoc`

### Production Server (Nginx Reverse Proxy):
- **Base URL**: `https://wecare.techconnect.co.id/gid/api/v1`
- **API Documentation**: `https://wecare.techconnect.co.id/gid/docs` (Swagger UI)
- **Alternative Docs**: `https://wecare.techconnect.co.id/gid/redoc`

> ⚠️ **IMPORTANT**: Don't test the base URL alone! Always add the endpoint path like `/pegawai/` or `/health`

> 🔥 **Quick Test URLs**:
> - `https://wecare.techconnect.co.id/gid/docs` (API Documentation)
> - `https://wecare.techconnect.co.id/gid/api/v1/pegawai/` (Employee API)
> - `https://wecare.techconnect.co.id/gid/api/v1/health` (Health Check)

## 🎯 **API Categories Available**

1. **Employee Management APIs** (`/pegawai/*`) - CRUD operations for employees
2. **Global ID Data View APIs** (`/api/global_id*`) - Read-only access to Global ID tables
3. **System APIs** (`/health`, `/dashboard`, etc.) - System monitoring

## 📋 **Postman Collection Setup**

### 1. Create New Collection
1. Open Postman
2. Click "New" → "Collection"
3. Name it "Global ID Management API"
4. Add description: "Complete REST API testing for Global ID Management System"

### 2. Set Collection Variables
1. Click on your collection
2. Go to "Variables" tab
3. Add these variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `https://wecare.techconnect.co.id/gid/api/v1` | `https://wecare.techconnect.co.id/gid/api/v1` |
| `local_url` | `http://localhost:8001/api/v1` | `http://localhost:8001/api/v1` |
| `employee_id` | `` | `` |
| `g_id` | `` | `` |

### 3. Create Folders in Collection
Organize your requests into folders:
- 📁 **Employee Management** (`/pegawai/*`)
- 📁 **Global ID Data Views** (`/api/global_id*`)
- 📁 **System Endpoints** (`/health`, `/dashboard`)

## 🧪 **Test Requests**

### **Request 1: GET All Employees**

**Method**: `GET`
**URL**: `{{base_url}}/pegawai/`
**Description**: Get paginated list of all employees

> ⚠️ **Important**: Use `/pegawai/` endpoint, not just the base URL!

#### Query Parameters (Optional):
- `page`: `1` (Page number)
- `size`: `20` (Page size)
- `search`: `john` (Search term)
- `include_deleted`: `false` (Include deleted employees)

#### Headers:
```
Content-Type: application/json
```

#### Example URL with parameters:
```
{{base_url}}/pegawai/?page=1&size=10&search=test
```

#### Full Production URL Example:
```
https://wecare.techconnect.co.id/gid/api/v1/pegawai/?page=1&size=20
```

#### Expected Response (200 OK):
```json
{
  "total_count": 150,
  "page": 1,
  "size": 20,
  "total_pages": 8,
  "employees": [
    {
      "id": 1,
      "name": "John Doe",
      "personal_number": "EMP001",
      "no_ktp": "1234567890123456",
      "bod": "1990-01-01",
      "g_id": "G025AA01",
      "created_at": "2025-01-01T10:00:00",
      "updated_at": "2025-01-01T10:00:00",
      "deleted_at": null
    }
  ]
}
```

---

### **Request 2: POST Create Employee**

**Method**: `POST`
**URL**: `{{baseUrl}}/`
**Description**: Create a new employee

#### Headers:
```
Content-Type: application/json
```

#### Body (raw JSON):
```json
{
  "name": "Jane Smith",
  "personal_number": "EMP999",
  "no_ktp": "9876543210123456",
  "bod": "1995-05-15"
}
```

#### Test Scripts (Postman Tests tab):
```javascript
// Save employee ID for other requests
if (pm.response.code === 201) {
    const response = pm.response.json();
    if (response.success && response.employee) {
        pm.collectionVariables.set("employeeId", response.employee.id);
        console.log("Employee ID saved:", response.employee.id);
    }
}

// Test response structure
pm.test("Status code is 201", function () {
    pm.response.to.have.status(201);
});

pm.test("Response has success property", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('success');
    pm.expect(jsonData.success).to.be.true;
});

pm.test("Response has employee data", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('employee');
    pm.expect(jsonData.employee).to.have.property('id');
    pm.expect(jsonData.employee).to.have.property('name');
    pm.expect(jsonData.employee).to.have.property('no_ktp');
});
```

#### Expected Response (201 Created):
```json
{
  "success": true,
  "message": "Employee created successfully",
  "employee": {
    "id": 123,
    "name": "Jane Smith",
    "personal_number": "EMP999",
    "no_ktp": "9876543210123456",
    "bod": "1995-05-15",
    "g_id": null,
    "created_at": "2025-10-01T09:50:50",
    "updated_at": "2025-10-01T09:50:50",
    "deleted_at": null
  }
}
```

---

### **Request 3: GET Employee by ID**

**Method**: `GET`
**URL**: `{{baseUrl}}/{{employeeId}}`
**Description**: Get specific employee by ID

#### Headers:
```
Content-Type: application/json
```

#### Test Scripts:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Employee ID matches", function () {
    const jsonData = pm.response.json();
    const expectedId = parseInt(pm.collectionVariables.get("employeeId"));
    pm.expect(jsonData.id).to.equal(expectedId);
});
```

#### Expected Response (200 OK):
```json
{
  "id": 123,
  "name": "Jane Smith",
  "personal_number": "EMP999",
  "no_ktp": "9876543210123456",
  "bod": "1995-05-15",
  "g_id": null,
  "created_at": "2025-10-01T09:50:50",
  "updated_at": "2025-10-01T09:50:50",
  "deleted_at": null
}
```

---

### **Request 4: PUT Update Employee**

**Method**: `PUT`
**URL**: `{{baseUrl}}/{{employeeId}}`
**Description**: Update existing employee

#### Headers:
```
Content-Type: application/json
```

#### Body (raw JSON):
```json
{
  "name": "Jane Smith Updated",
  "personal_number": "EMP999A"
}
```

#### Test Scripts:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Employee updated successfully", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
    pm.expect(jsonData.employee.name).to.equal("Jane Smith Updated");
});
```

#### Expected Response (200 OK):
```json
{
  "success": true,
  "message": "Employee updated successfully",
  "employee": {
    "id": 123,
    "name": "Jane Smith Updated",
    "personal_number": "EMP999A",
    "no_ktp": "9876543210123456",
    "bod": "1995-05-15",
    "g_id": null,
    "created_at": "2025-10-01T09:50:50",
    "updated_at": "2025-10-01T10:15:30",
    "deleted_at": null
  }
}
```

---

### **Request 5: GET Employee Statistics**

**Method**: `GET`
**URL**: `{{baseUrl}}/stats/summary`
**Description**: Get employee statistics

#### Headers:
```
Content-Type: application/json
```

#### Expected Response (200 OK):
```json
{
  "success": true,
  "statistics": {
    "total_employees": 150,
    "employees_with_gid": 120,
    "employees_without_gid": 30,
    "gid_assignment_rate": 80.0
  }
}
```

---

### **Request 6: DELETE Employee**

**Method**: `DELETE`
**URL**: `{{baseUrl}}/{{employeeId}}`
**Description**: Soft delete employee

#### Headers:
```
Content-Type: application/json
```

#### Test Scripts:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Employee deleted successfully", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
    pm.expect(jsonData.message).to.include("deleted successfully");
});
```

#### Expected Response (200 OK):
```json
{
  "success": true,
  "message": "Employee 123 deleted successfully"
}
```

## 🧪 **Error Testing**

### **Test Invalid KTP Number**

**Method**: `POST`
**URL**: `{{baseUrl}}/`

#### Body (raw JSON):
```json
{
  "name": "Invalid Employee",
  "no_ktp": "12345"
}
```

#### Expected Response (422 Unprocessable Entity):
```json
{
  "success": false,
  "error": "Validation error",
  "detail": "KTP number must be exactly 16 digits"
}
```

### **Test Non-existent Employee**

**Method**: `GET`
**URL**: `{{baseUrl}}/999999`

#### Expected Response (404 Not Found):
```json
{
  "success": false,
  "error": "Employee not found",
  "detail": "Employee with ID 999999 not found"
}
```

## 🔄 **Running Tests in Sequence**

### Test Order:
1. **GET All Employees** - See existing data
2. **POST Create Employee** - Create test employee
3. **GET Employee by ID** - Verify creation
4. **PUT Update Employee** - Test update functionality  
5. **GET Employee Statistics** - Check statistics
6. **DELETE Employee** - Clean up test data

### Collection Runner:
1. Click on your collection
2. Click "Run" button
3. Select all requests
4. Click "Run Pegawai REST API"
5. View results and response times

## 📊 **Monitoring and Variables**

### Environment Variables:
Create different environments for testing:

#### Local Development:
- `baseUrl`: `http://localhost:8000/api/v1/pegawai`

#### Production:
- `baseUrl`: `https://wecare.techconnect.co.id/gid/api/v1/pegawai`

### Global Variables to Track:
- `{{employeeId}}` - Automatically set from POST response
- `{{testKtpNumber}}` - Generate unique KTP for testing
- `{{timestamp}}` - Use for unique data generation

## 🚀 **Quick Start Steps**

1. **Import Collection**: Copy the JSON below and import into Postman
2. **Set Environment**: Configure `baseUrl` variable
3. **Test Server**: Run GET all employees first
4. **Create Test Data**: Use POST to create a test employee
5. **Run Full Suite**: Execute all requests in sequence

## 📁 **Postman Collection JSON**

Save this as a file and import into Postman:

```json
{
  "info": {
    "name": "Pegawai REST API",
    "description": "Employee management API for Global ID System",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000/api/v1/pegawai"
    },
    {
      "key": "employeeId",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "Get All Employees",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{baseUrl}}/?page=1&size=20",
          "host": ["{{baseUrl}}"],
          "query": [
            {"key": "page", "value": "1"},
            {"key": "size", "value": "20"}
          ]
        }
      }
    },
    {
      "name": "Create Employee",
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
          "raw": "{\n  \"name\": \"Test Employee Postman\",\n  \"personal_number\": \"TEST001\",\n  \"no_ktp\": \"1111222233334444\",\n  \"bod\": \"1990-01-01\"\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/",
          "host": ["{{baseUrl}}"]
        }
      }
    }
  ]
}
```

---

## � **NEW: Global ID Data View APIs**

### **Request 7: GET All Global ID Records**

**Method**: `GET`
**URL**: `{{base_url}}/api/global_id`
**Description**: View all records from the global_id table

#### Query Parameters (Optional):
- `page`: `1` (Page number)
- `size`: `50` (Page size, max 1000)
- `status`: `Active` (Filter by status: Active, Non Active)
- `source`: `database_pegawai` (Filter by source)
- `search`: `G024` (Search by name, KTP, or G_ID)

#### Expected Response (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "g_id": "G024AA01",
      "name": "John Doe",
      "personal_number": "EMP001",
      "no_ktp": "1234567890123456",
      "bod": "1990-01-15",
      "status": "Active",
      "source": "database_pegawai",
      "created_at": "2025-10-01T10:30:00Z",
      "updated_at": "2025-10-01T10:30:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

### **Request 8: GET All Global ID Non-Database Records**

**Method**: `GET`
**URL**: `{{base_url}}/api/global_id_non_database`
**Description**: View all records from the global_id_non_database table (Excel imports)

#### Query Parameters (Optional):
- `page`: `1` (Page number)
- `size`: `50` (Page size, max 1000)
- `status`: `Active` (Filter by status)
- `source`: `excel` (Filter by source)
- `search`: `Jane` (Search term)

#### Expected Response (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "g_id": "G024AA02",
      "name": "Jane Smith",
      "personal_number": null,
      "no_ktp": "9876543210123456",
      "bod": "1985-05-20",
      "status": "Active",
      "source": "excel",
      "created_at": "2025-09-15T08:00:00Z",
      "updated_at": "2025-09-15T08:00:00Z"
    }
  ],
  "total_count": 25,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### **Request 9: GET Specific Global ID Record**

**Method**: `GET`
**URL**: `{{base_url}}/api/global_id/{{g_id}}`
**Description**: Get a specific Global ID record by G_ID

#### Path Variables:
- `g_id`: `G024AA01` (Set this in collection variables after creating an employee)

#### Expected Response (200 OK):
```json
{
  "g_id": "G024AA01",
  "name": "John Doe",
  "personal_number": "EMP001",
  "no_ktp": "1234567890123456",
  "bod": "1990-01-15",
  "status": "Active",
  "source": "database_pegawai",
  "created_at": "2025-10-01T10:30:00Z",
  "updated_at": "2025-10-01T10:30:00Z"
}
```

### **Request 10: GET Specific Global ID Non-Database Record**

**Method**: `GET`
**URL**: `{{base_url}}/api/global_id_non_database/{{g_id}}`
**Description**: Get a specific Global ID Non-Database record by G_ID

#### Expected Response (200 OK):
```json
{
  "g_id": "G024AA02",
  "name": "Jane Smith",
  "personal_number": null,
  "no_ktp": "9876543210123456",
  "bod": "1985-05-20",
  "status": "Active",
  "source": "excel",
  "created_at": "2025-09-15T08:00:00Z",
  "updated_at": "2025-09-15T08:00:00Z"
}
```

---

## 🧪 **Complete Testing Workflow**

### **Scenario 1: Employee Lifecycle with G_ID Verification**
1. **POST** Create new employee → Save `employee_id` and `g_id` from response
2. **GET** List all employees → Verify new employee appears
3. **GET** Employee by ID → Confirm details match
4. **GET** Global ID record → Verify G_ID was created in global_id table
5. **PUT** Update employee → Verify changes
6. **DELETE** Employee → Test soft deletion
7. **GET** Global ID record again → Verify status changes

### **Scenario 2: Data Validation Testing**
1. Try creating employee with duplicate KTP → Should return 422
2. Try creating employee with invalid data → Should return 422
3. Try accessing non-existent employee → Should return 404
4. Try accessing non-existent G_ID → Should return 404

### **Scenario 3: Pagination & Search Testing**
1. Create multiple employees (5-10)
2. Test pagination with different page sizes
3. Test search functionality across different endpoints
4. Test filtering by status and source

## 🎯 **Success Criteria**

Your API is working correctly if:
- ✅ **Employee Creation**: Returns 201 with G_ID generated automatically
- ✅ **G_ID Integration**: Created employees appear in Global ID table
- ✅ **CRUD Operations**: All employee operations work correctly
- ✅ **Data Views**: Global ID endpoints return paginated data
- ✅ **Error Handling**: Proper HTTP status codes and error messages
- ✅ **Validation**: Input validation works correctly
- ✅ **Search & Filter**: Pagination and filtering work across endpoints

## 🆘 **Troubleshooting**

### **ETIMEDOUT Error (Connection Timeout) - SOLVED! ✅**

**✅ GOOD NEWS**: Your API endpoints are working perfectly! The issue is with Postman configuration.

**Server Status Verified** ✅:
- `https://wecare.techconnect.co.id/gid/docs` → ✅ Working (200 OK)
- `https://wecare.techconnect.co.id/gid/api/v1/health` → ✅ Working (200 OK)  
- `https://wecare.techconnect.co.id/gid/api/v1/pegawai/` → ✅ Working (200 OK, 7504 employees found)

**🔧 POSTMAN FIX STEPS**:

1. **⚙️ Postman Settings (CRITICAL)**:
   - File → Settings → General → ❌ Turn OFF "SSL certificate verification"
   - File → Settings → General → Set "Request timeout" to **60000ms** (60 seconds)
   - File → Settings → Proxy → ❌ Turn OFF "Use the system proxy"

2. **🌐 Postman Global Proxy (if using corporate network)**:
   - File → Settings → Proxy → Add proxy bypass for: `*.techconnect.co.id`
   - Or completely disable proxy: "Proxy Configuration" → Off

3. **🔄 Alternative Testing Methods**:
   ```
   # Method 1: Test in Browser (Works immediately)
   https://wecare.techconnect.co.id/gid/docs
   
   # Method 2: PowerShell Test (Proven working)
   Invoke-WebRequest -Uri "https://wecare.techconnect.co.id/gid/api/v1/pegawai/" -Method GET
   
   # Method 3: Use different HTTP client
   # Try Thunder Client (VS Code extension) or Insomnia
   ```

4. **🔧 Postman Request Configuration**:
   - Method: `GET`
   - URL: `https://wecare.techconnect.co.id/gid/api/v1/pegawai/`
   - Headers: Remove all headers (let Postman auto-generate)
   - Body: None (for GET requests)
   - Auth: None
   - Pre-request Script: None

5. **🛠️ If Still Having Issues**:
   - Try **Postman Desktop App** instead of web version
   - Restart Postman completely
   - Clear Postman cache: Settings → Data → Clear
   - Try with VPN ON/OFF to test network routing
   - Check Windows Firewall settings

### **OpenAPI/Swagger Documentation Issues:**
If you see "end of the stream or document separator is expected" or "Unable to render this definition":

1. **Server Restart Required**: 
   ```bash
   sudo systemctl restart gid-system.service
   sudo systemctl status gid-system.service
   ```

2. **Check Service Logs**:
   ```bash
   sudo journalctl -u gid-system.service -f
   tail -f /var/www/G_ID_engine_production/gid_system.log
   ```

3. **Test OpenAPI Schema Generation**:
   ```bash
   cd /var/www/G_ID_engine_production
   python3 fix_openapi_docs.py
   ```

4. **Direct Server Access**: Test without nginx proxy:
   ```bash
   curl http://localhost:8001/docs
   curl http://localhost:8001/openapi.json
   ```

5. **Clear Browser Cache**: Hard refresh (Ctrl+F5) or incognito mode

### **Connection Issues:**
1. **Connection Refused**: Ensure FastAPI server is running on port 8001
2. **502 Bad Gateway**: Check if systemd service is running:
   ```bash
   sudo systemctl status gid-system.service
   sudo systemctl restart gid-system.service
   ```
3. **SSL/HTTPS Issues**: For production, ensure SSL certificates are valid

### **API Response Issues:**
1. **404 Not Found**: Verify URL paths are correct
2. **422 Validation Error**: Check JSON format and required fields
3. **500 Internal Server Error**: Check server logs:
   ```bash
   tail -f /var/www/G_ID_engine_production/gid_system.log
   ```

### **Authentication Issues:**
- Current system uses open endpoints (no authentication required)
- If you get 401/403 errors, check server configuration

### **Data Issues:**
1. **No G_ID Generated**: Check if GID generator service is working
2. **Database Connection**: Verify environment variables in .env
3. **Missing Data**: Ensure database tables exist and are populated

## 📊 **HTTP Status Code Reference**

- **200 OK**: Successful GET, PUT, DELETE operations
- **201 Created**: Successful POST operations (employee creation)
- **400 Bad Request**: Malformed request
- **404 Not Found**: Resource not found (employee, G_ID, etc.)
- **422 Unprocessable Entity**: Validation errors (duplicate data, invalid format)
- **500 Internal Server Error**: Server-side errors (database, application)

## 🔗 **Interactive Testing**

### **Swagger UI**: 
- Production: `https://wecare.techconnect.co.id/gid/docs`
- Local: `http://localhost:8001/docs`

The Swagger UI provides:
- ✅ Interactive API testing interface
- ✅ Complete request/response documentation
- ✅ Schema validation
- ✅ Example requests and responses
- ✅ Authentication testing (if implemented)

## 📱 **Alternative Testing Tools**

If you prefer other tools besides Postman:
- **curl** (command line)
- **HTTPie** (command line, user-friendly)
- **Insomnia** (GUI alternative to Postman)
- **Thunder Client** (VS Code extension)
- **REST Client** (VS Code extension)