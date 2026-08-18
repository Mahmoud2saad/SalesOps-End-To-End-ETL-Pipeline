-- 1. Create the Database and Schema
CREATE DATABASE IF NOT EXISTS SALES_OPS_DB;
CREATE SCHEMA IF NOT EXISTS SALES_OPS_DB.BRONZE;

-- 2. Create the Warehouse 
CREATE WAREHOUSE IF NOT EXISTS BRONZE_ODS 
WITH WAREHOUSE_SIZE = 'XSMALL' 
AUTO_SUSPEND = 60 
AUTO_RESUME = TRUE;

-- 3. Create the Role
CREATE ROLE IF NOT EXISTS BRONZE_ETL_ROLE;

-- 4. Grant Permissions
GRANT USAGE ON WAREHOUSE BRONZE_ODS TO ROLE BRONZE_ETL_ROLE;

-- Note: You named your DB 'SALES_OPS_DB' above, 
-- but your grant statement tried to grant on a DB named 'BRONZE'.
-- Fixed below to match your CREATE DATABASE statement:
GRANT ALL ON DATABASE SALES_OPS_DB TO ROLE BRONZE_ETL_ROLE;
GRANT ALL ON SCHEMA SALES_OPS_DB.BRONZE TO ROLE BRONZE_ETL_ROLE;

-- 5. Assign to User
GRANT ROLE BRONZE_ETL_ROLE TO USER IBRAHIMHEGAZI;




-- Now Bronze Schema Creation

