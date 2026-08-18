-- Run FIRST to create schemas
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;

-- Set search path
ALTER DATABASE data_platform_db SET search_path TO bronze, silver;