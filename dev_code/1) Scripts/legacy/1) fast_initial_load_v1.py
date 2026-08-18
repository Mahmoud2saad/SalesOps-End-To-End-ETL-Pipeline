import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import monotonically_increasing_id, max as spark_max
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from audit.watermark_manager import WatermarkManager
from audit.audit_logger import AuditLogger

def run_production_initial_load():
    print("🚀 Starting ENTERPRISE-GRADE Full Load with PySpark (JDBC)...")

    spark = SparkSession.builder \
        .appName("Initial_Data_Load_Enterprise_JDBC") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "200") \
        .getOrCreate()

    jdbc_url = "jdbc:postgresql://postgres-local:5432/data_platform_db?rewriteBatchedInserts=true"
    
    control_engine = create_engine('postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control')
    wm_manager = WatermarkManager(control_engine)
    audit_logger = AuditLogger(control_engine)

    data_dir = '/home/jovyan/data/tpch-sf1-parquet/'
    
    tables_config = {
        'region': 'r_regionkey', 'nation': 'n_nationkey', 
        'part': 'p_partkey', 'supplier': 's_suppkey', 
        'customer': 'c_custkey', 'orders': 'o_orderkey', 
        'partsupp': 'ps_id', 'lineitem': 'l_id'
    }

    execution_id = 'prod_jdbc_load_v1'

    for table, inc_col in tables_config.items():
        file_path = os.path.join(data_dir, f"{table}_data.parquet")
        table_name_full = f"bronze.{table}"
        
        if os.path.exists(file_path):
            print(f"\n{'='*50}\n🔄 Processing {table_name_full}...")
            audit_id = audit_logger.log_start("SalesOps_JDBC_Load", execution_id, f"load_{table}_initial", table_name_full)
            
            try:
                df = spark.read.parquet(file_path)
                
                if table == 'partsupp' and 'ps_id' not in df.columns:
                    df = df.withColumn("ps_id", monotonically_increasing_id())
                elif table == 'lineitem' and 'l_id' not in df.columns:
                    df = df.withColumn("l_id", monotonically_increasing_id())
                
                rows_count = df.count()
                optimal_partitions = max(1, int(rows_count / 500000))
                
                print(f"   ⚖️ Data size: {rows_count} rows. Repartitioning into {optimal_partitions} optimized chunks...")
                df_optimized = df.repartition(optimal_partitions)
                
                conn_props = {
                    "user": "source_user",
                    "password": "source_pass",
                    "driver": "org.postgresql.Driver",
                    "batchsize": "100000", 
                    "numPartitions": str(optimal_partitions)
                }
                
                print(f"   💾 Writing chunks to PostgreSQL via JDBC in parallel...")
                df_optimized.write.jdbc(url=jdbc_url, table=table_name_full, mode="append", properties=conn_props)
                
                print(f"   📈 Calculating Max ID for watermark...")
                max_id_row = df.agg(spark_max(inc_col).alias("max_id")).collect()[0]
                max_id_val = max_id_row["max_id"] if max_id_row["max_id"] is not None else 0
                
                print(f"   🔖 Auto-Updating Watermark to ID: {max_id_val}")
                wm_manager.update_watermark(table_name_full, int(max_id_val))
                
                with control_engine.begin() as conn:
                    conn.execute(text(f"UPDATE control.watermarks SET incremental_column = '{inc_col}' WHERE table_name = '{table_name_full}'"))

                audit_logger.log_complete(audit_id, status='SUCCESS', rows_processed=rows_count)
                print(f"   ✅ {table_name_full} loaded successfully via JDBC!")
                
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                audit_logger.log_complete(audit_id, status='FAILED', error_message=str(e))
        else:
            print(f"❌ File not found: {file_path}")

    spark.stop()
    print("\n🎉 ENTERPRISE JDBC INITIAL LOAD COMPLETE!")

if __name__ == "__main__":
    run_production_initial_load()