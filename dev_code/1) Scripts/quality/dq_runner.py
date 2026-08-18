"""
Runs the data quality check suite and writes every result to
control.data_quality_metrics. Exits non-zero if any CRITICAL check fails, so
it can be used as an Airflow task that fails the DAG run without extra glue
code.

Usage:
    python dq_runner.py            # runs the bronze suite (what the live DAG calls)
    python dq_runner.py --layer silver   # runs the silver suite
    python dq_runner.py --layer all      # runs both
"""

import argparse
import json
import sys
from datetime import datetime

from sqlalchemy import create_engine, text

sys.path.append(__file__.rsplit("/", 2)[0])  # allow `from quality...` imports if run standalone

from dq_checks import (
    check_row_count_not_zero,
    check_no_nulls_in_key_column,
    check_unique_key,
    check_referential_row_ratio,
)

SOURCE_CONN = "postgresql+psycopg2://source_user:source_pass@postgres-local:5432/data_platform_db"
CONTROL_CONN = "postgresql+psycopg2://control_user:control_pass@postgres-control:5432/control"


def build_bronze_check_suite():
    """
    Checks target the bronze layer. This is the suite bronze_layer_dag.py
    calls right after the bronze incremental load — the only tables
    guaranteed to be freshly populated at that point in the DAG.

    Note: bronze foreign-key constraints are intentionally dropped for load
    performance (see "5) Bronze Incremental Load.py"), which is exactly why
    the referential integrity check below earns its place — the database
    itself won't catch a broken lineitem -> orders link at this layer.
    """
    return [
        lambda engine: check_row_count_not_zero(engine, "bronze.orders"),
        lambda engine: check_row_count_not_zero(engine, "bronze.lineitem"),
        lambda engine: check_row_count_not_zero(engine, "bronze.customer"),
        lambda engine: check_no_nulls_in_key_column(engine, "bronze.orders", "o_orderkey"),
        lambda engine: check_no_nulls_in_key_column(engine, "bronze.lineitem", "l_orderkey"),
        lambda engine: check_unique_key(engine, "bronze.orders", ["o_orderkey"]),
        lambda engine: check_unique_key(engine, "bronze.lineitem", ["l_orderkey", "l_linenumber"]),
        lambda engine: check_referential_row_ratio(
            engine,
            child_table="bronze.lineitem",
            child_fk_column="l_orderkey",
            parent_table="bronze.orders",
            parent_pk_column="o_orderkey",
            max_orphan_ratio=0.0,
            severity="ERROR",
        ),
    ]


def build_silver_check_suite():
    """
    Checks target the silver layer (dev_code/1) Scripts/6) and 7) Silver
    *.py). Not yet wired into any Airflow DAG — silver builds are still run
    manually — but callable standalone (`--layer silver`) or once silver is
    chained into orchestration.

    Silver also has no FK constraints (see "6) Silver Initial Load.py"), so
    the same referential-integrity gap that justifies the bronze check
    applies here too — a bad transform could silently drop matching orders
    without the database ever noticing.

    Also checks the partsupp SCD Type 2 columns specifically, since that's
    the one dimension in this repo with actual history tracking, and a bug
    there (e.g. two rows marked is_current for the same key) would be easy
    to miss without a dedicated check.
    """
    return [
        lambda engine: check_row_count_not_zero(engine, "silver.orders"),
        lambda engine: check_row_count_not_zero(engine, "silver.lineitem"),
        lambda engine: check_row_count_not_zero(engine, "silver.partsupp"),
        lambda engine: check_no_nulls_in_key_column(engine, "silver.orders", "o_orderkey"),
        lambda engine: check_no_nulls_in_key_column(engine, "silver.lineitem", "l_orderkey"),
        lambda engine: check_unique_key(engine, "silver.orders", ["o_orderkey"]),
        lambda engine: check_unique_key(engine, "silver.lineitem", ["l_orderkey", "l_linenumber"]),
        lambda engine: check_referential_row_ratio(
            engine,
            child_table="silver.lineitem",
            child_fk_column="l_orderkey",
            parent_table="silver.orders",
            parent_pk_column="o_orderkey",
            max_orphan_ratio=0.0,
            severity="ERROR",
        ),
        # SCD2 invariant: a given (ps_partkey, ps_suppkey) should have at
        # most one row where is_current = TRUE. More than one is a real bug
        # in the SCD2 merge logic, not a data issue, so this is CRITICAL.
        lambda engine: check_unique_key(
            engine,
            "(SELECT ps_partkey, ps_suppkey FROM silver.partsupp WHERE is_current = TRUE) AS current_partsupp",
            ["ps_partkey", "ps_suppkey"],
        ),
    ]


def write_result(control_engine, execution_id, result):
    # Column list matches control.data_quality_metrics as created in
    # "4) Bronze Initial Load.py" — metric_type and execution_id are real
    # columns on that table, not extras.
    insert_sql = text("""
        INSERT INTO control.data_quality_metrics
            (table_name, check_name, metric_type, expected_value, actual_value,
             passed, severity, execution_id, details, checked_at)
        VALUES
            (:table_name, :check_name, :metric_type, :expected_value, :actual_value,
             :passed, :severity, :execution_id, :details, CURRENT_TIMESTAMP)
    """)
    with control_engine.begin() as conn:
        conn.execute(insert_sql, {
            "table_name": result["table_name"],
            "check_name": result["check_name"],
            "metric_type": result.get("metric_type", "integrity"),
            "expected_value": result["expected_value"],
            "actual_value": result["actual_value"],
            "passed": result["passed"],
            "severity": result["severity"],
            "execution_id": str(execution_id),
            "details": json.dumps(result.get("details", {})),
        })


def run_checks(check_fns, execution_id, source_engine, control_engine):
    results = []
    for check_fn in check_fns:
        try:
            result = check_fn(source_engine)
        except Exception as e:
            result = {
                "check_name": "check_execution_error",
                "table_name": "unknown",
                "expected_value": "check runs without error",
                "actual_value": str(e),
                "passed": False,
                "severity": "CRITICAL",
                "details": {"exception": str(e)},
            }
        write_result(control_engine, execution_id, result)
        results.append(result)

        symbol = "✅" if result["passed"] else "❌"
        print(f"{symbol} [{result['severity']}] {result['check_name']} on {result['table_name']}: "
              f"expected {result['expected_value']}, got {result['actual_value']}")
    return results


def run_all_checks(layer="bronze", execution_id=None):
    execution_id = execution_id or datetime.utcnow().strftime("dq_%Y%m%d_%H%M%S")
    source_engine = create_engine(SOURCE_CONN)
    control_engine = create_engine(CONTROL_CONN)

    suites = []
    if layer in ("bronze", "all"):
        suites += build_bronze_check_suite()
    if layer in ("silver", "all"):
        suites += build_silver_check_suite()

    results = run_checks(suites, execution_id, source_engine, control_engine)

    critical_failures = [r for r in results if not r["passed"] and r["severity"] == "CRITICAL"]
    if critical_failures:
        print(f"\n🛑 {len(critical_failures)} CRITICAL check(s) failed.")
        sys.exit(1)

    failures = [r for r in results if not r["passed"]]
    if failures:
        print(f"\n⚠️ {len(failures)} non-critical check(s) failed. Continuing.")
    else:
        print(f"\n🎉 All {len(results)} data quality checks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--layer", choices=["bronze", "silver", "all"], default="bronze")
    args = parser.parse_args()
    run_all_checks(layer=args.layer)
