from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from datetime import timedelta
import pendulum

default_args = {
    'owner': 'Data_Engineering_Team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['data_alerts@yourcompany.com'],
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

# NOTE: this previously pointed at "3) fast_incremental_load.py", a legacy
# script that has since been moved to dev_code/1) Scripts/legacy/ and is no
# longer compatible with the current control.watermarks schema. Fixed to run
# the current bronze incremental loader instead.
BRONZE_INCREMENTAL_SCRIPT = '/opt/airflow/dev_code/1) Scripts/5) Bronze Incremental Load.py'
DQ_RUNNER_SCRIPT = '/opt/airflow/dev_code/1) Scripts/quality/dq_runner.py'

# NOTE: silver LOAD is intentionally not chained into this DAG. Unlike the
# bronze incremental script, "7) Silver Incremental Load.py" is parameterized
# by a manual batch/year argument (defaults to 1996 if none is passed) rather
# than driving off the current date — it's a batch backfill tool, not a
# continuous incremental job as written. Chaining it into a daily cron DAG
# as-is would silently reprocess the same default batch every run, which
# would be worse than not automating it at all. Real fix for that is
# rewriting the script to compute its own date window, tracked as a TODO in
# Future Improvements rather than faked here.
#
# What IS wired in below: silver DQ checks run against whatever silver data
# currently exists (from the last manual load), so at least drift/corruption
# in silver gets caught daily even though the load itself isn't automated yet.

with DAG(
    dag_id='SalesOps_Enterprise_Incremental_Load',
    default_args=default_args,
    description='Enterprise-grade Incremental Pipeline for Bronze Layer (PySpark + COPY) + DQ gate',
    schedule_interval='0 2 * * *',
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=['Bronze', 'SalesOps', 'PySpark', 'CDC'],
) as dag:

    start_pipeline = DummyOperator(task_id='start_pipeline')
    end_pipeline = DummyOperator(task_id='end_pipeline')

    run_incremental_load = BashOperator(
        task_id='extract_and_load_incremental',
        bash_command=f'python "{BRONZE_INCREMENTAL_SCRIPT}"',
        do_xcom_push=False,
    )

    # dq_runner.py exits 1 if any CRITICAL check fails, so BashOperator
    # naturally fails the task (and, via default_args retries, gets retried
    # before the DAG run is marked failed) — no extra branching logic needed
    # to distinguish "DQ passed" from "DQ failed critically".
    run_bronze_data_quality_checks = BashOperator(
        task_id='run_bronze_data_quality_checks',
        bash_command=f'python "{DQ_RUNNER_SCRIPT}" --layer bronze',
        do_xcom_push=False,
    )

    # Checks whatever silver data currently exists — see the module-level
    # NOTE above for why silver load isn't chained in ahead of this.
    run_silver_data_quality_checks = BashOperator(
        task_id='run_silver_data_quality_checks',
        bash_command=f'python "{DQ_RUNNER_SCRIPT}" --layer silver',
        do_xcom_push=False,
    )

    start_pipeline >> run_incremental_load >> run_bronze_data_quality_checks >> run_silver_data_quality_checks >> end_pipeline
