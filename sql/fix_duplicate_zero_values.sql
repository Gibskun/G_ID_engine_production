-- =========================================
-- Remove Unique Constraints for '0' Value Issue
-- Fix duplicate '0' passport_id problem
-- =========================================

USE g_id;
GO

PRINT 'Fixing duplicate 0 value issue...';
PRINT 'Removing unique constraints that cause 0 value conflicts';

-- Step 1: Drop unique indexes that prevent multiple '0' values
PRINT 'Step 1: Dropping unique indexes...';

-- For global_id table
BEGIN TRY
    DROP INDEX IX_global_id_no_ktp_unique ON dbo.global_id;
    PRINT 'Dropped index: IX_global_id_no_ktp_unique';
END TRY
BEGIN CATCH
    PRINT 'Index IX_global_id_no_ktp_unique not found or already dropped';
END CATCH;

BEGIN TRY
    DROP INDEX IX_global_id_passport_id_unique ON dbo.global_id;
    PRINT 'Dropped index: IX_global_id_passport_id_unique';
END TRY
BEGIN CATCH
    PRINT 'Index IX_global_id_passport_id_unique not found or already dropped';
END CATCH;

-- For global_id_non_database table
BEGIN TRY
    DROP INDEX IX_global_id_non_db_no_ktp_unique ON dbo.global_id_non_database;
    PRINT 'Dropped index: IX_global_id_non_db_no_ktp_unique';
END TRY
BEGIN CATCH
    PRINT 'Index IX_global_id_non_db_no_ktp_unique not found or already dropped';
END CATCH;

BEGIN TRY
    DROP INDEX IX_global_id_non_db_passport_id_unique ON dbo.global_id_non_database;
    PRINT 'Dropped index: IX_global_id_non_db_passport_id_unique';
END TRY
BEGIN CATCH
    PRINT 'Index IX_global_id_non_db_passport_id_unique not found or already dropped';
END CATCH;

-- For pegawai table
BEGIN TRY
    DROP INDEX IX_pegawai_no_ktp_unique ON dbo.pegawai;
    PRINT 'Dropped index: IX_pegawai_no_ktp_unique';
END TRY
BEGIN CATCH
    PRINT 'Index IX_pegawai_no_ktp_unique not found or already dropped';
END CATCH;

BEGIN TRY
    DROP INDEX IX_pegawai_passport_id_unique ON dbo.pegawai;
    PRINT 'Dropped index: IX_pegawai_passport_id_unique';
END TRY
BEGIN CATCH
    PRINT 'Index IX_pegawai_passport_id_unique not found or already dropped';
END CATCH;

PRINT 'Step 1 completed: All unique constraints removed';

-- Step 2: Clean existing '0' values to NULL
PRINT 'Step 2: Converting 0 values to NULL...';

UPDATE dbo.global_id 
SET no_ktp = NULL 
WHERE no_ktp = '0';

UPDATE dbo.global_id 
SET passport_id = NULL 
WHERE passport_id = '0';

UPDATE dbo.global_id_non_database 
SET no_ktp = NULL 
WHERE no_ktp = '0';

UPDATE dbo.global_id_non_database 
SET passport_id = NULL 
WHERE passport_id = '0';

UPDATE dbo.pegawai 
SET no_ktp = NULL 
WHERE no_ktp = '0';

UPDATE dbo.pegawai 
SET passport_id = NULL 
WHERE passport_id = '0';

PRINT 'Step 2 completed: All 0 values converted to NULL';

-- Step 3: Create new conditional unique indexes (only for non-null values)
PRINT 'Step 3: Creating conditional unique indexes...';

-- For global_id table (only unique when NOT NULL and NOT '0')
CREATE UNIQUE INDEX IX_global_id_no_ktp_unique 
    ON dbo.global_id (no_ktp) 
    WHERE no_ktp IS NOT NULL AND no_ktp <> '0';

CREATE UNIQUE INDEX IX_global_id_passport_id_unique 
    ON dbo.global_id (passport_id) 
    WHERE passport_id IS NOT NULL AND passport_id <> '0';

-- For global_id_non_database table
CREATE UNIQUE INDEX IX_global_id_non_db_no_ktp_unique 
    ON dbo.global_id_non_database (no_ktp) 
    WHERE no_ktp IS NOT NULL AND no_ktp <> '0';

CREATE UNIQUE INDEX IX_global_id_non_db_passport_id_unique 
    ON dbo.global_id_non_database (passport_id) 
    WHERE passport_id IS NOT NULL AND passport_id <> '0';

-- For pegawai table
CREATE UNIQUE INDEX IX_pegawai_no_ktp_unique 
    ON dbo.pegawai (no_ktp) 
    WHERE no_ktp IS NOT NULL AND no_ktp <> '0';

CREATE UNIQUE INDEX IX_pegawai_passport_id_unique 
    ON dbo.pegawai (passport_id) 
    WHERE passport_id IS NOT NULL AND passport_id <> '0';

PRINT 'Step 3 completed: Conditional unique indexes created';

-- Step 4: Verify the changes
PRINT 'Step 4: Verifying changes...';

SELECT 
    'global_id' AS table_name,
    COUNT(*) AS total_records,
    COUNT(no_ktp) AS non_null_ktp,
    COUNT(passport_id) AS non_null_passport,
    SUM(CASE WHEN no_ktp = '0' THEN 1 ELSE 0 END) AS zero_ktp_count,
    SUM(CASE WHEN passport_id = '0' THEN 1 ELSE 0 END) AS zero_passport_count
FROM dbo.global_id

UNION ALL

SELECT 
    'global_id_non_database' AS table_name,
    COUNT(*) AS total_records,
    COUNT(no_ktp) AS non_null_ktp,
    COUNT(passport_id) AS non_null_passport,
    SUM(CASE WHEN no_ktp = '0' THEN 1 ELSE 0 END) AS zero_ktp_count,
    SUM(CASE WHEN passport_id = '0' THEN 1 ELSE 0 END) AS zero_passport_count
FROM dbo.global_id_non_database

UNION ALL

SELECT 
    'pegawai' AS table_name,
    COUNT(*) AS total_records,
    COUNT(no_ktp) AS non_null_ktp,
    COUNT(passport_id) AS non_null_passport,
    SUM(CASE WHEN no_ktp = '0' THEN 1 ELSE 0 END) AS zero_ktp_count,
    SUM(CASE WHEN passport_id = '0' THEN 1 ELSE 0 END) AS zero_passport_count
FROM dbo.pegawai;

PRINT '';
PRINT '🎉 DUPLICATE 0 VALUE ISSUE FIXED!';
PRINT '✅ Unique constraints removed for 0 values';
PRINT '✅ Existing 0 values converted to NULL';
PRINT '✅ Conditional unique indexes created';
PRINT '✅ Multiple records with passport_id=0 will now be accepted as NULL';
PRINT '';
PRINT '🚀 READY FOR UPLOAD!';
PRINT 'Your Excel file with passport_id=0 values should now process ALL records!';

GO