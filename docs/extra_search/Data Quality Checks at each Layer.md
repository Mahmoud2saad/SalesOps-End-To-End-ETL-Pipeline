# Comprehensive Data Quality Checklist for Medallion Architecture

This checklist ensures data quality progressively improves through each layer: **Bronze (Raw)** → **Silver (Cleansed/Validated)** → **Gold (Aggregated/Business-Ready)** .

---

## Quality Dimensions Framework

All checks align with standard data quality dimensions:
- **Completeness** - No missing values
- **Uniqueness** - No duplicates
- **Validity** - Conforms to format/rules
- **Accuracy** - Correct values
- **Consistency** - Aligned across tables
- **Integrity** - Referential relationships intact
- **Timeliness** - Freshness/recency
- **Reasonability** - Logical ranges/patterns

---

## 1. BRONZE LAYER (Raw/Landing Zone)

### Purpose
Ensure **data is captured completely and accurately** from source systems before any transformation.

### 1.1 Ingestion Quality

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **B-001** | Record Count Match | Verify extracted row count matches source row count | Compare source count vs staged count |
| **B-002** | Data Volume Anomaly | Detect sudden spikes/drops in data volume | `ABS(COUNT(*) - LAG(COUNT(*)) OVER()) > (0.2 * COUNT(*))` |
| **B-003** | File Completeness | All expected files/partitions arrived | Check file manifest against expected list |
| **B-004** | Load Timestamp | All records have extraction timestamp | `WHERE extract_timestamp IS NULL` |
| **B-005** | Source System Tracking | Each record traceable to source | Verify `source_system`, `source_file`, `batch_id` populated |

### 1.2 Structural Integrity

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **B-006** | Schema Compliance | All columns present with correct data types | Validate against expected schema definition |
| **B-007** | Character Encoding | No invalid characters in text fields | `WHERE column ~ '[^\x00-\x7F]'` (detect non-ASCII) |
| **B-008** | Column Count | No missing or extra columns | Verify number of columns matches expectation |
| **B-009** | Partition Structure | Data correctly partitioned | Check partition directory structure |

### 1.3 Initial Validation

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **B-010** | Nullable Columns Check | Columns marked NOT NULL have no nulls | `WHERE required_column IS NULL` |
| **B-011** | Primary Key Uniqueness | Source primary keys are unique in staging | `COUNT(*) > 1 GROUP BY pk_columns` |
| **B-012** | Data Type Boundaries | Numeric values don't exceed type limits | `WHERE amount > 999999999999` |
| **B-013** | Date Format Validation | All dates in expected format | `WHERE date_column !~ '^\d{4}-\d{2}-\d{2}$'` |

---

## 2. SILVER LAYER (Cleansed/Validated)

### Purpose
Ensure data is **clean, consistent, and ready for business logic** application.

### 2.1 Completeness & Null Handling

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **S-001** | Critical Field Completeness | Business-critical fields 100% populated | `SUM(CASE WHEN critical_field IS NULL THEN 1 ELSE 0 END) = 0` |
| **S-002** | Acceptable Null Threshold | Optional fields within acceptable null % | `null_percentage < 5%` for optional fields |
| **S-003** | Default Value Validation | Default values not used inappropriately | `WHERE field = 'UNKNOWN' AND business_rules_require_value` |
| **S-004** | Blank String Handling | Empty strings converted to NULL consistently | `WHERE field = ''` |

### 2.2 Uniqueness & Duplication

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **S-005** | Business Key Uniqueness | Surrogate keys unique | `COUNT(*) > 1 GROUP BY surrogate_key` |
| **S-006** | Natural Key Uniqueness | Natural/business keys unique where required | `COUNT(*) > 1 GROUP BY natural_key` |
| **S-007** | Duplicate Record Detection | No exact duplicate rows | `COUNT(*) > 1 GROUP BY *` |
| **S-008** | Fuzzy Duplicate Detection | Near-identical records flagged | Levenshtein distance on name fields |

### 2.3 Validity & Format

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **S-009** | Email Format | Valid email pattern | `WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'` |
| **S-010** | Phone Number Format | Standardized phone format | `WHERE phone !~ '^\+?[0-9\s\-\(\)]{10,20}$'` |
| **S-011** | Postal/ZIP Code | Valid format per country | `WHERE postal_code !~ '^\d{5}(-\d{4})?$'` (US) |
| **S-012** | Date Range Validity | Logical dates (not future, not too old) | `WHERE birth_date > CURRENT_DATE OR birth_date < '1900-01-01'` |
| **S-013** | Enum/Code Values | Values within allowed list | `WHERE status NOT IN ('ACTIVE', 'INACTIVE', 'PENDING')` |
| **S-014** | ID Format Validation | IDs follow expected pattern | `WHERE customer_id !~ '^CUST\d{10}$'` |

