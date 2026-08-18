import pandas as pd
from sqlalchemy import create_engine, text
import sys
import os

# إضافة المسار عشان نقدر نوصل لملفات الـ Audit
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audit.watermark_manager import WatermarkManager
from audit.audit_logger import AuditLogger

def extract_incremental_lineitems():
    print("🚀 Starting Incremental Extraction for 'lineitem' table (The Giant)...")
    
    # 1. إعداد الاتصال بقواعد البيانات
    source_engine = create_engine('postgresql+psycopg2://source_user:source_pass@postgres-local:5432/data_platform_db')
    control_engine = create_engine('postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control')
    
    wm_manager = WatermarkManager(control_engine)
    audit_logger = AuditLogger(control_engine)
    
    table_name = 'bronze.lineitem'
    task_name = 'extract_lineitems_incremental'
    execution_id = 'manual_test_002' # Airflow هيغير الرقم ده بعدين
    
    # 2. تسجيل بداية العملية
    audit_id = audit_logger.log_start("SalesOps_Incremental_ETL", execution_id, task_name, table_name)
    
    try:
        # 3. قراءة الـ Watermark القديم
        watermark = wm_manager.get_watermark(table_name)
        safe_id = watermark['safe_extraction_id'] if watermark else 0
        
        extract_query = text(f"""
            SELECT * FROM bronze.lineitem 
            WHERE l_id > :safe_id 
            ORDER BY l_id ASC
        """)
        
        print(f"📡 Fetching records with ID > {safe_id}... (Reading in chunks to save RAM)")
        
        rows_extracted = 0
        max_id = 0
        
        # 4. السحب الذكي على دفعات (Chunks) لحماية الذاكرة
        with source_engine.connect() as conn:
            # هنقرا 500 ألف صف في المرة الواحدة
            df_iterator = pd.read_sql(extract_query, conn, params={"safe_id": safe_id}, chunksize=500000)
            
            for i, chunk in enumerate(df_iterator):
                rows_extracted += len(chunk)
                current_max = chunk['l_id'].max()
                if current_max > max_id:
                    max_id = current_max
                print(f"   ⏳ Processed chunk {i+1}... (Total rows so far: {rows_extracted})")
                
                # Note: In a real pipeline, we would save each chunk to a Parquet file here.
        
        print(f"📦 Successfully extracted {rows_extracted} new rows from {table_name}.")
        
        if rows_extracted > 0:
            # 5. تحديث الـ Watermark
            wm_manager.update_watermark(table_name, new_max_id=int(max_id))
        
        # 6. تسجيل النهاية بنجاح
        audit_logger.log_complete(audit_id, status='SUCCESS', rows_processed=rows_extracted)
        print("🎉 Extraction completed safely and successfully!")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        audit_logger.log_complete(audit_id, status='FAILED', error_message=str(e))

if __name__ == "__main__":
    extract_incremental_lineitems()