#!/bin/bash

echo "🔍 Testing Monitoring API Endpoints..."

# Test monitoring status endpoint
echo "=== Testing Monitoring Status ==="
curl -s "http://localhost:8001/api/v1/monitoring/status" | head -5

echo -e "\n=== Testing Audit Logs ==="
# Test audit logs endpoint
curl -s "http://localhost:8001/api/v1/audit/logs?page=1&size=5" | head -5

echo -e "\n🔍 Testing through public domain..."

echo "=== Testing Monitoring Status (Public) ==="
curl -s "https://wecare.techconnect.co.id/gid/api/v1/monitoring/status" | head -5

echo -e "\n=== Testing Audit Logs (Public) ==="
curl -s "https://wecare.techconnect.co.id/gid/api/v1/audit/logs?page=1&size=5" | head -5

echo -e "\n✅ Monitoring API test complete!"