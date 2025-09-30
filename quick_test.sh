#!/bin/bash

echo "🚀 Quick Performance Test..."

# Test just the database query without the full API
echo "=== Direct Database Query Test ==="
python3 -c "
import sys, time
sys.path.append('/var/www/G_ID_engine_production')
from app.models.database import get_db
from sqlalchemy import text

print('Testing optimized dashboard query...')
db = next(get_db())
try:
    start_time = time.time()
    
    result = db.execute(text('''
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_records,
            SUM(CASE WHEN status = 'Non Active' THEN 1 ELSE 0 END) as inactive_records,
            SUM(CASE WHEN source = 'database_pegawai' THEN 1 ELSE 0 END) as database_source,
            SUM(CASE WHEN source = 'excel' THEN 1 ELSE 0 END) as excel_source
        FROM dbo.global_id
    ''')).fetchone()
    
    query_time = time.time() - start_time
    print(f'✅ Query completed in {query_time:.2f} seconds')
    print(f'📊 Total records: {result.total_records}')
    print(f'📊 Active: {result.active_records}, Inactive: {result.inactive_records}')
    print(f'📊 Database source: {result.database_source}, Excel source: {result.excel_source}')
    
    if query_time > 10:
        print('⚠️  Query is still slow - need to investigate further')
    elif query_time > 5:
        print('⚠️  Query is moderately slow - could be improved')
    else:
        print('✅ Query performance is good')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
"

# Test a simple count query
echo -e "\n=== Simple Count Query Test ==="
python3 -c "
import sys, time
sys.path.append('/var/www/G_ID_engine_production')
from app.models.database import get_db
from app.models.models import GlobalID

print('Testing simple count query...')
db = next(get_db())
try:
    start_time = time.time()
    count = db.query(GlobalID).count()
    query_time = time.time() - start_time
    print(f'✅ Simple count completed in {query_time:.2f} seconds')
    print(f'📊 Total records: {count}')
except Exception as e:
    print(f'❌ Error: {e}')
finally:
    db.close()
"

# Test the actual API endpoint
echo -e "\n=== API Endpoint Test ==="
echo "Testing /api/v1/dashboard endpoint..."
start_time=$(date +%s)
response=$(curl -m 30 -s -w "%{http_code}" "http://localhost:8001/api/v1/dashboard" -o /tmp/api_test.json)
end_time=$(date +%s)
duration=$((end_time - start_time))

echo "HTTP Status: $response"
echo "Response time: ${duration} seconds"

if [ "$response" = "200" ]; then
    echo "✅ API responded successfully"
    echo "Response preview:"
    head -3 /tmp/api_test.json | jq . 2>/dev/null || head -3 /tmp/api_test.json
else
    echo "❌ API request failed"
    echo "Error response:"
    cat /tmp/api_test.json
fi

echo -e "\n🔍 Performance test complete!"