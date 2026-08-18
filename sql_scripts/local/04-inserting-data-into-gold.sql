-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- (NEEDS REVISION)
-- Run SECOND - Silver layer (Transform & Cleanse)
-- This layer prepares data for the gold star schema

-- =====================================================
-- Silver Schema
-- =====================================================
CREATE SCHEMA IF NOT EXISTS silver;

-- =====================================================
-- Silver: dim_date (Generate date dimension)
-- =====================================================
-- Generate dates for a reasonable range (e.g., 10 years before/after data range)
INSERT INTO gold.dim_date (date_key, full_date, year, quarter, month, month_name, week, day_of_month, day_of_week)
SELECT 
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_key,
    d AS full_date,
    EXTRACT(YEAR FROM d) AS year,
    EXTRACT(QUARTER FROM d) AS quarter,
    EXTRACT(MONTH FROM d) AS month,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(WEEK FROM d) AS week,
    EXTRACT(DAY FROM d) AS day_of_month,
    EXTRACT(ISODOW FROM d) AS day_of_week  -- Monday=1, Sunday=7
FROM generate_series(
    '1990-01-01'::DATE,
    '2025-12-31'::DATE,
    '1 day'::INTERVAL
) AS d;

-- =====================================================
-- Silver: dim_part
-- =====================================================
INSERT INTO gold.dim_part (
    part_key,
    name,
    manufacturer,
    brand,
    type,
    size,
    container,
    retail_price
)
SELECT 
    p_partkey,
    p_name,
    p_mfgr,
    p_brand,
    p_type,
    p_size,
    p_container,
    p_retailprice
FROM bronze.part
WHERE p_partkey IS NOT NULL;

-- =====================================================
-- Silver: dim_customer (Denormalized with nation & region)
-- =====================================================
INSERT INTO gold.dim_customer (
    customer_key,
    name,
    phone,
    account_balance,
    market_segment,
    nation_key,
    nation_name,
    region_key,
    region_name
)
SELECT 
    c_custkey,
    c_name,
    c_phone,
    c_acctbal,
    c_mktsegment,
    n.n_nationkey,
    n.n_name,
    r.r_regionkey,
    r.r_name
FROM bronze.customer c
LEFT JOIN bronze.nation n ON c.c_nationkey = n.n_nationkey
LEFT JOIN bronze.region r ON n.n_regionkey = r.r_regionkey
WHERE c_custkey IS NOT NULL;

-- =====================================================
-- Silver: dim_supplier (Denormalized with nation & region)
-- =====================================================
INSERT INTO gold.dim_supplier (
    supplier_key,
    name,
    phone,
    account_balance,
    nation_key,
    nation_name,
    region_key,
    region_name
)
SELECT 
    s_suppkey,
    s_name,
    s_phone,
    s_acctbal,
    n.n_nationkey,
    n.n_name,
    r.r_regionkey,
    r.r_name
FROM bronze.supplier s
LEFT JOIN bronze.nation n ON s.s_nationkey = n.n_nationkey
LEFT JOIN bronze.region r ON n.n_regionkey = r.r_regionkey
WHERE s_suppkey IS NOT NULL;

-- =====================================================
-- Silver: fact_orders
-- =====================================================
INSERT INTO gold.fact_orders (
    order_key,
    customer_key,
    order_status,
    total_price,
    order_date,
    order_priority
)
SELECT 
    o_orderkey,
    o_custkey,
    o_orderstatus,
    o_totalprice,
    o_orderdate,
    o_orderpriority
FROM bronze.orders o
WHERE o_orderkey IS NOT NULL
  AND EXISTS (SELECT 1 FROM gold.dim_customer dc WHERE dc.customer_key = o.o_custkey);

