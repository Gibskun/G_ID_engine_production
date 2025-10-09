-- =========================================
-- SQL Script to Update Source Columns to SAP
-- Run this script on your database server
-- =========================================

USE g_id;
GO

PRINT 'Starting SAP Source Update Process...';
PRINT '========================================';

-- Step 1: Add source column to pegawai table if it doesn't exist
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'pegawai' AND COLUMN_NAME = 'source'
)
BEGIN
    PRINT 'Adding source column to pegawai table...';
    ALTER TABLE dbo.pegawai ADD source NVARCHAR(20) NOT NULL DEFAULT 'SAP';
    PRINT '✓ Source column added to pegawai table';
END
ELSE
BEGIN
    PRINT '✓ Source column already exists in pegawai table';
END

-- Step 2: Update all global_id records to have source = 'SAP'
PRINT 'Updating global_id table source to SAP...';
UPDATE dbo.global_id 
SET source = 'SAP',
    updated_at = GETDATE();

DECLARE @global_id_updated INT = @@ROWCOUNT;
PRINT '✓ Updated ' + CAST(@global_id_updated AS NVARCHAR(10)) + ' records in global_id table to source=SAP';

-- Step 3: Update all pegawai records to have source = 'SAP'
PRINT 'Updating pegawai table source to SAP...';
UPDATE dbo.pegawai 
SET source = 'SAP',
    updated_at = GETDATE()
WHERE deleted_at IS NULL;

DECLARE @pegawai_updated INT = @@ROWCOUNT;
PRINT '✓ Updated ' + CAST(@pegawai_updated AS NVARCHAR(10)) + ' records in pegawai table to source=SAP';

-- Step 4: Verification
PRINT '';
PRINT 'Verification Results:';
PRINT '====================';

-- Check global_id table
SELECT @global_id_updated = COUNT(*) FROM dbo.global_id WHERE source = 'SAP';
DECLARE @global_id_total INT = (SELECT COUNT(*) FROM dbo.global_id);
PRINT 'global_id table:';
PRINT '  Total records: ' + CAST(@global_id_total AS NVARCHAR(10));
PRINT '  Records with source=SAP: ' + CAST(@global_id_updated AS NVARCHAR(10));

-- Check pegawai table
SELECT @pegawai_updated = COUNT(*) FROM dbo.pegawai WHERE source = 'SAP' AND deleted_at IS NULL;
DECLARE @pegawai_total INT = (SELECT COUNT(*) FROM dbo.pegawai WHERE deleted_at IS NULL);
PRINT 'pegawai table:';
PRINT '  Total active records: ' + CAST(@pegawai_total AS NVARCHAR(10));
PRINT '  Records with source=SAP: ' + CAST(@pegawai_updated AS NVARCHAR(10));

-- Verify column exists
IF EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'pegawai' AND COLUMN_NAME = 'source'
)
BEGIN
    PRINT 'pegawai source column exists: ✓ Yes';
END
ELSE
BEGIN
    PRINT 'pegawai source column exists: ✗ No';
END

PRINT '';
PRINT '🎉 SAP Source Update completed successfully!';
PRINT 'Next steps:';
PRINT '1. Restart the application server to load updated models';
PRINT '2. Test the new SAP export functionality';
PRINT '3. Verify export downloads from pegawai table';

GO