import os
import sys
import shutil
import psycopg2
import glob
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import max as spark_max
from sqlalchemy import create_engine, text

# =====================================================================
# EMBEDDED AUDIT LOGGER
# =====================================================================
class SimpleAuditLogger:
    def __init__(self, engine):
        self.engine = engine

    def log_start(self, pipeline_name, execution_id, task_name, table_name):
        insert_sql = text("""
            INSERT INTO control.audit_log (pipeline_name, execution_id, task_name, table_name, status)
            VALUES (:pipeline_name, :execution_id, :task_name, :table_name, 'STARTED')
            RETURNING audit_id;
        """)
        with self.engine.begin() as conn:
            result = conn.execute(insert_sql, {
                "pipeline_name": pipeline_name,
                "execution_id": execution_id,
                "task_name": task_name,
                "table_name": table_name
            })
            return result.scalar()

    def log_complete(self, audit_id, status, rows_processed=0, error_message=None):
        update_sql = text("""
            UPDATE control.audit_log
            SET completed_at = CURRENT_TIMESTAMP,
                status = :status,
                rows_processed = :rows_processed,
                error_message = :error_message
            WHERE audit_id = :audit_id;
        """)
        with self.engine.begin() as conn:
            conn.execute(update_sql, {
                "status": status,
                "rows_processed": rows_processed,
                "error_message": error_message,
                "audit_id": audit_id
            })

# =====================================================================
# MAIN INCREMENTAL LOAD LOGIC
# =====================================================================
def _drop_bronze_foreign_keys(pg_conn):
    """
    Drops rigid Foreign Key constraints from the Bronze layer to allow 
    for out-of-order time-series ingestion of synthetic data.
    """
    print("\n" + "="*50)
    
    drop_sql = """
        ALTER TABLE bronze.lineitem DROP CONSTRAINT IF EXISTS lineitem_l_orderkey_fkey;
        ALTER TABLE bronze.lineitem DROP CONSTRAINT IF EXISTS lineitem_l_partkey_fkey;
        ALTER TABLE bronze.lineitem DROP CONSTRAINT IF EXISTS lineitem_l_suppkey_fkey;
        
        -- Add any additional tables/constraints here if needed
        ALTER TABLE bronze.orders DROP CONSTRAINT IF EXISTS orders_o_custkey_fkey;
        ALTER TABLE bronze.customer DROP CONSTRAINT IF EXISTS customer_c_nationkey_fkey;
        ALTER TABLE bronze.supplier DROP CONSTRAINT IF EXISTS supplier_s_nationkey_fkey;
        ALTER TABLE bronze.partsupp DROP CONSTRAINT IF EXISTS partsupp_ps_partkey_fkey;
        ALTER TABLE bronze.partsupp DROP CONSTRAINT IF EXISTS partsupp_ps_suppkey_fkey;
        ALTER TABLE bronze.nation DROP CONSTRAINT IF EXISTS nation_n_regionkey_fkey;
    """
    try:
        cur = pg_conn.cursor()
        cur.execute(drop_sql)
        print("   ✅ Bronze FK constraints dropped successfully.")
    except Exception as e:
        print(f"   ⚠️ Could not drop constraints: {e}")
    finally:
        cur.close()

def run_fast_incremental_load(target_year):
    # Ensure year format is correct (extracts just the year if "batch_1996" is passed)
    year_str = str(target_year).replace("batch_", "").replace("year_", "")
    print(f"🚀 Starting ULTRA-FAST Incremental Load for BATCH/YEAR {year_str} ...")

    spark = SparkSession.builder \
        .appName(f"Fast_Inc_Load_{year_str}") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()

    control_engine = create_engine('postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control')
    audit_logger = SimpleAuditLogger(control_engine)

    inc_dir = f'/home/jovyan/data/raw/tables/work_data/increments/batch_{year_str}'
    temp_dir_base = '/home/jovyan/work/temp_csv_export_inc'
    
    tables_config = {
        'orders': {'inc_col': 'o_orderdate', 'is_date': True},
        'lineitem': {'inc_col': 'l_shipdate', 'is_date': True}
    }

    pg_conn = psycopg2.connect(
        host="postgres-local", port=5432, 
        dbname="data_platform_db", user="source_user", password="source_pass"
    )
    pg_conn.autocommit = True
    
    # Run the constraint drop before looping through the tables
    _drop_bronze_foreign_keys(pg_conn)

    cur = pg_conn.cursor()
    execution_id = f'prod_fast_inc_v4_batch_{year_str}'

    for table, config in tables_config.items():
        file_pattern = f"{inc_dir}/**/{table}.parquet"
        inc_col = config['inc_col']
        is_date = config['is_date']
        incremental_type = 'date' if is_date else 'numeric'
        table_name_full = f"bronze.{table}"
        temp_dir = f"{temp_dir_base}_{table}"
        
        # Now glob will search the folder and any subfolders inside it
        matched_files = glob.glob(file_pattern, recursive=True)
        
        if matched_files:
            # Pick the first matched file path to read
            actual_file_path = matched_files[0]
            print(f"\n{'='*50}\n🔍 Checking for NEW data in {table_name_full} from Batch {year_str}...")
            
            with control_engine.connect() as conn:
                query = text(f"SELECT last_processed_value FROM control.watermarks WHERE table_name = '{table_name_full}'")
                result = conn.execute(query).fetchone()
                
                if result and result[0] is not None:
                    current_wm = result[0]
                else:
                    current_wm = '1900-01-01' if is_date else '0'
                
            print(f"   📌 Current Watermark: {current_wm}")
            audit_id = audit_logger.log_start("SalesOps_Fast_Incremental", execution_id, f"fast_inc_{table}", table_name_full)
            
            try:
                # Read ONLY the specific parquet file, not the parent directory
                df_source = spark.read.parquet(actual_file_path)
                
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
                
                print(f"   📈 Calculating NEW Max Value...")
                max_id_row = df_new.agg(spark_max(inc_col).alias("max_id")).collect()[0]
                new_max_val = max_id_row["max_id"]
                
                print(f"   🔖 Updating Watermark to NEW Value: {new_max_val}")
                
                formatted_new_max = str(new_max_val)
                
                upsert_query = text("""
                    INSERT INTO control.watermarks (table_name, last_processed_value, incremental_column, incremental_type, updated_at)
                    VALUES (:table_name, :max_val, :inc_col, :inc_type, CURRENT_TIMESTAMP)
                    ON CONFLICT (table_name) 
                    DO UPDATE SET 
                        last_processed_value = EXCLUDED.last_processed_value,
                        incremental_column = EXCLUDED.incremental_column,
                        incremental_type = EXCLUDED.incremental_type,
                        updated_at = CURRENT_TIMESTAMP;
                """)
                
                with control_engine.begin() as conn:
                    conn.execute(upsert_query, {
                        "table_name": table_name_full,
                        "max_val": formatted_new_max,
                        "inc_col": inc_col,
                        "inc_type": incremental_type
                    })

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
    print(f"\n🎉 ULTRA-FAST INCREMENTAL LOAD FOR BATCH {year_str} COMPLETE!")

if __name__ == "__main__":
    import re
    
    # Default to 1996 if nothing is passed
    target_input = "1996" 
    
    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
        # Extract just the 4-digit year, whether they passed "1996", "batch_1996", or "year_1996"
        match = re.search(r'\d{4}', raw_input)
        if match:
            target_input = match.group(0)
        else:
            print(f"❌ Error: Could not find a valid year in argument '{raw_input}'")
            sys.exit(1)
            
    run_fast_incremental_load(target_input)