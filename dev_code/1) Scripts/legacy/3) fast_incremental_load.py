import os
import sys
import shutil
import psycopg2
import glob
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import max as spark_max
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from audit.audit_logger import AuditLogger

def run_fast_incremental_load(batch_name):
    print(f"🚀 Starting ULTRA-FAST Incremental Load for {batch_name.upper()} ...")

    spark = SparkSession.builder \
        .appName(f"Fast_Inc_Load_{batch_name}") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()

    control_engine = create_engine('postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control')
    audit_logger = AuditLogger(control_engine)

    inc_dir = f'/home/jovyan/data/raw/tables/work_data/increments/{batch_name}'
    temp_dir_base = '/home/jovyan/work/temp_csv_export_inc'
    
    tables_config = {
        'orders': {'inc_col': 'o_orderkey'},
        'lineitem': {'inc_col': 'l_orderkey'}
    }

    pg_conn = psycopg2.connect(
        host="postgres-local", port=5432, 
        dbname="data_platform_db", user="source_user", password="source_pass"
    )
    pg_conn.autocommit = True
    cur = pg_conn.cursor()

    execution_id = f'prod_fast_inc_v3_{batch_name}'

    for table, config in tables_config.items():
        file_pattern = f"{inc_dir}/*/{table}.parquet"
        inc_col = config['inc_col']
        table_name_full = f"bronze.{table}"
        temp_dir = f"{temp_dir_base}_{table}"
        
        matched_files = glob.glob(file_pattern)
        
        if matched_files:
            print(f"\n{'='*50}\n🔍 Checking for NEW data in {table_name_full} from {batch_name} (Across all years)...")
            
            with control_engine.connect() as conn:
                query = text(f"SELECT last_processed_id FROM control.watermarks WHERE table_name = '{table_name_full}'")
                result = conn.execute(query).fetchone()
                current_wm = float(result[0]) if result and result[0] is not None else 0.0
                
            print(f"   📌 Current Watermark: {current_wm}")
            audit_id = audit_logger.log_start("SalesOps_Fast_Incremental", execution_id, f"fast_inc_{table}", table_name_full)
            
            try:
                df_source = spark.read.parquet(file_pattern)
                df_new = df_source.filter(F.col(inc_col) > current_wm)
                new_rows_count = df_new.count()
                
                if new_rows_count == 0:
                    print(f"   🛑 No new data found > {current_wm}. Skipping gracefully.")
                    audit_logger.log_complete(audit_id, status='SUCCESS', rows_processed=0)
                    continue
                
                if table == 'lineitem':
                    if 'l_id' in df_new.columns:
                        df_new = df_new.drop('l_id') 
                    df_new = df_new.withColumn("l_id", F.monotonically_increasing_id()) 

                print(f"   ⚡ Found {new_rows_count} NEW rows! Exporting to CSV...")
                df_new.write.csv(temp_dir, header=True, mode="overwrite", quote='"', escape='"')
                
                print(f"   🚀 Injecting new data directly into PostgreSQL using COPY...")
                columns_str = ", ".join(df_new.columns)
                copy_sql = f"COPY {table_name_full} ({columns_str}) FROM STDIN WITH CSV HEADER QUOTE '\"' ESCAPE '\"'"
                
                for file_name in os.listdir(temp_dir):
                    if file_name.endswith(".csv"):
                        with open(os.path.join(temp_dir, file_name), 'r') as f:
                            cur.copy_expert(copy_sql, f)
                
                print(f"   📈 Calculating NEW Max ID...")
                max_id_row = df_new.agg(spark_max(inc_col).alias("max_id")).collect()[0]
                new_max_val = max_id_row["max_id"]
                
                print(f"   🔖 Updating Watermark to NEW ID: {new_max_val}")
                
                upsert_query = text(f"""
                    INSERT INTO control.watermarks (table_name, last_processed_id, incremental_column, updated_at)
                    VALUES ('{table_name_full}', {new_max_val}, '{inc_col}', CURRENT_TIMESTAMP)
                    ON CONFLICT (table_name) 
                    DO UPDATE SET 
                        last_processed_id = EXCLUDED.last_processed_id,
                        incremental_column = EXCLUDED.incremental_column,
                        updated_at = CURRENT_TIMESTAMP;
                """)
                
                with control_engine.begin() as conn:
                    conn.execute(upsert_query)

                audit_logger.log_complete(audit_id, status='SUCCESS', rows_processed=new_rows_count)
                print(f"   ✅ Incremental load for {table_name_full} completed successfully!")
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                audit_logger.log_complete(audit_id, status='FAILED', error_message=str(e))
                
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    print(f"   🧹 Smart Cleanup: Deleted temporary folder '{temp_dir}'")
        else:
            print(f"❌ No data found matching pattern: {file_pattern}")

    cur.close()
    pg_conn.close()
    spark.stop()
    print(f"\n🎉 ULTRA-FAST INCREMENTAL LOAD FOR {batch_name.upper()} COMPLETE!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_batch = sys.argv[1]
    else:
        target_batch = "batch_1" 
        
    run_fast_incremental_load(target_batch)

