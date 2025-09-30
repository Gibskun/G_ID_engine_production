"""
Quick fix: Create optimized dashboard endpoint without slow sync service
This will test if sync service is the bottleneck
"""

# Create a temporary optimized dashboard endpoint
import os
import sys

# Add the project path
sys.path.append('/var/www/G_ID_engine_production')

from fastapi import FastAPI, HTTPException
from app.models.database import get_db
from sqlalchemy import text
import time

# Test the optimized dashboard without sync service
def test_dashboard_without_sync():
    print("🔍 Testing dashboard without sync service...")
    
    db = next(get_db())
    try:
        start_time = time.time()
        
        # Get aggregated stats (we know this is fast)
        stats_query = text("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_records,
                SUM(CASE WHEN status = 'Non Active' THEN 1 ELSE 0 END) as inactive_records,
                SUM(CASE WHEN source = 'database_pegawai' THEN 1 ELSE 0 END) as database_source,
                SUM(CASE WHEN source = 'excel' THEN 1 ELSE 0 END) as excel_source
            FROM dbo.global_id
        """)
        
        result = db.execute(stats_query).fetchone()
        
        # Mock sync status instead of calling the slow service
        mock_sync_status = {
            "status": "healthy",
            "last_sync": "2025-09-30T10:00:00",
            "records_synced": result.total_records,
            "sync_duration": "0.1s"
        }
        
        # Get recent activities (we know this is fast)
        from app.models.models import GlobalID
        recent_records = db.query(GlobalID).order_by(GlobalID.updated_at.desc()).limit(10).all()
        
        recent_activities = []
        for record in recent_records:
            recent_activities.append({
                "g_id": record.g_id,
                "name": record.name,
                "action": "Created",
                "timestamp": record.updated_at.isoformat(),
                "source": record.source,
                "status": record.status
            })
        
        # Create response
        dashboard_response = {
            "total_records": result.total_records,
            "active_records": result.active_records,
            "inactive_records": result.inactive_records,
            "database_source_records": result.database_source,
            "excel_source_records": result.excel_source,
            "sync_status": mock_sync_status,
            "recent_activities": recent_activities
        }
        
        query_time = time.time() - start_time
        print(f"✅ Dashboard completed in {query_time:.2f} seconds")
        print(f"📊 Total records: {result.total_records}")
        print(f"📊 Response size: {len(str(dashboard_response))} chars")
        
        if query_time < 1:
            print("🎉 CONFIRMED: Dashboard is fast without sync service!")
            print("🔧 The sync service is the bottleneck")
        
        return dashboard_response, query_time
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, 0
    finally:
        db.close()

if __name__ == "__main__":
    test_dashboard_without_sync()