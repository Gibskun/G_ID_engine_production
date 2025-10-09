-- =========================================
-- COMPLETE DUPLICATE REMOVAL SOLUTION
-- Remove ALL constraints that prevent duplicate data
-- =========================================

USE g_id;
GO

PRINT 'Starting complete duplicate removal...';

-- Step 1: Drop ALL unique constraints and indexes
PRINT 'Step 1: Removing all unique constraints...';

DECLARE @sql NVARCHAR(MAX) = '';

-- Get all unique constraints and indexes on passport_id and no_ktp
SELECT @sql = @sql + 'DROP INDEX ' + i.name + ' ON ' + OBJECT_SCHEMA_NAME(i.object_id) + '.' + OBJECT_NAME(i.object_id) + ';' + CHAR(13)
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.is_unique = 1 
  AND c.name IN ('passport_id', 'no_ktp')
  AND i.name IS NOT NULL;

-- Execute the drop statements
IF LEN(@sql) > 0
BEGIN
    PRINT 'Executing constraint removal SQL:';
    PRINT @sql;
    EXEC sp_executesql @sql;
END
ELSE
BEGIN
    PRINT 'No unique constraints found to remove';
END

-- Step 2: Handle existing data to prevent conflicts
PRINT 'Step 2: Converting problematic values to NULL...';

-- Convert all '0' values to NULL
UPDATE dbo.global_id SET passport_id = NULL WHERE passport_id = '0' OR passport_id = '';
UPDATE dbo.global_id SET no_ktp = NULL WHERE no_ktp = '0' OR no_ktp = '';

UPDATE dbo.global_id_non_database SET passport_id = NULL WHERE passport_id = '0' OR passport_id = '';
UPDATE dbo.global_id_non_database SET no_ktp = NULL WHERE no_ktp = '0' OR no_ktp = '';

UPDATE dbo.pegawai SET passport_id = NULL WHERE passport_id = '0' OR passport_id = '';
UPDATE dbo.pegawai SET no_ktp = NULL WHERE no_ktp = '0' OR no_ktp = '';

PRINT 'Converted all 0 and empty values to NULL';

-- Step 3: Create new non-unique indexes for performance only
PRINT 'Step 3: Creating performance indexes (non-unique)...';

-- Create non-unique indexes for performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_global_id_passport_id_perf')
    CREATE INDEX IX_global_id_passport_id_perf ON dbo.global_id (passport_id) WHERE passport_id IS NOT NULL;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_global_id_no_ktp_perf')
    CREATE INDEX IX_global_id_no_ktp_perf ON dbo.global_id (no_ktp) WHERE no_ktp IS NOT NULL;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_global_id_non_db_passport_id_perf')
    CREATE INDEX IX_global_id_non_db_passport_id_perf ON dbo.global_id_non_database (passport_id) WHERE passport_id IS NOT NULL;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_global_id_non_db_no_ktp_perf')
    CREATE INDEX IX_global_id_non_db_no_ktp_perf ON dbo.global_id_non_database (no_ktp) WHERE no_ktp IS NOT NULL;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_pegawai_passport_id_perf')
    CREATE INDEX IX_pegawai_passport_id_perf ON dbo.pegawai (passport_id) WHERE passport_id IS NOT NULL;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_pegawai_no_ktp_perf')
    CREATE INDEX IX_pegawai_no_ktp_perf ON dbo.pegawai (no_ktp) WHERE no_ktp IS NOT NULL;

PRINT 'Performance indexes created';

-- Step 4: Verify the changes
PRINT 'Step 4: Verification...';

-- Show remaining constraints
SELECT 
    'Remaining unique constraints:' as info,
    i.name as constraint_name,
    OBJECT_NAME(i.object_id) as table_name,
    c.name as column_name
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE i.is_unique = 1 
  AND c.name IN ('passport_id', 'no_ktp')
  AND i.name IS NOT NULL;

-- Show data statistics
SELECT 'global_id' as table_name, 
       COUNT(*) as total_records,
       COUNT(passport_id) as non_null_passport_ids,
       COUNT(no_ktp) as non_null_ktps
FROM dbo.global_id
UNION ALL
SELECT 'global_id_non_database' as table_name, 
       COUNT(*) as total_records,
       COUNT(passport_id) as non_null_passport_ids,
       COUNT(no_ktp) as non_null_ktps
FROM dbo.global_id_non_database
UNION ALL
SELECT 'pegawai' as table_name, 
       COUNT(*) as total_records,
       COUNT(passport_id) as non_null_passport_ids,
       COUNT(no_ktp) as non_null_ktps
FROM dbo.pegawai;

PRINT '';
PRINT '🎉 COMPLETE DUPLICATE REMOVAL FINISHED!';
PRINT '✅ All unique constraints removed';
PRINT '✅ All 0 and empty values converted to NULL';
PRINT '✅ Performance indexes created (non-unique)';
PRINT '✅ Database ready to accept duplicate passport_id and no_ktp values';
PRINT '';
PRINT '🚀 NEXT: Restart your application server';
PRINT 'Your Excel upload should now process ALL records with 0 skipped!';

GO