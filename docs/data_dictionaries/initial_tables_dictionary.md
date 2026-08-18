# 📊 Data Dictionary

## 🗄️ Source Database (PostgreSQL - `data_platform_db`)

### Schema: `bronze` (Raw/Staging Layer)

---

#### **Table: `bronze.region`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `r_regionkey` | BIGINT | PRIMARY KEY | Unique identifier for geographic region |
| `r_name` | VARCHAR(25) | NOT NULL | Region name (e.g., AFRICA, AMERICA, ASIA, EUROPE, MIDDLE EAST) |
| `r_comment` | VARCHAR(152) | | Descriptive comment about the region |
| `_loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit column - timestamp when record was loaded |

**Primary Key:** `r_regionkey`  


---

#### **Table: `bronze.nation`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `n_nationkey` | BIGINT | PRIMARY KEY | Unique identifier for nation/country |
| `n_name` | VARCHAR(25) | NOT NULL | Nation name (e.g., ALGERIA, ARGENTINA, BRAZIL, CANADA) |
| `n_regionkey` | BIGINT | FOREIGN KEY → `bronze.region(r_regionkey)` | References the region containing this nation |
| `n_comment` | VARCHAR(152) | | Descriptive comment about the nation |
| `_loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit column - timestamp when record was loaded |

**Primary Key:** `n_nationkey`  
**Foreign Key:** `n_regionkey` references `region(r_regionkey)`  


---

#### **Table: `bronze.customer`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `c_custkey` | BIGINT | PRIMARY KEY | Unique customer identifier |
| `c_name` | VARCHAR(25) | NOT NULL | Customer's name (format: Customer#000000001) |
| `c_address` | VARCHAR(40) | NOT NULL | Street address of customer |
| `c_nationkey` | BIGINT | FOREIGN KEY → `bronze.nation(n_nationkey)` | Nation where customer resides |
| `c_phone` | CHAR(15) | NOT NULL | Phone number (format: 10-123-456-7890) |
| `c_acctbal` | DECIMAL(15,2) | DEFAULT 0.00 | Current account balance |
| `c_mktsegment` | VARCHAR(10) | NOT NULL | Market segment (AUTOMOBILE, BUILDING, FURNITURE, HOUSEHOLD, MACHINERY) |
| `c_comment` | VARCHAR(117) | | Customer comment/notes |
| `_loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit column - timestamp when record was loaded |

**Primary Key:** `c_custkey`  
**Foreign Key:** `c_nationkey` references `nation(n_nationkey)`  


---

#### **Table: `bronze.supplier`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `s_suppkey` | BIGINT | PRIMARY KEY | Unique supplier identifier |
| `s_name` | VARCHAR(25) | NOT NULL | Supplier name (format: Supplier#000000001) |
| `s_address` | VARCHAR(40) | NOT NULL | Street address of supplier |
| `s_nationkey` | BIGINT | FOREIGN KEY → `bronze.nation(n_nationkey)` | Nation where supplier is located |
| `s_phone` | CHAR(15) | NOT NULL | Contact phone number |
| `s_acctbal` | DECIMAL(15,2) | DEFAULT 0.00 | Current account balance |
| `s_comment` | VARCHAR(101) | | Supplier comment/notes |
| `_loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit column - timestamp when record was loaded |

**Primary Key:** `s_suppkey`  
**Foreign Key:** `s_nationkey` references `nation(n_nationkey)`  


---

