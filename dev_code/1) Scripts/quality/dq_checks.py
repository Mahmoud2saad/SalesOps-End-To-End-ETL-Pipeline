"""
Data quality checks for the SalesOps pipeline.

Each check function takes a SQLAlchemy engine and returns a dict describing
the result. They're intentionally simple, table-integrity checks (row
counts, nulls in key columns, uniqueness of primary keys, referential
consistency) rather than business-rule validation — the goal is to catch
pipeline bugs (a failed load, a broken join, a watermark that skipped rows),
not to validate the source data itself, since TPC-H's generated data is
already clean.

Severity levels follow control.data_quality_metrics: INFO, WARNING, ERROR,
CRITICAL. A check "passing" or "failing" is a boolean; severity is what the
runner does about a failure.
"""

from sqlalchemy import text


def check_row_count_not_zero(engine, table_name, severity="CRITICAL"):
    """Fails if a table that should have data is empty."""
    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()

    return {
        "check_name": "row_count_not_zero",
        "table_name": table_name,
        "expected_value": "> 0",
        "actual_value": str(count),
        "passed": count > 0,
        "severity": severity,
        "details": {"row_count": count},
    }


def check_no_nulls_in_key_column(engine, table_name, column_name, severity="ERROR"):
    """Fails if a column that should never be null (e.g. a primary/foreign key) has nulls."""
    with engine.connect() as conn:
        null_count = conn.execute(
            text(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL")
        ).scalar()

    return {
        "check_name": f"no_nulls_in_{column_name}",
        "table_name": table_name,
        "expected_value": "0",
        "actual_value": str(null_count),
        "passed": null_count == 0,
        "severity": severity,
        "details": {"column": column_name, "null_count": null_count},
    }


def check_unique_key(engine, table_name, key_columns, severity="CRITICAL"):
    """Fails if the given column(s) have duplicate values (should be a primary/business key)."""
    cols = ", ".join(key_columns)
    query = text(f"""
        SELECT COUNT(*) FROM (
            SELECT {cols} FROM {table_name}
            GROUP BY {cols}
            HAVING COUNT(*) > 1
        ) dupes
    """)
    with engine.connect() as conn:
        dup_groups = conn.execute(query).scalar()

    return {
        "check_name": f"unique_key_{'_'.join(key_columns)}",
        "table_name": table_name,
        "expected_value": "0 duplicate groups",
        "actual_value": str(dup_groups),
        "passed": dup_groups == 0,
        "severity": severity,
        "details": {"key_columns": key_columns, "duplicate_groups": dup_groups},
    }


def check_referential_row_ratio(
    engine,
    child_table,
    child_fk_column,
    parent_table,
    parent_pk_column,
    max_orphan_ratio=0.0,
    severity="ERROR",
):
    """
    Fails if more than `max_orphan_ratio` of rows in the child table reference
    a key that doesn't exist in the parent table (a broken join / dangling FK
    that a database-level constraint wouldn't necessarily have caught, since
    the bronze layer intentionally drops FK constraints for load performance).
    """
    query = text(f"""
        SELECT COUNT(*) AS orphans
        FROM {child_table} c
        LEFT JOIN {parent_table} p ON c.{child_fk_column} = p.{parent_pk_column}
        WHERE p.{parent_pk_column} IS NULL AND c.{child_fk_column} IS NOT NULL
    """)
    total_query = text(f"SELECT COUNT(*) FROM {child_table}")

    with engine.connect() as conn:
        orphans = conn.execute(query).scalar()
        total = conn.execute(total_query).scalar()

    ratio = (orphans / total) if total else 0.0

    return {
        "check_name": f"referential_integrity_{child_table}_{parent_table}",
        "table_name": child_table,
        "expected_value": f"<= {max_orphan_ratio:.2%} orphaned rows",
        "actual_value": f"{ratio:.2%}",
        "passed": ratio <= max_orphan_ratio,
        "severity": severity,
        "details": {
            "orphan_count": orphans,
            "total_rows": total,
            "orphan_ratio": ratio,
        },
    }


def check_watermark_advanced(engine, table_name, expected_min_value=None, severity="WARNING"):
    """
    Sanity check that a table's watermark actually moved — catches the case
    where an incremental load silently processed zero new rows for longer
    than expected (e.g. an upstream extraction bug, not a genuinely quiet day).
    """
    query = text("""
        SELECT last_processed_id, last_processed_value, updated_at
        FROM control.watermarks
        WHERE table_name = :table_name
    """)
    with engine.connect() as conn:
        row = conn.execute(query, {"table_name": table_name}).mappings().fetchone()

    if row is None:
        return {
            "check_name": "watermark_advanced",
            "table_name": table_name,
            "expected_value": "watermark row exists",
            "actual_value": "missing",
            "passed": False,
            "severity": severity,
            "details": {},
        }

    current = row["last_processed_id"] or row["last_processed_value"]
    passed = expected_min_value is None or (
        current is not None and str(current) >= str(expected_min_value)
    )

    return {
        "check_name": "watermark_advanced",
        "table_name": table_name,
        "expected_value": f">= {expected_min_value}" if expected_min_value else "any",
        "actual_value": str(current),
        "passed": passed,
        "severity": severity,
        "details": {"updated_at": str(row["updated_at"])},
    }
