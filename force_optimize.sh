#!/bin/bash

echo "🔧 Force-applying Performance Optimizations..."

# Stop the service first
echo "=== Stopping Service ==="
sudo systemctl stop gid-system

# Ensure we're in the right directory and have latest code
echo "=== Pulling Latest Code ==="
cd /var/www/G_ID_engine_production
git pull origin main

# Force create indexes (ignore if they exist)
echo "=== Creating Database Indexes ==="
python3 -c "
import sys
sys.path.append('/var/www/G_ID_engine_production')
from app.models.database import get_db
from sqlalchemy import text

db = next(get_db())
try:
    indexes = [
        'CREATE NONCLUSTERED INDEX IX_global_id_status ON dbo.global_id (status)',
        'CREATE NONCLUSTERED INDEX IX_global_id_source ON dbo.global_id (source)',
        'CREATE NONCLUSTERED INDEX IX_global_id_status_source ON dbo.global_id (status, source)',
        'CREATE NONCLUSTERED INDEX IX_global_id_updated_at ON dbo.global_id (updated_at DESC)',
        'CREATE NONCLUSTERED INDEX IX_global_id_no_ktp ON dbo.global_id (no_ktp)'
    ]
    
    for index_sql in indexes:
        try:
            db.execute(text(index_sql))
            db.commit()
            index_name = index_sql.split('IX_')[1].split(' ')[0]
            print(f'✅ Created index: IX_{index_name}')
        except Exception as e:
            if 'already exists' in str(e) or 'duplicate' in str(e).lower() or 'There is already an object' in str(e):
                index_name = index_sql.split('IX_')[1].split(' ')[0]
                print(f'ℹ️  Index already exists: IX_{index_name}')
            else:
                print(f'❌ Error creating index: {e}')
                
    print('🔧 Index creation completed')
except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()
"

# Update statistics on the table to help query optimizer
echo "=== Updating Table Statistics ==="
python3 -c "
import sys
sys.path.append('/var/www/G_ID_engine_production')
from app.models.database import get_db
from sqlalchemy import text

db = next(get_db())
try:
    db.execute(text('UPDATE STATISTICS dbo.global_id'))
    db.commit()
    print('✅ Updated table statistics')
except Exception as e:
    print(f'Error updating statistics: {e}')
finally:
    db.close()
"

# Clear any Python cache
echo "=== Clearing Python Cache ==="
find /var/www/G_ID_engine_production -name "*.pyc" -delete
find /var/www/G_ID_engine_production -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Restart the service
echo "=== Starting Service ==="
sudo systemctl start gid-system

# Wait a moment for service to start
sleep 3

# Check service status
echo "=== Service Status ==="
sudo systemctl status gid-system --no-pager -l

# Test the API directly
echo "=== Testing API Performance ==="
echo "Testing dashboard endpoint..."
time curl -m 15 -s "http://localhost:8001/api/v1/dashboard" > /tmp/dashboard_test.json

if [ $? -eq 0 ]; then
    echo "✅ API responded successfully"
    echo "Response preview:"
    head -5 /tmp/dashboard_test.json
    
    # Check response size
    response_size=$(wc -c < /tmp/dashboard_test.json)
    echo "Response size: $response_size bytes"
else
    echo "❌ API request failed or timed out"
fi

echo "🎯 Forced optimization complete!"
echo "🌐 Test the dashboard at: https://wecare.techconnect.co.id/gid/"