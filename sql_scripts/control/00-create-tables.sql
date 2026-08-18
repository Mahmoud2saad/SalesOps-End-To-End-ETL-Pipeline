-- -- ============================================================================
-- -- CONTROL SCHEMA - Production Level (Watermarks, Audit Logs, Quality)
-- -- ============================================================================

-- -- 1. Create schema if not exists
-- CREATE SCHEMA IF NOT EXISTS control;

-- -- ============================================================================
-- -- TABLE DEFINITIONS
-- -- ============================================================================

-- -- 2. Watermarks table for tracking extraction progress
-- CREATE TABLE IF NOT EXISTS control.watermarks (
--     table_name VARCHAR(50) PRIMARY KEY,
--     last_processed_id BIGINT DEFAULT 0,
--     last_processed_timestamp TIMESTAMP,
--     last_processed_value VARCHAR(100), 
--     safety_margin_minutes INT DEFAULT 120,
--     safety_margin_rows INT DEFAULT 10000,
--     incremental_column VARCHAR(50) DEFAULT 'last_processed_timestamp',
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_by VARCHAR(50) DEFAULT CURRENT_USER
-- );
-- -- Note: NO MANUAL INSERTS. The pipeline will auto-initialize these during Initial Load.

-- -- 3. Audit log table for pipeline tracking
-- CREATE TABLE IF NOT EXISTS control.audit_log (
--     audit_id BIGSERIAL PRIMARY KEY,
--     pipeline_name VARCHAR(100),
--     execution_id VARCHAR(100),
--     task_name VARCHAR(100),
--     table_name VARCHAR(100),
--     status VARCHAR(20) CHECK (status IN ('STARTED', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')),
--     rows_input BIGINT,
--     rows_output BIGINT,
--     rows_processed BIGINT,
--     error_code VARCHAR(20),
--     error_message TEXT,
--     started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     completed_at TIMESTAMP,
--     duration_seconds INTEGER,
--     metadata JSONB
-- );

-- -- 4. Data quality metrics table
-- CREATE TABLE IF NOT EXISTS control.data_quality_metrics (
--     metric_id BIGSERIAL PRIMARY KEY,
--     table_name VARCHAR(100),
--     check_name VARCHAR(100),
--     metric_type VARCHAR(50), 
--     expected_value VARCHAR(500),
--     actual_value VARCHAR(500),
--     passed BOOLEAN,
--     severity VARCHAR(20) CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
--     execution_id VARCHAR(100),
--     checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     details JSONB
-- );

-- -- ============================================================================
-- -- AUTOMATION FUNCTIONS (Stored Procedures)
-- -- ============================================================================

-- -- Function to auto-log batch execution start
-- CREATE OR REPLACE FUNCTION control.log_batch_start(
--     p_pipeline_name VARCHAR,
--     p_execution_id VARCHAR,
--     p_task_name VARCHAR,
--     p_table_name VARCHAR
-- ) RETURNS BIGINT AS $$
-- DECLARE
--     v_audit_id BIGINT;
-- BEGIN
--     INSERT INTO control.audit_log (
--         pipeline_name, execution_id, task_name, table_name, status, started_at
--     ) VALUES (
--         p_pipeline_name, p_execution_id, p_task_name, p_table_name, 'STARTED', CURRENT_TIMESTAMP
--     ) RETURNING audit_id INTO v_audit_id;
    
--     RETURN v_audit_id;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- Function to auto-log batch completion
-- CREATE OR REPLACE FUNCTION control.log_batch_complete(
--     p_audit_id BIGINT,
--     p_status VARCHAR,
--     p_rows_processed BIGINT,
--     p_error_message TEXT DEFAULT NULL
-- ) RETURNS VOID AS $$
-- BEGIN
--     UPDATE control.audit_log
--     SET 
--         status = p_status,
--         rows_processed = p_rows_processed,
--         completed_at = CURRENT_TIMESTAMP,
--         duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))::INTEGER,
--         error_message = p_error_message
--     WHERE audit_id = p_audit_id;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- Function to auto-update watermark (Handles both Initial & Incremental loads using UPSERT)
-- CREATE OR REPLACE FUNCTION control.update_watermark(
--     p_table_name VARCHAR,
--     p_last_processed_id BIGINT,
--     p_last_processed_timestamp TIMESTAMP DEFAULT NULL,
--     p_safety_margin_minutes INT DEFAULT NULL,
--     p_safety_margin_rows INT DEFAULT NULL
-- ) RETURNS VOID AS $$
-- BEGIN
--     -- Try to update existing record first (For Incremental Loads)
--     UPDATE control.watermarks
--     SET 
--         last_processed_id = p_last_processed_id,
--         last_processed_timestamp = COALESCE(p_last_processed_timestamp, last_processed_timestamp),
--         safety_margin_minutes = COALESCE(p_safety_margin_minutes, safety_margin_minutes),
--         safety_margin_rows = COALESCE(p_safety_margin_rows, safety_margin_rows),
--         updated_at = CURRENT_TIMESTAMP
--     WHERE table_name = p_table_name;
    
