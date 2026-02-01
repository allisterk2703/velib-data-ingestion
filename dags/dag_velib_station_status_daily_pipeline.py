from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from pendulum import timezone

from utils.alerting import notify_task_failure
from utils.telegram_notifier import send_telegram_message

HOME = Path.home()
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
PROJECT_NAME = PROJECT_ROOT.split("/")[-1].lower()
PROJECT_VENV = HOME / ".pyenv" / "versions" / f"{PROJECT_NAME}-env" / "bin"

PYENV_PYTHON = PROJECT_VENV / "python"
DBT_BIN = PROJECT_VENV / "dbt"


DAG_DOC_MD = """
### dag_velib_station_status_daily_pipeline

This DAG consolidates Velib station status data collected during the previous day (D-1) and publishes the cleaned dataset to S3.
It represents the daily batch layer of the Velib data pipeline, complementing the near-real-time ingestion DAG.

#### Schedule

- Frequency: Runs once per day at 00:00 (Europe/Paris)
- Catchup: disabled

#### Tasks

1. **compile_yesterday_raw_files**
   - Executes a Python script responsible for aggregating all raw station status files generated during the previous day.
   - Applies basic cleaning and normalization rules.
   - Produces a consolidated dataset in the clean layer.

2. **sync_clean_to_s3**
   - Executes a shell script to synchronize the cleaned station status data to an S3 bucket.
   - Ensures durable storage and downstream availability for analytics and machine learning use cases.

3. **notify_telegram**
   - Sends a Telegram notification once the DAG has completed successfully.
   - Provides lightweight operational monitoring outside of the Airflow UI.

This DAG ensures that a single, consistent daily snapshot of Velib station statuses is available for downstream batch processing.
"""

default_args = {
    "owner": "Allister",
    "start_date": datetime(2025, 6, 1, tzinfo=timezone("Europe/Paris")),
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_task_failure,
}

dag = DAG(
    dag_id="dag_velib_station_status_daily_pipeline",
    description="2) Pipeline to concatenate yesterday's statuses and push to S3",
    default_args=default_args,
    schedule="5 0 * * 1",
    dagrun_timeout=timedelta(minutes=1),
    catchup=False,
    max_active_tasks=1,
    tags=["velib-data-ingestion"],
    doc_md=DAG_DOC_MD,
)

build_incremental_table = BashOperator(
    task_id="build_incremental_table",
    dag=dag,
    bash_command=f"""
    set -e
    source {PROJECT_ROOT}/activate-dbt
    {DBT_BIN} run --target prod --select mart_station_status
    """,
    cwd=PROJECT_ROOT,
)

notify_telegram = PythonOperator(
    task_id="notify_telegram",
    dag=dag,
    python_callable=lambda: send_telegram_message(
        "DAG `concatenate_yesterday_statuses_and_push_to_s3` executed successfully"
    ),
)

build_incremental_table >> notify_telegram
