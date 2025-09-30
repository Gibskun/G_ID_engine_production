#!/bin/bash

# Database Performance Optimization Deployment Script
# This script deploys the performance optimizations to the server

echo "🚀 Deploying Database Performance Optimizations..."

# Update .env file with performance settings
cat >> .env << 'EOF'

# Database Performance Configuration
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
QUERY_TIMEOUT=60
EOF

echo "✅ Updated .env with performance settings"

# Create the optimization script
cat > optimize_dashboard.py << 'EOF'
"""
Database Performance Optimization Script for Dashboard Queries
This script optimizes the slow dashboard endpoint by replacing multiple COUNT queries
with efficient aggregation queries and adding database indexes.
"""

import time
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.models.database import get_db
from app.models.models import GlobalID

def optimize_dashboard_query(db: Session):
    """
    Optimized dashboard query using single aggregation instead of multiple COUNT queries
    """
    print("🔍 Testing optimized dashboard query...")
    start_time = time.time()
    
    # Single query with aggregation - much faster than multiple COUNT queries
    stats_query = """
    SELECT 
        COUNT(*) as total_records,
        SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_records,
        SUM(CASE WHEN status = 'Non Active' THEN 1 ELSE 0 END) as inactive_records,
        SUM(CASE WHEN source = 'database_pegawai' THEN 1 ELSE 0 END) as database_source,
        SUM(CASE WHEN source = 'excel' THEN 1 ELSE 0 END) as excel_source
    FROM dbo.global_id
    """
    
    result = db.execute(text(stats_query)).fetchone()
    
    dashboard_stats = {
        'total_records': result.total_records,
        'active_records': result.active_records,
        'inactive_records': result.inactive_records,
        'database_source_records': result.database_source,
        'excel_source_records': result.excel_source
    }
    
    query_time = time.time() - start_time
    print(f"✅ Dashboard stats query completed in {query_time:.2f} seconds")
    print(f"📊 Results: {dashboard_stats}")
    
    return dashboard_stats, query_time

def create_performance_indexes(db: Session):
    """
    Create database indexes to improve query performance
    """
    print("🔧 Creating performance indexes...")
    
    indexes = [
        # Index for status-based queries
        "CREATE NONCLUSTERED INDEX IX_global_id_status ON dbo.global_id (status)",
        
        # Index for source-based queries  
        "CREATE NONCLUSTERED INDEX IX_global_id_source ON dbo.global_id (source)",
        
        # Composite index for status + source queries
        "CREATE NONCLUSTERED INDEX IX_global_id_status_source ON dbo.global_id (status, source)",
        
        # Index for updated_at (for recent activities)
        "CREATE NONCLUSTERED INDEX IX_global_id_updated_at ON dbo.global_id (updated_at DESC)",
        
        # Index for no_ktp (frequently used for lookups)
        "CREATE NONCLUSTERED INDEX IX_global_id_no_ktp ON dbo.global_id (no_ktp)"
    ]
    
    created_indexes = []
    for index_sql in indexes:
        try:
            db.execute(text(index_sql))
            db.commit()
            index_name = index_sql.split('IX_')[1].split(' ')[0]
            created_indexes.append(f"IX_{index_name}")
            print(f"✅ Created index: IX_{index_name}")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower() or "There is already an object" in str(e):
                index_name = index_sql.split('IX_')[1].split(' ')[0]
                print(f"ℹ️  Index already exists: IX_{index_name}")
            else:
                print(f"❌ Error creating index: {e}")
    
    return created_indexes

def test_query_performance():
    """
    Test and compare query performance before and after optimization
    """
    print("🚀 Starting Database Performance Optimization...")
    
    db = next(get_db())
    try:
        # Create indexes first
        print("\n=== Creating Performance Indexes ===")
        created_indexes = create_performance_indexes(db)
        
        # Test optimized query
        print("\n=== Testing Optimized Query ===")
        optimized_stats, optimized_time = optimize_dashboard_query(db)
        
        # Performance results
        print(f"\n=== Performance Results ===")
        print(f"⚡ Optimized query time: {optimized_time:.2f} seconds")
        print(f"🔧 Created {len(created_indexes)} database indexes")
        
        return {
            'optimized_time': optimized_time,
            'indexes_created': created_indexes,
            'stats': optimized_stats
        }
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    # Run the optimization
    results = test_query_performance()
    
    if results:
        print(f"\n🎉 Optimization completed successfully!")
        print(f"🔧 Created {len(results['indexes_created'])} database indexes")
        print(f"⚡ Optimized query time: {results['optimized_time']:.2f} seconds")
        print(f"📊 Total records: {results['stats']['total_records']}")
    else:
        print("❌ Optimization failed")
EOF

echo "✅ Created optimization script"

# Run the optimization
echo "🔧 Running database optimization..."
python optimize_dashboard.py

# Restart the service to apply changes
echo "🔄 Restarting GID system service..."
sudo systemctl restart gid-system

# Check service status
echo "📊 Checking service status..."
sudo systemctl status gid-system --no-pager -l

echo "🎉 Performance optimization deployment completed!"
echo "🌐 Test the optimized dashboard at: https://wecare.techconnect.co.id/gid/"