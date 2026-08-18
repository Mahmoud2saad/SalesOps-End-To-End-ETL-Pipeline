# Legacy scripts

These are earlier iterations of the bronze-layer load scripts, kept for
history rather than active use. They were superseded by the numbered
pipeline in the parent folder:

- `1) fast_initial_load_v1.py` → superseded by `4) Bronze Initial Load.py`
- `2) fast_initial_load_v2.py` → superseded by `4) Bronze Initial Load.py`
- `3) fast_incremental_load.py` → superseded by `5) Bronze Incremental Load.py`

Do not run these against the current schema — `control.watermarks` and
`control.audit_log` have changed shape since these were written (e.g. the
watermark table now stores `last_processed_value` as a string to support
both numeric and date-based incremental columns; these scripts still assume
a purely numeric `last_processed_id`).
