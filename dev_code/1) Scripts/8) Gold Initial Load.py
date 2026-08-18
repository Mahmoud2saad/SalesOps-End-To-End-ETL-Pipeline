# build_and_load_gold.py
import os
import time
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
import snowflake.connector

# ====================== CONFIGURATION ======================
# PostgreSQL connection details (Local database)
POSTGRES_HOST = "localhost"  # or "127.0.0.1"
POSTGRES_PORT = "5432"
POSTGRES_DATABASE = "your_database_name"  # Change this
POSTGRES_USER = "your_username"  # Change this
POSTGRES_PASSWORD = "your_password"  # Change this
POSTGRES_SCHEMA = "silver"  # Schema where your silver layer tables are stored

# Snowflake connection details (pulled from environment variables — never hardcode credentials)
SNOWFLAKE_ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]
SNOWFLAKE_USER = os.environ["SNOWFLAKE_USER"]
SNOWFLAKE_PASSWORD = os.environ["SNOWFLAKE_PASSWORD"]
SNOWFLAKE_ROLE = os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
SNOWFLAKE_WAREHOUSE = "ETL_WH"
SNOWFLAKE_DATABASE = "MY_DB"
SNOWFLAKE_SCHEMA = "GOLD"

# PostgreSQL JDBC URL
POSTGRES_URL = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

# PostgreSQL connection properties
postgres_properties = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "driver": "org.postgresql.Driver"
}

# Spark Snowflake connector options
sfOptions = {
    "sfURL": f"{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com",
    "sfUser": SNOWFLAKE_USER,
    "sfPassword": SNOWFLAKE_PASSWORD,
    "sfDatabase": SNOWFLAKE_DATABASE,
    "sfSchema": SNOWFLAKE_SCHEMA,
    "sfWarehouse": SNOWFLAKE_WAREHOUSE,
    "sfRole": SNOWFLAKE_ROLE,
    "sfTimezone": "UTC",
    "sfCompress": "on",
    "sfSSL": "on",
    "columnmapping": "caseinsensitive",
    "truncate_table": "ON",
    "usestagingtable": "OFF",
    "autopushdown": "on"
}

# ====================== SNOWFLAKE SETUP FUNCTIONS ======================
def create_snowflake_objects():
    """Create database, warehouse, and schema if they don't exist"""
    print("\n🏗️  Setting up Snowflake objects...")
    
    ctx = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        role=SNOWFLAKE_ROLE
    )
    cs = ctx.cursor()
    
    try:
        # Create warehouse
        print(f"Creating warehouse: {SNOWFLAKE_WAREHOUSE} if not exists...")
        cs.execute(f"""
            CREATE WAREHOUSE IF NOT EXISTS {SNOWFLAKE_WAREHOUSE}
            WITH WAREHOUSE_SIZE = 'XSMALL'
            AUTO_SUSPEND = 300
            AUTO_RESUME = TRUE
            INITIALLY_SUSPENDED = FALSE
        """)
        print(f"✅ Warehouse {SNOWFLAKE_WAREHOUSE} ready")
        
        # Create database
        print(f"Creating database: {SNOWFLAKE_DATABASE} if not exists...")
        cs.execute(f"CREATE DATABASE IF NOT EXISTS {SNOWFLAKE_DATABASE}")
        print(f"✅ Database {SNOWFLAKE_DATABASE} ready")
        
        # Create schema
        print(f"Creating schema: {SNOWFLAKE_SCHEMA} if not exists...")
        cs.execute(f"CREATE SCHEMA IF NOT EXISTS {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}")
        print(f"✅ Schema {SNOWFLAKE_SCHEMA} ready")
        
    except Exception as e:
        print(f"❌ Failed to create Snowflake objects: {e}")
        raise
    finally:
        cs.close()
        ctx.close()

