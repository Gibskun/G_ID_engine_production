"""
Production Deployment Validation Script for Port 8001
Validates that all Pegawai REST API endpoints are working correctly on the production server
"""

import requests
import json
import time
from datetime import datetime
import sys

# Production server configuration
PRODUCTION_BASE_URL = "https://wecare.techconnect.co.id:8001/api/v1/pegawai"
PRODUCTION_SERVER_URL = "https://wecare.techconnect.co.id:8001"
LOCAL_BASE_URL = "http://localhost:8001/api/v1/pegawai"

class ProductionValidator:
    """Validates production deployment of Pegawai REST API"""
    
    def __init__(self, base_url: str, server_name: str = "Production"):
        self.base_url = base_url
        self.server_name = server_name
        self.test_results = []
        self.test_employee_id = None
    
    def log_result(self, test_name: str, success: bool, message: str, details: dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} [{self.server_name}] {test_name}: {message}")
        
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def test_server_health(self):
        """Test if server is responding"""
        try:
            server_url = self.base_url.replace("/api/v1/pegawai", "")
            response = requests.get(f"{server_url}/docs", timeout=10)
            
            if response.status_code == 200:
                self.log_result(
                    "Server Health Check",
                    True,
                    f"Server responding on {server_url}"
                )
            else:
                self.log_result(
                    "Server Health Check",
                    False,
                    f"Server returned status {response.status_code}",
                    {"status_code": response.status_code}
                )
        except requests.exceptions.RequestException as e:
            self.log_result(
                "Server Health Check",
                False,
                f"Server connection failed: {str(e)}"
            )
    
    def test_api_documentation(self):
        """Test API documentation accessibility"""
        try:
            server_url = self.base_url.replace("/api/v1/pegawai", "")
            docs_url = f"{server_url}/docs"
            response = requests.get(docs_url, timeout=10)
            
            if response.status_code == 200 and "swagger" in response.text.lower():
                self.log_result(
                    "API Documentation",
                    True,
                    f"Swagger UI accessible at {docs_url}"
                )
            else:
                self.log_result(
                    "API Documentation",
                    False,
                    f"API docs not accessible or invalid",
                    {"status_code": response.status_code}
                )
        except requests.exceptions.RequestException as e:
            self.log_result(
                "API Documentation",
                False,
                f"Documentation access failed: {str(e)}"
            )
    
    def test_get_all_employees(self):
        """Test GET /pegawai/ endpoint"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_count", "page", "size", "total_pages", "employees"]
                
                if all(field in data for field in required_fields):
                    self.log_result(
                        "GET All Employees",
                        True,
                        f"Retrieved {data['total_count']} employees successfully"
                    )
                else:
                    self.log_result(
                        "GET All Employees",
                        False,
                        "Response missing required fields",
                        {"missing_fields": [f for f in required_fields if f not in data]}
                    )
            else:
                self.log_result(
                    "GET All Employees",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except requests.exceptions.RequestException as e:
            self.log_result("GET All Employees", False, f"Request failed: {str(e)}")
    
    def test_create_employee(self):
        """Test POST /pegawai/ endpoint"""
        try:
            # Generate unique data for production testing
            timestamp = str(int(time.time()))[-10:]
            test_ktp = f"999888{timestamp}"
            
            employee_data = {
                "name": f"Production Test Employee {timestamp}",
                "personal_number": f"PROD{timestamp[:6]}",
                "no_ktp": test_ktp,
                "bod": "1985-06-15"
            }
            
            response = requests.post(
                f"{self.base_url}/",
                headers={"Content-Type": "application/json"},
                json=employee_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                if data.get("success") and "employee" in data:
                    self.test_employee_id = data["employee"]["id"]
                    self.log_result(
                        "CREATE Employee",
                        True,
                        f"Employee created successfully - ID: {self.test_employee_id}"
                    )
                else:
                    self.log_result(
                        "CREATE Employee",
                        False,
                        "Response format incorrect",
                        {"response": data}
                    )
            else:
                self.log_result(
                    "CREATE Employee",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except requests.exceptions.RequestException as e:
            self.log_result("CREATE Employee", False, f"Request failed: {str(e)}")
    
    def test_get_employee_by_id(self):
        """Test GET /pegawai/{id} endpoint"""
        if not self.test_employee_id:
            self.log_result("GET Employee by ID", False, "No test employee ID available")
            return
        
        try:
            response = requests.get(f"{self.base_url}/{self.test_employee_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == self.test_employee_id:
                    self.log_result(
                        "GET Employee by ID",
                        True,
                        f"Retrieved employee {self.test_employee_id} successfully"
                    )
                else:
                    self.log_result(
                        "GET Employee by ID",
                        False,
                        "Employee ID mismatch in response"
                    )
            else:
                self.log_result(
                    "GET Employee by ID",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except requests.exceptions.RequestException as e:
            self.log_result("GET Employee by ID", False, f"Request failed: {str(e)}")
    
    def test_update_employee(self):
        """Test PUT /pegawai/{id} endpoint"""
        if not self.test_employee_id:
            self.log_result("UPDATE Employee", False, "No test employee ID available")
            return
        
        try:
            update_data = {
                "name": f"Production Test Employee Updated"
            }
            
            response = requests.put(
                f"{self.base_url}/{self.test_employee_id}",
                headers={"Content-Type": "application/json"},
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "Updated" in data.get("employee", {}).get("name", ""):
                    self.log_result(
                        "UPDATE Employee",
                        True,
                        f"Employee {self.test_employee_id} updated successfully"
                    )
                else:
                    self.log_result(
                        "UPDATE Employee",
                        False,
                        "Update response format incorrect"
                    )
            else:
                self.log_result(
                    "UPDATE Employee",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except requests.exceptions.RequestException as e:
            self.log_result("UPDATE Employee", False, f"Request failed: {str(e)}")
    
    def test_get_statistics(self):
        """Test GET /pegawai/stats/summary endpoint"""
        try:
            response = requests.get(f"{self.base_url}/stats/summary", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "statistics" in data:
                    stats = data["statistics"]
                    self.log_result(
                        "GET Statistics",
                        True,
                        f"Statistics retrieved - Total employees: {stats.get('total_employees', 'N/A')}"
                    )
                else:
                    self.log_result(
                        "GET Statistics",
                        False,
                        "Statistics response format incorrect"
                    )
            else:
                self.log_result(
                    "GET Statistics",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except requests.exceptions.RequestException as e:
            self.log_result("GET Statistics", False, f"Request failed: {str(e)}")
    
    def test_delete_employee(self):
        """Test DELETE /pegawai/{id} endpoint"""
        if not self.test_employee_id:
            self.log_result("DELETE Employee", False, "No test employee ID available")
            return
        
        try:
            response = requests.delete(f"{self.base_url}/{self.test_employee_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result(
                        "DELETE Employee",
                        True,
                        f"Employee {self.test_employee_id} deleted successfully"
                    )
                else:
                    self.log_result(
                        "DELETE Employee",
                        False,
                        "Delete response format incorrect"
                    )
            else:
                self.log_result(
                    "DELETE Employee",
                    False,
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
        except requests.exceptions.RequestException as e:
            self.log_result("DELETE Employee", False, f"Request failed: {str(e)}")
    
    def run_validation(self):
        """Run all validation tests"""
        print(f"\n🚀 Starting {self.server_name} Server Validation")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Run tests in sequence
        self.test_server_health()
        self.test_api_documentation()
        self.test_get_all_employees()
        self.test_create_employee()
        self.test_get_employee_by_id()
        self.test_update_employee()
        self.test_get_statistics()
        self.test_delete_employee()  # Cleanup
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 {self.server_name} Validation Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed / total * 100):.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        else:
            print(f"\n🎉 All tests passed on {self.server_name} server!")
        
        return passed == total


def main():
    """Main validation function"""
    print("🔍 Production Deployment Validation for Pegawai REST API")
    print("Port: 8001")
    print("Server: wecare.techconnect.co.id")
    
    # Test production server
    production_validator = ProductionValidator(PRODUCTION_BASE_URL, "Production")
    production_success = production_validator.run_validation()
    
    # Optionally test local server on port 8001
    test_local = input("\n🤔 Also test local server on port 8001? (y/N): ").lower().strip() == 'y'
    local_success = True
    
    if test_local:
        local_validator = ProductionValidator(LOCAL_BASE_URL, "Local")
        local_success = local_validator.run_validation()
    
    # Final summary
    print("\n" + "🎯" * 20)
    print("FINAL DEPLOYMENT STATUS")
    print("🎯" * 20)
    
    if production_success:
        print("✅ Production server (Port 8001): READY FOR DEPLOYMENT")
    else:
        print("❌ Production server (Port 8001): ISSUES DETECTED")
    
    if test_local:
        if local_success:
            print("✅ Local server (Port 8001): WORKING CORRECTLY")
        else:
            print("❌ Local server (Port 8001): ISSUES DETECTED")
    
    # Recommendations
    print("\n📋 Deployment Recommendations:")
    if production_success:
        print("  ✅ All Pegawai REST API endpoints are working correctly")
        print("  ✅ Server is ready to handle production traffic")
        print("  ✅ API documentation is accessible")
        print("  🔗 Production API: https://wecare.techconnect.co.id:8001/api/v1/pegawai")
        print("  📚 Documentation: https://wecare.techconnect.co.id:8001/docs")
    else:
        print("  ⚠️  Fix identified issues before deploying to production")
        print("  🔍 Check server logs for detailed error information")
        print("  🔧 Verify database connectivity and configuration")
    
    return production_success and local_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)