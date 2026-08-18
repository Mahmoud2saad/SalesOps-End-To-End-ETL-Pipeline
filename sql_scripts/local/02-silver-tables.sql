-- =============================================================================
-- SILVER LAYER SCHEMA DEFINITIONS
-- Database: silver_tpch
-- =============================================================================

  
            -- 3. CREATE DIMENSION TABLES
            
            -- Region Dimension
            CREATE TABLE silver.region (
                r_regionkey INTEGER PRIMARY KEY,
                r_name VARCHAR(25),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Nation Dimension
            CREATE TABLE silver.nation (
                n_nationkey INTEGER PRIMARY KEY,
                n_name VARCHAR(25),
                n_regionkey INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Part Dimension (with extracted IDs)
            CREATE TABLE silver.part (
                p_partkey INTEGER PRIMARY KEY,
                p_name VARCHAR(55),
                p_mfgr_id INTEGER,
                p_brand_id INTEGER,
                p_type VARCHAR(25),
                p_size INTEGER,
                p_container VARCHAR(10),
                p_retailprice DECIMAL(15,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Supplier Dimension (cleaned)
            CREATE TABLE silver.supplier (
                s_suppkey INTEGER PRIMARY KEY,
                s_name_id INTEGER,  -- Modified to hold extracted integer ID
                s_nationkey INTEGER,
                s_acctbal DECIMAL(15,2),
                s_phone VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Customer Dimension (no address column)
            CREATE TABLE silver.customer (
                c_custkey INTEGER PRIMARY KEY,
                c_name_id INTEGER,  -- Modified to hold extracted integer ID
                c_nationkey INTEGER,
                c_acctbal DECIMAL(15,2),
                c_phone VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Partsupp Table (with SCD Type 2)
            CREATE TABLE silver.partsupp (
                ps_partkey INTEGER,
                ps_suppkey INTEGER,
                ps_availqty INTEGER,
                ps_supplycost DECIMAL(15,2),
                valid_from TIMESTAMP,
                valid_to TIMESTAMP,
                is_current BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (ps_partkey, ps_suppkey, valid_from)
            );
            
            -- Orders Fact Table (cleaned)
            CREATE TABLE silver.orders (
                o_orderkey INTEGER PRIMARY KEY,
                o_custkey INTEGER,
                o_orderstatus CHAR(1),
                o_totalprice DECIMAL(15,2),
                o_orderdate DATE,
                o_orderpriority VARCHAR(15),
                o_clerk_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Lineitem Fact Table
            CREATE TABLE silver.lineitem (
                l_orderkey INTEGER,
                l_partkey INTEGER,
                l_suppkey INTEGER,
                l_linenumber INTEGER,
                l_quantity DECIMAL(15,2),
                l_extendedprice DECIMAL(15,2),
                l_discount DECIMAL(15,2),
                l_tax DECIMAL(15,2),
                l_returnflag CHAR(1),
                l_linestatus CHAR(1),
                l_shipdate DATE,
                l_commitdate DATE,
                l_receiptdate DATE,
                l_shipinstruct VARCHAR(25),
                l_shipmode VARCHAR(10),
                l_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (l_orderkey, l_linenumber)
            );

-- -----------------------------------------------------------------------------
-- FOREIGN KEY CONSTRAINTS (for documentation - enforced at application level)
-- -----------------------------------------------------------------------------
-- ALTER TABLE silver_tpch.customer ADD CONSTRAINT fk_customer_nation FOREIGN KEY (c_nationkey) REFERENCES silver_tpch.nation(n_nationkey);
-- ALTER TABLE silver_tpch.lineitem ADD CONSTRAINT fk_lineitem_order FOREIGN KEY (l_orderkey) REFERENCES silver_tpch.orders(o_orderkey);
-- ALTER TABLE silver_tpch.lineitem ADD CONSTRAINT fk_lineitem_part FOREIGN KEY (l_partkey) REFERENCES silver_tpch.part(p_partkey);
-- ALTER TABLE silver_tpch.lineitem ADD CONSTRAINT fk_lineitem_supplier FOREIGN KEY (l_suppkey) REFERENCES silver_tpch.supplier(s_suppkey);
-- ALTER TABLE silver_tpch.nation ADD CONSTRAINT fk_nation_region FOREIGN KEY (n_regionkey) REFERENCES silver_tpch.region(r_regionkey);
-- ALTER TABLE silver_tpch.orders ADD CONSTRAINT fk_orders_customer FOREIGN KEY (o_custkey) REFERENCES silver_tpch.customer(c_custkey);
-- ALTER TABLE silver_tpch.partsupp ADD CONSTRAINT fk_partsupp_part FOREIGN KEY (ps_partkey) REFERENCES silver_tpch.part(p_partkey);
-- ALTER TABLE silver_tpch.partsupp ADD CONSTRAINT fk_partsupp_supplier FOREIGN KEY (ps_suppkey) REFERENCES silver_tpch.supplier(s_suppkey);
-- ALTER TABLE silver_tpch.supplier ADD CONSTRAINT fk_supplier_nation FOREIGN KEY (s_nationkey) REFERENCES silver_tpch.nation(n_nationkey);