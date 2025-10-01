# 🚀 REST API Integration Guide

## 📋 **API Status Summary**

Your system now has **comprehensive REST API functionality**! Here's what's available:

### ✅ **Employee Management APIs** (Already Existed + Enhanced)
- `POST /api/v1/pegawai/` - Create new employee **with automatic G_ID generation**
- `GET /api/v1/pegawai/` - Get all employees (paginated, searchable)
- `GET /api/v1/pegawai/{id}` - Get employee by ID
- `PUT /api/v1/pegawai/{id}` - Update employee
- `DELETE /api/v1/pegawai/{id}` - Soft delete employee
- `GET /api/v1/pegawai/stats/summary` - Employee statistics

### ✅ **Global ID Data Views** (Newly Added)
- `GET /api/v1/api/global_id` - View all Global_ID table data
- `GET /api/v1/api/global_id_non_database` - View all Global_ID_Non_Database table data
- `GET /api/v1/api/global_id/{g_id}` - Get specific Global_ID record
- `GET /api/v1/api/global_id_non_database/{g_id}` - Get specific Global_ID_Non_Database record

## 🔧 **Files Modified/Created**

### **New Files:**
1. `app/api/globalid_endpoints.py` - New REST API endpoints for Global ID data views
2. `API_INTEGRATION_GUIDE.md` - This documentation file

### **Modified Files:**  
1. `app/api/routes.py` - Added Global ID router integration
2. `app/services/pegawai_service.py` - Enhanced to auto-generate G_ID on employee creation

## 🌐 **API URLs (Production)**

Based on your server configuration with Nginx reverse proxy:

**Base URL:** `https://wecare.techconnect.co.id/gid/api/v1/`

### **Employee Management:**
- `POST https://wecare.techconnect.co.id/gid/api/v1/pegawai/`
- `GET https://wecare.techconnect.co.id/gid/api/v1/pegawai/`
- `GET https://wecare.techconnect.co.id/gid/api/v1/pegawai/{id}`
- `PUT https://wecare.techconnect.co.id/gid/api/v1/pegawai/{id}`
- `DELETE https://wecare.techconnect.co.id/gid/api/v1/pegawai/{id}`

### **Global ID Data Views:**
- `GET https://wecare.techconnect.co.id/gid/api/v1/api/global_id`
- `GET https://wecare.techconnect.co.id/gid/api/v1/api/global_id_non_database`
- `GET https://wecare.techconnect.co.id/gid/api/v1/api/global_id/{g_id}`

## � **Postman Testing**

**📋 For complete Postman testing guide, see: [`POSTMAN_TESTING_GUIDE.md`](./POSTMAN_TESTING_GUIDE.md)**

The Postman guide includes:
- ✅ Complete collection setup with variables
- ✅ All 10+ API endpoints with examples
- ✅ Testing scenarios and workflows
- ✅ Error handling and troubleshooting
- ✅ Success criteria and validation steps

## �📝 **Quick API Testing Examples**

### **1. Create New Employee with G_ID Generation**

```bash
curl -X POST "https://wecare.techconnect.co.id/gid/api/v1/pegawai/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "personal_number": "EMP001",
    "no_ktp": "1234567890123456",
    "bod": "1990-01-15"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Employee created successfully",
  "employee": {
    "id": 123,
    "name": "John Doe",
    "personal_number": "EMP001",
    "no_ktp": "1234567890123456",
    "bod": "1990-01-15",
    "g_id": "G024AA01",
    "created_at": "2025-10-01T10:30:00Z",
    "updated_at": "2025-10-01T10:30:00Z",
    "deleted_at": null
  }
}
```

### **2. Get All Employees**

```bash
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/?page=1&size=20&search=John"
```

### **3. Delete Employee**

```bash
curl -X DELETE "https://wecare.techconnect.co.id/gid/api/v1/pegawai/123"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Employee 123 deleted successfully"
}
```

### **4. View Global ID Data**

```bash
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/api/global_id?page=1&size=50&status=Active"
```

### **5. View Global ID Non-Database Data**

```bash
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/api/global_id_non_database?page=1&size=50"
```

## 🚀 **Deployment Steps**

### **1. Push to GitHub**
```bash
git add .
git commit -m "Add Global ID REST API endpoints and enhance employee creation with G_ID generation"
git push origin main
```

### **2. Deploy on Server**
```bash
# SSH to your server
ssh your-server

# Navigate to application directory
cd /var/www/G_ID_engine_production

# Pull latest changes  
git pull origin main

# Restart the service
sudo systemctl restart gid-system.service

# Check service status
sudo systemctl status gid-system.service
```

### **3. Verify Deployment**
```bash
# Test health endpoint
curl https://wecare.techconnect.co.id/gid/api/v1/health

# Check API documentation
# Visit: https://wecare.techconnect.co.id/gid/docs
```

## 🧪 **Testing Checklist**

After deployment, test these scenarios:

- [ ] **Create Employee** - Verify G_ID is generated and returned
- [ ] **List Employees** - Check pagination and search functionality
- [ ] **View Global ID Data** - Confirm newly created employee appears
- [ ] **Update Employee** - Test employee modification
- [ ] **Delete Employee** - Verify soft delete functionality
- [ ] **View Global ID Non-Database** - Check Excel-imported data
- [ ] **API Documentation** - Verify Swagger UI works at `/docs`

## 🔍 **Troubleshooting**

### **Service Issues:**
```bash
# Check service logs
sudo journalctl -u gid-system.service -f

# Check application logs
tail -f /var/www/G_ID_engine_production/gid_system.log
```

### **Database Connection:**
```bash
# Test database connectivity
cd /var/www/G_ID_engine_production
python3 -c "from app.models.database import get_db; next(get_db())"
```

### **API Response Issues:**
- Check Content-Type headers
- Verify JSON format in requests
- Check server logs for detailed error messages
- Ensure all required fields are provided

## 📚 **API Documentation**

Full interactive API documentation is available at:
**https://wecare.techconnect.co.id/gid/docs**

This includes:
- Complete endpoint documentation
- Request/response schemas
- Interactive testing interface
- Authentication requirements (if any)

## 🎯 **Key Features**

1. **Automatic G_ID Generation** - New employees get G_IDs immediately
2. **Comprehensive CRUD** - Full employee lifecycle management
3. **Data Views** - Read-only access to Global ID tables
4. **Production Ready** - Proper error handling and logging
5. **Scalable** - Pagination and filtering support
6. **Documented** - Full Swagger/OpenAPI documentation