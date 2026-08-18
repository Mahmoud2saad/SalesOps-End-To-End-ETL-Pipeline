"""
Integration tests for dq_checks.py against a real Postgres database — the
actual SQL each check runs, against real tables with known data, rather than
a mocked scalar() return. See test_watermark_manager_integration.py for how
to run these locally; skipped automatically if TEST_DATABASE_URL isn't set.
"""

import os

import pytest
from sqlalchemy import create_engine, text

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL not set — skipping integration tests",
    ),
]

from dq_checks import (  # noqa: E402
    check_row_count_not_zero,
    check_no_nulls_in_key_column,
    check_unique_key,
    check_referential_row_ratio,
)


@pytest.fixture
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    with eng.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS dqtest"))
        conn.execute(text("""
            CREATE TABLE dqtest.orders (
                o_orderkey INTEGER PRIMARY KEY,
                o_custkey INTEGER
            )
        """))
        conn.execute(text("""
            CREATE TABLE dqtest.lineitem (
                l_orderkey INTEGER,
                l_linenumber INTEGER,
                PRIMARY KEY (l_orderkey, l_linenumber)
            )
        """))
    yield eng
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA dqtest CASCADE"))
    eng.dispose()


def test_row_count_check_against_real_empty_table(engine):
    result = check_row_count_not_zero(engine, "dqtest.orders")
    assert result["passed"] is False
    assert result["actual_value"] == "0"


def test_row_count_check_against_real_populated_table(engine):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO dqtest.orders (o_orderkey, o_custkey) VALUES (1, 10), (2, 20)"))

    result = check_row_count_not_zero(engine, "dqtest.orders")
    assert result["passed"] is True
    assert result["actual_value"] == "2"


def test_unique_key_check_catches_real_duplicates(engine):
    # o_orderkey is a real PK here, so insert into lineitem instead, which
    # allows duplicate l_orderkey values (only the composite key is unique) —
    # this is exactly the shape of bug the check exists to catch.
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO dqtest.lineitem (l_orderkey, l_linenumber) VALUES
                (1, 1), (1, 2), (2, 1)
        """))

    # l_orderkey alone has a real duplicate (order 1 appears twice) even
    # though the table's actual PK (l_orderkey, l_linenumber) is fine.
    result = check_unique_key(engine, "dqtest.lineitem", ["l_orderkey"])
    assert result["passed"] is False
    assert result["details"]["duplicate_groups"] == 1


def test_no_nulls_check_against_real_data_with_nulls(engine):
    with engine.begin() as conn:
        # o_custkey is nullable in this test schema even though o_orderkey isn't
        conn.execute(text("INSERT INTO dqtest.orders (o_orderkey, o_custkey) VALUES (1, NULL), (2, 20)"))

    result = check_no_nulls_in_key_column(engine, "dqtest.orders", "o_custkey")
    assert result["passed"] is False
    assert result["details"]["null_count"] == 1


def test_referential_ratio_catches_real_orphaned_rows(engine):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO dqtest.orders (o_orderkey, o_custkey) VALUES (1, 10)"))
        conn.execute(text("""
            INSERT INTO dqtest.lineitem (l_orderkey, l_linenumber) VALUES
                (1, 1),   -- matches a real order
                (999, 1)  -- orphaned: no order 999 exists
        """))

    result = check_referential_row_ratio(
        engine,
        child_table="dqtest.lineitem",
        child_fk_column="l_orderkey",
        parent_table="dqtest.orders",
        parent_pk_column="o_orderkey",
        max_orphan_ratio=0.0,
    )

    assert result["passed"] is False
    assert result["details"]["orphan_count"] == 1
    assert result["details"]["total_rows"] == 2
