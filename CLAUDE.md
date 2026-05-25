# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment setup

```bash
make create-env                  # create .venv/ with Python 3.10.14 via uv
make install-requirements        # install main deps from requirements.txt
make install-requirements-dev    # install dev deps (pytest, ruff, dbt-athena, etc.)
```

The project venv is always `.venv/` at the project root. DAGs use `PROJECT_VENV = Path(__file__).resolve().parent.parent / ".venv" / "bin"` to locate Python at runtime.

## Common commands

```bash
make ruff               # lint + format with Ruff (checks dags/, src/, tests/, utils/)
.venv/bin/pytest tests/ # run all tests
```

Running a single script manually:
```bash
.venv/bin/python src/fetch_velib_data.py
.venv/bin/python src/enrich_velib_station_info.py
```

## dbt

dbt runs inside the same `.venv/`. The `activate-dbt` script sets `DBT_PROJECT_DIR` and `DBT_PROFILES_DIR` to `dbt/velib_data_ingestion_dbt/`. Source it before using `dbt` manually:

```bash
source activate-dbt
dbt run --target prod --select mart_station_status
dbt run --target prod --select mart_station_status --full-refresh
```

Or via make: `make refresh-mart`

## Deploying DAGs

```bash
make deploy-dags   # creates symlink ~/airflow/dags/velib-data-ingestion -> ./dags/
```

After modifying DAGs, reserialize in Airflow:
```bash
~/airflow/.venv/bin/airflow dags reserialize
```

## Architecture

Two Airflow DAGs orchestrate the pipeline via `BashOperator`, each invoking scripts from `src/` using the project `.venv` Python.

**dag_velib_station_status_ingestion** (every 15 min):
1. `src/fetch_velib_data.py` — calls Vélib' public API, writes `data/station_status/raw/YYYY/MM/DD/velib_data_<timestamp>.csv`
2. `src/enrich_velib_station_info.py` — joins raw status with static station metadata from `data/station_info/velib_station_info_enriched.csv`
3. `scripts/upload_to_s3.sh` — syncs `data/station_status/raw/` to S3 bucket `velib-airflow-<region>-<account_id>`

**dag_velib_station_status_weekly_pipeline** (weekly at 00:05 Monday):
1. dbt incremental run — `mart_station_status` reads from `velib_data_ingestion.station_status_raw`, appends snapshots since the last partition to the partitioned Parquet table. If triggered outside Monday, data is appended up to the moment of the run, not up to end of week.
2. Telegram notification via `utils/telegram_notifier.py`

**S3 / AWS Glue / Athena**: Terraform in `terraform/` provisions the S3 bucket, Glue crawler, and Athena database. AWS auth uses `AWS_PROFILE` from `.env`; the S3 upload script resolves the bucket name dynamically via `aws sts get-caller-identity`.

**Alerting**: Task failures trigger `utils/alerting.py` (email via Mailjet, using Airflow Variables `ALERT_EMAILS`). Success triggers a Telegram message via `utils/telegram_notifier.py`.

## Required `.env` file

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EMAIL_ADDRESS_RECEIVER=
EMAIL_ADDRESS_SENDER=
AWS_PROFILE=
AWS_REGION=
```
