"""
Unit tests for AuditLogger. Since log_start/log_complete call Postgres
functions (control.log_batch_start / log_batch_complete) rather than raw
SQL, these tests mock at the engine.execute() boundary and check the params
passed in — they don't (and can't, without a live DB) verify the SQL
functions themselves. That's a gap worth covering with an integration test
against a real Postgres instance eventually; see the CI workflow notes.
"""

from audit_logger import AuditLogger
from fakes import FakeEngine, scalar_result


def test_log_start_returns_generated_audit_id():
    logger = AuditLogger(FakeEngine(lambda q, p: scalar_result(42)))

    audit_id = logger.log_start(
        pipeline_name="bronze_incremental",
        execution_id="run_123",
        task_name="extract_orders",
        table_name="bronze.orders",
    )

    assert audit_id == 42


def test_log_start_passes_correct_params():
    captured = {}

    def side_effect(query, params):
        captured.update(params)
        return scalar_result(1)

    logger = AuditLogger(FakeEngine(side_effect))
    logger.log_start(
        pipeline_name="bronze_incremental",
        execution_id=123,
        task_name="extract_orders",
        table_name="bronze.orders",
    )

    assert captured["pipeline_name"] == "bronze_incremental"
    # execution_id should be coerced to str before hitting the DB
    assert captured["execution_id"] == "123"
    assert captured["task_name"] == "extract_orders"
    assert captured["table_name"] == "bronze.orders"


def test_log_complete_passes_status_and_row_count():
    captured = {}

    def side_effect(query, params):
        captured.update(params)
        return scalar_result(None)

    logger = AuditLogger(FakeEngine(side_effect))
    logger.log_complete(audit_id=42, status="SUCCESS", rows_processed=5000)

    assert captured["audit_id"] == 42
    assert captured["status"] == "SUCCESS"
    assert captured["rows_processed"] == 5000
    assert captured["error_message"] is None


def test_log_complete_carries_error_message_on_failure():
    captured = {}

    def side_effect(query, params):
        captured.update(params)
        return scalar_result(None)

    logger = AuditLogger(FakeEngine(side_effect))
    logger.log_complete(
        audit_id=42,
        status="FAILED",
        rows_processed=0,
        error_message="connection to postgres-local timed out",
    )

    assert captured["status"] == "FAILED"
    assert captured["error_message"] == "connection to postgres-local timed out"
