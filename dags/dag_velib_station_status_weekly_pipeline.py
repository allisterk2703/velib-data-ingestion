from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from pendulum import timezone

from callbacks.notify import notify_task_failure
from utils.telegram_notifier import send_telegram_message

HOME = Path.home()
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
PROJECT_NAME = PROJECT_ROOT.split("/")[-1].lower()
PROJECT_VENV = Path(PROJECT_ROOT) / ".venv" / "bin"

PYENV_PYTHON = PROJECT_VENV / "python"
DBT_BIN = PROJECT_VENV / "dbt"


DAG_DOC_MD = """
### dag_velib_station_status_weekly_pipeline

This DAG runs the dbt incremental model that appends the previous week's raw Vélib station status records into the `mart_station_status` Athena/Parquet table.
It represents the weekly batch transform layer of the Vélib data pipeline, downstream of the near-real-time ingestion DAG.

#### Schedule

- Frequency: Runs every Monday at 00:05 (Europe/Paris)
- Catchup: disabled

#### Tasks

1. **build_incremental_table**
   - Sources `activate-dbt` to set dbt environment variables, then runs `dbt run --target prod --select mart_station_status`.
   - Appends new partitions (year/month/day) to the `mart_station_status` Parquet table on S3/Athena.
   - Uses an incremental append strategy partitioned by year, month, and day.

2. **notify_success**
   - Sends a Telegram notification once the DAG has completed successfully.
   - Provides lightweight operational monitoring outside of the Airflow UI.
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
    dag_id="dag_velib_station_status_weekly_pipeline",
    description="2) Weekly dbt incremental run on mart_station_status + Telegram notification",
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

notify_success = PythonOperator(
    task_id="notify_success",
    dag=dag,
    python_callable=lambda: send_telegram_message(
        "dag_velib_station_status_weekly_pipeline was executed successfully ✅"
    ),
)

build_incremental_table >> notify_success
