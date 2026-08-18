-- 1. Create the Database and Schema
-- CREATE DATABASE IF NOT EXISTS SALES_OPS_DB;
CREATE SCHEMA IF NOT EXISTS SALES_OPS_DB.GOLD;

-- 2. Create the Warehouse 
CREATE WAREHOUSE IF NOT EXISTS GOLD_DWH
WITH WAREHOUSE_SIZE = 'XSMALL' 
AUTO_SUSPEND = 60 
AUTO_RESUME = TRUE;

-- 3. Create the Role
CREATE ROLE IF NOT EXISTS GOLD_ETL_ROLE;

-- 4. Grant Permissions
GRANT USAGE ON WAREHOUSE GOLD_DWH TO ROLE GOLD_ETL_ROLE;
GRANT ALL ON DATABASE SALES_OPS_DB TO ROLE GOLD_ETL_ROLE;
GRANT ALL ON SCHEMA SALES_OPS_DB.SILVER TO ROLE GOLD_ETL_ROLE;

-- 5. Assign to User
GRANT ROLE GOLD_ETL_ROLE TO USER IBRAHIMHEGAZI;



-- Get your account URL
SELECT CURRENT_ACCOUNT() AS ACCOUNT;

-- Get your current warehouse
SELECT CURRENT_WAREHOUSE() AS WAREHOUSE;

-- Get your current role
SELECT CURRENT_ROLE() AS ROLE;









-- dim_customer (fixed)
CREATE OR REPLACE TABLE gold.dim_customer (
    customer_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    customer_natural_key INTEGER NOT NULL,
    name VARCHAR(50),
    phone VARCHAR(15),
    account_balance DECIMAL(15,2),
    market_segment VARCHAR(10),
    nation_key INTEGER,
    nation_name VARCHAR(25),
    region_key INTEGER,
    region_name VARCHAR(25)
);

INSERT INTO gold.dim_customer 
    (customer_natural_key, name, phone, account_balance, market_segment, nation_key, nation_name, region_key, region_name)
SELECT 
    c.c_custkey,
    'Customer#' || LPAD(c.c_custkey::VARCHAR, 9, '0') AS name,
    c.c_phone,
    c.c_acctbal,
    c.c_mktsegment,
    n.n_nationkey,
    n.n_name,
    r.r_regionkey,
    r.r_name
FROM silver.customer c
LEFT JOIN silver.nation n ON c.c_nationkey = n.n_nationkey
LEFT JOIN silver.region r ON n.n_regionkey = r.r_regionkey;

-- dim_supplier (fixed)
CREATE OR REPLACE TABLE gold.dim_supplier (
    supplier_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    supplier_natural_key INTEGER NOT NULL,
    name VARCHAR(50),
    phone VARCHAR(15),
    account_balance DECIMAL(15,2),
    nation_key INTEGER,
    nation_name VARCHAR(25),
    region_key INTEGER,
    region_name VARCHAR(25)
);

INSERT INTO gold.dim_supplier 
    (supplier_natural_key, name, phone, account_balance, nation_key, nation_name, region_key, region_name)
SELECT 
    s.s_suppkey,
    'Supplier#' || LPAD(s.s_suppkey::VARCHAR, 9, '0') AS name,
    s.s_phone,
    s.s_acctbal,
    n.n_nationkey,
    n.n_name,
    r.r_regionkey,
    r.r_name
FROM silver.supplier s
LEFT JOIN silver.nation n ON s.s_nationkey = n.n_nationkey
LEFT JOIN silver.region r ON n.n_regionkey = r.r_regionkey;

-- dim_part (fixed)
CREATE OR REPLACE TABLE gold.dim_part (
    part_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    part_natural_key INTEGER NOT NULL,
    name VARCHAR(55),
    type VARCHAR(25),
    size INTEGER,
    container VARCHAR(10),
    retail_price DECIMAL(15,2)
);

INSERT INTO gold.dim_part (part_natural_key, name, type, size, container, retail_price)
SELECT p_partkey, p_name, p_type, p_size, p_container, p_retailprice
FROM silver.part;









