from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from pendulum import timezone

from utils.alerting import notify_task_failure

HOME = Path.home()
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
PROJECT_NAME = PROJECT_ROOT.split("/")[-1].lower()
PROJECT_VENV = HOME / ".pyenv" / "versions" / f"{PROJECT_NAME}-env" / "bin"

PYENV_PYTHON = PROJECT_VENV / "python"


DAG_DOC_MD = """
### dag_velib_station_status_ingestion

This DAG performs near-real-time ingestion of Velib station data every 15 minutes.
It orchestrates the extraction, enrichment, and persistence of station status data to S3, forming the raw and enriched layers of the Velib data pipeline.
The data produced by this DAG serves as the foundation for downstream batch processing, analytics, and machine learning workloads.

#### Schedule

- Frequency: Runs every 15 minutes
- Catchup: disabled

#### Tasks

1. **fetch_station_status**
   - Executes a Python script that fetches live Velib station status data from the official public API.
   - Stores the collected data locally in the raw layer, preserving the original structure for traceability and reprocessing.

2. **enrich_station_info_data**
   - Enriches the raw station status data with static station metadata (geolocation, capacity, station identifiers, operational attributes).
   - Produces a normalized and enriched dataset suitable for downstream processing.

3. **sync_raw_to_s3**
   - Synchronizes the raw station status data to an S3-compatible storage.
   - Ensures durable storage, historical retention, and availability for batch consolidation and analytical use cases.

This DAG is designed to be idempotent at the task level and resilient to transient API or network failures.
"""

default_args = {
    "owner": "Allister",
    "start_date": datetime(2025, 6, 1, tzinfo=timezone("Europe/Paris")),
    "depends_on_past": False,
    "retries": 0,
    "on_failure_callback": notify_task_failure,
}

dag = DAG(
    dag_id="dag_velib_station_status_ingestion",
    description="1) Pipeline to fetch and enrich Velib data",
    default_args=default_args,
    dagrun_timeout=timedelta(minutes=1),
    schedule="0,15,30,45 * * * *",  # every 15 minutes
    catchup=False,
    max_active_tasks=1,
    tags=["velib-data-ingestion"],
    doc_md=DAG_DOC_MD,
)

fetch_velib_data = BashOperator(
    task_id="fetch_station_status",
    dag=dag,
    bash_command=f"{PYENV_PYTHON} src/fetch_velib_data.py",
    cwd=PROJECT_ROOT,
)

enrich_station_info_data = BashOperator(
    task_id="enrich_station_info_data",
    dag=dag,
    bash_command=f"{PYENV_PYTHON} src/enrich_velib_station_info.py",
    cwd=PROJECT_ROOT,
)

sync_raw_to_s3 = BashOperator(
    task_id="sync_raw_to_s3",
    dag=dag,
    bash_command=f"bash -c '{PROJECT_ROOT}/scripts/upload_to_s3.sh data/station_status/raw station_status/raw'",
    cwd=PROJECT_ROOT,
)

fetch_velib_data >> enrich_station_info_data >> sync_raw_to_s3
