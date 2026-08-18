import pandas as pd
from sqlalchemy import create_engine, text
import sys
import os

# Add the parent directory to the path so we can import our audit modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audit.watermark_manager import WatermarkManager
from audit.audit_logger import AuditLogger

def extract_incremental_orders():
    print("🚀 Starting Incremental Extraction for 'orders' table...")
    
    # 1. Setup Connections (Using internal Docker network ports)
    source_engine = create_engine('postgresql+psycopg2://source_user:source_pass@postgres-local:5432/data_platform_db')
    control_engine = create_engine('postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control')
    
    wm_manager = WatermarkManager(control_engine)
    audit_logger = AuditLogger(control_engine)
    
    table_name = 'bronze.orders'
    task_name = 'extract_orders_incremental'
    execution_id = 'manual_test_001' # Airflow will provide this dynamically later
    
    # 2. Log Start in Audit Table
    audit_id = audit_logger.log_start("SalesOps_Incremental_ETL", execution_id, task_name, table_name)
    
    try:
        # 3. Get Watermark (Find out where we left off)
        watermark = wm_manager.get_watermark(table_name)
        safe_id = watermark['safe_extraction_id'] if watermark else 0
        
        # 4. Extract NEW Data Only
        extract_query = text(f"""
            SELECT * FROM bronze.orders 
            WHERE o_orderkey > :safe_id 
            ORDER BY o_orderkey ASC
        """)
        
        print(f"📡 Fetching records with ID > {safe_id}...")
        with source_engine.connect() as conn:
            df = pd.read_sql(extract_query, conn, params={"safe_id": safe_id})
        
        rows_extracted = len(df)
        print(f"📦 Extracted {rows_extracted} new rows from {table_name}.")
        
        if rows_extracted > 0:
            # Note: In the full pipeline, we would save this DF to Parquet or send to Spark here.
            
            # 5. Update Watermark for the next run
            max_id = df['o_orderkey'].max()
            wm_manager.update_watermark(table_name, new_max_id=int(max_id))
        
        # 6. Log Completion
        audit_logger.log_complete(audit_id, status='SUCCESS', rows_processed=rows_extracted)
        print("🎉 Extraction completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        audit_logger.log_complete(audit_id, status='FAILED', error_message=str(e))

if __name__ == "__main__":
    extract_incremental_orders()