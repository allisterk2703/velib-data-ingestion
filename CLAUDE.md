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
pre-commit run --all-files  # run pre-commit hooks (ruff lint/format)
```

CI (`.github/workflows/ci.yml`) runs lint + format check + pytest on every push and PR.

Running a single script manually:
```bash
.venv/bin/python src/fetch_station_status.py
.venv/bin/python src/fetch_station_info.py
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
1. `src/fetch_station_status.py` — calls Vélib' public API, writes `data/station_status/raw/YYYY/MM/DD/velib_data_<timestamp>.csv`
2. `src/fetch_station_info.py` — fetches static station metadata
3. `src/enrich_velib_station_info.py` — spatial join (GeoPandas) with communes (data.gouv.fr) and arrondissements (opendata.paris.fr) GeoJSON files
4. `scripts/upload_to_s3.sh` — syncs `data/station_status/raw/` to S3 bucket `velib-data-ingestion-<account_id>-<region>`

**dag_velib_station_status_weekly_pipeline** (weekly at 00:05 Monday):
1. dbt incremental run — `mart_station_status` reads from `velib_data_ingestion.station_status_raw`, appends snapshots since the last partition to the partitioned Parquet table. Filters on quarter-hour timestamps (0, 15, 30, 45 min). If triggered outside Monday, data is appended up to the moment of the run, not up to end of week.
2. Telegram notification via `utils/telegram_notifier.py`

**dbt targets** (`dbt/velib_data_ingestion_dbt/profiles.yml`): `dev` → Athena database `allister_sandbox`; `prod` → `velib_data_ingestion`. Sandbox model `bikes_by_station` lives in `models/sandbox/` (dev only).

**S3 / AWS Glue / Athena**: Terraform in `terraform/` provisions the S3 bucket, Glue crawler, Athena database, and two external Glue tables (`station_status_raw`, `station_info`). AWS auth uses `AWS_PROFILE` from `.env`; the S3 upload script resolves the bucket name dynamically via `aws sts get-caller-identity`.

**Alerting**: Task failures trigger an email via Airflow's `send_email()` — global callback in `~/airflow/plugins/callbacks/notify.py`, SMTP via Resend (`airflow@allisterkohn.com`), recipients in Airflow Variable `ALERT_EMAILS`. Success triggers a Telegram message via `utils/telegram_notifier.py`.

## Required `.env` file

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
AWS_PROFILE=
AWS_REGION=
```
