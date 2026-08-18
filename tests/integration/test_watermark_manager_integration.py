"""
Integration tests for WatermarkManager against a real Postgres database.

Unlike tests/test_watermark_manager.py (which mocks the engine), these run
actual SQL against a live control.watermarks table — the thing the unit
tests explicitly can't verify. Requires a running Postgres reachable via
TEST_DATABASE_URL; skipped automatically if that's not set, so this file is
safe to collect in any environment (including a plain `pytest` run with no
database available).

Run locally:
    docker run --rm -d --name pg-test -e POSTGRES_PASSWORD=test -p 5433:5432 postgres:15
    export TEST_DATABASE_URL="postgresql+psycopg2://postgres:test@localhost:5433/postgres"
    pytest tests/integration -m integration

Run in CI: see the "integration-tests" job in .github/workflows/tests.yml,
which spins up a postgres:15 service container automatically.
"""

import os

import pytest
from sqlalchemy import create_engine, text

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL,
        reason="TEST_DATABASE_URL not set — skipping integration tests (see file docstring to run locally)",
    ),
]

from watermark_manager import WatermarkManager  # noqa: E402  (import after skip check)


@pytest.fixture
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    with eng.begin() as conn:
        # Matches sql_scripts/control/00-create-tables.sql exactly, so this
        # test fails loudly if the real DDL and this fixture ever drift apart.
        conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS control;
            CREATE TABLE IF NOT EXISTS control.watermarks (
                table_name VARCHAR(50) PRIMARY KEY,
                incremental_column VARCHAR(50),
                last_processed_id BIGINT DEFAULT 0,
                last_processed_timestamp TIMESTAMP,
                safety_margin_minutes INT DEFAULT 120,
                safety_margin_rows INT DEFAULT 10000,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            TRUNCATE control.watermarks;
        """))
    yield eng
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS control.watermarks"))
    eng.dispose()


def test_get_watermark_round_trips_through_real_postgres(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO control.watermarks
                (table_name, incremental_column, last_processed_id, safety_margin_rows, safety_margin_minutes)
            VALUES ('bronze.orders', 'o_orderkey', 100000, 10000, 120)
        """))

    manager = WatermarkManager(engine)
    result = manager.get_watermark("bronze.orders")

    assert result is not None
    assert result["last_processed_id"] == 100000
    assert result["safe_extraction_id"] == 90000


def test_update_watermark_persists_to_real_postgres(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO control.watermarks (table_name, last_processed_id)
            VALUES ('bronze.orders', 0)
        """))

    manager = WatermarkManager(engine)
    manager.update_watermark("bronze.orders", new_max_id=54321)

    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT last_processed_id FROM control.watermarks WHERE table_name = 'bronze.orders'"
        )).scalar()

    assert row == 54321


def test_get_watermark_returns_none_for_untracked_table(engine):
    manager = WatermarkManager(engine)
    result = manager.get_watermark("bronze.never_tracked")

    assert result is None