def run_snowflake_ddl():
    """Execute DDL to create all tables"""
    print("\n🏗️  Creating tables...")
    
    ctx = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        role=SNOWFLAKE_ROLE,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )
    cs = ctx.cursor()
    
    ddl_statements = [
        # Dimension tables
        """
        CREATE TABLE IF NOT EXISTS dim_date (
          date_key INTEGER PRIMARY KEY,
          full_date DATE NOT NULL,
          year INTEGER NOT NULL,
          quarter INTEGER NOT NULL,
          month INTEGER NOT NULL,
          month_name VARCHAR(20) NOT NULL,
          week INTEGER NOT NULL,
          day_of_month INTEGER NOT NULL,
          day_of_week INTEGER NOT NULL
        ) CLUSTER BY (date_key);
        """,
        
        """
        CREATE TABLE IF NOT EXISTS dim_part (
          part_key BIGINT PRIMARY KEY,
          name VARCHAR(55),
          manufacturer VARCHAR(25),
          brand VARCHAR(10),
          type VARCHAR(25),
          size INTEGER,
          container VARCHAR(10),
          retail_price NUMBER(15,2)
        ) CLUSTER BY (part_key);
        """,
        
        """
        CREATE TABLE IF NOT EXISTS dim_customer (
          customer_key BIGINT PRIMARY KEY,
          name VARCHAR(25),
          phone CHAR(15),
          account_balance NUMBER(15,2),
          market_segment VARCHAR(10),
          nation_key BIGINT,
          nation_name VARCHAR(50),
          region_key BIGINT,
          region_name VARCHAR(50)
        ) CLUSTER BY (customer_key);
        """,
        
        """
        CREATE TABLE IF NOT EXISTS dim_supplier (
          supplier_key BIGINT PRIMARY KEY,
          name VARCHAR(25),
          phone CHAR(15),
          account_balance NUMBER(15,2),
          nation_key BIGINT,
          nation_name VARCHAR(50),
          region_key BIGINT,
          region_name VARCHAR(50)
        ) CLUSTER BY (supplier_key);
        """,
        
        # Reference tables
        """
        CREATE TABLE IF NOT EXISTS ref_order_status (
          status_code CHAR(1) PRIMARY KEY,
          status_name VARCHAR(20) NOT NULL,
          status_description VARCHAR(100) NOT NULL,
          is_active BOOLEAN DEFAULT TRUE,
          created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS ref_order_priority (
          priority_code CHAR(15) PRIMARY KEY,
          priority_level INTEGER NOT NULL,
          priority_name VARCHAR(30) NOT NULL,
          priority_description VARCHAR(100),
          expected_processing_days INTEGER,
          created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS ref_return_flag (
          return_code CHAR(1) PRIMARY KEY,
          return_name VARCHAR(30) NOT NULL,
          return_description VARCHAR(100) NOT NULL,
          is_returned BOOLEAN DEFAULT FALSE,
          created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS ref_line_status (
          status_code CHAR(1) PRIMARY KEY,
          status_name VARCHAR(20) NOT NULL,
          status_description VARCHAR(100) NOT NULL,
          is_fulfilled BOOLEAN DEFAULT FALSE,
          created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS ref_ship_instructions (
          instruction_code CHAR(25) PRIMARY KEY,
          instruction_name VARCHAR(50) NOT NULL,
          instruction_description VARCHAR(200) NOT NULL,
          requires_signature BOOLEAN DEFAULT FALSE,
          created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS ref_ship_mode (
          mode_code CHAR(10) PRIMARY KEY,
          mode_name VARCHAR(30) NOT NULL,
          mode_category VARCHAR(20) NOT NULL,
          average_transit_days INTEGER,
          tracking_available BOOLEAN DEFAULT TRUE,
          created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        );
        """,
        
        # Fact tables
        """
        CREATE TABLE IF NOT EXISTS fact_orders (
          order_key BIGINT PRIMARY KEY,
          customer_key BIGINT NOT NULL,
          order_status CHAR(1),
          total_price NUMBER(15,2),
          order_date DATE,
          order_priority CHAR(15)
        ) CLUSTER BY (order_date, customer_key);
        """,
        
        """
        CREATE TABLE IF NOT EXISTS fact_line_items (
          line_item_key BIGINT PRIMARY KEY,
          order_key BIGINT NOT NULL,
          customer_key BIGINT NOT NULL,
          part_key BIGINT NOT NULL,
          supplier_key BIGINT NOT NULL,
          line_number INTEGER,
          quantity NUMBER(15,2),
          extended_price NUMBER(15,2),
          discount NUMBER(15,2),
          tax NUMBER(15,2),
          return_flag CHAR(1),
          line_status CHAR(1),
          ship_date DATE,
          commit_date DATE,
          receipt_date DATE,
          ship_instructions CHAR(25),
          ship_mode CHAR(10)
        ) CLUSTER BY (ship_date, order_key);
        """,
        
        """
        CREATE TABLE IF NOT EXISTS fact_partsupp_inventory (
          partsupp_key BIGINT PRIMARY KEY,
          part_key BIGINT NOT NULL,
          supplier_key BIGINT NOT NULL,
          available_quantity INTEGER,
          supply_cost NUMBER(15,2)
        ) CLUSTER BY (part_key, supplier_key);
        """
    ]
    
    for stmt in ddl_statements:
        try:
            cs.execute(stmt)
            # Extract table name for logging
            table_name = stmt.split("CREATE TABLE IF NOT EXISTS")[1].split("(")[0].strip()
            print(f"✅ Created: {table_name}")
        except Exception as e:
            print(f"⚠️ Warning executing DDL for table: {e}")
    
    cs.close()
    ctx.close()
    print("✅ Table creation complete")

