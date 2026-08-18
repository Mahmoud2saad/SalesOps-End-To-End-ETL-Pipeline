## Control Schema Explanation: Watermarks, Audit Log, and Data Quality Metrics

These three tables form the backbone of a **production-grade ETL/ELT pipeline** with built-in observability, reliability, and data quality management. Let me explain each one's purpose and usage.

---

## 1. Watermarks Table

### **Purpose**
Tracks **incremental loading progress** to enable efficient, repeatable data extraction without reprocessing historical data.

### **How It Works**
The watermark acts as a "bookmark" indicating how much data has already been processed from source systems.

### **Columns Explained**

| Column | Purpose | Example Usage |
|--------|---------|---------------|
| `table_name` | Identifies which source/destination table this watermark tracks | 'customers', 'orders', 'line_items' |
| `last_processed_id` | For integer-based incremental columns (auto-increment IDs) | Last customer_id processed = 15234 |
| `last_processed_timestamp` | For timestamp-based incremental columns | Last order_date processed = '2024-01-15 23:59:59' |
| `last_processed_value` | Generic field for other incremental strategies | Last processed cursor value |
| `safety_margin_minutes` | Buffer to handle late-arriving data (look back X minutes) | 120 minutes (2 hours) |
| `safety_margin_rows` | Buffer for ID-based increments to handle gaps | Look back 10,000 rows for missed IDs |
| `incremental_column` | Specifies which column drives the incremental logic | 'last_processed_timestamp' or 'last_processed_id' |
| `updated_at` | Tracks when watermark was last updated | For monitoring pipeline freshness |
| `updated_by` | Identifies which process/user updated the watermark | 'etl_pipeline_v2' or 'dbt_run_123' |

### **Usage Example**
```sql
-- Extract new orders after the last processed timestamp + safety margin
SELECT * FROM source.orders
WHERE order_date > (
    SELECT last_processed_timestamp - INTERVAL '120 minutes'
    FROM control.watermarks 
    WHERE table_name = 'orders'
)
ORDER BY order_date;
```

---

## 2. Audit Log Table

### **Purpose**
Provides **end-to-end pipeline observability** by tracking every execution, including success/failure, processing metrics, and timing.

### **How It Works**
Each pipeline run gets a unique `execution_id`, and each step/task gets an `audit_id` for granular monitoring.

### **Columns Explained**

| Column | Purpose | Example Usage |
|--------|---------|---------------|
| `audit_id` | Unique identifier for each task/step execution | 1001, 1002, 1003 |
| `pipeline_name` | Name of the overall pipeline | 'customer_360_etl', 'order_facts_daily' |
| `execution_id` | Unique ID for a complete pipeline run | 'exec_20240115_080000' |
| `task_name` | Specific task within the pipeline | 'extract_customers', 'transform_silver', 'load_gold' |
| `table_name` | Table being processed | 'stg_customers', 'dim_customer' |
| `status` | Current state of the task | 'STARTED', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED' |
| `rows_input` | Number of rows read from source | 1,234,567 |
| `rows_output` | Number of rows written to target | 1,198,321 |
| `rows_processed` | Number of rows processed (successful) | 1,200,000 |
| `error_code` | Standardized error code if failed | 'SQLSTATE-23505' (duplicate key) |
| `error_message` | Detailed error message | 'Violation of unique constraint on customer_key' |
| `started_at` | Task start timestamp | 2024-01-15 08:00:00.123 |
| `completed_at` | Task completion timestamp | 2024-01-15 08:05:23.456 |
| `duration_seconds` | Calculated runtime | 323 seconds |
| `metadata` | Flexible JSON field for additional context | `{"batch_id": "123", "retry_count": 0, "source_system": "postgres_prod"}` |

### **Usage Example**
```sql
-- Get daily pipeline health summary
SELECT 
    DATE(started_at) as run_date,
    pipeline_name,
    COUNT(DISTINCT execution_id) as total_runs,
    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_tasks,
    AVG(duration_seconds) as avg_duration_seconds
FROM control.audit_log
WHERE started_at > CURRENT_DATE - INTERVAL '30 days'
GROUP BY run_date, pipeline_name
ORDER BY run_date DESC;
```

---

## 3. Data Quality Metrics Table

### **Purpose**
Captures **automated data quality checks** to ensure data meets business requirements before being used in reporting/analytics.

### **How It Works**
Quality checks run automatically after each pipeline stage, storing results for monitoring, alerting, and compliance.

### **Columns Explained**

