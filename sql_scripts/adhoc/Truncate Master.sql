-- Truncate all tables in the bronze schema
TRUNCATE TABLE bronze.customer, 
         bronze.lineitem, 
         bronze.nation, 
         bronze.orders, 
         bronze.part, 
         bronze.partsupp, 
         bronze.region, 
         bronze.supplier;


TRUNCATE TABLE silver.customer, 
         silver.lineitem, 
         silver.nation, 
         silver.orders, 
         silver.part, 
         silver.partsupp, 
         silver.region, 
         silver.supplier;


TRUNCATE TABLE gold.customer, 
         gold.lineitem, 
         gold.nation, 
         gold.orders, 
         gold.part, 
         gold.partsupp, 
         gold.region, 
         gold.supplier;


TRUNCATE TABLE control.watermarks, 
         control.data_quality_metrics, 
         control.audit_log