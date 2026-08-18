# SalesOps ETL Pipeline

[![Unit Tests](https://github.com/Mahmoud2saad/SalesOps-End-To-End-ETL-Pipeline/actions/workflows/tests.yml/badge.svg)](https://github.com/Mahmoud2saad/SalesOps-End-To-End-ETL-Pipeline/actions/workflows/tests.yml)

A layered ETL pipeline that moves the TPC-H benchmark dataset through bronze, silver, and gold stages — PostgreSQL for staging, Snowflake for the analytical warehouse — orchestrated with Airflow and built on PySpark.

This project is based on [Ibrahim-Hegazi/SalesOps-End-To-End-ETL-Pipeline](https://github.com/Ibrahim-Hegazi/SalesOps-End-To-End-ETL-Pipeline), originally built by a six-person team. I downloaded the original codebase, worked on it independently, and pushed it here as a standalone repository. See [Provenance](#provenance) for exactly what's inherited versus what I added.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Status](#status)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Directory Structure](#directory-structure)
- [Setup](#setup)
- [Running the Tests](#running-the-tests)
- [Database Schema](#database-schema)
- [Airflow DAGs](#airflow-dags)
- [Roadmap](#roadmap)
- [Provenance](#provenance)
- [Contact](#contact)

## Overview

The pipeline extracts TPC-H order and line-item data incrementally, using a watermark table with a configurable safety margin to handle late-arriving rows. Data lands in a PostgreSQL bronze layer, gets cleaned and conformed into a silver layer, and the gold layer loads into Snowflake for analytics. One dimension (`partsupp`) carries full SCD Type 2 history.

A data quality module runs row-count, null, uniqueness, and referential-integrity checks against both bronze and silver, writing results to a control schema and failing the pipeline on critical issues. An Airflow DAG runs the bronze load and both DQ suites on a schedule; a test suite (unit and integration) runs in CI on every push.

## Architecture

```mermaid
graph TB
    subgraph Source
        PG[(PostgreSQL<br/>TPC-H)]
    end
    subgraph Control
        CTRL[(Watermarks & Audit Log)]
    end
    subgraph Orchestration
        AF[Airflow]
    end
    subgraph Processing
        PY[PySpark Transformations]
        DQ[Data Quality Checks]
    end
    subgraph Warehouse
        SF[(Snowflake)]
    end

    PG -->|incremental extract| AF
    CTRL -->|watermarks| AF
    AF --> PY
    PY --> DQ
    DQ -->|gold load| SF

    style PG fill:#e1f5fe
    style CTRL fill:#fff3e0
    style AF fill:#e8f5e8
    style SF fill:#f3e5f5
```

## Status

| Component | Status |
|---|---|
| Bronze layer (initial + incremental load) | Done |
| Silver layer (initial + incremental load) | Done — incremental load takes a manual batch/year argument rather than a computed date window |
| Gold layer (Snowflake load) | Done |
| SCD Type 2 | Done for `partsupp`; not implemented on other dimensions |
| Watermarking | Done — ID and timestamp-based, with safety margin |
| Audit logging | Done — every load script logs start/complete/fail |
| Data quality checks | Done for bronze and silver (row count, nulls, uniqueness, referential integrity, SCD2 invariants) |
| Airflow orchestration | Bronze load + bronze/silver DQ checks run on a schedule. Silver and gold *loads* are still manual — see note below. |
| Monitoring / alerting | Not implemented |
| BI dashboards | Not implemented |
| Unit tests | 18 tests, mocked engine, run in CI |
| Integration tests | 8 tests against a live Postgres instance, run in CI against a real service container |

**On silver orchestration:** `7) Silver Incremental Load.py` takes a manual year argument rather than computing its own date window, so it isn't chained into the daily DAG — doing so would silently reprocess the same default batch on every run. The DAG instead runs DQ checks against whatever silver data currently exists, which catches drift even though the load itself isn't automated yet. Making this script date-driven is the next real step toward full orchestration; see [Roadmap](#roadmap).

## Features

| Feature | Notes |
|---|---|
| Incremental extraction | Watermark-based, with configurable row and time safety margins |
| SCD Type 2 | `partsupp` bridge table, with a Snowflake `ROW_NUMBER()`-based recompute of `is_current` |
| Data quality | Bronze and silver checks; writes to `control.data_quality_metrics`; fails the DAG on critical checks |
| Audit trail | Every load logs start/complete/fail with row counts to `control.audit_log` |
| Idempotency | Watermark tracking plus `ON CONFLICT` upserts make reruns safe |
| Testing | Unit tests (mocked) and integration tests (live Postgres), both in CI |
| Containerized | Docker Compose for Postgres, Airflow, pgAdmin, Jupyter |

## Tech Stack

| Category | Tools |
|---|---|
| Orchestration | Apache Airflow (LocalExecutor) |
| Databases | PostgreSQL 15 (staging + control), Snowflake (warehouse) |
| Processing | Python, PySpark, Pandas |
| Testing | pytest, GitHub Actions |
| Containers | Docker, Docker Compose |

## Directory Structure

```
SalesOps-End-To-End-ETL-Pipeline/
├── docker-compose.yaml
├── pytest.ini
├── README.md
│
├── .github/workflows/
│   └── tests.yml                   # unit-tests + integration-tests jobs
│
├── airflow/dags/
│   ├── bronze_layer_dag.py         # bronze load → bronze DQ → silver DQ
│   └── test_airflow_setup.py       # smoke test for the Airflow install
│
├── dev_code/
│   ├── 1) Scripts/
│   │   ├── 4) Bronze Initial Load.py
│   │   ├── 5) Bronze Incremental Load.py
│   │   ├── 6) Silver Initial Load.py
│   │   ├── 7) Silver Incremental Load.py
│   │   ├── 8) Gold Initial Load.py
│   │   ├── audit/                  # watermark_manager.py, audit_logger.py
│   │   ├── extract/
│   │   ├── quality/                # dq_checks.py, dq_runner.py
│   │   └── legacy/                 # superseded early drafts, kept for history
│   ├── 2) Notebooks/
│   └── 3) Final Dance/
│
├── tests/
│   ├── test_watermark_manager.py
│   ├── test_audit_logger.py
│   ├── test_dq_checks.py
│   └── integration/
│       ├── test_watermark_manager_integration.py
│       └── test_dq_checks_integration.py
│
├── sql_scripts/
│   ├── local/                      # bronze/silver/gold DDL
│   ├── control/                    # watermarks, audit_log, dq metrics
│   ├── snowflake_sql/
│   └── adhoc/
│
├── data/raw/wholedatasets/         # links to the TPC-H source data
└── docs/
```

## Setup

**Prerequisites:** Docker Desktop (12GB+ memory allocated), Git, a Snowflake account.

```bash
git clone https://github.com/Mahmoud2saad/SalesOps-End-To-End-ETL-Pipeline.git
cd SalesOps-End-To-End-ETL-Pipeline
```

Create a `.env` file with your Snowflake connection string:

```
SNOWFLAKE_CONN="snowflake://YOUR_USER:YOUR_PASSWORD@YOUR_ACCOUNT/TPCH_DB?warehouse=LOAD_WH"
```

Start the stack:

```bash
docker-compose up -d
```

First run takes 15–20 minutes while packages download. Once containers are up:

| Service | URL | Credentials |
|---|---|---|
| Airflow | http://localhost:8080 | admin / admin |
| Jupyter | http://localhost:8888?token=devtoken | token: devtoken |
| pgAdmin | http://localhost:5050 | admin@example.com / admin |

Verify the schemas came up:

```bash
docker exec postgres-local psql -U source_user -d data_platform_db -c "\dn"
docker exec postgres-control psql -U control_user -d control -c "\dt control.*"
```

### Common issues

**Tables not created** — Postgres only runs init scripts against an empty data volume. Stop the container, clear `postgres-local/data`, restart.

**Airflow container exits immediately** — check `docker logs airflow-webserver`; usually a metadata DB issue, fixed by clearing `postgres-airflow/data` and restarting.

**Snowflake connection fails** — confirm `SNOWFLAKE_CONN` in `.env`, then test from the dev container:

```bash
docker exec -it python-dev python -c "
import snowflake.connector
conn = snowflake.connector.connect(user='...', password='...', account='...')
print('connected')
"
```

**Schema changes not reflected** — same root cause as the first issue: Postgres init scripts only run once, against an empty volume. Stop the relevant container, clear its data directory, restart.

## Running the Tests

Unit tests mock the database and run without any infrastructure:

```bash
pip install -r tests/requirements-test.txt
pytest -m "not integration"
```

Integration tests run the same logic against a real Postgres instance and are skipped automatically if none is configured:

```bash
docker run --rm -d --name pg-test -e POSTGRES_PASSWORD=test -p 5433:5432 postgres:15
export TEST_DATABASE_URL="postgresql+psycopg2://postgres:test@localhost:5433/postgres"
pytest tests/integration -m integration
```

CI runs both as separate jobs — `unit-tests` and `integration-tests` — the latter against a real `postgres:15` service container.

## Database Schema

**Bronze** — raw TPC-H tables (`orders`, `lineitem`, `customer`, `part`, `supplier`), loaded as-is with a `_loaded_at` timestamp.

**Silver** — cleaned and conformed tables. `partsupp` carries SCD Type 2 columns (`valid_from`, `valid_to`, `is_current`).

**Control** — `watermarks` (last processed position per table), `audit_log` (task-level execution history), `data_quality_metrics` (DQ check results).

## Airflow DAGs

`bronze_layer_dag.py` runs on a daily schedule:

```
start → bronze incremental load → bronze DQ checks → silver DQ checks → end
```

DQ checks exit non-zero on a critical failure, which fails the task directly — no separate branching logic needed. `test_airflow_setup.py` is a smoke-test DAG confirming the Airflow install is healthy.

## Roadmap

- Rewrite the silver incremental load to compute its own date window, so it can be chained into the DAG the way bronze already is
- Extend data quality checks to the gold/Snowflake layer
- Add a Snowflake integration test (current integration suite covers Postgres only)
- Chain gold builds into orchestration
- Extend SCD Type 2 beyond `partsupp`
- Monitoring DAG (stalled tasks, Snowflake credit usage, DQ pass-rate trends), Slack alerting
- BI dashboards
- Streaming/CDC, Kubernetes, Terraform, observability stack (Prometheus/Grafana/OpenTelemetry), data catalog and lineage tracking

## Provenance

This project began as a copy of [Ibrahim-Hegazi/SalesOps-End-To-End-ETL-Pipeline](https://github.com/Ibrahim-Hegazi/SalesOps-End-To-End-ETL-Pipeline), originally built as a six-person team project — see `docs/tasks_distribution/` for the original task breakdown and team roster (Ibrahim, Manar, Ahmed, Abram, Habiba, Shrouk). I downloaded the original codebase, developed independently on my own machine, and pushed the result here as a standalone repository rather than a GitHub fork. The Snowflake environment (account, schema and role grants) is inherited from that original setup and left unchanged, since it's tied to a real account rather than just a name.

**What I added on top of the original:**
- The full data quality framework — bronze and silver checks, including SCD2 invariants — writing to `control.data_quality_metrics`
- The unit test suite (18 tests, mocked) and integration test suite (8 tests, against a live Postgres instance)
- CI pipeline (GitHub Actions) running both test suites on every push
- Watermark and audit logging hardening
- Fixes to the Airflow DAG, which previously pointed at a stale legacy script

## Contact

**Mahmoud Saad**
Data Engineer

[GitHub](https://github.com/Mahmoud2saad) · [LinkedIn](https://www.linkedin.com/in/mahmoud-saad0/)
