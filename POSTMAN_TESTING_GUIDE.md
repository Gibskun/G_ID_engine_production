# Postman Testing Guide for Pegawai REST API

## 🚀 **Server Information**

### Local Development:
- **Base URL**: `http://localhost:8000/api/v1/pegawai/` ⚠️ **Note the trailing slash!**
- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc`

### Production Server (Port 8001):
- **Base URL**: `https://wecare.techconnect.co.id:8001/api/v1/pegawai`
- **API Documentation**: `https://wecare.techconnect.co.id:8001/docs` (Swagger UI)
- **Alternative Docs**: `https://wecare.techconnect.co.id:8001/redoc`

## 📋 **Postman Collection Setup**

### 1. Create New Collection
1. Open Postman
2. Click "New" → "Collection"
3. Name it "Pegawai REST API"
4. Add description: "Employee management API for Global ID System"

### 2. Set Collection Variables
1. Click on your collection
2. Go to "Variables" tab
3. Add these variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `baseUrl` | `https://wecare.techconnect.co.id:8001/api/v1/pegawai` | `https://wecare.techconnect.co.id:8001/api/v1/pegawai` |
| `employeeId` | `` | `` |

**Note**: For local testing, use `http://localhost:8000/api/v1/pegawai/` ⚠️ **Don't forget the trailing slash!**

## 🧪 **Test Requests**

### **Request 1: GET All Employees**

**Method**: `GET`
**URL**: `{{baseUrl}}/`
**Description**: Get paginated list of all employees

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
{{baseUrl}}/?page=1&size=10&search=test
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

## 🎯 **Success Criteria**

Your API is working correctly if:
- ✅ GET requests return 200 status codes
- ✅ POST requests return 201 status codes  
- ✅ PUT requests return 200 status codes
- ✅ DELETE requests return 200 status codes
- ✅ Error cases return appropriate 4xx status codes
- ✅ Response structure matches expected format
- ✅ Employee ID is properly set and retrieved
- ✅ Validation errors are clearly communicated

## 🆘 **Troubleshooting**

### Common Issues:

1. **Connection Refused (ECONNREFUSED)**: Make sure FastAPI server is running
2. **307 Temporary Redirect**: Add trailing slash `/` to your URL 
   - Wrong: `http://localhost:8000/api/v1/pegawai`
   - Correct: `http://localhost:8000/api/v1/pegawai/`
3. **404 Not Found**: Check the URL path is correct
4. **422 Validation Error**: Verify request body format
5. **500 Internal Server Error**: Check server logs for database issues

### Server Status Check:
Visit: `http://localhost:8000/docs` to see the interactive API documentation.