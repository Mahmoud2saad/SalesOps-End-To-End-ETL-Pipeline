-- -- -- Run these in Snowflake Worksheet (web UI)


-- -- CREATE DATABASE TPCH_GOLD;

-- -- CREATE SCHEMA TPCH_GOLD.GOLD;

-- -- -- Create a role for your pipeline (better than ACCOUNTADMIN)
-- -- CREATE ROLE GOLD_ETL_ROLE;
-- -- GRANT USAGE ON WAREHOUSE GOLD_WH TO ROLE GOLD_ETL_ROLE;
-- -- GRANT ALL ON DATABASE TPCH_GOLD TO ROLE GOLD_ETL_ROLE;
-- -- GRANT ALL ON SCHEMA TPCH_GOLD.GOLD TO ROLE GOLD_ETL_ROLE;

-- -- -- Grant to your user
-- -- GRANT ROLE GOLD_ETL_ROLE TO USER IBRAHIMHEGAZI;





-- -- CREATE OR REPLACE TABLE TPCH_GOLD.GOLD.dim_customer (
-- --     customer_key      NUMBER(38) PRIMARY KEY,
-- --     name              VARCHAR(25),
-- --     phone             CHAR(15),
-- --     account_balance   NUMBER(15,2),
-- --     market_segment    VARCHAR(10),
-- --     nation_key        NUMBER(38),
-- --     nation_name       VARCHAR(50),
-- --     region_key        NUMBER(38),
-- --     region_name       VARCHAR(50),
-- --     _loaded_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
-- -- );


-- select * FROM TPCH_GOLD.GOLD.dim_customer;

-- DROP DATABASE TPCH_GOLD;


CREATE OR REPLACE STAGE  SALES_OPS_DB.BRONZE.BRONZE_ODS 
    FILE_FORMAT = (TYPE = PARQUET);



-- Set context
USE DATABASE SALES_OPS_DB;
USE SCHEMA BRONZE;
USE WAREHOUSE BRONZE_ODS;
USE ROLE BRONZE_ETL_ROLE;

-- Generate load_id
SET load_id = 'load_' || TO_CHAR(CURRENT_TIMESTAMP(), 'YYYYMMDD_HH24MISS') || '_' || LEFT(MD5(RANDOM()::VARCHAR), 8);

-- Create file format if not exists
CREATE OR REPLACE FILE FORMAT parquet_format
    TYPE = PARQUET;

-- Note: Your stage already exists: SALES_OPS_DB.BRONZE.BRONZE_ODS
-- The stage name is BRONZE_ODS (not lineitem_stage)
-- Set context
-- Set context
USE DATABASE SALES_OPS_DB;
USE SCHEMA BRONZE;
USE WAREHOUSE BRONZE_ODS;
USE ROLE BRONZE_ETL_ROLE;

-- Create file format if not exists
CREATE OR REPLACE FILE FORMAT parquet_format
    TYPE = PARQUET;

-- Set context
USE DATABASE SALES_OPS_DB;
USE SCHEMA BRONZE;
USE WAREHOUSE BRONZE_ODS;
USE ROLE BRONZE_ETL_ROLE;

-- Create file format if not exists
CREATE OR REPLACE FILE FORMAT parquet_format
    TYPE = PARQUET;

-- Set context
USE DATABASE SALES_OPS_DB;
USE SCHEMA BRONZE;
USE WAREHOUSE BRONZE_ODS;
USE ROLE BRONZE_ETL_ROLE;

-- Create file format
CREATE OR REPLACE FILE FORMAT parquet_format
    TYPE = PARQUET;















-- Set context
USE DATABASE SALES_OPS_DB;
USE SCHEMA BRONZE;
USE WAREHOUSE BRONZE_ODS;
USE ROLE BRONZE_ETL_ROLE;

-- Create file format if not exists
CREATE OR REPLACE FILE FORMAT parquet_format
    TYPE = PARQUET;

