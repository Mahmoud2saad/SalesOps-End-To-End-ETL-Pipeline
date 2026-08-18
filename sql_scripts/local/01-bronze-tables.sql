-- -- NEEDS MODIFICATION
-- -- Run SECOND - Bronze layer (ODS)
-- -- Region table
CREATE TABLE IF NOT EXISTS bronze.region (
    r_regionkey BIGINT PRIMARY KEY,
    r_name VARCHAR(25),
    r_comment VARCHAR(152),
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Nation table
CREATE TABLE IF NOT EXISTS bronze.nation (
    n_nationkey BIGINT PRIMARY KEY,
    n_name VARCHAR(25),
    n_regionkey BIGINT REFERENCES bronze.region(r_regionkey),
    n_comment VARCHAR(152),
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Part table
CREATE TABLE IF NOT EXISTS bronze.part (
    p_partkey BIGINT PRIMARY KEY,
    p_name VARCHAR(55),
    p_mfgr VARCHAR(25),
    p_brand VARCHAR(10),
    p_type VARCHAR(25),
    p_size INTEGER,
    p_container VARCHAR(10),
    p_retailprice DECIMAL(15,2),
    p_comment VARCHAR(23),
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier table
CREATE TABLE IF NOT EXISTS bronze.supplier (
    s_suppkey BIGINT PRIMARY KEY,
    s_name VARCHAR(25),
    s_address VARCHAR(40),
    s_nationkey BIGINT REFERENCES bronze.nation(n_nationkey),
    s_phone CHAR(15),
    s_acctbal DECIMAL(15,2),
    s_comment VARCHAR(101),
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer table
CREATE TABLE IF NOT EXISTS bronze.customer (
    c_custkey BIGINT PRIMARY KEY,
    c_name VARCHAR(25),
    c_address VARCHAR(40),
    c_nationkey BIGINT REFERENCES bronze.nation(n_nationkey),
    c_phone CHAR(15),
    c_acctbal DECIMAL(15,2),
    c_mktsegment VARCHAR(10),
    c_comment VARCHAR(117),
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS bronze.orders (
    o_orderkey BIGINT PRIMARY KEY,
    o_custkey BIGINT REFERENCES bronze.customer(c_custkey),
    o_orderstatus CHAR(1),
    o_totalprice DECIMAL(15,2),
    o_orderdate DATE,
    o_orderpriority CHAR(15),
    o_clerk CHAR(15),
    o_shippriority INTEGER,
    o_comment VARCHAR(79),
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Partsupp table (Composite key: partkey + suppkey)
CREATE TABLE IF NOT EXISTS bronze.partsupp (
    ps_id BIGINT PRIMARY KEY,
    ps_partkey BIGINT REFERENCES bronze.part(p_partkey),
    ps_suppkey BIGINT REFERENCES bronze.supplier(s_suppkey),
    ps_availqty INTEGER,
    ps_supplycost DECIMAL(15,2),
    ps_comment VARCHAR(199),
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lineitem table
CREATE TABLE IF NOT EXISTS bronze.lineitem (
    l_id BIGINT PRIMARY KEY,
    l_orderkey BIGINT REFERENCES bronze.orders(o_orderkey),
    l_partkey BIGINT REFERENCES bronze.part(p_partkey),
    l_suppkey BIGINT REFERENCES bronze.supplier(s_suppkey),
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
    l_shipinstruct CHAR(25),
    l_shipmode CHAR(10),
    l_comment VARCHAR(44),
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);






-- updated bronze layer (to catch the data raw really)



-- -- Region table
-- CREATE TABLE IF NOT EXISTS bronze.region (
--     r_regionkey BIGINT,
--     r_name VARCHAR(25),
--     r_comment VARCHAR(152),
--     _source_table VARCHAR(50) DEFAULT 'region',
--     _last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _is_duplicate BOOLEAN DEFAULT FALSE,
--     _error_flag BOOLEAN DEFAULT FALSE,
--     _error_message TEXT,
--     _record_hash VARCHAR(64),
--     _load_id VARCHAR(100)
-- );

-- -- Nation table
-- CREATE TABLE IF NOT EXISTS bronze.nation (
--     n_nationkey BIGINT,
--     n_name VARCHAR(25),
--     n_regionkey BIGINT,
--     n_comment VARCHAR(152),
--     _source_table VARCHAR(50) DEFAULT 'nation',
--     _last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _is_duplicate BOOLEAN DEFAULT FALSE,
--     _error_flag BOOLEAN DEFAULT FALSE,
--     _error_message TEXT,
--     _record_hash VARCHAR(64),
--     _load_id VARCHAR(100)
-- );

-- -- Part table
-- CREATE TABLE IF NOT EXISTS bronze.part (
--     p_partkey BIGINT,
--     p_name VARCHAR(55),
--     p_mfgr VARCHAR(25),
--     p_brand VARCHAR(10),
--     p_type VARCHAR(25),
--     p_size INTEGER,
--     p_container VARCHAR(10),
--     p_retailprice DECIMAL(15,2),
--     p_comment VARCHAR(23),
--     _source_table VARCHAR(50) DEFAULT 'part',
--     _last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _is_duplicate BOOLEAN DEFAULT FALSE,
--     _error_flag BOOLEAN DEFAULT FALSE,
--     _error_message TEXT,
--     _record_hash VARCHAR(64),
--     _load_id VARCHAR(100)
-- );

-- -- Supplier table
-- CREATE TABLE IF NOT EXISTS bronze.supplier (
--     s_suppkey BIGINT,
--     s_name VARCHAR(25),
--     s_address VARCHAR(40),
--     s_nationkey BIGINT,
--     s_phone CHAR(15),
--     s_acctbal DECIMAL(15,2),
--     s_comment VARCHAR(101),
--     _source_table VARCHAR(50) DEFAULT 'supplier',
--     _last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _is_duplicate BOOLEAN DEFAULT FALSE,
--     _error_flag BOOLEAN DEFAULT FALSE,
--     _error_message TEXT,
--     _record_hash VARCHAR(64),
--     _load_id VARCHAR(100)
-- );

-- -- Customer table
-- CREATE TABLE IF NOT EXISTS bronze.customer (
--     c_custkey BIGINT,
--     c_name VARCHAR(25),
--     c_address VARCHAR(40),
--     c_nationkey BIGINT,
--     c_phone CHAR(15),
--     c_acctbal DECIMAL(15,2),
--     c_mktsegment VARCHAR(10),
--     c_comment VARCHAR(117),
--     _source_table VARCHAR(50) DEFAULT 'customer',
--     _last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _is_duplicate BOOLEAN DEFAULT FALSE,
--     _error_flag BOOLEAN DEFAULT FALSE,
--     _error_message TEXT,
--     _record_hash VARCHAR(64),
--     _load_id VARCHAR(100)
-- );

-- -- Orders table (no PRIMARY KEY constraint)
-- CREATE TABLE IF NOT EXISTS bronze.orders (
--     o_orderkey BIGINT,
--     o_custkey BIGINT,
--     o_orderstatus CHAR(1),
--     o_totalprice DECIMAL(15,2),
--     o_orderdate DATE,
--     o_orderpriority CHAR(15),
--     o_clerk CHAR(15),
--     o_shippriority INTEGER,
--     o_comment VARCHAR(500),  -- Increased from 79 to handle corrupted data
--     _source_table VARCHAR(50) DEFAULT 'orders',
--     _last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _is_duplicate BOOLEAN DEFAULT FALSE,
--     _error_flag BOOLEAN DEFAULT FALSE,
--     _error_message TEXT,
--     _record_hash VARCHAR(64),
--     _load_id VARCHAR(100)
-- );

-- -- Partsupp table (no PRIMARY KEY constraint)
-- CREATE TABLE IF NOT EXISTS bronze.partsupp (
--     ps_id BIGINT,
--     ps_partkey BIGINT,
--     ps_suppkey BIGINT,
--     ps_availqty INTEGER,
--     ps_supplycost DECIMAL(15,2),
--     ps_comment VARCHAR(199),
--     _source_table VARCHAR(50) DEFAULT 'partsupp',
--     _last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _is_duplicate BOOLEAN DEFAULT FALSE,
--     _error_flag BOOLEAN DEFAULT FALSE,
--     _error_message TEXT,
--     _record_hash VARCHAR(64),
--     _load_id VARCHAR(100)
-- );

-- -- Lineitem table (no PRIMARY KEY constraint)
-- CREATE TABLE IF NOT EXISTS bronze.lineitem (
--     l_id BIGINT,
--     l_orderkey BIGINT,
--     l_partkey BIGINT,
--     l_suppkey BIGINT,
--     l_linenumber INTEGER,
--     l_quantity DECIMAL(15,2),
--     l_extendedprice DECIMAL(15,2),
--     l_discount DECIMAL(15,2),
--     l_tax DECIMAL(15,2),
--     l_returnflag CHAR(1),
--     l_linestatus CHAR(1),
--     l_shipdate DATE,
--     l_commitdate DATE,
--     l_receiptdate DATE,
--     l_shipinstruct CHAR(25),
--     l_shipmode CHAR(10),
--     l_comment VARCHAR(500),  -- Increased from 44 to handle corrupted data
--     _source_table VARCHAR(50) DEFAULT 'lineitem',
--     _last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     _is_duplicate BOOLEAN DEFAULT FALSE,
--     _error_flag BOOLEAN DEFAULT FALSE,
--     _error_message TEXT,
--     _record_hash VARCHAR(64),
--     _load_id VARCHAR(100)
-- );




-- Lineage columns Explained:

-- _source_table: Track which table the data came from

-- _last_update_time: When the record was last updated

-- _processed_at: When the record was processed

-- _loaded_at: When the record was loaded

-- _is_duplicate: Flag for duplicate records

-- _error_flag: Flag for records with errors

-- _error_message: Detailed error message

-- _record_hash: For deduplication

-- _load_id: Batch load identifier