CREATE OR REPLACE TABLE gold.fact_orders (
    order_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    order_natural_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL,
    order_date_key INTEGER NOT NULL,
    order_status CHAR(1),
    total_price DECIMAL(15,2),
    order_priority VARCHAR(15)
);

INSERT INTO gold.fact_orders 
    (order_natural_key, customer_key, order_date_key, order_status, total_price, order_priority)
SELECT 
    o.o_orderkey,
    dc.customer_key,
    dd.date_key,
    o.o_orderstatus,
    o.o_totalprice,
    o.o_orderpriority
FROM silver.orders o
INNER JOIN gold.dim_customer dc ON o.o_custkey = dc.customer_natural_key
INNER JOIN gold.dim_date dd ON dd.full_date = o.o_orderdate;








CREATE OR REPLACE TABLE gold.fact_line_items (
    line_item_key BIGINT PRIMARY KEY,           -- reuse from silver
    order_natural_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL,
    part_key BIGINT NOT NULL,
    supplier_key BIGINT NOT NULL,
    order_date_key INTEGER NOT NULL,
    line_number INTEGER,
    quantity DECIMAL(15,2),
    extended_price DECIMAL(15,2),
    discount DECIMAL(15,2),
    tax DECIMAL(15,2),
    return_flag CHAR(1),
    line_status CHAR(1),
    ship_date DATE,
    commit_date DATE,
    receipt_date DATE,
    ship_instructions VARCHAR(25),
    ship_mode VARCHAR(10)
);

INSERT INTO gold.fact_line_items 
    (line_item_key, order_natural_key, customer_key, part_key, supplier_key, order_date_key,
     line_number, quantity, extended_price, discount, tax,
     return_flag, line_status, ship_date, commit_date, receipt_date,
     ship_instructions, ship_mode)
SELECT 
    l.l_surrogate_key,
    l.l_orderkey,
    dc.customer_key,
    dp.part_key,
    ds.supplier_key,
    dd.date_key,
    l.l_linenumber,
    l.l_quantity,
    l.l_extendedprice,
    l.l_discount,
    l.l_tax,
    l.l_returnflag,
    l.l_linestatus,
    l.l_shipdate,
    l.l_commitdate,
    l.l_receiptdate,
    l.l_shipinstruct,
    l.l_shipmode
FROM silver.lineitem l
INNER JOIN silver.orders o        ON l.l_orderkey = o.o_orderkey
INNER JOIN gold.dim_customer dc   ON o.o_custkey = dc.customer_natural_key
INNER JOIN gold.dim_part dp       ON l.l_partkey = dp.part_natural_key
INNER JOIN gold.dim_supplier ds   ON l.l_suppkey = ds.supplier_natural_key
INNER JOIN gold.dim_date dd       ON dd.full_date = o.o_orderdate;   -- using order date






select * from fact_orders


-- Check final row counts in Gold
SELECT 'gold.dim_customer' AS table_name, COUNT(*) FROM gold.dim_customer
UNION ALL
SELECT 'gold.dim_part', COUNT(*) FROM gold.dim_part
UNION ALL
SELECT 'gold.dim_supplier', COUNT(*) FROM gold.dim_supplier
UNION ALL
SELECT 'gold.fact_orders', COUNT(*) FROM gold.fact_orders
UNION ALL
SELECT 'gold.fact_line_items', COUNT(*) FROM gold.fact_line_items;




-- TRUNCATE TABLE dim_customer;
-- TRUNCATE TABLE dim_part;
-- TRUNCATE TABLE dim_supplier;
-- TRUNCATE TABLE fact_orders;
-- TRUNCATE TABLE fact_line_items;














select * from fact_line_items









-- Set context
USE ROLE GOLD_ETL_ROLE;
USE WAREHOUSE GOLD_DWH;
USE DATABASE SALES_OPS_DB;
USE SCHEMA GOLD;

-- Method 1: Using INFORMATION_SCHEMA (Detailed column information)
SELECT 
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CHARACTER_MAXIMUM_LENGTH,
    NUMERIC_PRECISION,
    NUMERIC_SCALE,
    COLUMN_DEFAULT,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'GOLD'
ORDER BY TABLE_NAME, ORDINAL_POSITION;