#### **Table: `bronze.part`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `p_partkey` | BIGINT | PRIMARY KEY | Unique part identifier |
| `p_name` | VARCHAR(55) | NOT NULL | Part name/description |
| `p_mfgr` | VARCHAR(25) | NOT NULL | Manufacturer name (Manufacturer#1-5) |
| `p_brand` | VARCHAR(10) | NOT NULL | Brand name (Brand#1-5) |
| `p_type` | VARCHAR(25) | NOT NULL | Part type (e.g., STANDARD, SMALL, MEDIUM, LARGE, ECONOMY, PROMO) |
| `p_size` | INTEGER | NOT NULL | Size category (1-50) |
| `p_container` | VARCHAR(10) | NOT NULL | Container type (CASE, BOX, BAG, JAR, PKG, WRAP, DRUM, CAN) |
| `p_retailprice` | DECIMAL(15,2) | NOT NULL | Retail price of the part |
| `p_comment` | VARCHAR(23) | | Part comment/notes |
| `_loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit column - timestamp when record was loaded |

**Primary Key:** `p_partkey`  


---

#### **Table: `bronze.orders`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `o_orderkey` | BIGINT | PRIMARY KEY | Unique order identifier |
| `o_custkey` | BIGINT | FOREIGN KEY → `bronze.customer(c_custkey)` | Customer who placed the order |
| `o_orderstatus` | CHAR(1) | NOT NULL | Order status (F = fulfilled, O = open, P = pending) |
| `o_totalprice` | DECIMAL(15,2) | NOT NULL | Total order amount |
| `o_orderdate` | DATE | NOT NULL | Date order was placed |
| `o_orderpriority` | CHAR(15) | NOT NULL | Priority (1-URGENT, 2-HIGH, 3-MEDIUM, 4-NOT SPECIFIED, 5-LOW) |
| `o_clerk` | CHAR(15) | NOT NULL | Clerk who processed the order |
| `o_shippriority` | INTEGER | NOT NULL | Shipping priority (0 = lowest, 1 = highest) |
| `o_comment` | VARCHAR(79) | | Order comment/notes |
| `_loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit column - timestamp when record was loaded |

**Primary Key:** `o_orderkey`  
**Foreign Key:** `o_custkey` references `customer(c_custkey)`  


---

#### **Table: `bronze.partsupp`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `ps_id` | BIGINT | PRIMARY KEY | Unique identifier for part-supplier relationship |
| `ps_partkey` | BIGINT | FOREIGN KEY → `bronze.part(p_partkey)` | Part being supplied |
| `ps_suppkey` | BIGINT | FOREIGN KEY → `bronze.supplier(s_suppkey)` | Supplier providing the part |
| `ps_availqty` | INTEGER | NOT NULL | Available quantity in stock |
| `ps_supplycost` | DECIMAL(15,2) | NOT NULL | Cost per unit from supplier |
| `ps_comment` | VARCHAR(199) | | Part-supplier relationship comments |
| `_loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit column - timestamp when record was loaded |

**Primary Key:** `ps_id`  
**Foreign Keys:** `ps_partkey` references `part(p_partkey)`, `ps_suppkey` references `supplier(s_suppkey)`  


---

#### **Table: `bronze.lineitem`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `l_id` | BIGINT | PRIMARY KEY | Unique identifier for line item |
| `l_orderkey` | BIGINT | FOREIGN KEY → `bronze.orders(o_orderkey)` | Parent order identifier |
| `l_partkey` | BIGINT | FOREIGN KEY → `bronze.part(p_partkey)` | Part being ordered |
| `l_suppkey` | BIGINT | FOREIGN KEY → `bronze.supplier(s_suppkey)` | Supplier of the part |
| `l_linenumber` | INTEGER | NOT NULL | Line number within the order (1-based) |
| `l_quantity` | DECIMAL(15,2) | NOT NULL | Quantity ordered |
| `l_extendedprice` | DECIMAL(15,2) | NOT NULL | Price * quantity (before discount) |
| `l_discount` | DECIMAL(15,2) | NOT NULL | Discount applied (0.00-1.00) |
| `l_tax` | DECIMAL(15,2) | NOT NULL | Tax applied (0.00-1.00) |
| `l_returnflag` | CHAR(1) | NOT NULL | Return flag (A = returned, N = not returned, R = returned but replaced) |
| `l_linestatus` | CHAR(1) | NOT NULL | Line status (F = fulfilled, O = open) |
| `l_shipdate` | DATE | NOT NULL | Date item was shipped |
| `l_commitdate` | DATE | NOT NULL | Date item was committed for shipment |
| `l_receiptdate` | DATE | NOT NULL | Date item was received |
| `l_shipinstruct` | CHAR(25) | NOT NULL | Shipping instructions |
| `l_shipmode` | CHAR(10) | NOT NULL | Shipping mode (AIR, REG AIR, SHIP, TRUCK, MAIL, FOB, RAIL) |
| `l_comment` | VARCHAR(44) | | Line item comment |
| `_loaded_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit column - timestamp when record was loaded |

**Primary Key:** `l_id`  
**Foreign Keys:** `l_orderkey` references `orders(o_orderkey)`, `l_partkey` references `part(p_partkey)`, `l_suppkey` references `supplier(s_suppkey)`  


---

## 🗄️ Control Database (PostgreSQL - `control`)

### Schema: `control`

---

#### **Table: `control.watermarks`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `table_name` | VARCHAR(50) | PRIMARY KEY | Name of the source table being tracked (e.g., 'bronze.orders') |
| `last_processed_id` | BIGINT | DEFAULT 0 | Last processed record ID (for ID-based incremental loads) |
| `last_processed_timestamp` | TIMESTAMP | | Last processed timestamp (for timestamp-based incremental loads) |
| `last_processed_value` | VARCHAR(100) | | Last processed value for non-numeric keys |
| `safety_margin_minutes` | INT | DEFAULT 120 | Minutes to look back for late-arriving data |
| `safety_margin_rows` | INT | DEFAULT 10000 | Number of rows to look back for safety |
| `incremental_column` | VARCHAR(50) | DEFAULT 'last_processed_timestamp' | Column name used for incremental extraction |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when watermark was last updated |
| `updated_by` | VARCHAR(50) | DEFAULT CURRENT_USER | User/process that last updated the watermark |

**Primary Key:** `table_name`  
**Purpose:** Tracks incremental extraction progress for each source table  
**Usage:** Checked before each extraction to determine what data to fetch

---

#### **Table: `control.audit_log`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `audit_id` | BIGSERIAL | PRIMARY KEY | Unique audit record identifier |
| `pipeline_name` | VARCHAR(100) | | Name of the pipeline (e.g., 'orders_etl', 'monitoring') |
| `execution_id` | VARCHAR(100) | | Unique identifier for pipeline execution (UUID format) |
| `task_name` | VARCHAR(100) | | Name of the specific task within the pipeline |
| `table_name` | VARCHAR(100) | | Table being processed by this task |
| `status` | VARCHAR(20) | CHECK (status IN ('STARTED', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')) | Current status of the task |
| `rows_input` | BIGINT | | Number of rows read as input |
| `rows_output` | BIGINT | | Number of rows produced as output |
| `rows_processed` | BIGINT | | Number of rows successfully processed |
| `error_code` | VARCHAR(20) | | Error code if task failed |
| `error_message` | TEXT | | Detailed error message if task failed |
| `started_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when task started |
| `completed_at` | TIMESTAMP | | Timestamp when task completed |
| `duration_seconds` | INTEGER | | Duration in seconds (calculated from started_at to completed_at) |
| `metadata` | JSONB | | Additional metadata (e.g., parameters, context, query information) |

**Primary Key:** `audit_id`  

---

#### **Table: `control.data_quality_metrics`**
| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| `metric_id` | BIGSERIAL | PRIMARY KEY | Unique quality metric identifier |
| `table_name` | VARCHAR(100) | NOT NULL | Table being validated |
| `check_name` | VARCHAR(100) | NOT NULL | Name of the quality check (e.g., 'null_order_keys', 'negative_prices') |
| `metric_type` | VARCHAR(50) | | Type of check: 'null_check', 'uniqueness', 'range_check', 'referential_integrity', 'business_rule', 'schema_validation' |
| `expected_value` | VARCHAR(500) | | Expected value for the metric (e.g., '0', '>= 0', '100%') |
| `actual_value` | VARCHAR(500) | | Actual measured value |
| `passed` | BOOLEAN | | Whether the check passed (true = success, false = failure) |
| `severity` | VARCHAR(20) | CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')) | Severity level of the check failure |
| `execution_id` | VARCHAR(100) | | Reference to the pipeline execution that ran this check |
| `checked_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when the check was executed |
| `details` | JSONB | | Additional details (e.g., sample of failing rows, threshold values, query used) |

**Primary Key:** `metric_id`  
**Purpose:** Tracks data quality metrics over time for monitoring, alerting, and trend analysis

---

## 📊 Data Volume Estimates

| Table | Estimated Rows | Growth Rate | Notes |
|-------|---------------|-------------|-------|
| `bronze.region` | 5 | Static | Dimension table |
| `bronze.nation` | 25 | Static | Dimension table |
| `bronze.customer` | 150,000 | Low | Dimension table |
| `bronze.supplier` | 10,000 | Low | Dimension table |
| `bronze.part` | 200,000 | Low | Dimension table |
| `bronze.orders` | 1,500,000 | Medium (daily) | Fact table |
| `bronze.partsupp` | 800,000 | Low | Relationship table |
| `bronze.lineitem` | 6,001,215 | High (daily) | Fact table |
| `control.watermarks` | 8 | Static | Configuration |
| `control.audit_log` | Growing | Medium | Log table |
| `control.data_quality_metrics` | Growing | Medium | Metrics table |

---

## 🔗 Foreign Key Relationships

```
region (r_regionkey) ← nation (n_regionkey)
nation (n_nationkey) ← customer (c_nationkey)
nation (n_nationkey) ← supplier (s_nationkey)
customer (c_custkey) ← orders (o_custkey)
orders (o_orderkey) ← lineitem (l_orderkey)
part (p_partkey) ← partsupp (ps_partkey)
supplier (s_suppkey) ← partsupp (ps_suppkey)
part (p_partkey) ← lineitem (l_partkey)
supplier (s_suppkey) ← lineitem (l_suppkey)
```

---

## 📝 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Tables | `snake_case` | `bronze.customer` |
| Columns | `snake_case` | `c_custkey` |
| Primary Keys | `{table_singular}_key` | `c_custkey` |
| Foreign Keys | `{referenced_table}_key` | `c_nationkey` |
| Audit Columns | `_loaded_at`, `_processed_at` | `_loaded_at` |
| Indexes | `idx_{table}_{columns}` | `idx_customer_c_nationkey` |

---

## 🎯 Common Query Patterns

### Get Customer Orders with Details
```sql
SELECT c.c_name, c.c_mktsegment, o.o_orderkey, o.o_totalprice, o.o_orderdate
FROM bronze.customer c
JOIN bronze.orders o ON c.c_custkey = o.o_custkey
WHERE o.o_orderdate >= '2023-01-01'
ORDER BY o.o_totalprice DESC;
```

### Get Part Supply Chain Information
```sql
SELECT p.p_name, p.p_brand, s.s_name, ps.ps_availqty, ps.ps_supplycost
FROM bronze.part p
JOIN bronze.partsupp ps ON p.p_partkey = ps.ps_partkey
JOIN bronze.supplier s ON ps.ps_suppkey = s.s_suppkey
WHERE ps.ps_availqty < 100
ORDER BY ps.ps_supplycost;
```

### Check Recent Pipeline Execution Status
```sql
SELECT execution_id, task_name, status, 
       rows_processed, duration_seconds, completed_at
FROM control.audit_log
WHERE started_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY started_at DESC;
```

---

This data dictionary serves as the single source of truth for your database schema and should be updated whenever schema changes are made.