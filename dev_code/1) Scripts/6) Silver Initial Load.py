import os
import shutil
import psycopg2
from datetime import date
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    monotonically_increasing_id, max as spark_max, col, abs, 
    regexp_extract, current_timestamp, lit
)
from pyspark.sql.types import IntegerType, DecimalType, DateType, LongType, TimestampType
from sqlalchemy import create_engine, text

# ============================================================================
# HELPER FUNCTIONS (Integrated Cleaning)
# ============================================================================

def remove_comment_column(df, table_name):
    """Remove comment column from dataframe"""
    if 'p_comment' in df.columns:
        df = df.drop('p_comment')
        print(f"   ✓ Removed p_comment from {table_name}")
    if 'c_comment' in df.columns:
        df = df.drop('c_comment')
        print(f"   ✓ Removed c_comment from {table_name}")
    if 'o_comment' in df.columns:
        df = df.drop('o_comment')
        print(f"   ✓ Removed o_comment from {table_name}")
    if 'l_comment' in df.columns:
        df = df.drop('l_comment')
        print(f"   ✓ Removed l_comment from {table_name}")
    if 's_comment' in df.columns:
        df = df.drop('s_comment')
        print(f"   ✓ Removed s_comment from {table_name}")
    if 'n_comment' in df.columns:
        df = df.drop('n_comment')
        print(f"   ✓ Removed n_comment from {table_name}")
    if 'r_comment' in df.columns:
        df = df.drop('r_comment')
        print(f"   ✓ Removed r_comment from {table_name}")
    if 'ps_comment' in df.columns:
        df = df.drop('ps_comment')
        print(f"   ✓ Removed ps_comment from {table_name}")
    return df

def write_single_parquet(df, output_path):
    """Write DataFrame as a single parquet file (not a directory)"""
    temp_dir = output_path + "_temp"
    df.coalesce(1).write.mode("overwrite").parquet(temp_dir)
    for file in os.listdir(temp_dir):
        if file.endswith('.parquet'):
            shutil.move(os.path.join(temp_dir, file), output_path)
            break
    shutil.rmtree(temp_dir)
    return output_path