-- =====================================================
-- Silver: fact_line_items
-- =====================================================
INSERT INTO gold.fact_line_items (
    line_item_key,
    order_key,
    customer_key,
    part_key,
    supplier_key,
    line_number,
    quantity,
    extended_price,
    discount,
    tax,
    return_flag,
    line_status,
    ship_date,
    commit_date,
    receipt_date,
    ship_instructions,
    ship_mode
)
SELECT 
    l.l_id,
    l.l_orderkey,
    o.o_custkey,  -- Denormalize customer_key from orders
    l.l_partkey,
    l.l_suppkey,
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
FROM bronze.lineitem l
INNER JOIN bronze.orders o ON l.l_orderkey = o.o_orderkey
WHERE l.l_id IS NOT NULL
  AND EXISTS (SELECT 1 FROM gold.dim_customer dc WHERE dc.customer_key = o.o_custkey)
  AND EXISTS (SELECT 1 FROM gold.dim_part dp WHERE dp.part_key = l.l_partkey)
  AND EXISTS (SELECT 1 FROM gold.dim_supplier ds WHERE ds.supplier_key = l.l_suppkey);

-- =====================================================
-- Silver: fact_partsupp_inventory
-- =====================================================
INSERT INTO gold.fact_partsupp_inventory (
    partsupp_key,
    part_key,
    supplier_key,
    available_quantity,
    supply_cost
)
SELECT 
    ps_id,
    ps_partkey,
    ps_suppkey,
    ps_availqty,
    ps_supplycost
FROM bronze.partsupp ps
WHERE ps_id IS NOT NULL
  AND EXISTS (SELECT 1 FROM gold.dim_part dp WHERE dp.part_key = ps.ps_partkey)
  AND EXISTS (SELECT 1 FROM gold.dim_supplier ds WHERE ds.supplier_key = ps.ps_suppkey);

-- =====================================================
-- Data Validation Queries (Optional - for monitoring)
-- =====================================================

-- Validate row counts match expectations
DO $$
DECLARE
    bronze_count BIGINT;
    gold_count BIGINT;
BEGIN
    -- Part validation
    SELECT COUNT(*) INTO bronze_count FROM bronze.part;
    SELECT COUNT(*) INTO gold_count FROM gold.dim_part;
    RAISE NOTICE 'Part: Bronze=%, Gold=%, Match=%', bronze_count, gold_count, (bronze_count = gold_count);
    
    -- Customer validation
    SELECT COUNT(*) INTO bronze_count FROM bronze.customer;
    SELECT COUNT(*) INTO gold_count FROM gold.dim_customer;
    RAISE NOTICE 'Customer: Bronze=%, Gold=%, Match=%', bronze_count, gold_count, (bronze_count = gold_count);
    
    -- Supplier validation
    SELECT COUNT(*) INTO bronze_count FROM bronze.supplier;
    SELECT COUNT(*) INTO gold_count FROM gold.dim_supplier;
    RAISE NOTICE 'Supplier: Bronze=%, Gold=%, Match=%', bronze_count, gold_count, (bronze_count = gold_count);
    
    -- Orders validation
    SELECT COUNT(*) INTO bronze_count FROM bronze.orders;
    SELECT COUNT(*) INTO gold_count FROM gold.fact_orders;
    RAISE NOTICE 'Orders: Bronze=%, Gold=%, Match=%', bronze_count, gold_count, (bronze_count = gold_count);
    
    -- Line items validation
    SELECT COUNT(*) INTO bronze_count FROM bronze.lineitem;
    SELECT COUNT(*) INTO gold_count FROM gold.fact_line_items;
    RAISE NOTICE 'Line Items: Bronze=%, Gold=%, Match=%', bronze_count, gold_count, (bronze_count = gold_count);
    
    -- Partsupp validation
    SELECT COUNT(*) INTO bronze_count FROM bronze.partsupp;
    SELECT COUNT(*) INTO gold_count FROM gold.fact_partsupp_inventory;
    RAISE NOTICE 'Partsupp: Bronze=%, Gold=%, Match=%', bronze_count, gold_count, (bronze_count = gold_count);
END $$;
















-- Testing
SELECT 
    fo.order_key,
    fo.total_price,
    ros.status_name,
    rop.priority_name
FROM gold.fact_orders fo
LEFT JOIN gold.ref_order_status ros ON fo.order_status = ros.status_code
LEFT JOIN gold.ref_order_priority rop ON fo.order_priority = rop.priority_code
LIMIT 10;