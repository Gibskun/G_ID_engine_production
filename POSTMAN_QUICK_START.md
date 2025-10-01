# 🚀 Quick Postman Setup Guide - Based on Your Screenshot

## ✅ **What You've Already Done (Great Job!)**
From your screenshot, I can see you've successfully:
- ✅ Created "Pegawai REST" collection
- ✅ Set up the `baseUrl` variable correctly
- ✅ Opened the Variables tab

## 📋 **Next Steps to Complete Your Setup**

### **Step 1: Import the Complete Collection**
Since you already have a collection started, you can either:

**Option A: Add to your existing collection**
1. In your current "Pegawai REST" collection, click the "..." menu
2. Select "Add request"
3. Follow the manual steps below

**Option B: Import the complete collection**
1. Click "Import" in Postman
2. Select "File" tab
3. Upload the file: `Pegawai_REST_API_Collection.json` (I just created this for you)
4. Click "Import"

### **Step 2: First Test - GET All Employees**

Since you have the `baseUrl` variable set up perfectly, let's create your first request:

1. **Click "Add request" in your collection**
2. **Set the details:**
   - **Name**: `GET All Employees`
   - **Method**: `GET`
   - **URL**: `{{baseUrl}}/`

3. **Click "Send"**

### **Step 3: Expected Result**
You should see a response like this:
```json
{
  "total_count": [number],
  "page": 1,
  "size": 20,
  "total_pages": [number],
  "employees": [
    {
      "id": 1,
      "name": "Employee Name",
      "personal_number": "EMP001",
      "no_ktp": "1234567890123456",
      "bod": "1990-01-01",
      "g_id": "G025AA01",
      "created_at": "2025-10-01T...",
      "updated_at": "2025-10-01T...",
      "deleted_at": null
    }
  ]
}
```

## 🧪 **Quick Test Sequence**

### **Test 1: GET All Employees**
- **URL**: `{{baseUrl}}/`
- **Method**: GET
- **Expected**: 200 OK status

### **Test 2: Create Test Employee**
- **URL**: `{{baseUrl}}/`
- **Method**: POST
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "name": "Test Employee from Postman",
  "personal_number": "TEST123",
  "no_ktp": "1111222233334444",
  "bod": "1990-01-01"
}
```
- **Expected**: 201 Created status

### **Test 3: Get Statistics**
- **URL**: `{{baseUrl}}/stats/summary`
- **Method**: GET
- **Expected**: 200 OK with statistics

## 📊 **Your Current Setup Analysis**

Based on your screenshot:
- ✅ **Collection Name**: "Pegawai REST" ✓
- ✅ **Base URL**: `http://localhost:8000/api/v1/pegawai` ✓
- ✅ **Variables Tab**: Open and configured ✓

You're ready to start testing!

## 🎯 **Immediate Action Steps**

1. **First, make sure your server is running:**
   ```bash
   # Check if server is running by visiting:
   http://localhost:8000/docs
   ```

2. **Create your first request:**
   - Click "Add request" in your collection
   - Name it: "GET All Employees"
   - Set URL to: `{{baseUrl}}/`
   - Click Send

3. **If you get an error:**
   - Check if the FastAPI server is running
   - Verify the URL is correct
   - Look at the server terminal for error messages

## 🔧 **Server Status Check**

Before testing, make sure your server is running. You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

## 📝 **Quick Reference for Your Variables**

Your current setup:
- `{{baseUrl}}` = `http://localhost:8000/api/v1/pegawai`

You can add more variables like:
- `{{employeeId}}` = (will be set automatically from POST responses)
- `{{testKtpNumber}}` = `1111222233334444`

## 🚀 **Ready to Test!**

You're all set! Your Postman collection is properly configured. Just:
1. Add your first request
2. Test the GET endpoint
3. Move on to POST, PUT, DELETE operations

Great job setting up the variables correctly! 🎉