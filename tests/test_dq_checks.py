"""
Unit tests for the new dq_checks module. Each check runs a single query, so
these mostly verify the pass/fail threshold logic rather than SQL
correctness — that part still needs an integration test against a real
Postgres instance with known TPC-H data loaded.
"""

from unittest.mock import MagicMock

from dq_checks import (
    check_row_count_not_zero,
    check_no_nulls_in_key_column,
    check_unique_key,
    check_referential_row_ratio,
)
from fakes import FakeEngine, scalar_result


def test_row_count_not_zero_passes_when_rows_exist():
    result = check_row_count_not_zero(FakeEngine(lambda q, p: scalar_result(1500)), "silver.orders")

    assert result["passed"] is True
    assert result["actual_value"] == "1500"
    assert result["severity"] == "CRITICAL"


def test_row_count_not_zero_fails_when_table_empty():
    result = check_row_count_not_zero(FakeEngine(lambda q, p: scalar_result(0)), "silver.orders")

    assert result["passed"] is False


def test_no_nulls_check_passes_with_zero_nulls():
    result = check_no_nulls_in_key_column(
        FakeEngine(lambda q, p: scalar_result(0)), "silver.orders", "o_orderkey"
    )

    assert result["passed"] is True


def test_no_nulls_check_fails_with_nulls_present():
    result = check_no_nulls_in_key_column(
        FakeEngine(lambda q, p: scalar_result(3)), "silver.orders", "o_orderkey"
    )

    assert result["passed"] is False
    assert result["details"]["null_count"] == 3


def test_unique_key_passes_with_no_duplicate_groups():
    result = check_unique_key(FakeEngine(lambda q, p: scalar_result(0)), "silver.orders", ["o_orderkey"])

    assert result["passed"] is True


def test_unique_key_fails_with_duplicate_groups():
    result = check_unique_key(
        FakeEngine(lambda q, p: scalar_result(7)), "silver.lineitem", ["l_orderkey", "l_linenumber"]
    )

    assert result["passed"] is False
    assert result["details"]["duplicate_groups"] == 7


def test_referential_ratio_passes_when_no_orphans():
    # First execute() call returns orphan count, second returns total count.
    calls = iter([scalar_result(0), scalar_result(1000)])

    engine = FakeEngine(lambda q, p: next(calls))
    result = check_referential_row_ratio(
        engine,
        child_table="silver.lineitem",
        child_fk_column="l_orderkey",
        parent_table="silver.orders",
        parent_pk_column="o_orderkey",
        max_orphan_ratio=0.0,
    )

    assert result["passed"] is True
    assert result["actual_value"] == "0.00%"


def test_referential_ratio_fails_when_orphans_exceed_threshold():
    calls = iter([scalar_result(50), scalar_result(1000)])  # 5% orphaned

    engine = FakeEngine(lambda q, p: next(calls))
    result = check_referential_row_ratio(
        engine,
        child_table="silver.lineitem",
        child_fk_column="l_orderkey",
        parent_table="silver.orders",
        parent_pk_column="o_orderkey",
        max_orphan_ratio=0.0,
    )

    assert result["passed"] is False
    assert result["details"]["orphan_count"] == 50


def test_referential_ratio_handles_empty_child_table_without_dividing_by_zero():
    calls = iter([scalar_result(0), scalar_result(0)])

    engine = FakeEngine(lambda q, p: next(calls))
    result = check_referential_row_ratio(
        engine,
        child_table="silver.lineitem",
        child_fk_column="l_orderkey",
        parent_table="silver.orders",
        parent_pk_column="o_orderkey",
        max_orphan_ratio=0.0,
    )

    assert result["passed"] is True
    assert result["details"]["orphan_ratio"] == 0.0
