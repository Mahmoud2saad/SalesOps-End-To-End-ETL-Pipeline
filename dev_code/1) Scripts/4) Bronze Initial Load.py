# Gemini answer 2
import os
import shutil
import psycopg2
from datetime import date
from pyspark.sql import SparkSession
from pyspark.sql.functions import monotonically_increasing_id, max as spark_max
from sqlalchemy import create_engine, text

# =====================================================================
# EMBEDDED AUDIT LOGGER AND DATABASE SETUP
# =====================================================================
class SimpleAuditLogger:
    def __init__(self, engine):
        self.engine = engine
        self._reset_and_initialize_database()

    def _reset_and_initialize_database(self):
        """Drops the control schema and recreates all necessary tables."""
        print("🔧 Resetting and initializing the control database schema...")
        setup_sql = text("""
            -- 1. DROP THE ENTIRE SCHEMA TO START FRESH
            DROP SCHEMA IF EXISTS control CASCADE;
            CREATE SCHEMA control;

            -- 2. CREATE FLEXIBLE WATERMARKS TABLE
            CREATE TABLE control.watermarks (
                table_name VARCHAR(100) PRIMARY KEY,
                last_processed_value VARCHAR(100), -- CHANGED: Stores both dates and IDs as strings
                incremental_column VARCHAR(50),
                incremental_type VARCHAR(20),      -- 'numeric' or 'date'
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 3. CREATE AUDIT LOG TABLE
            CREATE TABLE control.audit_log (
                audit_id BIGSERIAL PRIMARY KEY,
                pipeline_name VARCHAR(100),
                execution_id VARCHAR(100),
                task_name VARCHAR(100),
                table_name VARCHAR(100),
                status VARCHAR(20) CHECK (status IN ('STARTED', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED')),
                rows_processed BIGINT,
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            -- 4. CREATE DATA QUALITY METRICS TABLE
            CREATE TABLE control.data_quality_metrics (
                metric_id BIGSERIAL PRIMARY KEY,
                table_name VARCHAR(100),
                check_name VARCHAR(100),
                metric_type VARCHAR(50), 
                expected_value VARCHAR(500),
                actual_value VARCHAR(500),
                passed BOOLEAN,
                severity VARCHAR(20) CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                execution_id VARCHAR(100),
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details JSONB
            );
        """)
        with self.engine.begin() as conn:
            conn.execute(setup_sql)
        print("✅ Control schema initialized successfully.")

    def log_start(self, pipeline_name, execution_id, task_name, table_name):
        """Logs the start of a task and returns the audit_id."""
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
        """Updates the log entry with completion status."""
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
# MAIN PIPELINE LOGIC
# =====================================================================
def run_fast_initial_load():
    print("🚀 Starting ULTRA-FAST Initial Bulk Load")

    spark = SparkSession.builder \
        .appName("Fast_Bulk_Load_Standalone") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()

    control_engine = create_engine('postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control')
    
    # Initialize the embedded logger (this will drop and recreate the tables)
    audit_logger = SimpleAuditLogger(control_engine)

    base_dir_dims = '/home/jovyan/data/raw/tables/original'
    base_dir_facts = '/home/jovyan/data/raw/tables/work_data/bases'
    temp_dir_base = '/home/jovyan/work/temp_csv_export'
    
    tables_config = {
        'region': {'inc_col': 'r_regionkey', 'is_date': False, 'file_path': f"{base_dir_dims}/region.parquet"},
        'nation': {'inc_col': 'n_nationkey', 'is_date': False, 'file_path': f"{base_dir_dims}/nation.parquet"},
        'part': {'inc_col': 'p_partkey', 'is_date': False, 'file_path': f"{base_dir_dims}/part.parquet"},
        'supplier': {'inc_col': 's_suppkey', 'is_date': False, 'file_path': f"{base_dir_dims}/supplier.parquet"},
        'customer': {'inc_col': 'c_custkey', 'is_date': False, 'file_path': f"{base_dir_dims}/customer.parquet"},
        'partsupp': {'inc_col': 'ps_partkey', 'is_date': False, 'file_path': f"{base_dir_dims}/partsupp.parquet"},
        'orders': {'inc_col': 'o_orderdate', 'is_date': True, 'file_path': f"{base_dir_facts}/orders_base.parquet"},
        'lineitem': {'inc_col': 'l_shipdate', 'is_date': True, 'file_path': f"{base_dir_facts}/lineitem_base.parquet"}
    }

    pg_conn = psycopg2.connect(
        host="postgres-local", port=5432, 
        dbname="data_platform_db", user="source_user", password="source_pass"
    )
    pg_conn.autocommit = True
    cur = pg_conn.cursor()

    execution_id = 'prod_bulk_load_v5_flexible_watermarks'

    for table, config in tables_config.items():
        file_path = config['file_path']
        inc_col = config['inc_col']
        is_date = config['is_date']
        incremental_type = 'date' if is_date else 'numeric'
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
                
                print(f"   📈 Calculating Max Value ({inc_col}) for watermark...")
                max_val_row = df.agg(spark_max(inc_col).alias("max_val")).collect()[0]
                max_val = max_val_row["max_val"]
                
                if max_val is None:
                    max_val = '1900-01-01' if is_date else 0
                
                print(f"   🔖 Explicitly Saving Watermark: {max_val}")
                
                # Treat everything as a string to fit the new VARCHAR column
                formatted_max_val = str(max_val)

                # Update query to target last_processed_value
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
                        "max_val": formatted_max_val,
                        "inc_col": inc_col,
                        "inc_type": incremental_type
                    })

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