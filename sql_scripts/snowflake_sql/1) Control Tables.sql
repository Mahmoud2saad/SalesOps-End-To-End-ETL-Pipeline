-- 1. DROP THE ENTIRE SCHEMA TO START FRESH
-- Note: Snowflake does not require CASCADE for schemas in the same way, but it is supported.
DROP SCHEMA IF EXISTS control CASCADE;
CREATE SCHEMA control;

-- 2. CREATE FLEXIBLE WATERMARKS TABLE
CREATE TABLE control.watermarks (
    table_name VARCHAR(100) PRIMARY KEY,
    last_processed_value VARCHAR(100), 
    incremental_column VARCHAR(50),
    incremental_type VARCHAR(20),      -- 'numeric' or 'date'
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 3. CREATE AUDIT LOG TABLE
CREATE TABLE control.audit_log (
    audit_id NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    pipeline_name VARCHAR(100),
    execution_id VARCHAR(100),
    task_name VARCHAR(100),
    table_name VARCHAR(100),
    status VARCHAR(20) CHECK (status IN ('STARTED', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')),
    rows_processed BIGINT,
    error_message STRING, -- TEXT/STRING are interchangeable in Snowflake
    started_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    completed_at TIMESTAMP_NTZ
);

-- 4. CREATE DATA QUALITY METRICS TABLE
CREATE TABLE control.data_quality_metrics (
    metric_id NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    table_name VARCHAR(100),
    check_name VARCHAR(100),
    metric_type VARCHAR(50), 
    expected_value VARCHAR(500),
    actual_value VARCHAR(500),
    passed BOOLEAN,
    severity VARCHAR(20) CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    execution_id VARCHAR(100),
    checked_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    details VARIANT -- Replaces JSONB for semi-structured data
);