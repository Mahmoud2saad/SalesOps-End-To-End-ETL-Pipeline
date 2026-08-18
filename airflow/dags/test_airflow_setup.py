from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def check_everything_ok():
    print("=========================================")
    print("SUCCESS: Airflow Scheduler and Worker are running perfectly!")
    print("=========================================")

with DAG(
    dag_id='test_setup_dag',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:

    test_task = PythonOperator(
        task_id='print_success',
        python_callable=check_everything_ok
    )