--     -- If no record was updated (table not found), insert a new one (For Initial Loads)
--     IF NOT FOUND THEN
--         INSERT INTO control.watermarks (
--             table_name,
--             last_processed_id,
--             last_processed_timestamp,
--             safety_margin_minutes,
--             safety_margin_rows
--         ) VALUES (
--             p_table_name,
--             p_last_processed_id,
--             p_last_processed_timestamp,
--             COALESCE(p_safety_margin_minutes, 120),
--             COALESCE(p_safety_margin_rows, 10000)
--         );
--     END IF;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- ============================================================================
-- -- PERFORMANCE OPTIMIZATION (INDEXES)
-- -- ============================================================================

-- -- Indexes for Audit Log (To speed up queries and dashboards)
-- CREATE INDEX IF NOT EXISTS idx_audit_table_name ON control.audit_log(table_name);
-- CREATE INDEX IF NOT EXISTS idx_audit_status ON control.audit_log(status);
-- CREATE INDEX IF NOT EXISTS idx_audit_started_at ON control.audit_log(started_at);
-- CREATE INDEX IF NOT EXISTS idx_audit_pipeline ON control.audit_log(pipeline_name);

-- -- Indexes for Data Quality Metrics
-- CREATE INDEX IF NOT EXISTS idx_dqm_table_name ON control.data_quality_metrics(table_name);
-- CREATE INDEX IF NOT EXISTS idx_dqm_severity ON control.data_quality_metrics(severity);

-- -- Indexes for Watermarks (For faster lookups during pipeline execution)
-- CREATE INDEX IF NOT EXISTS idx_watermarks_updated_at ON control.watermarks(updated_at);








-- ============================================================================
-- CONTROL SCHEMA - Production Level (Watermarks, Audit Logs, Quality)
-- ============================================================================

-- 1. Create schema if not exists
CREATE SCHEMA IF NOT EXISTS control;

-- ============================================================================
-- TABLE DEFINITIONS
-- ============================================================================

-- 2. Watermarks table for tracking extraction progress (UPDATED for Date support)
CREATE TABLE IF NOT EXISTS control.watermarks (
    table_name VARCHAR(50) PRIMARY KEY,
    last_processed_id BIGINT DEFAULT 0,                    -- For numeric keys
    last_processed_date DATE,                               -- NEW: For date-based incremental
    last_processed_timestamp TIMESTAMP,                    -- Keep for backward compatibility
    last_processed_value VARCHAR(100),                     -- Generic string value
    safety_margin_minutes INT DEFAULT 120,
    safety_margin_rows INT DEFAULT 10000,
    incremental_column VARCHAR(50) DEFAULT 'last_processed_timestamp',
    incremental_type VARCHAR(20) DEFAULT 'numeric',        -- NEW: 'numeric' or 'date'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50) DEFAULT CURRENT_USER
);