# =====================================================================
# SILVER DATABASE SETUP
# =====================================================================
class SilverSchemaManager:
    def __init__(self, engine):
        self.engine = engine
        self._create_silver_schema_and_tables()

    def _create_silver_schema_and_tables(self):
        """Creates the silver schema and all necessary tables """
        print("🔧 Creating silver schema and tables ")
        
        setup_sql = text("""
            -- 1. CREATE SILVER SCHEMA
            CREATE SCHEMA IF NOT EXISTS silver;
            
            -- 2. DROP EXISTING TABLES IF THEY EXIST (FOR CLEAN SLATE)
            DROP TABLE IF EXISTS silver.region CASCADE;
            DROP TABLE IF EXISTS silver.nation CASCADE;
            DROP TABLE IF EXISTS silver.part CASCADE;
            DROP TABLE IF EXISTS silver.supplier CASCADE;
            DROP TABLE IF EXISTS silver.customer CASCADE;
            DROP TABLE IF EXISTS silver.partsupp CASCADE;
            DROP TABLE IF EXISTS silver.orders CASCADE;
            DROP TABLE IF EXISTS silver.lineitem CASCADE;
            
            -- 3. CREATE DIMENSION TABLES
            
            -- Region Dimension
            CREATE TABLE silver.region (
                r_regionkey INTEGER PRIMARY KEY,
                r_name VARCHAR(25),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Nation Dimension
            CREATE TABLE silver.nation (
                n_nationkey INTEGER PRIMARY KEY,
                n_name VARCHAR(25),
                n_regionkey INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Part Dimension (with extracted IDs)
            CREATE TABLE silver.part (
                p_partkey INTEGER PRIMARY KEY,
                p_name VARCHAR(55),
                p_mfgr_id INTEGER,
                p_brand_id INTEGER,
                p_type VARCHAR(25),
                p_size INTEGER,
                p_container VARCHAR(10),
                p_retailprice DECIMAL(15,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Supplier Dimension (cleaned)
            CREATE TABLE silver.supplier (
                s_suppkey INTEGER PRIMARY KEY,
                s_name_id INTEGER,  -- Modified to hold extracted integer ID
                s_nationkey INTEGER,
                s_acctbal DECIMAL(15,2),
                s_phone VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Customer Dimension (no address column)
            CREATE TABLE silver.customer (
                c_custkey INTEGER PRIMARY KEY,
                c_name_id INTEGER,  -- Modified to hold extracted integer ID
                c_nationkey INTEGER,
                c_acctbal DECIMAL(15,2),
                c_phone VARCHAR(15),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Partsupp Table (with SCD Type 2)
            CREATE TABLE silver.partsupp (
                ps_partkey INTEGER,
                ps_suppkey INTEGER,
                ps_availqty INTEGER,
                ps_supplycost DECIMAL(15,2),
                valid_from TIMESTAMP,
                valid_to TIMESTAMP,
                is_current BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (ps_partkey, ps_suppkey, valid_from)
            );
            
            -- Orders Fact Table (cleaned)
            CREATE TABLE silver.orders (
                o_orderkey INTEGER PRIMARY KEY,
                o_custkey INTEGER,
                o_orderstatus CHAR(1),
                o_totalprice DECIMAL(15,2),
                o_orderdate DATE,
                o_orderpriority VARCHAR(15),
                o_clerk_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Lineitem Fact Table
            CREATE TABLE silver.lineitem (
                l_orderkey INTEGER,
                l_partkey INTEGER,
                l_suppkey INTEGER,
                l_linenumber INTEGER,
                l_quantity DECIMAL(15,2),
                l_extendedprice DECIMAL(15,2),
                l_discount DECIMAL(15,2),
                l_tax DECIMAL(15,2),
                l_returnflag CHAR(1),
                l_linestatus CHAR(1),
                l_shipdate DATE,
                l_commitdate DATE,
                l_receiptdate DATE,
                l_shipinstruct VARCHAR(25),
                l_shipmode VARCHAR(10),
                l_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (l_orderkey, l_linenumber)
            );
            
            -- 4. CREATE INDEXES FOR PERFORMANCE 
            CREATE INDEX idx_nation_regionkey ON silver.nation(n_regionkey);
            CREATE INDEX idx_supplier_nationkey ON silver.supplier(s_nationkey);
            CREATE INDEX idx_customer_nationkey ON silver.customer(c_nationkey);
            CREATE INDEX idx_orders_custkey ON silver.orders(o_custkey);
            CREATE INDEX idx_orders_orderdate ON silver.orders(o_orderdate);
            CREATE INDEX idx_lineitem_orderkey ON silver.lineitem(l_orderkey);
            CREATE INDEX idx_lineitem_partkey ON silver.lineitem(l_partkey);
            CREATE INDEX idx_lineitem_suppkey ON silver.lineitem(l_suppkey);
            CREATE INDEX idx_lineitem_shipdate ON silver.lineitem(l_shipdate);
            CREATE INDEX idx_partsupp_partkey ON silver.partsupp(ps_partkey);
            CREATE INDEX idx_partsupp_suppkey ON silver.partsupp(ps_suppkey);
            CREATE INDEX idx_partsupp_current ON silver.partsupp(is_current);
            
            -- 5. CREATE COMMENTS FOR DOCUMENTATION
            COMMENT ON SCHEMA silver IS 'Silver layer - Cleaned and transformed TPC-H data';
            COMMENT ON TABLE silver.region IS 'Region dimension table';
            COMMENT ON TABLE silver.nation IS 'Nation dimension table';
            COMMENT ON TABLE silver.part IS 'Part dimension with extracted manufacturer and brand IDs';
            COMMENT ON TABLE silver.supplier IS 'Supplier dimension with cleaned account balance';
            COMMENT ON TABLE silver.customer IS 'Customer dimension table';
            COMMENT ON TABLE silver.partsupp IS 'Part-Supplier bridge table with SCD Type 2 tracking';
            COMMENT ON TABLE silver.orders IS 'Orders fact table with extracted clerk ID';
            COMMENT ON TABLE silver.lineitem IS 'Lineitem fact table';
        """)
        
        with self.engine.begin() as conn:
            conn.execute(setup_sql)
        
        print("✅ Silver schema and tables created successfully!")

