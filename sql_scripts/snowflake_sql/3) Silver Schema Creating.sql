-- =====================================================
-- SILVER LAYER SCHEMA WITH AUDIT COLUMNS
-- Compatible with Snowflake
-- =====================================================

-- 1. Create the Database and Schema
-- CREATE DATABASE IF NOT EXISTS SALES_OPS_DB;
CREATE SCHEMA IF NOT EXISTS SALES_OPS_DB.SILVER;

-- 2. Create the Warehouse 
CREATE WAREHOUSE IF NOT EXISTS SILVER_STG
WITH WAREHOUSE_SIZE = 'XSMALL' 
AUTO_SUSPEND = 60 
AUTO_RESUME = TRUE;

-- 3. Create the Role
CREATE ROLE IF NOT EXISTS SILVER_ETL_ROLE;

-- 4. Grant Permissions
GRANT USAGE ON WAREHOUSE SILVER_STG TO ROLE SILVER_ETL_ROLE;
GRANT ALL ON DATABASE SALES_OPS_DB TO ROLE SILVER_ETL_ROLE;
GRANT ALL ON SCHEMA SALES_OPS_DB.SILVER TO ROLE SILVER_ETL_ROLE;

-- 5. Assign to User
GRANT ROLE SILVER_ETL_ROLE TO USER IBRAHIMHEGAZI;

-- =====================================================
-- DIMENSION TABLES WITH AUDIT COLUMNS
-- =====================================================

