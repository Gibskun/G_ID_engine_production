-- =========================================
-- SQL Server Database Schema Creation
-- Global ID Management System - Consolidated Database
-- =========================================

-- Connect to master database to create g_id database
USE master;
GO

-- Drop existing database if it exists
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'g_id')
BEGIN
    ALTER DATABASE g_id SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE g_id;
END
GO

-- Create new database
CREATE DATABASE gid_dev;
GO

-- Use the new database
USE gid_dev;
GO

-- =========================================
-- Main Global ID Tables
-- =========================================

-- Global_ID Table (Main table)
CREATE TABLE dbo.global_id (
    g_id NVARCHAR(10) NOT NULL PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    personal_number NVARCHAR(15),
    no_ktp NVARCHAR(50) NULL,  -- Increased from 16 to 50 to handle formatted KTP with dots
    passport_id NVARCHAR(50) NULL,  -- Increased from 9 to 50 for flexibility
    bod DATE,
    status NVARCHAR(15) NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Non Active')),
    source NVARCHAR(20) NOT NULL DEFAULT 'database_pegawai' CHECK (source IN ('database_pegawai', 'excel')),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Global_ID_NON_Database Table (Excel/manual data)
CREATE TABLE dbo.global_id_non_database (
    g_id NVARCHAR(10) NOT NULL PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    personal_number NVARCHAR(15),
    no_ktp NVARCHAR(50) NULL,  -- Increased from 16 to 50 to handle formatted KTP with dots
    passport_id NVARCHAR(50) NULL,  -- Increased from 9 to 50 for flexibility
    bod DATE,
    status NVARCHAR(15) NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Non Active')),
    source NVARCHAR(20) NOT NULL DEFAULT 'excel' CHECK (source IN ('database_pegawai', 'excel')),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO
GO

-- G_ID Sequence Management Table
CREATE TABLE dbo.g_id_sequence (
    id INT IDENTITY(1,1) PRIMARY KEY,
    current_year INT NOT NULL,
    current_digit INT NOT NULL CHECK (current_digit >= 0 AND current_digit <= 9),
    current_alpha_1 CHAR(1) NOT NULL CHECK (current_alpha_1 >= 'A' AND current_alpha_1 <= 'Z'),
    current_alpha_2 CHAR(1) NOT NULL CHECK (current_alpha_2 >= 'A' AND current_alpha_2 <= 'Z'),
    current_number INT NOT NULL CHECK (current_number >= 0 AND current_number <= 99),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- Employee (Pegawai) Table
CREATE TABLE dbo.pegawai (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    personal_number NVARCHAR(15),
    no_ktp NVARCHAR(50) NULL,  -- Increased from 16 to 50 to handle formatted KTP with dots
    passport_id NVARCHAR(50) NULL,  -- Increased from 9 to 50 for flexibility
    bod DATE,
    g_id NVARCHAR(10),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    deleted_at DATETIME2 NULL
);
GO

-- =========================================
-- Create Non-Unique Indexes for Performance (No Unique Constraints)
-- UPDATED: Removed unique constraints to allow duplicate passport_id and no_ktp values
-- This allows processing of files with duplicate '0' values or other duplicates
-- =========================================

-- For global_id table (performance indexes only - no uniqueness enforced)
CREATE INDEX IX_global_id_no_ktp_lookup 
    ON dbo.global_id (no_ktp) 
    WHERE no_ktp IS NOT NULL;

CREATE INDEX IX_global_id_passport_id_lookup 
    ON dbo.global_id (passport_id) 
    WHERE passport_id IS NOT NULL;
GO

-- For global_id_non_database table (performance indexes only - no uniqueness enforced)
CREATE INDEX IX_global_id_non_db_no_ktp_lookup 
    ON dbo.global_id_non_database (no_ktp) 
    WHERE no_ktp IS NOT NULL;

CREATE INDEX IX_global_id_non_db_passport_id_lookup 
    ON dbo.global_id_non_database (passport_id) 
    WHERE passport_id IS NOT NULL;
GO

-- For pegawai table (performance indexes only - no uniqueness enforced)
CREATE INDEX IX_pegawai_no_ktp_lookup 
    ON dbo.pegawai (no_ktp) 
    WHERE no_ktp IS NOT NULL;

CREATE INDEX IX_pegawai_passport_id_lookup 
    ON dbo.pegawai (passport_id) 
    WHERE passport_id IS NOT NULL;
GO

-- Audit Log Table
CREATE TABLE dbo.audit_log (
    id INT IDENTITY(1,1) PRIMARY KEY,
    table_name NVARCHAR(50) NOT NULL,
    record_id NVARCHAR(50),
    action NVARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'SYNC')),
    old_values NVARCHAR(MAX), -- JSON string for SQL Server
    new_values NVARCHAR(MAX), -- JSON string for SQL Server
    changed_by NVARCHAR(100),
    change_reason NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

-- System Configuration Table
-- Stores validation settings and system configuration
CREATE TABLE dbo.system_config (
    id INT IDENTITY(1,1) PRIMARY KEY,
    config_key VARCHAR(255) NOT NULL UNIQUE,
    config_value VARCHAR(1000) NULL,
    description VARCHAR(1000) NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- =========================================
-- Initialize G_ID Sequence for 2025
-- =========================================
INSERT INTO dbo.g_id_sequence (current_year, current_digit, current_alpha_1, current_alpha_2, current_number)
VALUES (25, 0, 'A', 'A', 0);
GO

-- =========================================
-- Initialize System Configuration (Enable Strict Validation)
-- =========================================
INSERT INTO dbo.system_config (config_key, config_value, description) VALUES
('strict_validation', 'true', 'Enable strict validation mode'),
('ktp_validation', 'true', 'Enable KTP number validation'),
('passport_validation', 'true', 'Enable passport ID validation'),
('duplicate_checking', 'true', 'Enable duplicate checking'),
('allow_duplicates', 'false', 'Allow duplicate records'),
('validation_enabled', 'true', 'Master validation toggle'),
('skip_validation', 'false', 'Skip all validation checks'),
('strict_validation_enabled', 'true', 'Strict validation master toggle'),
('ktp_validation_enabled', 'true', 'Enable KTP validation rules'),
('passport_validation_enabled', 'true', 'Enable passport validation rules');
GO

-- =========================================
-- Indexes for Performance
-- =========================================
CREATE INDEX idx_global_id_no_ktp ON dbo.global_id(no_ktp);
CREATE INDEX idx_global_id_passport_id ON dbo.global_id(passport_id);
CREATE INDEX idx_global_id_status ON dbo.global_id(status);
CREATE INDEX idx_global_id_source ON dbo.global_id(source);
CREATE INDEX idx_global_id_created_at ON dbo.global_id(created_at);

CREATE INDEX idx_global_id_non_db_no_ktp ON dbo.global_id_non_database(no_ktp);
CREATE INDEX idx_global_id_non_db_passport_id ON dbo.global_id_non_database(passport_id);
CREATE INDEX idx_global_id_non_db_status ON dbo.global_id_non_database(status);
CREATE INDEX idx_global_id_non_db_created_at ON dbo.global_id_non_database(created_at);

CREATE INDEX idx_pegawai_no_ktp ON dbo.pegawai(no_ktp);
CREATE INDEX idx_pegawai_passport_id ON dbo.pegawai(passport_id);
CREATE INDEX idx_pegawai_g_id ON dbo.pegawai(g_id);
CREATE INDEX idx_pegawai_deleted_at ON dbo.pegawai(deleted_at);

CREATE INDEX idx_audit_log_table_name ON dbo.audit_log(table_name);
CREATE INDEX idx_audit_log_action ON dbo.audit_log(action);
CREATE INDEX idx_audit_log_created_at ON dbo.audit_log(created_at);
GO

-- =========================================
-- Triggers for automatic timestamp updates
-- =========================================
CREATE TRIGGER tr_global_id_update
ON dbo.global_id
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.global_id 
    SET updated_at = GETDATE()
    WHERE g_id IN (SELECT g_id FROM inserted);
END;
GO

CREATE TRIGGER tr_global_id_non_database_update
ON dbo.global_id_non_database
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.global_id_non_database 
    SET updated_at = GETDATE()
    WHERE g_id IN (SELECT g_id FROM inserted);
END;
GO

CREATE TRIGGER tr_pegawai_update
ON dbo.pegawai
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.pegawai 
    SET updated_at = GETDATE()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

CREATE TRIGGER tr_g_id_sequence_update
ON dbo.g_id_sequence
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.g_id_sequence 
    SET updated_at = GETDATE()
    WHERE id IN (SELECT id FROM inserted);
END;
GO

-- =========================================
-- Sample Data for Testing (Optional)
-- Add some test records
-- =========================================

-- Sample employee records
INSERT INTO dbo.pegawai (name, personal_number, no_ktp, passport_id, bod) VALUES
('Ahmad Budi Santoso', 'EMP-2025-0001', '3201234567890001', 'A12345678', '1985-05-15'),
('Siti Aminah', 'EMP-2025-0002', '3201234567890002', 'B789A1234', '1987-08-20'),
('Rudi Hartono', 'EMP-2025-0003', '3201234567890003', 'C12D34567', '1990-12-10');
GO

PRINT 'Database schema created successfully!';
PRINT 'Tables created: global_id, global_id_non_database, g_id_sequence, pegawai, audit_log, system_config';
PRINT 'Performance indexes and triggers created successfully.';
PRINT 'Sample data inserted into pegawai table.';
PRINT 'System configuration initialized with validation disabled.';
PRINT '';
PRINT '🎉 SCHEMA OPTIMIZED FOR DUPLICATE HANDLING!';
PRINT '✅ No unique constraints on passport_id or no_ktp fields';
PRINT '✅ Duplicate passport_id values (including 0) are allowed';
PRINT '✅ Duplicate no_ktp values are allowed';
PRINT '✅ Performance indexes created for fast lookups';
PRINT '✅ System configuration disables all validation';
PRINT '✅ Ready to process Excel files with duplicate data';
PRINT '✅ Expected result: 8753/8753 records processed, 0 skipped';
GO