-- 3. Audit log table for pipeline tracking (No changes needed)
CREATE TABLE IF NOT EXISTS control.audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100),
    execution_id VARCHAR(100),
    task_name VARCHAR(100),
    table_name VARCHAR(100),
    status VARCHAR(20) CHECK (status IN ('STARTED', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')),
    rows_input BIGINT,
    rows_output BIGINT,
    rows_processed BIGINT,
    error_code VARCHAR(20),
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    metadata JSONB
);

-- 4. Data quality metrics table
CREATE TABLE IF NOT EXISTS control.data_quality_metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    check_name VARCHAR(100),
    metric_type VARCHAR(50), 
    expected_value VARCHAR(500),
    actual_value VARCHAR(500),
    passed BOOLEAN,
    severity VARCHAR(20) CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    execution_id VARCHAR(100),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- ============================================================================
-- AUTOMATION FUNCTIONS (Stored Procedures)
-- ============================================================================

-- Function to auto-log batch execution start
CREATE OR REPLACE FUNCTION control.log_batch_start(
    p_pipeline_name VARCHAR,
    p_execution_id VARCHAR,
    p_task_name VARCHAR,
    p_table_name VARCHAR
) RETURNS BIGINT AS $$
DECLARE
    v_audit_id BIGINT;
BEGIN
    INSERT INTO control.audit_log (
        pipeline_name, execution_id, task_name, table_name, status, started_at
    ) VALUES (
        p_pipeline_name, p_execution_id, p_task_name, p_table_name, 'STARTED', CURRENT_TIMESTAMP
    ) RETURNING audit_id INTO v_audit_id;
    
    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

-- Function to auto-log batch completion
CREATE OR REPLACE FUNCTION control.log_batch_complete(
    p_audit_id BIGINT,
    p_status VARCHAR,
    p_rows_processed BIGINT,
    p_error_message TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE control.audit_log
    SET 
        status = p_status,
        rows_processed = p_rows_processed,
        completed_at = CURRENT_TIMESTAMP,
        duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))::INTEGER,
        error_message = p_error_message
    WHERE audit_id = p_audit_id;
END;
$$ LANGUAGE plpgsql;

-- UPDATED: Function to auto-update watermark (Supports both Numeric and Date types)
CREATE OR REPLACE FUNCTION control.update_watermark(
    p_table_name VARCHAR,
    p_last_processed_id BIGINT DEFAULT NULL,
    p_last_processed_date DATE DEFAULT NULL,
    p_last_processed_timestamp TIMESTAMP DEFAULT NULL,
    p_incremental_type VARCHAR DEFAULT 'numeric',
    p_incremental_column VARCHAR DEFAULT NULL,
    p_safety_margin_minutes INT DEFAULT NULL,
    p_safety_margin_rows INT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- Try to update existing record first (For Incremental Loads)
    UPDATE control.watermarks
    SET 
        last_processed_id = COALESCE(p_last_processed_id, last_processed_id),
        last_processed_date = COALESCE(p_last_processed_date, last_processed_date),
        last_processed_timestamp = COALESCE(p_last_processed_timestamp, last_processed_timestamp),
        incremental_type = COALESCE(p_incremental_type, incremental_type),
        incremental_column = COALESCE(p_incremental_column, incremental_column),
        safety_margin_minutes = COALESCE(p_safety_margin_minutes, safety_margin_minutes),
        safety_margin_rows = COALESCE(p_safety_margin_rows, safety_margin_rows),
        updated_at = CURRENT_TIMESTAMP
    WHERE table_name = p_table_name;
    
    -- If no record was updated (table not found), insert a new one (For Initial Loads)
    IF NOT FOUND THEN
        INSERT INTO control.watermarks (
            table_name,
            last_processed_id,
            last_processed_date,
            last_processed_timestamp,
            incremental_type,
            incremental_column,
            safety_margin_minutes,
            safety_margin_rows
        ) VALUES (
            p_table_name,
            p_last_processed_id,
            p_last_processed_date,
            p_last_processed_timestamp,
            COALESCE(p_incremental_type, 'numeric'),
            p_incremental_column,
            COALESCE(p_safety_margin_minutes, 120),
            COALESCE(p_safety_margin_rows, 10000)
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PERFORMANCE OPTIMIZATION (INDEXES)
-- ============================================================================

-- Indexes for Audit Log (To speed up queries and dashboards)
CREATE INDEX IF NOT EXISTS idx_audit_table_name ON control.audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_status ON control.audit_log(status);
CREATE INDEX IF NOT EXISTS idx_audit_started_at ON control.audit_log(started_at);
CREATE INDEX IF NOT EXISTS idx_audit_pipeline ON control.audit_log(pipeline_name);

-- Indexes for Data Quality Metrics
CREATE INDEX IF NOT EXISTS idx_dqm_table_name ON control.data_quality_metrics(table_name);
CREATE INDEX IF NOT EXISTS idx_dqm_severity ON control.data_quality_metrics(severity);

-- Indexes for Watermarks (For faster lookups during pipeline execution)
CREATE INDEX IF NOT EXISTS idx_watermarks_updated_at ON control.watermarks(updated_at);
CREATE INDEX IF NOT EXISTS idx_watermarks_type ON control.watermarks(incremental_type);