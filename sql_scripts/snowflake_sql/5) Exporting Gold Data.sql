-- Switch to the correct role and warehouse
USE ROLE GOLD_ETL_ROLE;
USE WAREHOUSE GOLD_DWH;
USE DATABASE SALES_OPS_DB;
USE SCHEMA GOLD;

-- Create a stage for exporting (using the role with proper permissions)
CREATE OR REPLACE STAGE gold_export_stage
COMMENT = 'Stage for exporting Gold layer tables to local device';

-- Verify stage creation
LIST @gold_export_stage;


-- Find all stages in the entire database
SHOW STAGES IN DATABASE SALES_OPS_DB;





-- -- 1. Export DIM_CUSTOMER
-- COPY INTO @gold_export_stage/dim_customer.csv
-- FROM (
--     SELECT 
--         customer_key,
--         customer_natural_key,
--         name,
--         phone,
--         account_balance,
--         market_segment,
--         nation_key,
--         nation_name,
--         region_key,
--         region_name
--     FROM gold.dim_customer
-- )
-- FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' NULL_IF = ('NULL') COMPRESSION = NONE)
-- HEADER = TRUE
-- SINGLE = TRUE
-- OVERWRITE = TRUE;

-- -- 2. Export DIM_SUPPLIER
-- COPY INTO @gold_export_stage/dim_supplier.csv
-- FROM (
--     SELECT 
--         supplier_key,
--         supplier_natural_key,
--         name,
--         phone,
--         account_balance,
--         nation_key,
--         nation_name,
--         region_key,
--         region_name
--     FROM gold.dim_supplier
-- )
-- FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' COMPRESSION = NONE)
-- HEADER = TRUE
-- SINGLE = TRUE
-- OVERWRITE = TRUE;

-- -- 3. Export DIM_PART
-- COPY INTO @gold_export_stage/dim_part.csv
-- FROM (
--     SELECT 
--         part_key,
--         part_natural_key,
--         name,
--         type,
--         size,
--         container,
--         retail_price
--     FROM gold.dim_part
-- )
-- FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' COMPRESSION = NONE)
-- HEADER = TRUE
-- SINGLE = TRUE
-- OVERWRITE = TRUE;

-- -- 4. Export FACT_ORDERS
-- COPY INTO @gold_export_stage/fact_orders.csv
-- FROM (
--     SELECT 
--         order_key,
--         order_natural_key,
--         customer_key,
--         order_date_key,
--         order_status,
--         total_price,
--         order_priority
--     FROM gold.fact_orders
-- )
-- FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' COMPRESSION = NONE)
-- HEADER = TRUE
-- SINGLE = TRUE
-- OVERWRITE = TRUE;

-- -- 5. Export FACT_LINE_ITEMS (largest table - will be split into multiple files)
-- COPY INTO @gold_export_stage/fact_line_items/
-- FROM (
--     SELECT 
--         line_item_key,
--         order_natural_key,
--         customer_key,
--         part_key,
--         supplier_key,
--         order_date_key,
--         line_number,
--         quantity,
--         extended_price,
--         discount,
--         tax,
--         return_flag,
--         line_status,
--         ship_date,
--         commit_date,
--         receipt_date,
--         ship_instructions,
--         ship_mode
--     FROM gold.fact_line_items
-- )
-- FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' COMPRESSION = NONE)
-- HEADER = TRUE
-- SINGLE = FALSE
-- MAX_FILE_SIZE = 104857600;  -- 100MB per file

-- -- For a single file export of fact_line_items (if file size is manageable)
-- -- COPY INTO @gold_export_stage/fact_line_items_single.csv
-- -- FROM (SELECT * FROM gold.fact_line_items)
-- -- FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"')
-- -- HEADER = TRUE
-- -- SINGLE = TRUE
-- -- OVERWRITE = TRUE;




WHERE stage_catalog = 'SALES_OPS_DB'
ORDER BY stage_schema, stage_name;






-- Set context
USE ROLE GOLD_ETL_ROLE;
USE WAREHOUSE GOLD_DWH;
USE DATABASE SALES_OPS_DB;
USE SCHEMA GOLD;
-- Create the stage
CREATE OR REPLACE STAGE GOLD_EXPORT_STAGE;
-- Verify your stage exists
SHOW STAGES;

