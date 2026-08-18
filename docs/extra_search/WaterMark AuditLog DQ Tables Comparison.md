## Difference Between Watermark, Audit Log, and Data Quality Metrics Tables

These three tables serve different purposes in your ETL/ELT pipeline. Here's a detailed breakdown:

---

## 1. **Watermarks Table** (Incremental Loading Control)

### **Purpose**: 
Tracks **where you left off** in incremental data processing to avoid reprocessing the same data.

### **What it stores**:
- Last processed ID/timestamp for each source table
- Safety margins to handle late-arriving data
- Which column is used for incremental extraction

### **When to use**:
- **Every incremental load** - to determine what new data to fetch
- **Pipeline start** - to know the starting point
- **After successful loads** - to update the checkpoint

### **Example scenario**:
```sql
-- Before loading new orders, check watermark
SELECT last_processed_id 
FROM control.watermarks 
WHERE table_name = 'bronze.orders';
-- Returns: 1500000 (last order key processed)

-- Load only orders with o_orderkey > 1500000
SELECT * FROM source.orders 
WHERE o_orderkey > 1500000;

-- After successful load, update watermark
UPDATE control.watermarks 
SET last_processed_id = 2000000 
WHERE table_name = 'bronze.orders';
```

### **Key features**:
- **Safety margins** - Handle late-arriving data (e.g., look back 2 hours)
- **Multiple strategies** - Can use IDs, timestamps, or both
- **Resilient** - Survives pipeline failures

---

## 2. **Audit Log Table** (Execution Tracking)

### **Purpose**:
Tracks **what happened during each pipeline execution** - who ran what, when, and what was the outcome.

### **What it stores**:
- Each execution's metadata (ID, start time, end time)
- Task-level status (SUCCESS/FAILED/STARTED)
- Row counts processed
- Error messages and codes
- Performance metrics (duration)

### **When to use**:
- **Every pipeline run** - log start and completion
- **Error investigation** - to understand what went wrong
- **Performance monitoring** - track execution times
- **Compliance** - maintain execution history
- **SLAs** - measure if pipelines meet SLAs

### **Example scenario**:
```sql
-- Start of pipeline
audit_id = log_batch_start('daily_sales', 'exec_20230321_001', 'load_orders', 'bronze.orders');

-- Run the pipeline...

-- On success
log_batch_complete(audit_id, 'SUCCESS', 50000);

-- On failure
log_batch_complete(audit_id, 'FAILED', 0, 'Connection timeout to source DB');
```

### **Key features**:
- **Chain of custody** - complete execution history
- **Troubleshooting** - error messages and stack traces
- **SLA monitoring** - track execution times
- **Root cause analysis** - correlate failures across tasks

---

## 3. **Data Quality Metrics Table** (Data Validation)

### **Purpose**:
Tracks **how good the data is** - measures data quality against business rules.

### **What it stores**:
- Quality checks performed (null counts, uniqueness, ranges, etc.)
- Pass/fail results for each check
- Severity levels (INFO → CRITICAL)
- Actual vs. expected values

### **When to use**:
- **After data loads** - validate data quality
- **Before critical transformations** - ensure input quality
- **Data profiling** - understand data characteristics
- **Anomaly detection** - identify data drift
- **Data contract validation** - enforce schema and business rules

### **Example scenario**:
```sql
-- Check for null keys in orders
INSERT INTO control.data_quality_metrics 
(table_name, check_name, metric_type, expected_value, actual_value, passed, severity)
SELECT 
    'bronze.orders',
    'null_order_keys',
    'null_check',
    '0',
    COUNT(*)::VARCHAR,
    COUNT(*) = 0,
    'CRITICAL'
FROM bronze.orders 
WHERE o_orderkey IS NULL;

-- Check for negative prices
INSERT INTO control.data_quality_metrics 
(table_name, check_name, metric_type, expected_value, actual_value, passed, severity)
SELECT 
    'bronze.orders',
    'negative_prices',
    'range_check',
    '>= 0',
    COUNT(*)::VARCHAR,
    COUNT(*) = 0,
    'ERROR'
FROM bronze.orders 
WHERE o_totalprice < 0;
```