def test_snowflake_connection():
    """Test Snowflake connection"""
    print("\n🔍 Testing Snowflake connection...")
    
    ctx = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        role=SNOWFLAKE_ROLE,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        login_timeout=15
    )
    
    cs = ctx.cursor()
    cs.execute("SELECT CURRENT_VERSION(), CURRENT_WAREHOUSE(), CURRENT_ROLE()")
    result = cs.fetchone()
    
    print(f"✅ Connected successfully!")
    print(f"   Version: {result[0]}")
    print(f"   Warehouse: {result[1]}")
    print(f"   Role: {result[2]}")
    
    cs.close()
    ctx.close()

def test_postgres_connection():
    """Test PostgreSQL connection"""
    print("\n🔍 Testing PostgreSQL connection...")
    
    try:
        # Create a test DataFrame to verify connection
        test_df = spark.read \
            .format("jdbc") \
            .option("url", POSTGRES_URL) \
            .option("dbtable", f"({POSTGRES_SCHEMA}.dim_date) as dim_date") \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("driver", "org.postgresql.Driver") \
            .load() \
            .limit(1)
        
        test_df.count()
        print(f"✅ PostgreSQL connection successful!")
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print(f"   Please check your PostgreSQL credentials and ensure the database is running")
        raise

# ====================== SPARK SETUP ======================
print("\n🚀 Initializing Spark session...")
spark = SparkSession.builder \
    .appName("GoldLayerBuilder") \
    .config("spark.jars.packages", 
            "net.snowflake:spark-snowflake_2.12:2.12.0-spark_3.4,"
            "net.snowflake:snowflake-jdbc:3.13.30,"
            "org.postgresql:postgresql:42.6.0") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

print("✅ Spark session ready")

# ====================== DATA LOADING FUNCTIONS ======================
def load_table_from_postgres(table_name):
    """Load a table from PostgreSQL into a Spark DataFrame"""
    print(f"\n📥 Loading {table_name} from PostgreSQL...")
    
    try:
        df = spark.read \
            .format("jdbc") \
            .option("url", POSTGRES_URL) \
            .option("dbtable", f"{POSTGRES_SCHEMA}.{table_name}") \
            .option("user", POSTGRES_USER) \
            .option("password", POSTGRES_PASSWORD) \
            .option("driver", "org.postgresql.Driver") \
            .option("fetchsize", "10000") \
            .load()
        
        row_count = df.count()
        print(f"   ✅ Loaded {row_count:,} rows from {table_name}")
        return df
        
    except Exception as e:
        print(f"   ❌ Failed to load {table_name}: {e}")
        raise

def write_df_to_snowflake(df, table_name, mode="overwrite"):
    """Write DataFrame to Snowflake"""
    print(f"\n🚀 Writing {table_name} to Snowflake (mode: {mode})...")
    
    try:
        row_count = df.count()
        print(f"   📊 Rows: {row_count:,}")
        
        df.write \
          .format("snowflake") \
          .options(**sfOptions) \
          .option("dbtable", table_name) \
          .mode(mode) \
          .save()
        
        print(f"   ✅ Successfully wrote {table_name}")
        
    except Exception as e:
        print(f"   ❌ Failed to write {table_name}: {e}")
        raise