-- First, create a temporary table to stage the data
CREATE OR REPLACE TEMPORARY TABLE lineitem_staging AS
SELECT 
    $1:l_id::NUMBER(38,0) AS l_id,
    $1:l_orderkey::NUMBER(38,0) AS l_orderkey,
    $1:l_partkey::NUMBER(38,0) AS l_partkey,
    $1:l_suppkey::NUMBER(38,0) AS l_suppkey,
    $1:l_linenumber::NUMBER(38,0) AS l_linenumber,
    $1:l_quantity::NUMBER(15,2) AS l_quantity,
    $1:l_extendedprice::NUMBER(15,2) AS l_extendedprice,
    $1:l_discount::NUMBER(15,2) AS l_discount,
    $1:l_tax::NUMBER(15,2) AS l_tax,
    $1:l_returnflag::VARCHAR(1) AS l_returnflag,
    $1:l_linestatus::VARCHAR(1) AS l_linestatus,
    $1:l_shipdate::DATE AS l_shipdate,
    $1:l_commitdate::DATE AS l_commitdate,
    $1:l_receiptdate::DATE AS l_receiptdate,
    $1:l_shipinstruct::VARCHAR(25) AS l_shipinstruct,
    $1:l_shipmode::VARCHAR(10) AS l_shipmode,
    $1:l_comment::VARCHAR(500) AS l_comment,
    SHA2(CONCAT(
        COALESCE(TO_VARCHAR($1:l_orderkey), 'NULL'), '|',
        COALESCE(TO_VARCHAR($1:l_linenumber), 'NULL')
    ), 256) AS _record_hash
FROM @SALES_OPS_DB.BRONZE.BRONZE_ODS
WHERE 1=1;  -- This will load all files in the stage

-- Generate load_id using subquery method
SET load_id = (SELECT 'load_' || TO_CHAR(CURRENT_TIMESTAMP(), 'YYYYMMDD_HH24MISS') || '_' || LEFT(MD5(RANDOM()::VARCHAR), 8));

-- Insert into lineitem with lineage columns
INSERT INTO lineitem (
    l_id, l_orderkey, l_partkey, l_suppkey, l_linenumber,
    l_quantity, l_extendedprice, l_discount, l_tax,
    l_returnflag, l_linestatus, l_shipdate, l_commitdate, l_receiptdate,
    l_shipinstruct, l_shipmode, l_comment,
    _source_table, _last_update_time, _processed_at, _loaded_at,
    _is_duplicate, _error_flag, _error_message, _record_hash, _load_id
)
SELECT 
    s.l_id, s.l_orderkey, s.l_partkey, s.l_suppkey, s.l_linenumber,
    s.l_quantity, s.l_extendedprice, s.l_discount, s.l_tax,
    s.l_returnflag, s.l_linestatus, s.l_shipdate, s.l_commitdate, s.l_receiptdate,
    s.l_shipinstruct, s.l_shipmode, s.l_comment,
    'lineitem' AS _source_table,
    CURRENT_TIMESTAMP() AS _last_update_time,
    CURRENT_TIMESTAMP() AS _processed_at,
    CURRENT_TIMESTAMP() AS _loaded_at,
    CASE WHEN t._record_hash IS NOT NULL THEN TRUE ELSE FALSE END AS _is_duplicate,
    CASE WHEN s.l_orderkey IS NULL OR s.l_linenumber IS NULL THEN TRUE ELSE FALSE END AS _error_flag,
    CASE 
        WHEN s.l_orderkey IS NULL THEN 'l_orderkey is NULL'
        WHEN s.l_linenumber IS NULL THEN 'l_linenumber is NULL'
        ELSE NULL 
    END AS _error_message,
    s._record_hash,
    $load_id AS _load_id
FROM lineitem_staging s
LEFT JOIN lineitem t ON s._record_hash = t._record_hash;

-- Clean up staging table
DROP TABLE IF EXISTS lineitem_staging;

-- Show summary
SELECT 
    'Total records loaded' AS metric,
    COUNT(*) AS value
FROM lineitem
WHERE _load_id = $load_id

UNION ALL

SELECT 
    'Records with errors' AS metric,
    COUNT(*) AS value
FROM lineitem
WHERE _load_id = $load_id AND _error_flag = TRUE

UNION ALL

SELECT 
    'Duplicate records' AS metric,
    COUNT(*) AS value
FROM lineitem
WHERE _load_id = $load_id AND _is_duplicate = TRUE

UNION ALL

SELECT 
    'Unique records' AS metric,
    COUNT(DISTINCT _record_hash) AS value
FROM lineitem
WHERE _load_id = $load_id;