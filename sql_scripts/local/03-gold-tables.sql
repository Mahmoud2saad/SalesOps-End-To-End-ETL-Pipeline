-- Run THIRD - Gold layer (Star Schema)
-- Create gold schema
CREATE SCHEMA IF NOT EXISTS gold;

-- =====================================================
-- Dimension Tables
-- =====================================================

-- dim_date - Time dimension
CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_key INTEGER PRIMARY KEY,  -- YYYYMMDD format
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    week INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL  -- 1 = Monday, 7 = Sunday (ISO standard)
);


-- dim_part - Part dimension
CREATE TABLE IF NOT EXISTS gold.dim_part (
    part_key BIGINT PRIMARY KEY,
    name VARCHAR(55),
    manufacturer VARCHAR(25),
    brand VARCHAR(10),
    type VARCHAR(25),
    size INTEGER,
    container VARCHAR(10),
    retail_price DECIMAL(15,2)
);




-- dim_customer - Customer dimension with nation & region denormalized
CREATE TABLE IF NOT EXISTS gold.dim_customer (
    customer_key BIGINT PRIMARY KEY,
    name VARCHAR(25),
    phone CHAR(15),
    account_balance DECIMAL(15,2),  
    market_segment VARCHAR(10),
    -- Nation attributes
    nation_key BIGINT,
    nation_name VARCHAR(50),
    -- Region attributes
    region_key BIGINT,
    region_name VARCHAR(50)
);


-- dim_supplier - Supplier dimension with nation & region denormalized
CREATE TABLE IF NOT EXISTS gold.dim_supplier (
    supplier_key BIGINT PRIMARY KEY,
    name VARCHAR(25),
    phone CHAR(15),
    account_balance DECIMAL(15,2),
    --Nation attributes
    nation_key BIGINT,
    nation_name VARCHAR(50),
    -- Region attributes
    region_key BIGINT,
    region_name VARCHAR(50)
);


-- =====================================================
-- Reference/Lookup Tables for Order Attributes
-- =====================================================