def transform_dim_date(orders_df, line_items_df):
    """Build dim_date from order_date, ship_date, commit_date, receipt_date"""
    print("\n🔄 Building dim_date dimension...")
    
    # Collect all dates from relevant columns
    date_cols = orders_df.select(F.to_date("order_date").alias("dt")).union(
        line_items_df.select(F.to_date("ship_date").alias("dt"))).union(
        line_items_df.select(F.to_date("commit_date").alias("dt"))).union(
        line_items_df.select(F.to_date("receipt_date").alias("dt"))) \
        .filter(F.col("dt").isNotNull()) \
        .distinct()
    
    dim_date = date_cols.withColumn("full_date", F.col("dt")) \
        .withColumn("date_key", F.date_format("full_date", "yyyyMMdd").cast("int")) \
        .withColumn("year", F.year("full_date")) \
        .withColumn("quarter", F.quarter("full_date")) \
        .withColumn("month", F.month("full_date")) \
        .withColumn("month_name", F.date_format("full_date", "MMMM")) \
        .withColumn("week", F.weekofyear("full_date")) \
        .withColumn("day_of_month", F.dayofmonth("full_date")) \
        .withColumn("day_of_week", F.date_format("full_date", "u").cast("int")) \
        .select("date_key", "full_date", "year", "quarter", "month", 
                "month_name", "week", "day_of_month", "day_of_week") \
        .dropDuplicates(["date_key"]) \
        .orderBy("date_key")
    
    print(f"   ✅ dim_date built with {dim_date.count():,} rows")
    return dim_date

# ====================== MAIN EXECUTION ======================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("GOLD LAYER BUILD - START")
    print("="*60)
    
    # Step 1: Set up Snowflake objects
    create_snowflake_objects()
    
    # Step 2: Create tables
    run_snowflake_ddl()
    
    # Step 3: Test connections
    test_postgres_connection()
    test_snowflake_connection()
    
    # Step 4: Load data from PostgreSQL
    print("\n📤 Loading data from PostgreSQL silver layer...")
    
    # Load all tables from PostgreSQL
    dim_part = load_table_from_postgres("dim_part")
    dim_customer = load_table_from_postgres("dim_customer")
    dim_supplier = load_table_from_postgres("dim_supplier")
    fact_orders = load_table_from_postgres("fact_orders")
    fact_line_items = load_table_from_postgres("fact_line_items")
    fact_partsupp_inventory = load_table_from_postgres("fact_partsupp_inventory")
    
    # Build dim_date from date columns in orders and line items
    dim_date = transform_dim_date(fact_orders, fact_line_items)
    
    # Load reference tables (assuming they exist in PostgreSQL)
    ref_order_status = load_table_from_postgres("ref_order_status")
    ref_order_priority = load_table_from_postgres("ref_order_priority")
    ref_return_flag = load_table_from_postgres("ref_return_flag")
    ref_line_status = load_table_from_postgres("ref_line_status")
    ref_ship_instructions = load_table_from_postgres("ref_ship_instructions")
    ref_ship_mode = load_table_from_postgres("ref_ship_mode")
    
    # Step 5: Write data to Snowflake
    print("\n📤 Loading data to Snowflake...")
    
    tables_to_write = [
        (dim_date, "dim_date", "overwrite"),
        (dim_part, "dim_part", "overwrite"),
        (dim_customer, "dim_customer", "overwrite"),
        (dim_supplier, "dim_supplier", "overwrite"),
        (ref_order_status, "ref_order_status", "overwrite"),
        (ref_order_priority, "ref_order_priority", "overwrite"),
        (ref_return_flag, "ref_return_flag", "overwrite"),
        (ref_line_status, "ref_line_status", "overwrite"),
        (ref_ship_instructions, "ref_ship_instructions", "overwrite"),
        (ref_ship_mode, "ref_ship_mode", "overwrite"),
        (fact_orders, "fact_orders", "append"),
        (fact_line_items, "fact_line_items", "append"),
        (fact_partsupp_inventory, "fact_partsupp_inventory", "append")
    ]
    
    for df, name, mode in tables_to_write:
        try:
            write_df_to_snowflake(df, name, mode)
        except Exception as e:
            print(f"❌ Error writing {name}: {e}")
            raise
    
    print("\n" + "="*60)
    print("🎉 GOLD LAYER BUILD - COMPLETE!")
    print("="*60)
    
    # Optional: Verify data in Snowflake
    print("\n🔍 Verifying data in Snowflake...")
    ctx = snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        role=SNOWFLAKE_ROLE,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )
    cs = ctx.cursor()
    
    for table in ["dim_date", "dim_part", "dim_customer", "dim_supplier", 
                  "fact_orders", "fact_line_items", "fact_partsupp_inventory"]:
        cs.execute(f"SELECT COUNT(*) FROM {table}")
        count = cs.fetchone()[0]
        print(f"   {table}: {count:,} rows")
    
    cs.close()
    ctx.close()
    
    # Clean up
    spark.stop()
    print("\n✅ Spark session closed")