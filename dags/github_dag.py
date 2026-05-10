from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'sabina',
    'start_date': datetime(2025, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'github_metrics_daily',
    default_args=default_args,
    schedule_interval='0 2 * * *',
    catchup=False,
) as dag:
    run_etl = BashOperator(
        task_id='run_etl',
        bash_command='python /opt/airflow/scripts/etl_github.py',
    )
    run_etl