-- Region Dimension
CREATE TABLE IF NOT EXISTS silver.region (
    r_regionkey INTEGER PRIMARY KEY,
    r_name VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit columns
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Nation Dimension
CREATE TABLE IF NOT EXISTS silver.nation (
    n_nationkey INTEGER PRIMARY KEY,
    n_name VARCHAR(25),
    n_regionkey INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit columns
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);


-- Part Dimension (with extracted IDs)
CREATE TABLE IF NOT EXISTS silver.part (
    p_partkey INTEGER PRIMARY KEY,
    p_name VARCHAR(55),
    p_type VARCHAR(25),
    p_size INTEGER,
    p_container VARCHAR(10),
    p_retailprice DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit columns
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Supplier Dimension (cleaned)
CREATE TABLE IF NOT EXISTS silver.supplier (
    s_suppkey INTEGER PRIMARY KEY,
    s_name_id INTEGER,
    s_nationkey INTEGER,
    s_acctbal DECIMAL(15,2),
    s_phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit columns
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Customer Dimension (no address column)
CREATE TABLE IF NOT EXISTS silver.customer (
    c_custkey INTEGER PRIMARY KEY,
    c_name_id INTEGER,
    c_nationkey INTEGER,
    c_phone VARCHAR(15),
    c_acctbal DECIMAL(15,2),
    c_mktsegment VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit columns
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- =====================================================
-- FACT TABLES WITH AUDIT COLUMNS
-- =====================================================
DROP TABLE PARTSUPP
-- Partsupp Table (with SCD Type 2)
CREATE TABLE IF NOT EXISTS silver.partsupp (
    ps_partkey INTEGER,
    ps_suppkey INTEGER,
    ps_availqty INTEGER,
    ps_supplycost DECIMAL(15,2),
    is_current BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ps_partkey, ps_suppkey),
    -- Audit columns
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

CREATE OR REPLACE TABLE silver.orders (
    o_orderkey INTEGER PRIMARY KEY,
    o_custkey INTEGER,
    o_orderstatus VARCHAR(1),
    o_totalprice DECIMAL(15,2),
    o_orderdate DATE,
    o_orderpriority VARCHAR(15),
    -- o_clerk_id removed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);




CREATE OR REPLACE TABLE silver.lineitem (
    l_surrogate_key BIGINT AUTOINCREMENT START 1 INCREMENT 1, -- Automatically counts up
    l_orderkey INTEGER,
    l_partkey INTEGER,
    l_suppkey INTEGER,
    l_linenumber INTEGER,
    l_quantity DECIMAL(15,2),
    l_extendedprice DECIMAL(15,2),
    l_discount DECIMAL(15,2),
    l_tax DECIMAL(15,2),
    l_returnflag VARCHAR(1),
    l_linestatus VARCHAR(1),
    l_shipdate DATE,
    l_commitdate DATE,
    l_receiptdate DATE,
    l_shipinstruct VARCHAR(25),
    l_shipmode VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);










-- Then for the batch add the data into a stage in snowflake:
-- =====================================================
-- SILVER LAYER ETL WITH LINEAGE COLUMNS
-- Extracts from Stage, loads to Silver tables with audit columns
-- =====================================================

-- Set context
USE SCHEMA SALES_OPS_DB.SILVER;
USE WAREHOUSE SILVER_STG;

-- Generate a unique load ID for this batch
SET load_id = (SELECT CONCAT('LOAD_', REPLACE(CURRENT_TIMESTAMP::STRING, ' ', '_'), '_', UUID_STRING()));
-- =====================================================
-- 1. REGION DIMENSION
-- =====================================================



INSERT INTO silver.region (
    r_regionkey,
    r_name,
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
)
SELECT 
    -- Extract values from the $1 variant object using the Parquet column names
    $1:r_regionkey::INTEGER as r_regionkey,
    $1:r_name::VARCHAR(25) as r_name,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as _last_update_time,
    CURRENT_TIMESTAMP() as _loaded_at,
    SHA2(CONCAT_WS('|', 
        COALESCE($1:r_regionkey::STRING, ''), 
        COALESCE($1:r_name::STRING, '')
    ), 256) as _record_hash,
    $load_id as _load_id
FROM @"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/region.parquet
WHERE $1:r_regionkey IS NOT NULL;




SELECT * FROM SALES_OPS_DB.SILVER.REGION;




-- =====================================================
-- 2. NATION DIMENSION (CORRECTED)
-- =====================================================
INSERT INTO silver.nation (
    n_nationkey,
    n_name,
    n_regionkey,
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
)
SELECT 
    $1:n_nationkey::INTEGER as n_nationkey,
    $1:n_name::VARCHAR(25) as n_name,
    $1:n_regionkey::INTEGER as n_regionkey,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as _last_update_time,
    CURRENT_TIMESTAMP() as _loaded_at,
    SHA2(CONCAT_WS('|', 
        COALESCE($1:n_nationkey::STRING, ''), 
        COALESCE($1:n_name::STRING, ''),
        COALESCE($1:n_regionkey::STRING, '')
    ), 256) as _record_hash,
    $load_id as _load_id
FROM @"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/nation.parquet
WHERE $1:n_nationkey IS NOT NULL;


SELECT * FROM SALES_OPS_DB.SILVER.NATION;



-- =====================================================
-- 3. PART DIMENSION (with extracted IDs)
-- =====================================================
INSERT INTO silver.part (
    p_partkey,
    p_name,
    p_type,
    p_size,
    p_container,
    p_retailprice,
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
)
SELECT 
    $1:p_partkey::INTEGER as p_partkey,
    $1:p_name::VARCHAR(55) as p_name,
    $1:p_type::VARCHAR(25) as p_type,
    $1:p_size::INTEGER as p_size,
    $1:p_container::VARCHAR(10) as p_container,
    $1:p_retailprice::DECIMAL(15,2) as p_retailprice,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as _last_update_time,
    CURRENT_TIMESTAMP() as _loaded_at,
    SHA2(CONCAT_WS('|', 
        COALESCE($1:p_partkey::STRING, ''), 
        COALESCE($1:p_name::STRING, ''),
        COALESCE($1:p_type::STRING, ''),
        COALESCE($1:p_size::STRING, ''),
        COALESCE($1:p_container::STRING, ''),
        COALESCE($1:p_retailprice::STRING, '')
    ), 256) as _record_hash,
    $load_id as _load_id
FROM @"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/part.parquet
WHERE $1:p_partkey IS NOT NULL;


select * from part

-- =====================================================
-- 4. SUPPLIER DIMENSION (cleaned)
-- =====================================================
-- =====================================================
-- FIXED SUPPLIER DIMENSION (Correct Object Notation)
-- =====================================================

TRUNCATE TABLE silver.supplier;

INSERT INTO silver.supplier (
    s_suppkey,
    s_name_id,
    s_nationkey,
    s_acctbal,
    s_phone,
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
)
SELECT
    $1:s_suppkey::INTEGER                                      AS s_suppkey,
    TRY_CAST(REGEXP_SUBSTR($1:s_name::VARCHAR, '[0-9]+') AS INTEGER) AS s_name_id,
    $1:s_nationkey::INTEGER                                    AS s_nationkey,
    $1:s_acctbal::DECIMAL(15,2)                                AS s_acctbal,
    $1:s_phone::VARCHAR(15)                                    AS s_phone,
    CURRENT_TIMESTAMP()                                        AS created_at,
    CURRENT_TIMESTAMP()                                        AS _last_update_time,
    CURRENT_TIMESTAMP()                                        AS _loaded_at,
    SHA2(CONCAT_WS('|', 
        COALESCE($1:s_suppkey::STRING,''), 
        COALESCE($1:s_name::STRING,''), 
        COALESCE($1:s_nationkey::STRING,''), 
        COALESCE($1:s_acctbal::STRING,''), 
        COALESCE($1:s_phone::STRING,'')
    ), 256)                                                    AS _record_hash,
    $load_id                                                   AS _load_id
FROM @"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/supplier.parquet
WHERE $1:s_suppkey IS NOT NULL;

-- Quick verification
SELECT COUNT(*) FROM silver.supplier;           -- should be ~30,000
SELECT * FROM silver.supplier LIMIT 5;


select * from supplier


--  NEEDS CLEANING: THE DATA TYPES OF BRAND AND MANUFACTURER
-- =====================================================
-- 5. CUSTOMER DIMENSION
-- =====================================================
INSERT INTO silver.customer (
    c_custkey,
    c_name_id,
    c_nationkey,
    c_acctbal,
    c_phone,
    c_mktsegment,
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
)
SELECT 
    $1:c_custkey::INTEGER as c_custkey,
    -- Extract numeric ID from name (e.g., 'Customer#8' -> 8)
    TRY_CAST(REGEXP_SUBSTR($1:c_name::VARCHAR, '[0-9]+') AS INTEGER) as c_name_id,
    $1:c_nationkey::INTEGER as c_nationkey,
    $1:c_acctbal::DECIMAL(15,2) as c_acctbal,
    $1:c_phone::VARCHAR(15) as c_phone,
    $1:c_mktsegment::VARCHAR(10) as c_mktsegment,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as _last_update_time,
    CURRENT_TIMESTAMP() as _loaded_at,
    SHA2(CONCAT_WS('|', 
        COALESCE($1:c_custkey::STRING, ''), 
        COALESCE($1:c_name::STRING, ''),
        COALESCE($1:c_nationkey::STRING, ''),
        COALESCE($1:c_acctbal::STRING, ''),
        COALESCE($1:c_phone::STRING, ''),
        COALESCE($1:c_mktsegment::STRING, '')
    ), 256) as _record_hash,
    $load_id as _load_id
FROM @"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/customer.parquet
WHERE $1:c_custkey IS NOT NULL;

SELECT * FROM SALES_OPS_DB.SILVER.customer;


-- =====================================================
-- 6. PARTSUPP TABLE (SCD Type 2)
-- =====================================================

-- 1. Clear out the bad data
TRUNCATE TABLE silver.partsupp;

-- =====================================================
-- 6. PARTSUPP TABLE (Max Qty Flag Logic)
-- =====================================================

-- 1. Clear out the old data
TRUNCATE TABLE silver.partsupp;

-- 2. Extract and Insert
INSERT INTO silver.partsupp (
    ps_partkey,
    ps_suppkey,
    ps_availqty,
    ps_supplycost,
    is_current,         -- Dynamically calculated flag
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
)
WITH extracted_data AS (
    -- First, extract all the raw data from the Variant Parquet object
    SELECT 
        $1:ps_partkey::INTEGER as ps_partkey,
        $1:ps_suppkey::INTEGER as ps_suppkey,
        $1:ps_availqty::INTEGER as ps_availqty,
        $1:ps_supplycost::DECIMAL(15,2) as ps_supplycost,
        CURRENT_TIMESTAMP() as created_at,
        CURRENT_TIMESTAMP() as _last_update_time,
        CURRENT_TIMESTAMP() as _loaded_at,
        SHA2(CONCAT_WS('|', 
            COALESCE($1:ps_partkey::STRING, ''), 
            COALESCE($1:ps_suppkey::STRING, ''),
            COALESCE($1:ps_availqty::STRING, ''),
            COALESCE($1:ps_supplycost::STRING, '')
        ), 256) as _record_hash,
        $load_id as _load_id
    FROM @"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/partsupp.parquet
    WHERE $1:ps_partkey IS NOT NULL
)
SELECT 
    ps_partkey,
    ps_suppkey,
    ps_availqty,
    ps_supplycost,
    
    -- Evaluate the flag: TRUE for the highest quantity per part, FALSE for the rest
    IFF(
        ROW_NUMBER() OVER(PARTITION BY ps_partkey ORDER BY ps_availqty DESC) = 1, 
        TRUE, 
        FALSE
    ) as is_current,
    
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
FROM extracted_data;



    SELECT * FROM SALES_OPS_DB.SILVER.PARTSUPP
    ORDER BY PS_PARTKEY, PS_AVAILQTY;

-- =====================================================
-- 7. ORDERS FACT TABLE
-- =====================================================
-- =====================================================
-- 7. ORDERS FACT TABLE
-- =====================================================
INSERT INTO silver.orders (
    o_orderkey,
    o_custkey,
    o_orderstatus,
    o_totalprice,
    o_orderdate,
    o_orderpriority,
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
)
SELECT 
    $1:o_orderkey::INTEGER as o_orderkey,
    $1:o_custkey::INTEGER as o_custkey,
    $1:o_orderstatus::VARCHAR(1) as o_orderstatus,
    $1:o_totalprice::DECIMAL(15,2) as o_totalprice,
    $1:o_orderdate::DATE as o_orderdate,
    $1:o_orderpriority::VARCHAR(15) as o_orderpriority,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as _last_update_time,
    CURRENT_TIMESTAMP() as _loaded_at,
    SHA2(CONCAT_WS('|', 
        COALESCE($1:o_orderkey::STRING, ''), 
        COALESCE($1:o_custkey::STRING, ''),
        COALESCE($1:o_orderstatus::STRING, ''),
        COALESCE($1:o_totalprice::STRING, ''),
        COALESCE($1:o_orderdate::STRING, ''),
        COALESCE($1:o_orderpriority::STRING, '')
    ), 256) as _record_hash,
    $load_id as _load_id
FROM @"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/orders_base.parquet
WHERE $1:o_orderkey IS NOT NULL;

select * from orders
-- =====================================================
-- 8. LINEITEM FACT TABLE
-- =====================================================



TRUNCATE TABLE silver.lineitem;

-- 2. Insert the data (Omit the identity column so Snowflake auto-generates it)
INSERT INTO silver.lineitem (
    l_orderkey,
    l_partkey,
    l_suppkey,
    l_linenumber,
    l_quantity,
    l_extendedprice,
    l_discount,
    l_tax,
    l_returnflag,
    l_linestatus,
    l_shipdate,
    l_commitdate,
    l_receiptdate,
    l_shipinstruct,
    l_shipmode,
    created_at,
    _last_update_time,
    _loaded_at,
    _record_hash,
    _load_id
)
SELECT 
    $1:l_orderkey::INTEGER as l_orderkey,
    $1:l_partkey::INTEGER as l_partkey,
    $1:l_suppkey::INTEGER as l_suppkey,
    $1:l_linenumber::INTEGER as l_linenumber,
    $1:l_quantity::DECIMAL(15,2) as l_quantity,
    $1:l_extendedprice::DECIMAL(15,2) as l_extendedprice,
    $1:l_discount::DECIMAL(15,2) as l_discount,
    $1:l_tax::DECIMAL(15,2) as l_tax,
    $1:l_returnflag::VARCHAR(1) as l_returnflag,
    $1:l_linestatus::VARCHAR(1) as l_linestatus,
    $1:l_shipdate::DATE as l_shipdate,
    $1:l_commitdate::DATE as l_commitdate,
    $1:l_receiptdate::DATE as l_receiptdate,
    $1:l_shipinstruct::VARCHAR(25) as l_shipinstruct,
    $1:l_shipmode::VARCHAR(10) as l_shipmode,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as _last_update_time,
    CURRENT_TIMESTAMP() as _loaded_at,
    SHA2(CONCAT_WS('|', 
        COALESCE($1:l_orderkey::STRING, ''), 
        COALESCE($1:l_partkey::STRING, ''),
        COALESCE($1:l_suppkey::STRING, ''),
        COALESCE($1:l_linenumber::STRING, ''),
        COALESCE($1:l_quantity::STRING, ''),
        COALESCE($1:l_extendedprice::STRING, ''),
        COALESCE($1:l_discount::STRING, ''),
        COALESCE($1:l_tax::STRING, ''),
        COALESCE($1:l_returnflag::STRING, ''),
        COALESCE($1:l_linestatus::STRING, ''),
        COALESCE($1:l_shipdate::STRING, ''),
        COALESCE($1:l_commitdate::STRING, ''),
        COALESCE($1:l_receiptdate::STRING, ''),
        COALESCE($1:l_shipinstruct::STRING, ''),
        COALESCE($1:l_shipmode::STRING, '')
    ), 256) as _record_hash,
    $load_id as _load_id
FROM @"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/lineitem_base.parquet
WHERE $1:l_orderkey IS NOT NULL;

select * from lineitem
select * from orders


select * from supplier
limit 1

select * from '@"SALES_OPS_DB"."BRONZE"."BRONZE_ODS"/supplier.parquet'