import pandas as pd
from sqlalchemy import create_engine, text
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audit.watermark_manager import WatermarkManager
from audit.audit_logger import AuditLogger

def extract_remaining_tables():
    print("🚀 Starting Incremental Extraction for the remaining tables...")
    
    source_engine = create_engine('postgresql+psycopg2://source_user:source_pass@postgres-local:5432/data_platform_db')
    control_engine = create_engine('postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control')
    
    wm_manager = WatermarkManager(control_engine)
    audit_logger = AuditLogger(control_engine)
    
    tables_to_extract = [
        'bronze.customer', 
        'bronze.part', 
        'bronze.supplier', 
        'bronze.nation', 
        'bronze.region',
        'bronze.partsupp'
    ]
    
    execution_id = 'manual_test_003'
    
    for table_name in tables_to_extract:
        print(f"\n{'='*50}")
        print(f"🔄 Processing table: {table_name}")
        
        clean_name = table_name.split(".")[1]
        task_name = f'extract_{clean_name}_incremental'
        
        audit_id = audit_logger.log_start("SalesOps_Incremental_ETL", execution_id, task_name, table_name)
        
        try:
            watermark = wm_manager.get_watermark(table_name)
            
            if not watermark:
                print(f"⚠️ Skipping {table_name} due to missing watermark configuration.")
                audit_logger.log_complete(audit_id, status='SKIPPED', error_message="No watermark config")
                continue
                
            safe_id = watermark['safe_extraction_id']
            inc_column = watermark['incremental_column'] 
            
            extract_query = text(f"""
                SELECT * FROM {table_name} 
                WHERE {inc_column} > :safe_id 
                ORDER BY {inc_column} ASC
            """)
            
            print(f"📡 Fetching records where {inc_column} > {safe_id}...")
            
            with source_engine.connect() as conn:
                df = pd.read_sql(extract_query, conn, params={"safe_id": safe_id})
            
            rows_extracted = len(df)
            print(f"📦 Extracted {rows_extracted} new rows from {table_name}.")
            
            if rows_extracted > 0:
                max_id = df[inc_column].max()
                wm_manager.update_watermark(table_name, new_max_id=int(max_id))
            
            audit_logger.log_complete(audit_id, status='SUCCESS', rows_processed=rows_extracted)
            
        except Exception as e:
            print(f"❌ Error during extraction of {table_name}: {e}")
            audit_logger.log_complete(audit_id, status='FAILED', error_message=str(e))
            
    print(f"\n🎉 All tables processed successfully!")

if __name__ == "__main__":
    extract_remaining_tables()