-- Export small tables as single Parquet files
COPY INTO @GOLD_EXPORT_STAGE/dim_customer.parquet 
FROM dim_customer 
FILE_FORMAT = (TYPE = PARQUET) 
SINGLE = TRUE 
OVERWRITE = TRUE;

COPY INTO @GOLD_EXPORT_STAGE/dim_supplier.parquet 
FROM dim_supplier 
FILE_FORMAT = (TYPE = PARQUET) 
SINGLE = TRUE 
OVERWRITE = TRUE;

COPY INTO @GOLD_EXPORT_STAGE/dim_part.parquet 
FROM dim_part 
FILE_FORMAT = (TYPE = PARQUET) 
SINGLE = TRUE 
OVERWRITE = TRUE;

-- Export fact_orders as multi-file Parquet
COPY INTO @GOLD_EXPORT_STAGE/fact_orders/
FROM fact_orders 
FILE_FORMAT = (TYPE = PARQUET) 
SINGLE = FALSE 
MAX_FILE_SIZE = 16777216;

-- Export first 50% of rows (1,816,232 rows)
COPY INTO @GOLD_EXPORT_STAGE/fact_line_items_part1/
FROM (
    SELECT * FROM fact_line_items 
    ORDER BY line_item_key
    LIMIT 1816232
)
FILE_FORMAT = (TYPE = PARQUET) 
SINGLE = FALSE 
MAX_FILE_SIZE = 16777216;

-- Export remaining 50% of rows (next 1,816,232 rows)
COPY INTO @GOLD_EXPORT_STAGE/fact_line_items_part2/
FROM (
    SELECT * FROM fact_line_items 
    ORDER BY line_item_key
    LIMIT 1816232 OFFSET 1816232
)
FILE_FORMAT = (TYPE = PARQUET) 
SINGLE = FALSE 
MAX_FILE_SIZE = 16777216;
-- Verify all exports
LIST @GOLD_EXPORT_STAGE;

















-- Set context
USE ROLE GOLD_ETL_ROLE;
USE WAREHOUSE GOLD_DWH;
USE DATABASE SALES_OPS_DB;
USE SCHEMA GOLD;

-- Calculate the split point first
SET split_point = (SELECT COUNT(*) * 0.5 FROM fact_line_items);

-- Export small tables
COPY INTO @GOLD_EXPORT_STAGE/dim_customer.parquet FROM dim_customer FILE_FORMAT = (TYPE = PARQUET) SINGLE = TRUE OVERWRITE = TRUE;
COPY INTO @GOLD_EXPORT_STAGE/dim_supplier.parquet FROM dim_supplier FILE_FORMAT = (TYPE = PARQUET) SINGLE = TRUE OVERWRITE = TRUE;
COPY INTO @GOLD_EXPORT_STAGE/dim_part.parquet FROM dim_part FILE_FORMAT = (TYPE = PARQUET) SINGLE = TRUE OVERWRITE = TRUE;

-- Export fact_orders
COPY INTO @GOLD_EXPORT_STAGE/fact_orders/ FROM fact_orders FILE_FORMAT = (TYPE = PARQUET) SINGLE = FALSE MAX_FILE_SIZE = 16777216;

-- Export first 50% of rows
COPY INTO @GOLD_EXPORT_STAGE/fact_line_items_part1/
FROM (
    SELECT * FROM fact_line_items 
    ORDER BY line_item_key
    LIMIT $split_point
)
FILE_FORMAT = (TYPE = PARQUET) 
SINGLE = FALSE 
MAX_FILE_SIZE = 16777216;

-- Export remaining 50% of rows
COPY INTO @GOLD_EXPORT_STAGE/fact_line_items_part2/
FROM fact_line_items 
WHERE line_item_key NOT IN (
    SELECT line_item_key 
    FROM fact_line_items 
    ORDER BY line_item_key 
    LIMIT $split_point
)
FILE_FORMAT = (TYPE = PARQUET) 
SINGLE = FALSE 
MAX_FILE_SIZE = 16777216;

-- Verify exports
LIST @GOLD_EXPORT_STAGE;

















REMOVE @GOLD_EXPORT_STAGE;

-- Verify cleanup
LIST @GOLD_EXPORT_STAGE;