### **Key features**:
- **Business rule validation** - ensures data meets requirements
- **Early warning system** - detect quality issues before they propagate
- **Trend analysis** - track quality over time
- **Data trust** - provide confidence metrics to stakeholders

---

## Comparison Table

| Aspect | **Watermarks** | **Audit Log** | **Data Quality Metrics** |
|--------|---------------|---------------|-------------------------|
| **Primary Purpose** | Incremental loading control | Execution tracking | Data validation |
| **Updated** | After successful loads | Every pipeline run | After data validation |
| **Query Pattern** | Single record per table | Many records per execution | Many records per table |
| **Used For** | Determining what to load | Troubleshooting failures | Ensuring data correctness |
| **Data Stored** | Checkpoint positions | Execution metadata | Quality metrics |
| **Retention** | Permanent (single record) | Long-term (for audits) | Medium-term (for trends) |
| **Business Impact** | Performance & efficiency | Operations & SLAs | Data trust & reliability |

---

## Real-World Usage Flow

Here's how all three work together in a typical pipeline:

```sql
-- 1. Check watermark to know what to load
DECLARE 
    v_last_id BIGINT;
    v_audit_id BIGINT;
    v_row_count BIGINT;
BEGIN
    -- Get last processed ID
    SELECT last_processed_id INTO v_last_id 
    FROM control.watermarks 
    WHERE table_name = 'bronze.orders';
    
    -- 2. Start audit log entry
    v_audit_id := control.log_batch_start(
        'daily_etl', 
        'exec_001', 
        'load_orders', 
        'bronze.orders'
    );
    
    -- 3. Load incremental data
    INSERT INTO bronze.orders
    SELECT * FROM source.orders 
    WHERE o_orderkey > v_last_id;
    
    GET DIAGNOSTICS v_row_count = ROW_COUNT;
    
    -- 4. Run data quality checks
    INSERT INTO control.data_quality_metrics
    SELECT 
        'bronze.orders',
        'key_uniqueness',
        'uniqueness_check',
        '0 duplicates',
        COUNT(*)::VARCHAR,
        COUNT(*) = 0,
        'CRITICAL'
    FROM (
        SELECT o_orderkey, COUNT(*) 
        FROM bronze.orders 
        GROUP BY o_orderkey 
        HAVING COUNT(*) > 1
    ) duplicates;
    
    -- 5. Update watermark if quality checks pass
    IF NOT EXISTS (
        SELECT 1 FROM control.data_quality_metrics 
        WHERE table_name = 'bronze.orders' 
        AND passed = false 
        AND severity = 'CRITICAL'
    ) THEN
        -- Update watermark
        UPDATE control.watermarks 
        SET last_processed_id = (SELECT MAX(o_orderkey) FROM bronze.orders)
        WHERE table_name = 'bronze.orders';
        
        -- Log success
        control.log_batch_complete(v_audit_id, 'SUCCESS', v_row_count);
    ELSE
        -- Log failure due to quality issues
        control.log_batch_complete(v_audit_id, 'FAILED', v_row_count, 
            'Data quality checks failed');
        RAISE EXCEPTION 'Quality checks failed - rolling back';
    END IF;
END;
```

## When to Query Each Table:

### **Watermarks**:
- **Daily**: "Where did we last load data from?"
- **During troubleshooting**: "Is the watermark stuck?"
- **Capacity planning**: "How much data are we loading each run?"

### **Audit Log**:
- **After failures**: "Why did yesterday's pipeline fail?"
- **Performance reviews**: "How long did last night's load take?"
- **Compliance**: "Who ran the pipeline and when?"
- **SLA monitoring**: "Are we meeting our SLAs?"

### **Data Quality Metrics**:
- **Before reporting**: "Is the data ready for consumption?"
- **Data governance**: "What's the quality trend over time?"
- **Issue detection**: "When did data quality start degrading?"
- **Data contract validation**: "Are we meeting quality SLAs?"

## Summary

- **Watermarks** = "Where are we?" (Checkpoint)
- **Audit Log** = "What happened?" (Process tracking)
- **Data Quality** = "Is it good?" (Quality assurance)

Together, they form a complete observability stack for your data pipeline!