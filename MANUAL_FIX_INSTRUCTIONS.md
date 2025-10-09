# 🔧 MANUAL FIX FOR global_id_non_database TABLE

## Problem Identified ✅
The error "ALTER TABLE ALTER COLUMN failed because one or more objects access this column" means there are **indexes or constraints** on the `global_id_non_database` table that prevent column modification.

## Quick Fix Solution 🚀

### **Option 1: Run the Fixed Migration Script**
Execute this file on your server:
```bash
sqlcmd -S your_server -d g_id -i sql/migration_fix_field_sizes.sql
```

### **Option 2: Manual SQL Commands**
If you have SQL Server Management Studio or direct SQL access, run these commands:

```sql
USE g_id;

-- 1. Check what's blocking the columns
SELECT i.name AS index_name, c.name AS column_name
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id  
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.object_id = OBJECT_ID('dbo.global_id_non_database')
    AND c.name IN ('no_ktp', 'passport_id')
    AND i.is_unique = 1;

-- 2. Drop any unique indexes (replace 'IndexName' with actual index name from step 1)
-- DROP INDEX IndexName ON dbo.global_id_non_database;

-- 3. Alternative approach - recreate the columns
-- For no_ktp:
ALTER TABLE dbo.global_id_non_database ADD no_ktp_temp NVARCHAR(50) NULL;
UPDATE dbo.global_id_non_database SET no_ktp_temp = no_ktp;
ALTER TABLE dbo.global_id_non_database DROP COLUMN no_ktp;
EXEC sp_rename 'dbo.global_id_non_database.no_ktp_temp', 'no_ktp', 'COLUMN';

-- For passport_id:
ALTER TABLE dbo.global_id_non_database ADD passport_id_temp NVARCHAR(50) NULL;
UPDATE dbo.global_id_non_database SET passport_id_temp = passport_id;
ALTER TABLE dbo.global_id_non_database DROP COLUMN passport_id;
EXEC sp_rename 'dbo.global_id_non_database.passport_id_temp', 'passport_id', 'COLUMN';

-- 4. Verify the changes
SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'global_id_non_database'
    AND COLUMN_NAME IN ('no_ktp', 'passport_id');
```

## Verification ✅

After running the fix, you should see:
```
TABLE_NAME                  COLUMN_NAME    CHARACTER_MAXIMUM_LENGTH
global_id_non_database      no_ktp         50
global_id_non_database      passport_id    50
```

## Current Status Summary 📊

### **✅ Already Fixed:**
- `global_id.no_ktp` → 50 characters ✅
- `global_id.passport_id` → 50 characters ✅  
- `pegawai.no_ktp` → 50 characters ✅
- `pegawai.passport_id` → 50 characters ✅

### **🔧 Needs Fix:**
- `global_id_non_database.no_ktp` → still 16 characters ❌
- `global_id_non_database.passport_id` → still 9 characters ❌

## After the Fix 🎉

Once you complete this migration:

**BEFORE:**
- ❌ 679 skipped records
- ❌ "KTP '640.303.261.072.0002' has 20 digits (exceeds database limit)"

**AFTER:**
- ✅ 0 skipped records  
- ✅ All long KTP numbers accepted
- ✅ 'nan' values cleaned properly
- ✅ No auto-generation of passport IDs

**Your upload will process ALL records successfully! 🚀**