### 2.4 Accuracy & Range

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **S-015** | Numeric Range | Values within business rules | `WHERE discount BETWEEN 0 AND 1` |
| **S-016** | Negative Value Detection | Non-negative fields negative | `WHERE quantity < 0 OR price < 0` |
| **S-017** | Zero Value Detection | Zero values where inappropriate | `WHERE quantity = 0 AND order_status = 'SHIPPED'` |
| **S-018** | Outlier Detection | Statistical outliers flagged | `WHERE amount > (AVG(amount) + 3 * STDDEV(amount))` |
| **S-019** | Monetary Precision | Currency fields consistent decimals | `WHERE amount::TEXT !~ '^\d+\.\d{2}$'` |

### 2.5 Consistency

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **S-020** | Cross-Column Logic | Column relationships valid | `WHERE ship_date < order_date` (impossible) |
| **S-021** | Status Transitions | Valid state machine transitions | `WHERE status = 'SHIPPED' AND previous_status NOT IN ('PAID', 'PROCESSED')` |
| **S-022** | Categorical Consistency | Matching fields consistent | `WHERE country = 'USA' AND currency != 'USD'` |
| **S-023** | Calculated Field Validation | Computed fields match source | `WHERE total_amount != quantity * unit_price` |

### 2.6 Referential Integrity

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **S-024** | Foreign Key Validity | All FKs exist in parent table | `LEFT JOIN dim WHERE dim.key IS NULL` |
| **S-025** | Orphan Record Detection | Child records without parent | `WHERE NOT EXISTS (SELECT 1 FROM parent WHERE parent.id = child.fk)` |
| **S-026** | Cascade Consistency | Deletions/updates propagated correctly | Verify soft deletes handled consistently |
| **S-027** | Hierarchical Integrity | Self-referential keys valid | `WHERE manager_id NOT IN (SELECT employee_id FROM employees)` |

### 2.7 Temporal Consistency

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **S-028** | Slowly Changing Dimension Validity | SCD Type 2 effective dates don't overlap | `WHERE effective_date <= end_date` |
| **S-029** | Time Series Continuity | No gaps in sequential data | `WHERE LAG(end_date) OVER() < start_date` |
| **S-030** | Freshness | Data updated within SLA | `MAX(updated_at) < CURRENT_TIMESTAMP - INTERVAL '24 hours'` |

---

## 3. GOLD LAYER (Business-Ready/Aggregated)

### Purpose
Ensure data is **accurate, complete, and consistent** for business reporting and analytics.

### 3.1 Business Logic Validation

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **G-001** | Aggregation Consistency | Sum of children equals parent | `SUM(line_item.amount) = order.total_amount` |
| **G-002** | Calculation Accuracy | Derived metrics correct | Verify profit = revenue - cost across all records |
| **G-003** | Business Rule Compliance | All business rules satisfied | `WHERE customer_tier = 'PREMIUM' AND total_spent < 10000` |
| **G-004** | Hierarchy Rollup | Hierarchical aggregates consistent | `SUM(regional_sales) = total_sales` |

### 3.2 Grain Integrity

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **G-005** | Fact Table Grain | All rows at correct aggregation level | No duplicate combinations of dimension keys |
| **G-006** | Dimension Grain | Each dimension row unique | `COUNT(*) > 1 GROUP BY dimension_key` |
| **G-007** | Many-to-Many Validation | Bridge tables correctly implemented | Verify bridge counts match actual relationships |
| **G-008** | Slowly Changing Dimension Currency | Only one active record per business key | `COUNT(*) > 1 WHERE is_current = TRUE GROUP BY business_key` |

### 3.3 Measure Completeness

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **G-009** | Fact Table Row Count | Row count aligns with expected business volume | Compare to historical averages ± 20% |
| **G-010** | Measure Coverage | All required measures populated | `WHERE total_sales IS NULL AND order_status = 'COMPLETED'` |
| **G-011** | Metric Reasonability | KPIs within expected ranges | `WHERE profit_margin NOT BETWEEN 0.05 AND 0.95` |
| **G-012** | Zero Measure Detection | Zero values where non-zero expected | `WHERE revenue = 0 AND units_sold > 1000` |

### 3.4 Relationship Integrity

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **G-013** | Fact-to-Dimension Joinability | All facts join to dimensions | `LEFT JOIN dim WHERE dim.key IS NULL` |
| **G-014** | Conformed Dimension Consistency | Same dimension used across facts | Verify customer dimension matches across all fact tables |
| **G-015** | Star Schema Integrity | Fact tables only link to dimensions (not other facts) | No direct fact-to-fact joins |
| **G-016** | Foreign Key Usage | No unnecessary FKs in fact tables | Validate FK columns align with grain |

### 3.5 Historical Consistency

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **G-017** | Trend Consistency | Month-over-month changes within reason | `ABS(mom_change) < 200%` for key metrics |
| **G-018** | Cumulative Values Non-Decreasing | Running totals never decrease | `WHERE running_total < LAG(running_total) OVER()` |
| **G-019** | Year-over-Year Comparability | Same periods comparable | Verify calendar alignment |
| **G-020** | No Future Dates | All dates in fact tables <= current date | `WHERE transaction_date > CURRENT_DATE` |

