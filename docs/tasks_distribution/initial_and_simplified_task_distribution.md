## TASK BREAKDOWN WITH TEAM ASSIGNMENTS

### PHASE 1: FOUNDATION (Days 1-2)

#### Task 1: Environment Setup & Data Generation
**Owners: Ibrahim**

**Subtasks:**
- [ ] Generate 30GB TPC-H data using dbgen
- [ ] Set up Docker containers (PostgreSQL source, control, Airflow)
- [ ] Configure persistent pip cache for slow internet
- [ ] Create source database with TPC-H schema
- [ ] Create control database with watermark/audit tables
- [ ] Test all connections work

**Deliverables:** Running Docker environment, 30GB source data, control tables

---

#### Task 2: Star Schema Design
**Owners: Ahmed & Abram**

**Subtasks:**
- [ ] Design dimension tables (customer, product, date, supplier)
- [ ] Design fact tables (orders, lineitems)
- [ ] Define SCD Type 2 strategy for dimensions
- [ ] Create DDL scripts for Snowflake
- [ ] Document all columns with data types
- [ ] Create data dictionary

**Deliverables:** Complete star schema documentation, Snowflake DDL

---

#### Task 3: Data Quality Framework Design
**Owners: Habiba & Shrouk & Manar**

**Subtasks:**
- [ ] Define 10+ DQ checks with severity levels
- [ ] Create DQ results table schema
- [ ] Design anomaly detection thresholds
- [ ] Document business rules validation
- [ ] Create test cases for intentional errors

**Deliverables:** DQ framework documentation, test cases

---

### PHASE 2: CORE PIPELINE (Days 3-5)

#### Task 4: Data Corruption & Error Injection
**Owners: Ibrahim & Manar**

**Subtasks:**
- [ ] Create intentional errors in source data:
  - Column name mismatches (e.g., "CUST_ID" vs "customer_id")
  - Orphan foreign keys
  - Null values in required columns
  - Duplicate records
  - Future dates
  - Negative quantities
  - Data type mismatches
  - Exceeding character limits
- [ ] Build Python script to inject errors systematically
- [ ] Create error injection toggle (enabled/disabled for testing)
- [ ] Document all injected errors with expected DQ detection
- [ ] Test that DQ framework catches injected errors
- [ ] Create error injection report with validation results

**Deliverables:** Error injection scripts, corrupted test data, validation report

---

#### Task 5: Source to PostgreSQL Loading
**Owners: Abram & Ahmed**

**Subtasks:**
- [ ] Implement watermark tables in control DB
- [ ] Create watermark read/update functions
- [ ] Build incremental extraction queries from source
- [ ] Add safety margin logic (ID-based + timestamp)
- [ ] Load data to PostgreSQL source tables
- [ ] Test with edge cases (first run, empty batches)
- [ ] Create audit logging tables and functions
- [ ] Build data validation checks after load

**Deliverables:** Working watermark system, audit framework, loaded PostgreSQL source

---

#### **Task 6: Data Division for Incremental Loads (Silver Layer Preparation)**
**Owners: Habiba & Shrouk**

**Subtasks:**
- [ ] Research and compare partitioning techniques (date-based, ID-based, hash-based, hybrid)
- [ ] Select optimal technique based on:
  - Query patterns (time-range vs. key lookups)
  - Data distribution (skewness analysis)
  - Incremental load frequency
- [ ] Create Python script to split TPC-H data using chosen technique:
  - 80% historical (batch processing)
  - 20% recent (simulated streaming)
- [ ] Build metadata table to track partitions
- [ ] Add validation queries to verify split correctness

**Deliverables:** Partitioning analysis report, data division scripts, partitioned source tables

---

#### Task 7: Exploratory Data Analysis
**Owners: Ibrahim & Manar**

**Subtasks:**
- [ ] Perform initial EDA on source data to understand data distribution
- [ ] Identify data patterns, outliers, and potential quality issues
- [ ] Create baseline statistics for key columns (null counts, distinct values, value ranges)
- [ ] Document findings with visualizations and summary statistics
- [ ] Create OR initialize version of data quality metrics table
- [ ] Identify columns requiring special handling in downstream layers

**Deliverables:** EDA report with visualizations, initial DQ metrics table, baseline statistics

---

#### Task 8: ODS Layer (Operational Data Store)
**Owners: Abram & Ahmed**