| Column | Purpose | Example Usage |
|--------|---------|---------------|
| `metric_id` | Unique identifier for each quality check execution | 5001, 5002 |
| `table_name` | Table where quality check was performed | 'fact_orders', 'dim_customer' |
| `check_name` | Name of the specific quality rule | 'not_null_customer_key', 'unique_order_key' |
| `metric_type` | Category of quality check | 'completeness', 'uniqueness', 'accuracy', 'freshness', 'consistency' |
| `expected_value` | What the data should meet | '100%', '0', '> 1000' |
| `actual_value` | What was actually measured | '98.5%', '5 nulls', '1250' |
| `passed` | Boolean indicating if check succeeded | TRUE or FALSE |
| `severity` | How critical is this rule | 'INFO', 'WARNING', 'ERROR', 'CRITICAL' |
| `execution_id` | Links back to audit_log for traceability | 'exec_20240115_080000' |
| `checked_at` | When the quality check ran | 2024-01-15 08:10:00 |
| `details` | Flexible JSON for check-specific context | `{"null_count": 12, "total_rows": 10000, "null_percentage": 0.12}` |

### **Common Data Quality Checks**

| Check Type | Example Rule | SQL Logic |
|------------|--------------|----------|
| **Completeness** | No NULLs in customer_key | `COUNT(*) WHERE customer_key IS NULL` |
| **Uniqueness** | All order_keys are unique | `COUNT(*) != COUNT(DISTINCT order_key)` |
| **Referential Integrity** | All customer_keys exist in dim_customer | `LEFT JOIN WHERE dim.customer_key IS NULL` |
| **Freshness** | Data updated within last 24 hours | `MAX(updated_at) < CURRENT_DATE - 1` |
| **Range Validation** | Discount between 0 and 1 | `discount < 0 OR discount > 1` |
| **Volume Monitoring** | Row count within expected range | `COUNT(*) BETWEEN expected_min AND expected_max` |
| **Pattern Matching** | Email format validation | `email NOT LIKE '%@%.%'` |

### **Usage Example**
```sql
-- Alert on critical quality failures
SELECT 
    table_name,
    check_name,
    actual_value,
    expected_value,
    checked_at
FROM control.data_quality_metrics
WHERE passed = FALSE 
  AND severity IN ('ERROR', 'CRITICAL')
  AND checked_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY checked_at DESC;

-- Track quality trends over time
SELECT 
    DATE(checked_at) as check_date,
    table_name,
    COUNT(*) as total_checks,
    AVG(CASE WHEN passed THEN 100 ELSE 0 END) as pass_rate_percentage
FROM control.data_quality_metrics
WHERE checked_at > CURRENT_DATE - INTERVAL '30 days'
GROUP BY check_date, table_name
ORDER BY check_date DESC;
```

---

## Automation Functions Explained

### **`control.log_batch_start()`**
Creates an audit record when a task begins, returning the `audit_id` for later updates.

### **`control.log_batch_complete()`**
Updates the audit record with completion status, row counts, and duration.

### **`control.update_watermark()`**
Performs an **UPSERT** operation (UPDATE or INSERT) on the watermark table:
- If the table exists → updates it (incremental loads)
- If it doesn't exist → inserts a new record (initial loads)

This ensures both initial and incremental loads are handled by the same function.

---

## Production Usage Flow

```sql
-- 1. Start pipeline execution
DO $$
DECLARE
    v_audit_id BIGINT;
    v_execution_id VARCHAR(100) := 'exec_' || TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS');
BEGIN
    -- 2. Log task start
    v_audit_id := control.log_batch_start(
        'daily_order_pipeline',
        v_execution_id,
        'extract_orders',
        'stg_orders'
    );
    
    -- 3. Check watermark for incremental extraction
    -- (Your ETL logic here)
    
    -- 4. Update watermark after successful extraction
    PERFORM control.update_watermark(
        'orders',
        15234,  -- last_processed_id
        CURRENT_TIMESTAMP,  -- last_processed_timestamp
        120,  -- safety_margin_minutes
        10000  -- safety_margin_rows
    );
    
    -- 5. Log successful completion
    PERFORM control.log_batch_complete(
        v_audit_id,
        'SUCCESS',
        10000,  -- rows_processed
        NULL  -- error_message
    );
    
EXCEPTION WHEN OTHERS THEN
    -- 6. Log failure
    PERFORM control.log_batch_complete(
        v_audit_id,
        'FAILED',
        0,
        SQLERRM
    );
    RAISE;
END;
$$;
```

---

## Benefits of This Approach

1. **Idempotent Pipelines** - Watermarks enable safe reprocessing without duplication
2. **Observability** - Complete audit trail for debugging and compliance
3. **Proactive Quality Management** - Catch data issues before they reach analytics
4. **SLA Monitoring** - Track pipeline performance and freshness
5. **Root Cause Analysis** - Link failures to specific tasks and executions
6. **Automated Recovery** - Safety margins handle late-arriving data gracefully

This control layer transforms your data warehouse from a simple storage system into a **managed, reliable, and trustworthy data platform**.