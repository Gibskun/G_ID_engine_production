# Test the validation endpoint directly on the server

echo "🔧 Testing G_ID Validation Endpoint on Server"
echo "=============================================="

echo "1. Testing direct server endpoint (port 8001)..."
curl -X GET "http://localhost:8001/api/v1/validation-config/status" -H "Accept: application/json" -v

echo ""
echo "2. Testing if nginx is forwarding correctly..."
curl -X GET "http://localhost/api/v1/validation-config/status" -H "Accept: application/json" -v

echo ""
echo "3. Testing with /gid prefix..."
curl -X GET "http://localhost/gid/api/v1/validation-config/status" -H "Accept: application/json" -v

echo ""
echo "4. Checking what's listening on ports..."
netstat -tlnp | grep -E "(8001|80|443)"

echo ""
echo "5. Testing from external URL..."
curl -X GET "https://wecare.techconnect.co.id/api/v1/validation-config/status" -H "Accept: application/json" -v