**Subtasks:**
- [ ] Create ODS tables in PostgreSQL (mirror of source)
- [ ] Implement daily snapshots for change tracking
- [ ] Build CDC (Change Data Capture) simulation
- [ ] Add timestamp columns for incremental tracking
- [ ] Create ODS maintenance procedures

**Deliverables:** ODS tables with CDC capability

---

#### Task 9: Data Quality Checks & Data Cleaning Implementation
**Owners: Habiba & Shrouk**

**Subtasks:**
- [ ] Review and enhance Ibrahim & Manar's initial EDA code
- [ ] Identify additional quality checks based on:
  - EDA findings and data patterns
  - Previously documented DQ framework (from Phase 1)
  - Intentionally injected errors from Task 4
  - Business rule validation requirements
- [ ] Write comprehensive data cleaning functions that handle:
  - Invalid data types
  - Out-of-range values
  - Orphan records
  - Duplicate resolution strategy
  - NULL handling based on business rules
- [ ] Implement all data quality checks in production-ready code
- [ ] Update and populate the data quality metrics table with check results
- [ ] **⚠️ CRITICAL: Address database-specific issues:**
  - Handle PostgreSQL vs Snowflake type compatibility
  - Manage connection pooling and timeout settings
  - Implement retry logic for transient database failures
  - Handle transaction boundaries correctly
  - Consider performance implications for 30GB dataset
- [ ] Create dead letter queue for records failing critical checks
- [ ] Document all implemented checks with severity levels and remediation steps

**Deliverables:** Production-ready DQ cleaning code, updated DQ metrics table, dead letter queue implementation

---

#### Task 10: Staging Layer 
**Owners: Ahmed & Abram**

**Subtasks:**
- [ ] Create staging tables in Snowflake (raw landing)
- [ ] Build PySpark transformation scripts
- [ ] Implement data type conversion
- [ ] Add null handling and default values
- [ ] Create staging validation checks
- [ ] Build error logging for rejected records

**Deliverables:** Staging tables, transformation scripts

---

#### Task 11: DWH Layer (Galaxy Schema)
**Owners: Ibrahim & Manar && Ahmed & Abram**

**Subtasks:**
- [ ] Create dimension tables in Snowflake
- [ ] Implement SCD Type 2 merge logic
- [ ] Create fact tables with surrogate keys
- [ ] Build referential integrity checks
- [ ] Add aggregate tables for performance
- [ ] Implement partition/clustering keys

**Deliverables:** Complete star schema in Snowflake

---

### PHASE 3: ORCHESTRATION & QUALITY (Days 6-7)

#### Task 10: Airflow DAG Development
**Owners: Abram & Ahmed**

**Subtasks:**
- [ ] Create master DAG with 15+ tasks
- [ ] Define task dependencies and ordering
- [ ] Configure retries and error handling
- [ ] Add SLA monitoring
- [ ] Implement XCom for data passing
- [ ] Create task documentation in DAG

**Deliverables:** Working Airflow DAG

---

#### Task 11: Data Quality Implementation
**Owners: Ibrahim & Manar**

**Subtasks:**
- [ ] Implement all 10+ DQ checks in code
- [ ] Build DQ runner that executes checks
- [ ] Create DQ results logging to control DB
- [ ] Add branching logic (FAIL stops pipeline)
- [ ] Build dead letter queue for failed records
- [ ] Create DQ dashboard in PowerBI

**Deliverables:** Automated DQ framework, dead letter queue

---

#### Task 12: Monitoring & Alerting
**Owners: Habiba & Shrouk**

**Subtasks:**
- [ ] Create monitoring DAG (runs every 15 min)
- [ ] Implement credit usage tracking
- [ ] Add stalled task detection (>2 hours)
- [ ] Build Slack alert integration
- [ ] Create DQ trend monitoring
- [ ] Set up email notifications

**Deliverables:** Monitoring system with alerts

---

### PHASE 4: VISUALIZATION & POLISH (Days 8-10)

#### Task 13: PowerBI Dashboard Development
**Owners: Abram & Ahmed & Ibrahim & Manar & Habiba & Shrouk** (ALL HANDS)

**Subtasks:**

**Sales Dashboard (Abram & Ahmed):**
- [ ] Connect PowerBI to Snowflake
- [ ] Create KPI cards (revenue, orders, AOV)
- [ ] Build time-series charts
- [ ] Add product/customer filters
- [ ] Implement drill-through pages

