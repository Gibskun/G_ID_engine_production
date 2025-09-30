#!/bin/bash

echo "🔍 Diagnosing Dashboard Performance Issues..."

# Check if the service is running with the latest code
echo "=== Service Status ==="
sudo systemctl status gid-system --no-pager -l

echo -e "\n=== Testing Dashboard API Directly ==="
echo "Testing dashboard endpoint with timeout..."
time curl -m 30 -s "http://localhost:8001/api/v1/dashboard" | head -200

echo -e "\n=== Checking Database Indexes ==="
python3 -c "
import sys
sys.path.append('/var/www/G_ID_engine_production')
from app.models.database import get_db
from sqlalchemy import text

db = next(get_db())
try:
    # Check if our indexes exist
    result = db.execute(text('''
        SELECT 
            i.name as index_name,
            t.name as table_name,
            c.name as column_name
        FROM sys.indexes i
        JOIN sys.tables t ON i.object_id = t.object_id
        JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE t.name = 'global_id' AND i.name LIKE 'IX_global_id%'
        ORDER BY i.name, ic.key_ordinal
    '''))
    
    print('=== Current Indexes on global_id table ===')
    for row in result:
        print(f'Index: {row.index_name} on {row.table_name}.{row.column_name}')
        
    # Test the optimized query directly
    print('\n=== Testing Optimized Query Performance ===')
    import time
    start_time = time.time()
    
    stats_result = db.execute(text('''
        SELECT 
            COUNT(*) as total_records,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_records,
            SUM(CASE WHEN status = 'Non Active' THEN 1 ELSE 0 END) as inactive_records,
            SUM(CASE WHEN source = 'database_pegawai' THEN 1 ELSE 0 END) as database_source,
            SUM(CASE WHEN source = 'excel' THEN 1 ELSE 0 END) as excel_source
        FROM dbo.global_id
    ''')).fetchone()
    
    query_time = time.time() - start_time
    print(f'Query completed in {query_time:.2f} seconds')
    print(f'Results: Total={stats_result.total_records}, Active={stats_result.active_records}, Inactive={stats_result.inactive_records}')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
"

echo -e "\n=== Checking Application Logs ==="
echo "Recent application logs:"
sudo journalctl -u gid-system --no-pager -n 20

echo -e "\n=== Environment Configuration ==="
echo "Current APP_PORT setting:"
grep "APP_PORT" /var/www/G_ID_engine_production/.env

echo -e "\n=== Process Information ==="
echo "Python processes running:"
ps aux | grep python | grep -v grep

echo "🔍 Diagnosis complete!"