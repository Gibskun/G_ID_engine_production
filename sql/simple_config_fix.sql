-- Simple system configuration fix
-- Creates table and disables all validation

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='system_config' AND xtype='U')
CREATE TABLE system_config (
    id INT IDENTITY(1,1) PRIMARY KEY,
    config_key VARCHAR(255) NOT NULL UNIQUE,
    config_value VARCHAR(1000) NULL,
    description VARCHAR(1000) NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
)