# Pegawai REST API Documentation

## Overview

The Pegawai REST API provides comprehensive employee management functionality for the Global ID Management System. This API allows external systems to perform CRUD operations on employee data with proper validation, error handling, and response formatting.

## Base URL

```
https://wecare.techconnect.co.id/gid/api/v1/pegawai
```

## Authentication

Currently, no authentication is required for these endpoints. In a production environment, consider implementing:
- API key authentication
- JWT token-based authentication
- Rate limiting

## Endpoints

### 1. Get All Employees

**GET** `/api/v1/pegawai/`

Retrieve a paginated list of all employees with optional search functionality.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-based) |
| `size` | integer | 20 | Page size (max 100) |
| `search` | string | null | Search term for name, personal number, or KTP |
| `include_deleted` | boolean | false | Include soft-deleted employees |

#### Example Request

```bash
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/?page=1&size=20&search=john"
```

#### Example Response

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

### 2. Get Employee by ID

**GET** `/api/v1/pegawai/{employee_id}`

Retrieve a specific employee by their unique ID.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `employee_id` | integer | Unique employee identifier |

#### Example Request

```bash
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/1"
```

#### Example Response

```json
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
```

### 3. Create New Employee

**POST** `/api/v1/pegawai/`

Create a new employee record with validation.

#### Request Body

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `name` | string | Yes | 1-255 chars | Employee full name |
| `personal_number` | string | No | Max 15 chars | Employee personal/staff number |
| `no_ktp` | string | Yes | Exactly 16 digits | KTP number (must be unique) |
| `bod` | date | No | YYYY-MM-DD | Birth date |

#### Example Request

```bash
curl -X POST "https://wecare.techconnect.co.id/gid/api/v1/pegawai/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "personal_number": "EMP001",
    "no_ktp": "1234567890123456",
    "bod": "1990-01-01"
  }'
```

#### Example Response

```json
{
  "success": true,
  "message": "Employee created successfully",
  "employee": {
    "id": 1,
    "name": "John Doe",
    "personal_number": "EMP001",
    "no_ktp": "1234567890123456",
    "bod": "1990-01-01",
    "g_id": null,
    "created_at": "2025-01-01T10:00:00",
    "updated_at": "2025-01-01T10:00:00",
    "deleted_at": null
  }
}
```

### 4. Update Employee

**PUT** `/api/v1/pegawai/{employee_id}`

Update an existing employee's information.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `employee_id` | integer | Unique employee identifier |

#### Request Body

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `name` | string | No | 1-255 chars | Employee full name |
| `personal_number` | string | No | Max 15 chars | Employee personal/staff number |
| `no_ktp` | string | No | Exactly 16 digits | KTP number (must be unique) |
| `bod` | date | No | YYYY-MM-DD | Birth date |

#### Example Request

```bash
curl -X PUT "https://wecare.techconnect.co.id/gid/api/v1/pegawai/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe Updated",
    "personal_number": "EMP001"
  }'
```

#### Example Response

```json
{
  "success": true,
  "message": "Employee updated successfully",
  "employee": {
    "id": 1,
    "name": "John Doe Updated",
    "personal_number": "EMP001",
    "no_ktp": "1234567890123456",
    "bod": "1990-01-01",
    "g_id": "G025AA01",
    "created_at": "2025-01-01T10:00:00",
    "updated_at": "2025-01-01T12:00:00",
    "deleted_at": null
  }
}
```

### 5. Delete Employee

**DELETE** `/api/v1/pegawai/{employee_id}`

Soft delete an employee (marks as deleted without removing from database).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `employee_id` | integer | Unique employee identifier |

#### Example Request

```bash
curl -X DELETE "https://wecare.techconnect.co.id/gid/api/v1/pegawai/1"
```

#### Example Response

```json
{
  "success": true,
  "message": "Employee 1 deleted successfully"
}
```

### 6. Get Employee Statistics

**GET** `/api/v1/pegawai/stats/summary`

Get basic statistics about employees in the system.

#### Example Request

```bash
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/stats/summary"
```

#### Example Response

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

## Error Responses

All endpoints return structured error responses with appropriate HTTP status codes:

### Validation Error (422)

```json
{
  "success": false,
  "error": "Validation error",
  "detail": "KTP number must be exactly 16 digits"
}
```

### Not Found (404)

```json
{
  "success": false,
  "error": "Employee not found",
  "detail": "Employee with ID 999 not found"
}
```

### Internal Server Error (500)

```json
{
  "success": false,
  "error": "Internal server error",
  "detail": "Failed to create employee"
}
```

## Data Validation Rules

### Employee Name
- **Required** for creation
- Must be 1-255 characters
- Leading/trailing whitespace is trimmed
- Cannot be empty after trimming

### Personal Number
- **Optional**
- Maximum 15 characters
- Must be unique among active employees
- Empty strings are converted to null

### KTP Number
- **Required** for creation
- Must be exactly 16 digits
- Must be unique among active employees
- Only numeric characters allowed

### Birth Date
- **Optional**
- Must be in YYYY-MM-DD format
- Must be a valid date

## Technical Implementation

### Technology Stack
- **FastAPI**: Web framework with automatic API documentation
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **SQL Server**: Database with optimized connection pooling

### Performance Features
- Connection pooling for optimal database performance
- Pagination for large datasets
- Optimized queries with proper indexing
- Soft deletion for data integrity

### Error Handling
- Comprehensive input validation
- Proper HTTP status codes
- Structured error responses
- Detailed logging for debugging

## API Documentation

FastAPI automatically generates interactive API documentation available at:

- **Swagger UI**: `https://wecare.techconnect.co.id/gid/docs`
- **ReDoc**: `https://wecare.techconnect.co.id/gid/redoc`

## Testing

### Manual Testing

You can test the API using:
- **curl** commands (examples above)
- **Postman** collection
- **Swagger UI** interactive interface

### Example curl Commands

```bash
# Get all employees
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/"

# Search employees
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/?search=john&page=1&size=10"

# Get specific employee
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/1"

# Create new employee
curl -X POST "https://wecare.techconnect.co.id/gid/api/v1/pegawai/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "no_ktp": "9876543210123456"}'

# Update employee
curl -X PUT "https://wecare.techconnect.co.id/gid/api/v1/pegawai/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith Updated"}'

# Delete employee
curl -X DELETE "https://wecare.techconnect.co.id/gid/api/v1/pegawai/1"

# Get statistics
curl -X GET "https://wecare.techconnect.co.id/gid/api/v1/pegawai/stats/summary"
```

## Production Considerations

### Security
- Implement authentication (API keys, JWT tokens)
- Add rate limiting to prevent abuse
- Validate and sanitize all inputs
- Use HTTPS for all communications

### Monitoring
- Log all API requests and responses
- Monitor response times and error rates
- Set up alerts for high error rates
- Track API usage patterns

### Scalability
- Database connection pooling is already optimized
- Consider caching for frequently accessed data
- Implement database read replicas if needed
- Monitor database performance metrics

### Backup and Recovery
- Regular database backups
- Test backup restoration procedures
- Implement database transaction logging
- Plan for disaster recovery scenarios

## Support

For technical support or questions about the Pegawai REST API:

1. Check the interactive API documentation at `/docs`
2. Review application logs for detailed error information
3. Contact the development team for assistance

## Version History

- **v1.0**: Initial release with CRUD operations
  - GET /pegawai (list with pagination and search)
  - GET /pegawai/{id} (get by ID)
  - POST /pegawai (create)
  - PUT /pegawai/{id} (update)
  - DELETE /pegawai/{id} (soft delete)
  - GET /pegawai/stats/summary (statistics)