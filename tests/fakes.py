"""
Shared fakes for testing code that takes a SQLAlchemy engine, without
needing a live Postgres connection. Each test supplies an `execute_side_effect`
callable that receives (query, params) and returns whatever conn.execute()
would — most tests use this to hand back a canned row or record what was
passed in.
"""

from unittest.mock import MagicMock


class FakeConnection:
    def __init__(self, execute_side_effect):
        self._side_effect = execute_side_effect

    def execute(self, query, params=None):
        return self._side_effect(query, params)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeEngine:
    """Fakes both engine.connect() and engine.begin(), since the real code
    uses connect() for reads and begin() for writes that need a transaction."""

    def __init__(self, execute_side_effect):
        self._side_effect = execute_side_effect

    def connect(self):
        return FakeConnection(self._side_effect)

    def begin(self):
        return FakeConnection(self._side_effect)


def scalar_result(value):
    """Fakes the .scalar() chain used by AuditLogger.log_start and the DQ checks."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = value
    return mock_result


def mapping_row_result(row_dict):
    """Fakes the .mappings().fetchone() chain used by WatermarkManager.get_watermark."""
    mock_result = MagicMock()
    mock_result.mappings.return_value.fetchone.return_value = row_dict
    return mock_result
