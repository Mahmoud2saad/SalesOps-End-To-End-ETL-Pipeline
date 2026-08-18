import os
import sys
import shutil
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import monotonically_increasing_id, max as spark_max
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from audit.audit_logger import AuditLogger

def run_fast_initial_load():
    print("🚀 Starting ULTRA-FAST Initial Bulk Load")

    spark = SparkSession.builder \
        .appName("Fast_Bulk_Load_V3") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()

    control_engine = create_engine('postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control')
    audit_logger = AuditLogger(control_engine)

    base_dir_dims = '/home/jovyan/data/raw/tables/original'
    base_dir_facts = '/home/jovyan/data/raw/tables/work_data/bases'
    temp_dir_base = '/home/jovyan/work/temp_csv_export'
    
    tables_config = {
        'region': {'inc_col': 'r_regionkey', 'file_path': f"{base_dir_dims}/region.parquet"},
        'nation': {'inc_col': 'n_nationkey', 'file_path': f"{base_dir_dims}/nation.parquet"},
        'part': {'inc_col': 'p_partkey', 'file_path': f"{base_dir_dims}/part.parquet"},
        'supplier': {'inc_col': 's_suppkey', 'file_path': f"{base_dir_dims}/supplier.parquet"},
        'customer': {'inc_col': 'c_custkey', 'file_path': f"{base_dir_dims}/customer.parquet"},
        'partsupp': {'inc_col': 'ps_partkey', 'file_path': f"{base_dir_dims}/partsupp.parquet"},
        'orders': {'inc_col': 'o_orderkey', 'file_path': f"{base_dir_facts}/orders_base_60.parquet"},
        'lineitem': {'inc_col': 'l_orderkey', 'file_path': f"{base_dir_facts}/lineitem_base_60.parquet"}
    }

    pg_conn = psycopg2.connect(
        host="postgres-local", port=5432, 
        dbname="data_platform_db", user="source_user", password="source_pass"
    )
    pg_conn.autocommit = True
    cur = pg_conn.cursor()

    execution_id = 'prod_bulk_load_v3_fixed'

    for table, config in tables_config.items():
        file_path = config['file_path']
        inc_col = config['inc_col']
        table_name_full = f"bronze.{table}"
        temp_dir = f"{temp_dir_base}_{table}"
        
        if os.path.exists(file_path):
            print(f"\n{'='*50}\n⚡ Bulk Loading {table_name_full} from {file_path.split('/')[-1]}...")
            audit_id = audit_logger.log_start("SalesOps_Initial_Bulk_Load", execution_id, f"bulk_load_{table}", table_name_full)
            
            try:
                df = spark.read.parquet(file_path)
                
                if table == 'partsupp' and 'ps_id' not in df.columns:
                    df = df.withColumn("ps_id", monotonically_increasing_id())
                elif table == 'lineitem' and 'l_id' not in df.columns:
                    df = df.withColumn("l_id", monotonically_increasing_id())
                
                rows_count = df.count()
                
                print(f"   💾 Exporting {rows_count} rows to temporary CSV chunks...")
                df.write.csv(temp_dir, header=True, mode="overwrite", quote='"', escape='"')
                
                print(f"   🚀 Injecting chunks directly into PostgreSQL using COPY...")
                columns_str = ", ".join(df.columns)
                copy_sql = f"COPY {table_name_full} ({columns_str}) FROM STDIN WITH CSV HEADER QUOTE '\"' ESCAPE '\"'"
                
                for file_name in os.listdir(temp_dir):
                    if file_name.endswith(".csv"):
                        with open(os.path.join(temp_dir, file_name), 'r') as f:
                            cur.copy_expert(copy_sql, f)
                
                print(f"   📈 Calculating Max ID ({inc_col}) for watermark...")
                max_id_row = df.agg(spark_max(inc_col).alias("max_id")).collect()[0]
                max_id_val = max_id_row["max_id"] if max_id_row["max_id"] is not None else 0
                
                print(f"   🔖 Explicitly Saving Watermark: {max_id_val}")
                
                upsert_query = text(f"""
                    INSERT INTO control.watermarks (table_name, last_processed_id, incremental_column, updated_at)
                    VALUES ('{table_name_full}', {max_id_val}, '{inc_col}', CURRENT_TIMESTAMP)
                    ON CONFLICT (table_name) 
                    DO UPDATE SET 
                        last_processed_id = EXCLUDED.last_processed_id,
                        incremental_column = EXCLUDED.incremental_column,
                        updated_at = CURRENT_TIMESTAMP;
                """)
                
                with control_engine.begin() as conn:
                    conn.execute(upsert_query)

                audit_logger.log_complete(audit_id, status='SUCCESS', rows_processed=rows_count)
                print(f"   ✅ {table_name_full} bulk loaded successfully in RECORD TIME!")
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                audit_logger.log_complete(audit_id, status='FAILED', error_message=str(e))
                
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    print(f"   🧹 Smart Cleanup: Deleted temporary folder '{temp_dir}'")
        else:
            print(f"❌ File not found: {file_path}")

    cur.close()
    pg_conn.close()
    spark.stop()
    print("\n🎉 ULTRA-FAST INITIAL LOAD COMPLETE!")

if __name__ == "__main__":
    run_fast_initial_load()