#!/usr/bin/env python3
"""
Verify Duplicate Validation Removal
Checks that all duplicate validation has been completely disabled
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_excel_service():
    """Check excel_service.py for disabled duplicate validation"""
    print("🔍 Checking excel_service.py...")
    
    with open('app/services/excel_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if duplicate checking is commented out
    if "#     duplicate_ktps = df[df.duplicated(subset=['no_ktp']" in content:
        print("✅ File-level KTP duplicate checking: DISABLED")
    else:
        print("❌ File-level KTP duplicate checking: STILL ACTIVE")
        return False
    
    return True

def check_excel_sync_service():
    """Check excel_sync_service.py for disabled duplicate validation"""
    print("🔍 Checking excel_sync_service.py...")
    
    with open('app/services/excel_sync_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if database duplicate checking is disabled
    if "# REMOVED: Database duplicate checking disabled" in content:
        print("✅ Database duplicate checking: DISABLED")
    else:
        print("❌ Database duplicate checking: STILL ACTIVE")
        return False
    
    return True

def check_advanced_workflow_service():
    """Check advanced_workflow_service.py for disabled duplicate validation"""
    print("🔍 Checking advanced_workflow_service.py...")
    
    with open('app/services/advanced_workflow_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if record existence checking is disabled
    if "# User wants ALL data processed regardless of duplicates" in content:
        print("✅ Record existence checking: DISABLED")
    else:
        print("❌ Record existence checking: STILL ACTIVE")
        return False
    
    return True

def check_database_schema():
    """Check if database schema allows duplicates"""
    print("🔍 Checking database schema...")
    
    with open('sql/create_schema_sqlserver.sql', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for system_config table
    if "CREATE TABLE dbo.system_config" in content:
        print("✅ System config table: EXISTS")
    else:
        print("❌ System config table: MISSING")
        return False
    
    # Check for validation disabled
    if "'strict_validation', 'false'" in content:
        print("✅ Validation settings: DISABLED")
    else:
        print("❌ Validation settings: NOT CONFIGURED")
        return False
    
    # Check no unique constraints
    if "IX_global_id_passport_id_lookup" in content and "UNIQUE" not in content.split("IX_global_id_passport_id_lookup")[1].split("GO")[0]:
        print("✅ Unique constraints: REMOVED")
    else:
        print("❌ Unique constraints: STILL EXIST")
        return False
    
    return True

def main():
    print("🔧 DUPLICATE VALIDATION REMOVAL VERIFICATION")
    print("=" * 60)
    print()
    
    checks = [
        ("Excel Service", check_excel_service),
        ("Excel Sync Service", check_excel_sync_service),
        ("Advanced Workflow Service", check_advanced_workflow_service),
        ("Database Schema", check_database_schema)
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"📋 {name}:")
        result = check_func()
        print()
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Duplicate validation is completely disabled")
        print("✅ Ready to process ALL 8753 records")
        print()
        print("🧪 NEXT STEPS:")
        print("1. Restart your server (if needed)")
        print("2. Upload your Excel file again")
        print("3. Expected result: 8753/8753 records processed, 0 skipped")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("Please review the failed checks above")

if __name__ == "__main__":
    main()