-- Region table
CREATE TABLE IF NOT EXISTS bronze.region (
    r_regionkey NUMBER(38,0),
    r_name VARCHAR(25),
    r_comment VARCHAR(152),
    _source_table VARCHAR(50) DEFAULT 'region',
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _is_duplicate BOOLEAN DEFAULT FALSE,
    _error_flag BOOLEAN DEFAULT FALSE,
    _error_message VARCHAR(16777216),  -- TEXT in Snowflake = VARCHAR
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Nation table
CREATE TABLE IF NOT EXISTS bronze.nation (
    n_nationkey NUMBER(38,0),
    n_name VARCHAR(25),
    n_regionkey NUMBER(38,0),
    n_comment VARCHAR(152),
    _source_table VARCHAR(50) DEFAULT 'nation',
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _is_duplicate BOOLEAN DEFAULT FALSE,
    _error_flag BOOLEAN DEFAULT FALSE,
    _error_message VARCHAR(16777216),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Part table
CREATE TABLE IF NOT EXISTS bronze.part (
    p_partkey NUMBER(38,0),
    p_name VARCHAR(55),
    p_mfgr VARCHAR(25),
    p_brand VARCHAR(10),
    p_type VARCHAR(25),
    p_size NUMBER(38,0),
    p_container VARCHAR(10),
    p_retailprice NUMBER(15,2),
    p_comment VARCHAR(23),
    _source_table VARCHAR(50) DEFAULT 'part',
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _is_duplicate BOOLEAN DEFAULT FALSE,
    _error_flag BOOLEAN DEFAULT FALSE,
    _error_message VARCHAR(16777216),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Supplier table
CREATE TABLE IF NOT EXISTS bronze.supplier (
    s_suppkey NUMBER(38,0),
    s_name VARCHAR(25),
    s_address VARCHAR(40),
    s_nationkey NUMBER(38,0),
    s_phone VARCHAR(15),  -- CHAR changed to VARCHAR for Snowflake flexibility
    s_acctbal NUMBER(15,2),
    s_comment VARCHAR(101),
    _source_table VARCHAR(50) DEFAULT 'supplier',
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _is_duplicate BOOLEAN DEFAULT FALSE,
    _error_flag BOOLEAN DEFAULT FALSE,
    _error_message VARCHAR(16777216),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Customer table
CREATE TABLE IF NOT EXISTS bronze.customer (
    c_custkey NUMBER(38,0),
    c_name VARCHAR(25),
    c_address VARCHAR(40),
    c_nationkey NUMBER(38,0),
    c_phone VARCHAR(15),  -- CHAR changed to VARCHAR
    c_acctbal NUMBER(15,2),
    c_mktsegment VARCHAR(10),
    c_comment VARCHAR(117),
    _source_table VARCHAR(50) DEFAULT 'customer',
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _is_duplicate BOOLEAN DEFAULT FALSE,
    _error_flag BOOLEAN DEFAULT FALSE,
    _error_message VARCHAR(16777216),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Orders table
CREATE TABLE IF NOT EXISTS bronze.orders (
    o_orderkey NUMBER(38,0),
    o_custkey NUMBER(38,0),
    o_orderstatus VARCHAR(1),  -- CHAR changed to VARCHAR
    o_totalprice NUMBER(15,2),
    o_orderdate DATE,
    o_orderpriority VARCHAR(15),  -- CHAR changed to VARCHAR
    o_clerk VARCHAR(15),  -- CHAR changed to VARCHAR
    o_shippriority NUMBER(38,0),
    o_comment VARCHAR(500),
    _source_table VARCHAR(50) DEFAULT 'orders',
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _is_duplicate BOOLEAN DEFAULT FALSE,
    _error_flag BOOLEAN DEFAULT FALSE,
    _error_message VARCHAR(16777216),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Partsupp table
CREATE TABLE IF NOT EXISTS bronze.partsupp (
    ps_id NUMBER(38,0),
    ps_partkey NUMBER(38,0),
    ps_suppkey NUMBER(38,0),
    ps_availqty NUMBER(38,0),
    ps_supplycost NUMBER(15,2),
    ps_comment VARCHAR(199),
    _source_table VARCHAR(50) DEFAULT 'partsupp',
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _is_duplicate BOOLEAN DEFAULT FALSE,
    _error_flag BOOLEAN DEFAULT FALSE,
    _error_message VARCHAR(16777216),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);

-- Lineitem table
CREATE TABLE IF NOT EXISTS bronze.lineitem (
    l_id NUMBER(38,0),
    l_orderkey NUMBER(38,0),
    l_partkey NUMBER(38,0),
    l_suppkey NUMBER(38,0),
    l_linenumber NUMBER(38,0),
    l_quantity NUMBER(15,2),
    l_extendedprice NUMBER(15,2),
    l_discount NUMBER(15,2),
    l_tax NUMBER(15,2),
    l_returnflag VARCHAR(1),  -- CHAR changed to VARCHAR
    l_linestatus VARCHAR(1),  -- CHAR changed to VARCHAR
    l_shipdate DATE,
    l_commitdate DATE,
    l_receiptdate DATE,
    l_shipinstruct VARCHAR(25),  -- CHAR changed to VARCHAR
    l_shipmode VARCHAR(10),  -- CHAR changed to VARCHAR
    l_comment VARCHAR(500),
    _source_table VARCHAR(50) DEFAULT 'lineitem',
    _last_update_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _processed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _is_duplicate BOOLEAN DEFAULT FALSE,
    _error_flag BOOLEAN DEFAULT FALSE,
    _error_message VARCHAR(16777216),
    _record_hash VARCHAR(64),
    _load_id VARCHAR(100)
);



-- Run the work/3) Final Dance/4) Local Bronze Layer to SnowFlake/Testing Connections.ipynb to load the customer table from your local machine to here to test the connection

-- SELECT * FROM SALES_OPS_DB.BRONZE.CUSTOMER;

-- -- Testing has been passed
-- -- Now delete the data you entered and start clean

-- TRUNCATE TABLE  SALES_OPS_DB.BRONZE.CUSTOMER;
-- SELECT * FROM SALES_OPS_DB.BRONZE.CUSTOMER;



-- Run the work/3) Final Dance/4) Local Bronze Layer to SnowFlake/Testing Connections.ipynb to load all the tables from your local machine to here 

-- SELECT * FROM SALES_OPS_DB.BRONZE.REGION
-- SELECT * FROM SALES_OPS_DB.BRONZE.PART
-- SELECT * FROM SALES_OPS_DB.BRONZE.LINEITEM