# =====================================================================
# MAIN SILVER LOAD LOGIC
# =====================================================================
def run_silver_initial_load():
    print("🚀 Starting Silver Layer Initial Load")
    print("="*80)

    # Initialize Spark
    spark = SparkSession.builder \
        .appName("Silver_Initial_Load") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .getOrCreate()

    # Create database connection for silver layer
    silver_engine = create_engine('postgresql+psycopg2://source_user:source_pass@postgres-local:5432/data_platform_db')
    
    # Initialize the silver schema manager (creates schema and tables)
    schema_manager = SilverSchemaManager(silver_engine)

    # Base directories for silver data
    base_dir_silver = '/home/jovyan/data/silver'
    dimensions_dir = f"{base_dir_silver}/dimensions"
    bases_dir = f"{base_dir_silver}/bases"
    
    # Temporary directory for CSV export
    temp_dir_base = '/home/jovyan/work/temp_silver_export'
    
    # Define expected columns for each table (matching the schema)
    expected_columns = {
        'region': ['r_regionkey', 'r_name'],
        'nation': ['n_nationkey', 'n_name', 'n_regionkey'],
        'part': ['p_partkey', 'p_name', 'p_mfgr_id', 'p_brand_id', 'p_type', 'p_size', 'p_container', 'p_retailprice'],
        'supplier': ['s_suppkey', 's_name_id', 's_nationkey', 's_acctbal', 's_phone'],
        'customer': ['c_custkey', 'c_name_id', 'c_nationkey', 'c_acctbal', 'c_phone'],
        'partsupp': ['ps_partkey', 'ps_suppkey', 'ps_availqty', 'ps_supplycost', 'valid_from', 'valid_to', 'is_current'],
        'orders': ['o_orderkey', 'o_custkey', 'o_orderstatus', 'o_totalprice', 'o_orderdate', 'o_orderpriority', 'o_clerk_id'],
        'lineitem': ['l_orderkey', 'l_partkey', 'l_suppkey', 'l_linenumber', 'l_quantity', 'l_extendedprice', 
                    'l_discount', 'l_tax', 'l_returnflag', 'l_linestatus', 'l_shipdate', 'l_commitdate', 
                    'l_receiptdate', 'l_shipinstruct', 'l_shipmode', 'l_id']
    }
    
    # Data type conversions for problematic columns
    type_conversions = {
        'l_quantity': lambda df: df.withColumn('l_quantity', col('l_quantity').cast(DecimalType(15,2))),
        'l_discount': lambda df: df.withColumn('l_discount', col('l_discount').cast(DecimalType(15,2))),
        'l_tax': lambda df: df.withColumn('l_tax', col('l_tax').cast(DecimalType(15,2)))
    }
    
    # Configuration for all silver tables
    tables_config = {
        'region': {
            'file_path': f"{dimensions_dir}/region.parquet",
            'table_name': 'silver.region',
            'has_surrogate_key': False,
            'expected_columns': expected_columns['region']
        },
        'nation': {
            'file_path': f"{dimensions_dir}/nation.parquet",
            'table_name': 'silver.nation',
            'has_surrogate_key': False,
            'expected_columns': expected_columns['nation']
        },
        'part': {
            'file_path': f"{dimensions_dir}/part.parquet",
            'table_name': 'silver.part',
            'has_surrogate_key': False,
            'expected_columns': expected_columns['part']
        },
        'supplier': {
            'file_path': f"{dimensions_dir}/supplier.parquet",
            'table_name': 'silver.supplier',
            'has_surrogate_key': False,
            'expected_columns': expected_columns['supplier']
        },
        'customer': {
            'file_path': f"{dimensions_dir}/customer.parquet",
            'table_name': 'silver.customer',
            'has_surrogate_key': False,
            'expected_columns': expected_columns['customer']
        },
        'partsupp': {
            'file_path': f"{dimensions_dir}/partsupp.parquet",
            'table_name': 'silver.partsupp',
            'has_surrogate_key': False,
            'expected_columns': expected_columns['partsupp']
        },
        'orders': {
            'file_path': f"{bases_dir}/orders_base.parquet",
            'table_name': 'silver.orders',
            'has_surrogate_key': False,
            'expected_columns': expected_columns['orders']
        },
        'lineitem': {
            'file_path': f"{bases_dir}/lineitem_base.parquet",
            'table_name': 'silver.lineitem',
            'has_surrogate_key': True,
            'surrogate_key_col': 'l_id',
            'expected_columns': expected_columns['lineitem']
        }
    }

    # PostgreSQL connection for COPY operations
    pg_conn = psycopg2.connect(
        host="postgres-local", port=5432, 
        dbname="data_platform_db", user="source_user", password="source_pass"
    )
    pg_conn.autocommit = True
    cur = pg_conn.cursor()

    # Track load statistics
    load_stats = []

    # Load each table
    for table_name, config in tables_config.items():
        file_path = config['file_path']
        full_table_name = config['table_name']
        temp_dir = f"{temp_dir_base}_{table_name}"
        
        if os.path.exists(file_path):
            print(f"\n{'='*60}")
            print(f"📥 Loading {full_table_name} from {file_path.split('/')[-1]}...")
            print(f"{'='*60}")
            
            try:
                # Read parquet file
                df = spark.read.parquet(file_path)
                
                # ====================================================================
                # INTEGRATED DATA CLEANING STEPS
                # ====================================================================
                # Remove comment columns from all tables
                df = remove_comment_column(df, table_name)
                
                if table_name == 'supplier':
                    if 's_address' in df.columns:
                        df = df.drop('s_address')
                        print("   ✓ Removed s_address from supplier")
                    df = df.withColumn('s_acctbal', abs(col('s_acctbal')))
                    print("   ✓ Converted negative s_acctbal to positive values")
                    if 's_name' in df.columns:
                        df = df.withColumn('s_name_id', regexp_extract(col('s_name'), r'#(\d+)', 1).cast(IntegerType()))
                        df = df.drop('s_name')
                        print("   ✓ Extracted s_name_id from supplier table")
                        
                elif table_name == 'customer':
                    if 'c_name' in df.columns:
                        df = df.withColumn('c_name_id', regexp_extract(col('c_name'), r'#(\d+)', 1).cast(IntegerType()))
                        df = df.drop('c_name')
                        print("   ✓ Extracted c_name_id from customer table")
                
                elif table_name == 'partsupp':
                    df = df.withColumn('valid_from', current_timestamp()) \
                           .withColumn('valid_to', lit(None).cast('timestamp')) \
                           .withColumn('is_current', lit(True))
                    print("   ✓ Added SCD Type 2 columns to partsupp (valid_from, valid_to, is_current)")
                    
                elif table_name == 'part':
                    if 'p_mfgr' in df.columns:
                        df = df.withColumn('p_mfgr_id', regexp_extract(col('p_mfgr'), r'#(\d+)', 1).cast(IntegerType()))
                        df = df.withColumn('p_brand_id', regexp_extract(col('p_brand'), r'#(\d+)', 1).cast(IntegerType()))
                        df = df.drop('p_mfgr', 'p_brand')
                        print("   ✓ Extracted p_mfgr_id and p_brand_id from part table")
                        
                elif table_name == 'orders':
                    if 'o_clerk' in df.columns:
                        df = df.withColumn('o_clerk_id', regexp_extract(col('o_clerk'), r'#(\d+)', 1).cast(LongType()))
                        df = df.drop('o_clerk')
                        print("   ✓ Extracted o_clerk_id from orders table")
                    if 'o_shippriority' in df.columns:
                        df = df.drop('o_shippriority')
                        print("   ✓ Removed o_shippriority column (constant value)")
                # ====================================================================

                # Select only the columns we need for the table
                available_columns = [c for c in config['expected_columns'] if c in df.columns]
                df = df.select(*available_columns)
                
                # Apply data type conversions for lineitem
                if table_name == 'lineitem':
                    for col_name, conversion_func in type_conversions.items():
                        if col_name in df.columns:
                            df = conversion_func(df)
                            print(f"   🔄 Converted {col_name} to Decimal type")
                
                # Add surrogate key for lineitem if needed
                if config.get('has_surrogate_key', False) and config['surrogate_key_col'] not in df.columns:
                    df = df.withColumn(config['surrogate_key_col'], monotonically_increasing_id())
                    print(f"   🔑 Added surrogate key column: {config['surrogate_key_col']}")
                
                # Get row count
                rows_count = df.count()
                print(f"   📊 Records to load: {rows_count:,}")
                print(f"   📋 Columns to load: {', '.join(df.columns)}")
                
                # Export to CSV chunks
                print(f"   💾 Exporting to temporary CSV files...")
                df.write.csv(temp_dir, header=True, mode="overwrite", quote='"', escape='"')
                
                # Get CSV files count
                csv_files = [f for f in os.listdir(temp_dir) if f.endswith(".csv")]
                print(f"   📁 Exported to {len(csv_files)} CSV chunk(s)")
                
                # Load using COPY command
                print(f"   🚀 Loading into PostgreSQL using COPY...")
                columns_str = ", ".join(df.columns)
                copy_sql = f"COPY {full_table_name} ({columns_str}) FROM STDIN WITH CSV HEADER QUOTE '\"' ESCAPE '\"'"
                
                rows_loaded = 0
                for file_name in csv_files:
                    with open(os.path.join(temp_dir, file_name), 'r') as f:
                        cur.copy_expert(copy_sql, f)
                    # Count rows in file (excluding header)
                    with open(os.path.join(temp_dir, file_name), 'r') as f:
                        rows_loaded += sum(1 for _ in f) - 1
                
                print(f"   ✅ Successfully loaded {rows_loaded:,} rows into {full_table_name}")
                
                # Verify row count
                cur.execute(f"SELECT COUNT(*) FROM {full_table_name}")
                db_count = cur.fetchone()[0]
                print(f"   🔍 Verification: {db_count:,} rows in database")
                
                if db_count == rows_count:
                    print(f"   ✓ Row count matches source")
                else:
                    print(f"   ⚠️ Row count mismatch: Source={rows_count:,}, DB={db_count:,}")
                
                load_stats.append({
                    "table": full_table_name,
                    "rows_loaded": rows_loaded,
                    "status": "SUCCESS"
                })
                
            except Exception as e:
                print(f"   ❌ ERROR loading {full_table_name}: {e}")
                import traceback
                traceback.print_exc()
                load_stats.append({
                    "table": full_table_name,
                    "rows_loaded": 0,
                    "status": "FAILED",
                    "error": str(e)
                })
            
            finally:
                # Cleanup temporary directory
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    print(f"   🧹 Cleaned up temporary directory: {temp_dir}")
        else:
            print(f"\n❌ File not found: {file_path}")
            load_stats.append({
                "table": full_table_name,
                "rows_loaded": 0,
                "status": "FILE_NOT_FOUND",
                "error": f"File not found: {file_path}"
            })

    # Close connections
    cur.close()
    pg_conn.close()
    spark.stop()
    
    # =====================================================================
    # FINAL SUMMARY
    # =====================================================================
    print("\n" + "="*80)
    print("✨ SILVER LAYER INITIAL LOAD COMPLETE!")
    print("="*80)
    
    print("\n📊 LOAD SUMMARY:")
    print("-" * 60)
    successful_loads = [stat for stat in load_stats if stat['status'] == 'SUCCESS']
    failed_loads = [stat for stat in load_stats if stat['status'] != 'SUCCESS']
    
    print(f"✅ Successful loads: {len(successful_loads)}/{len(tables_config)}")
    for stat in successful_loads:
        print(f"   - {stat['table']}: {stat['rows_loaded']:,} rows")
    
    if failed_loads:
        print(f"\n❌ Failed loads: {len(failed_loads)}")
        for stat in failed_loads:
            print(f"   - {stat['table']}: {stat.get('error', 'Unknown error')}")
    
    # Verify final database state
    print("\n🔍 FINAL DATABASE VERIFICATION:")
    print("-" * 60)
    
    silver_conn = psycopg2.connect(
        host="postgres-local", port=5432, 
        dbname="data_platform_db", user="source_user", password="source_pass"
    )
    silver_cur = silver_conn.cursor()
    
    for table_name in tables_config.keys():
        full_table_name = f"silver.{table_name}"
        try:
            silver_cur.execute(f"SELECT COUNT(*) FROM {full_table_name}")
            count = silver_cur.fetchone()[0]
            print(f"   ✅ {full_table_name}: {count:,} rows")
            
            # Show sample of first few rows for verification
            if count > 0:
                silver_cur.execute(f"SELECT * FROM {full_table_name} LIMIT 1")
                sample = silver_cur.fetchone()
                print(f"      Sample: {sample[:5]}...")
        except Exception as e:
            print(f"   ❌ {full_table_name}: Error - {e}")
    
    silver_cur.close()
    silver_conn.close()
    
    print("\n" + "="*80)
    print("🎉 SILVER LAYER INITIAL LOAD COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nNext steps:")
    print("   1. Run incremental loads for new data")
    print("   2. Create gold layer aggregations")
    print("="*80)

if __name__ == "__main__":
    run_silver_initial_load()