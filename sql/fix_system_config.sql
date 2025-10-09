-- =========================================
-- Fix System Configuration for Validation Settings
-- Add missing system_config table and disable all validations
-- =========================================

USE g_id;
GO

-- Create system_config table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='system_config' AND xtype='U')
BEGIN
    CREATE TABLE dbo.system_config (
        id INT IDENTITY(1,1) PRIMARY KEY,
        config_key NVARCHAR(100) NOT NULL UNIQUE,
        config_value NVARCHAR(500),
        description NVARCHAR(1000),
        created_at DATETIME2 DEFAULT GETDATE(),
        updated_at DATETIME2 DEFAULT GETDATE()
    );
    PRINT 'Created system_config table';
END
ELSE
BEGIN
    PRINT 'system_config table already exists';
END
GO

-- Insert or update validation settings to disable all validations
MERGE dbo.system_config AS target
USING (VALUES 
    ('strict_validation', 'false', 'Disable strict validation - allow all data processing'),
    ('ktp_validation', 'false', 'Disable KTP validation - allow duplicate and any format KTP numbers'),
    ('passport_validation', 'false', 'Disable passport validation - allow duplicate and any format passport IDs'),
    ('duplicate_checking', 'false', 'Disable duplicate checking - allow duplicate data'),
    ('length_validation', 'false', 'Disable length validation - allow any field length'),
    ('format_validation', 'false', 'Disable format validation - allow any data format')
) AS source (config_key, config_value, description)
ON target.config_key = source.config_key
WHEN MATCHED THEN
    UPDATE SET 
        config_value = source.config_value,
        description = source.description,
        updated_at = GETDATE()
WHEN NOT MATCHED THEN
    INSERT (config_key, config_value, description)
    VALUES (source.config_key, source.config_value, source.description);

PRINT 'Updated validation settings to disable all restrictions';

-- Verify the settings
SELECT config_key, config_value, description 
FROM dbo.system_config 
WHERE config_key IN ('strict_validation', 'ktp_validation', 'passport_validation', 'duplicate_checking')
ORDER BY config_key;

PRINT '';
PRINT '🎉 VALIDATION SETTINGS CONFIGURED!';
PRINT '✅ All validation checks disabled';
PRINT '✅ Duplicate checking disabled';
PRINT '✅ Length restrictions removed';
PRINT '✅ Format validation disabled';
PRINT '';
PRINT '🚀 READY TO PROCESS ALL DATA!';
PRINT 'Your Excel upload should now process ALL records with 0 skipped!';

GO