# DATA CLEANING DOCUMENTATION
## Bronze to Silver Layer Transformation

### Overview
This document outlines all data cleaning operations performed on the TPC-H benchmark data as it moves from the bronze (raw) layer to the silver (cleaned) layer.

---

### 1. COMMENT COLUMN REMOVAL - ALL TABLES

**Tables Affected:** customer, lineitem, nation, orders, part, partsupp, region, supplier

**Operation:** Drop all `*_comment` columns

**Reasoning:**
- Comment fields contain unstructured text with quality issues (leading/trailing spaces, special characters)
- EDA revealed 3% nulls and extensive formatting issues (944k leading spaces, 802k trailing spaces in base_lineitem)
- Comments provide minimal analytical value while consuming significant storage (~3% of rows)
- Removal improves query performance and reduces storage costs
- Business stakeholders confirmed comments are not used in current analytics

**Impact:** 
- Reduced table width by 1 column per table
- Eliminated need for text cleaning on these columns
- Storage savings: ~3-5% of total data volume

---

### 2. SUPPLIER TABLE CLEANING

#### 2.1 Remove Address Column

**Operation:** Drop `s_address` column

**Reasoning:**
- Address data is free-text with inconsistent formatting
- No standardization or geocoding applied at bronze level
- Address not used in current analytical queries
- Privacy considerations - reduces PII exposure
- Can be rejoined from bronze if needed for future use cases

**Impact:** 
- Removed 1 VARCHAR(40) column
- Reduced PII data footprint

#### 2.2 Fix Negative Account Balances

**Operation:** Convert negative `s_acctbal` values to positive using absolute value function

**Reasoning:**
- Business rule: Account balances cannot be negative
- EDA found negative values in source data (min: -496k in orders, similar pattern in supplier)
- Negative values likely due to data entry errors or returns processing
- Using absolute value maintains data integrity while enforcing business rule
- Alternative (removing rows) would lose valid supplier records

**Impact:**
- All supplier records retained
- Business rule enforced at silver layer
- Negative values eliminated (0 remaining)

---

### 3. PARTSUPP TABLE - SLOWLY CHANGING DIMENSION (SCD TYPE 2)

**Operation:** Add SCD Type 2 columns:
- `valid_from` (TIMESTAMP) - when the record became active
- `valid_to` (TIMESTAMP) - when the record was superseded
- `is_current` (BOOLEAN) - indicates current active record

**Reasoning:**
- Partsupp (bridge between part and supplier) changes over time
- Supply costs and availability quantities change historically
- SCD Type 2 preserves historical state for accurate time-based analysis
- Enables "as-was" reporting (e.g., "what was the supply cost on Jan 1, 1996?")
- Supports audit trails and compliance requirements

**Implementation Notes:**
- Initial load: all records marked as current with valid_from = load timestamp
- Future incremental loads: implement merge logic using hash comparison of business keys
- Track changes to `ps_supplycost` and `ps_availqty`

**Impact:**
- Historical tracking enabled
- 3 new columns added (minimal storage overhead)
- Enables temporal queries

---

### 4. PART TABLE - EXTRACT IDs FROM MANUFACTURER AND BRAND

**Operation:** 
- Extract numeric ID from `p_mfgr` (format "Manufacturer#1" → 1)
- Extract numeric ID from `p_brand` (format "Brand#13" → 13)
- Drop original string columns

**Reasoning:**
- String format is memory inefficient (repeating "Manufacturer#" prefix)
- IDs enable efficient joins with dimension tables
- Numeric IDs consume less storage (INT vs VARCHAR up to 25 chars)
- Faster for aggregations and filtering
- Stakeholder requirement: work with IDs, not formatted strings

**Example Transformation:**