### 3.6 Performance & Usability

| Check ID | Check Name | Description | SQL Example |
|----------|------------|-------------|-------------|
| **G-021** | Query Performance | All tables have appropriate indexes | Check index usage statistics |
| **G-022** | Partition Pruning | Queries leverage partitions | Verify WHERE clauses include partition keys |
| **G-023** | Column Statistics | Statistics updated for optimizer | `ANALYZE` after significant data changes |
| **G-024** | View Dependency Validation | All views reference existing objects | Check view definitions against current schema |

---

## 4. CROSS-LAYER QUALITY CHECKS

### 4.1 Lineage & Traceability

| Check ID | Check Name | Description |
|----------|------------|-------------|
| **C-001** | Row Count Traceability | Bronze → Silver → Gold row counts trackable |
| **C-002** | Data Lineage | Each Gold record traceable to source |
| **C-003** | Transformation Logic | Transformations documented and auditable |
| **C-004** | Code Versioning | All transformation code version controlled |

### 4.2 Performance SLA

| Check ID | Check Name | Description |
|----------|------------|-------------|
| **C-005** | Pipeline Duration | Bronze→Gold within SLA (e.g., < 2 hours) |
| **C-006** | Query Response Time | Dashboard queries < 5 seconds |
| **C-007** | Freshness SLA | Gold layer updated by 8 AM daily |
| **C-008** | Resource Utilization | CPU/Memory within thresholds |

### 4.3 Security & Compliance

| Check ID | Check Name | Description |
|----------|------------|-------------|
| **C-009** | PII Masking | Sensitive data properly masked/anonymized |
| **C-010** | Row-Level Security | Users only see authorized data |
| **C-011** | Audit Compliance | All access logged and retained |
| **C-012** | Retention Policy | Data retained according to policy |

---

## 5. IMPLEMENTATION MATRIX

| Quality Dimension | Bronze | Silver | Gold | Criticality |
|-------------------|--------|--------|------|-------------|
| **Completeness** | Basic NOT NULL | Business-critical fields 100% | Measure coverage | HIGH |
| **Uniqueness** | Source PK unique | Business keys unique | Grain integrity | HIGH |
| **Validity** | Data type only | Format validation | Business rule compliance | MEDIUM |
| **Accuracy** | Source mirror | Range checks | Calculation validation | CRITICAL |
| **Consistency** | None | Cross-column logic | Cross-fact consistency | HIGH |
| **Integrity** | None | Referential integrity | Star schema integrity | CRITICAL |
| **Timeliness** | Ingestion timestamp | Freshness SLA | Update SLA | MEDIUM |
| **Reasonability** | None | Outlier detection | Trend analysis | MEDIUM |

---

## 6. QUALITY THRESHOLDS BY SEVERITY

| Severity | Bronze | Silver | Gold | Action |
|----------|--------|--------|------|--------|
| **CRITICAL** | 0% tolerance | 0% tolerance | 0% tolerance | Stop pipeline, alert on-call |
| **ERROR** | < 0.1% | < 0.01% | < 0.001% | Log error, continue, notify team |
| **WARNING** | < 5% | < 1% | < 0.1% | Log warning, continue |
| **INFO** | Any | Any | Any | Log for monitoring only |

---

## 7. AUTOMATED QUALITY CHECK SQL TEMPLATE

```sql
-- Insert quality check results into control.data_quality_metrics
INSERT INTO control.data_quality_metrics (
    table_name,
    check_name,
    metric_type,
    expected_value,
    actual_value,
    passed,
    severity,
    execution_id,
    details
)
SELECT
    'gold.fact_orders' AS table_name,
    'G-001: Aggregation Consistency' AS check_name,
    'accuracy' AS metric_type,
    '0 mismatches' AS expected_value,
    COUNT(*)::VARCHAR || ' mismatches' AS actual_value,
    COUNT(*) = 0 AS passed,
    'CRITICAL' AS severity,
    'exec_20240328_001' AS execution_id,
    jsonb_build_object(
        'mismatch_count', COUNT(*),
        'sample_mismatches', jsonb_agg(
            jsonb_build_object(
                'order_key', order_key,
                'calculated_total', calculated_total,
                'stored_total', stored_total
            )
        ) FILTER (WHERE row_num <= 5)
    ) AS details
FROM (
    SELECT 
        o.order_key,
        o.total_price AS stored_total,
        SUM(li.extended_price * (1 - li.discount) * (1 + li.tax)) AS calculated_total,
        ROW_NUMBER() OVER () AS row_num
    FROM gold.fact_orders o
    JOIN gold.fact_line_items li ON o.order_key = li.order_key
    GROUP BY o.order_key, o.total_price
    HAVING ABS(o.total_price - SUM(li.extended_price * (1 - li.discount) * (1 + li.tax))) > 0.01
) mismatches;
```

---

This comprehensive checklist ensures your medallion architecture produces **trustworthy, reliable, and business-ready data** at every stage of the pipeline. Implement these checks progressively, starting with CRITICAL severity items in each layer, then expand coverage over time.