-- ref_order_status - Order status codes
CREATE TABLE IF NOT EXISTS gold.ref_order_status (
    status_code CHAR(1) PRIMARY KEY,
    status_name VARCHAR(20) NOT NULL,
    status_description VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate ref_order_status
INSERT INTO gold.ref_order_status (status_code, status_name, status_description) VALUES 
('O', 'Open', 'Order is open and pending fulfillment'),
('F', 'Fulfilled', 'Order fully fulfilled and complete'),
('P', 'Partially Fulfilled', 'Order partially fulfilled, some line items pending'),
('C', 'Cancelled', 'Order cancelled before or during fulfillment'),
('R', 'Returned', 'Order fully returned by customer');

-- =====================================================

-- ref_order_priority - Order priority levels
CREATE TABLE IF NOT EXISTS gold.ref_order_priority (
    priority_code CHAR(15) PRIMARY KEY,
    priority_level INTEGER NOT NULL,  -- 1 = highest, 5 = lowest
    priority_name VARCHAR(30) NOT NULL,
    priority_description VARCHAR(100),
    expected_processing_days INTEGER,  -- Business days expected for this priority
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate ref_order_priority
INSERT INTO gold.ref_order_priority (priority_code, priority_level, priority_name, priority_description, expected_processing_days) VALUES 
('1-URGENT', 1, 'Urgent', 'Immediate processing required', 1),
('2-HIGH', 2, 'High', 'Priority processing required', 2),
('3-MEDIUM', 3, 'Medium', 'Standard priority', 3),
('4-NOT SPECIFIED', 4, 'Not Specified', 'No priority specified', 5),
('5-LOW', 5, 'Low', 'Low priority, can be batched', 7);

-- =====================================================

-- Example of how to query with reference tables
-- SELECT 
--     fo.order_key,
--     fo.total_price,
--     fo.order_date,
--     ros.status_name AS order_status_name,
--     rop.priority_name AS order_priority_name
-- FROM gold.fact_orders fo
-- LEFT JOIN gold.ref_order_status ros ON fo.order_status = ros.status_code
-- LEFT JOIN gold.ref_order_priority rop ON fo.order_priority = rop.priority_code;



-- =====================================================
-- Reference/Lookup Tables for Line Item Attributes
-- =====================================================

-- ref_return_flag - Return flag codes
CREATE TABLE IF NOT EXISTS gold.ref_return_flag (
    return_code CHAR(1) PRIMARY KEY,
    return_name VARCHAR(30) NOT NULL,
    return_description VARCHAR(100) NOT NULL,
    is_returned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate ref_return_flag
INSERT INTO gold.ref_return_flag (return_code, return_name, return_description, is_returned) VALUES 
('A', 'Returned - Accepted', 'Line item returned and accepted', TRUE),
('N', 'Not Returned', 'Line item not returned', FALSE),
('R', 'Returned - Rejected', 'Line item returned and rejected', TRUE);

-- =====================================================

-- ref_line_status - Line item status codes
CREATE TABLE IF NOT EXISTS gold.ref_line_status (
    status_code CHAR(1) PRIMARY KEY,
    status_name VARCHAR(20) NOT NULL,
    status_description VARCHAR(100) NOT NULL,
    is_fulfilled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate ref_line_status
INSERT INTO gold.ref_line_status (status_code, status_name, status_description, is_fulfilled) VALUES 
('F', 'Fulfilled', 'Line item fulfilled and shipped', TRUE),
('O', 'Open', 'Line item open, not yet fulfilled', FALSE);

-- =====================================================

-- ref_ship_instructions - Shipping instruction codes
CREATE TABLE IF NOT EXISTS gold.ref_ship_instructions (
    instruction_code CHAR(25) PRIMARY KEY,
    instruction_name VARCHAR(50) NOT NULL,
    instruction_description VARCHAR(200) NOT NULL,
    requires_signature BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate ref_ship_instructions
INSERT INTO gold.ref_ship_instructions (instruction_code, instruction_name, instruction_description, requires_signature) VALUES 
('COLLECT COD', 'Collect COD', 'Collect cash on delivery upon shipment arrival', TRUE),
('DELIVER IN PERSON', 'Deliver In Person', 'Must be delivered in person to recipient', TRUE),
('NONE', 'No Special Instructions', 'Standard delivery with no special instructions', FALSE),
('TAKE BACK RETURN', 'Take Back Return', 'Driver must take back return item if applicable', TRUE);

-- =====================================================

-- ref_ship_mode - Shipping mode codes
CREATE TABLE IF NOT EXISTS gold.ref_ship_mode (
    mode_code CHAR(10) PRIMARY KEY,
    mode_name VARCHAR(30) NOT NULL,
    mode_category VARCHAR(20) NOT NULL,  -- Air, Ground, Mail, etc.
    average_transit_days INTEGER,
    tracking_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate ref_ship_mode
INSERT INTO gold.ref_ship_mode (mode_code, mode_name, mode_category, average_transit_days, tracking_available) VALUES 
('AIR', 'Air Freight', 'Air', 3, TRUE),
('FOB', 'Free On Board', 'Ground', 5, FALSE),
('MAIL', 'Standard Mail', 'Mail', 7, FALSE),
('RAIL', 'Rail Freight', 'Ground', 10, FALSE),
('REG AIR', 'Regular Air', 'Air', 4, TRUE),
('SHIP', 'Ocean Freight', 'Sea', 21, TRUE),
('TRUCK', 'Truck Freight', 'Ground', 5, TRUE);



-- =====================================================

-- Example of how to query with reference tables
-- SELECT 
--     fl.line_item_key,
--     fl.order_key,
--     fl.quantity,
--     fl.extended_price,
--     rrf.return_name AS return_status,
--     rls.status_name AS line_status_name,
--     rsi.instruction_name AS shipping_instruction,
--     rsm.mode_name AS shipping_mode,
--     rsm.mode_category AS shipping_category
-- FROM gold.fact_line_items fl
-- LEFT JOIN gold.ref_return_flag rrf ON fl.return_flag = rrf.return_code
-- LEFT JOIN gold.ref_line_status rls ON fl.line_status = rls.status_code
-- LEFT JOIN gold.ref_ship_instructions rsi ON fl.ship_instructions = rsi.instruction_code
-- LEFT JOIN gold.ref_ship_mode rsm ON fl.ship_mode = rsm.mode_code;




-- =====================================================
-- Fact Tables
-- =====================================================

 






-- -- =====================================================
-- -- Optional: Create indexes for better query performance
-- -- =====================================================

-- -- Indexes for fact_orders
-- CREATE INDEX IF NOT EXISTS idx_fact_orders_customer_key ON gold.fact_orders(customer_key);
-- CREATE INDEX IF NOT EXISTS idx_fact_orders_order_date ON gold.fact_orders(order_date);

-- -- Indexes for fact_line_items
-- CREATE INDEX IF NOT EXISTS idx_fact_line_items_order_key ON gold.fact_line_items(order_key);
-- CREATE INDEX IF NOT EXISTS idx_fact_line_items_customer_key ON gold.fact_line_items(customer_key);
-- CREATE INDEX IF NOT EXISTS idx_fact_line_items_part_key ON gold.fact_line_items(part_key);
-- CREATE INDEX IF NOT EXISTS idx_fact_line_items_supplier_key ON gold.fact_line_items(supplier_key);
-- CREATE INDEX IF NOT EXISTS idx_fact_line_items_ship_date ON gold.fact_line_items(ship_date);

-- -- Indexes for fact_partsupp_inventory
-- CREATE INDEX IF NOT EXISTS idx_fact_partsupp_inventory_part_key ON gold.fact_partsupp_inventory(part_key);
-- CREATE INDEX IF NOT EXISTS idx_fact_partsupp_inventory_supplier_key ON gold.fact_partsupp_inventory(supplier_key);

-- -- Indexes for dimension tables
-- CREATE INDEX IF NOT EXISTS idx_dim_customer_nation_key ON gold.dim_customer(nation_key);
-- CREATE INDEX IF NOT EXISTS idx_dim_customer_region_key ON gold.dim_customer(region_key);
-- CREATE INDEX IF NOT EXISTS idx_dim_supplier_nation_key ON gold.dim_supplier(nation_key);
-- CREATE INDEX IF NOT EXISTS idx_dim_supplier_region_key ON gold.dim_supplier(region_key);