"""
Unit tests for WatermarkManager. Uses a fake SQLAlchemy engine/connection so
these run without a live Postgres instance — fast enough to run on every
commit. See fakes.py for the mock plumbing.
"""

from datetime import datetime, timedelta

from watermark_manager import WatermarkManager
from fakes import FakeEngine, mapping_row_result


def test_get_watermark_applies_row_safety_margin():
    row = {
        "incremental_column": "o_orderkey",
        "last_processed_id": 100000,
        "last_processed_timestamp": None,
        "safety_margin_minutes": 120,
        "safety_margin_rows": 10000,
    }

    manager = WatermarkManager(FakeEngine(lambda q, p: mapping_row_result(row)))
    result = manager.get_watermark("bronze.orders")

    assert result["safe_extraction_id"] == 90000  # 100000 - 10000 safety margin
    assert result["last_processed_id"] == 100000


def test_get_watermark_safety_margin_never_goes_negative():
    row = {
        "incremental_column": "o_orderkey",
        "last_processed_id": 500,          # smaller than the safety margin
        "last_processed_timestamp": None,
        "safety_margin_minutes": 120,
        "safety_margin_rows": 10000,
    }

    manager = WatermarkManager(FakeEngine(lambda q, p: mapping_row_result(row)))
    result = manager.get_watermark("bronze.orders")

    # This is the exact bug class watermarking is supposed to prevent: a naive
    # `last_id - margin` would go negative and silently skip re-extracting
    # early rows. The real code clamps to 0 via max(0, ...) — this test pins
    # that behavior so it can't regress.
    assert result["safe_extraction_id"] == 0


def test_get_watermark_applies_timestamp_safety_margin():
    now = datetime(2026, 1, 1, 12, 0, 0)
    row = {
        "incremental_column": "o_orderdate",
        "last_processed_id": 0,
        "last_processed_timestamp": now,
        "safety_margin_minutes": 30,
        "safety_margin_rows": 0,
    }

    manager = WatermarkManager(FakeEngine(lambda q, p: mapping_row_result(row)))
    result = manager.get_watermark("bronze.orders")

    assert result["safe_extraction_timestamp"] == now - timedelta(minutes=30)


def test_get_watermark_returns_none_when_no_row_exists():
    manager = WatermarkManager(FakeEngine(lambda q, p: mapping_row_result(None)))
    result = manager.get_watermark("bronze.brand_new_table")

    assert result is None


def test_update_watermark_executes_with_correct_params():
    captured = {}

    def side_effect(query, params):
        captured.update(params)
        return mapping_row_result(None)

    manager = WatermarkManager(FakeEngine(side_effect))
    manager.update_watermark("bronze.orders", new_max_id=12345)

    assert captured["new_id"] == 12345
    assert captured["table_name"] == "bronze.orders"