**DQ Dashboard (Habiba & Shrouk):**
- [ ] Connect to audit.dq_results table
- [ ] Create pass rate visualizations
- [ ] Add failing checks table
- [ ] Build trend charts
- [ ] Implement conditional formatting

**Operations Dashboard (Ibrahim & Manar):**
- [ ] Show pipeline status
- [ ] Display watermark positions
- [ ] Track credit usage
- [ ] Show recent errors
- [ ] Add refresh controls

**Deliverables:** Three complete PowerBI dashboards

---

#### Task 14: Testing & Validation
**Owners: ALL**

**Subtasks:**
- [ ] Run full pipeline on 30GB data
- [ ] Verify row counts match source
- [ ] Test error injection detection
- [ ] Validate watermarks update correctly
- [ ] Confirm audit logs populated
- [ ] Test all alerts
- [ ] Document any issues

**Deliverables:** Test report, bug fixes

---

#### Task 15: Documentation & Demo Prep
**Owners: ALL**

**Subtasks:**
- [ ] Create architecture diagrams
- [ ] Write setup guide
- [ ] Document runbook procedures
- [ ] Create demo script (5 minutes)
- [ ] Prepare backup slides
- [ ] Practice demo

**Deliverables:** Complete documentation, demo ready

---

**Rationale for Changes:**
- **Error injection moved earlier**: Data corruption now happens at the source before loading, allowing DQ framework to catch errors naturally
- **Source loading follows corruption**: Load the corrupted data to test DQ effectiveness
- **Data division positioned logically**: After source is loaded, data is divided for incremental silver layer processing

---

## TEAM ASSIGNMENT SUMMARY (UPDATED)

| Phase | Task # | Task Name | Primary Owner(s) | Secondary/Support | Day(s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1: Foundation** | 1 | Environment Setup & Data Generation | Ibrahim | | 1-2 |
| | 2 | Star Schema Design | Ahmed & Abram | | 1-2 |
| | 3 | Data Quality Framework Design | Habiba, Shrouk, Manar | | 1-2 |
| **2: Core Pipeline** | 4 | Data Corruption & Error Injection | Ibrahim & Manar | | 3 |
| | 5 | Source to PostgreSQL Loading | Abram & Ahmed | | 3 |
| | 6 | Data Division for Incremental Loads | Habiba & Shrouk | | 4 |
| | 7 | EDA & Initial Data Quality Checks | Ibrahim & Manar | | 4 |
| | 8 | ODS Layer | Abram & Ahmed | | 4-5 |
| | 9 | Data Quality Checks & Data Cleaning | Habiba & Shrouk | Ibrahim & Manar | 5 |
| | 10 | Staging Layer | Ibrahim & Manar | | 5-6 |
| | 11 | DWH Layer (Star Schema) | Habiba & Shrouk | | 6 |
| **3: Orchestration & Quality** | 12 | Airflow DAG Development | Abram & Ahmed | | 7 |
| | 13 | Data Quality Implementation | Ibrahim & Manar | | 7-8 |
| | 14 | Monitoring & Alerting | Habiba & Shrouk | | 8 |
| **4: Visualization & Polish** | 15 | PowerBI Dashboard Development | ALL HANDS | | 9-10 |
| | 16 | Testing & Validation | ALL | | 10 |
| | 17 | Documentation & Demo Prep | ALL | | 10 |
---

## CRITICAL SUCCESS FACTORS

### What Makes This Plan Work:

1. **Clear ownership** - Every task has people assigned, no ambiguity
2. **Dependencies mapped** - Tasks build on each other logically
3. **All components covered** - No missing pieces
4. **Balanced workload** - Everyone has ~3 primary tasks
5. **Built-in quality** - DQ framework from day 1
6. **Error testing** - Intentional errors prove the system works
7. **Monitoring** - You'll know if it breaks

### What Will Kill This Project:

- **Waiting until Day 5 to start Airflow** (orchestration should be parallel)
- **No daily integration** (waiting until the end to connect pieces)
- **Vague task definitions** (like your original "Dividing the data")
- **Siloed knowledge** (only one person knows each component)

---

## YOUR NEXT STEP

Take this task breakdown, put it in a shared document, and have a **30-minute kickoff meeting** where everyone:

1. Reads their tasks aloud
2. Asks clarifying questions
3. Commits to their deliverables
4. Agrees on daily standup time (9 AM)

Then print the dependency chart and put it on the wall. Every day, mark progress.
