#!/bin/bash
# Quick test of server endpoints after service restart

echo "🔧 Testing Server Endpoints After Restart"
echo "=========================================="

echo "Server is running on port 8001 as shown in logs"
echo "Testing direct connection to validation endpoint..."
echo ""

echo "1. Testing validation status endpoint:"
curl -s -w "HTTP Code: %{http_code}\n" "http://localhost:8001/api/v1/validation-config/status"

echo ""
echo "2. Testing if the endpoint responds with JSON:"
curl -s "http://localhost:8001/api/v1/validation-config/status" | head -c 100

echo ""
echo ""
echo "3. Testing through nginx (if configured):"
curl -s -w "HTTP Code: %{http_code}\n" "http://localhost/api/v1/validation-config/status"

echo ""
echo "4. Testing with /gid prefix:"  
curl -s -w "HTTP Code: %{http_code}\n" "http://localhost/gid/api/v1/validation-config/status"

echo ""
echo "5. Checking what processes are listening:"
ss -tlnp | grep -E ":80|:8001|:443"

echo ""
echo "6. Testing external URL:"
curl -s -w "HTTP Code: %{http_code}\n" "https://wecare.techconnect.co.id/api/v1/validation-config/status"

echo ""
echo "If step 1 shows HTTP Code: 200, the FastAPI server is working."
echo "If step 6 shows HTTP Code: 404, it's an nginx configuration issue."