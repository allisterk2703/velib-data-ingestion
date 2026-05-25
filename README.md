# velib-data-ingestion

Apache Airflow pipeline for near-real-time ingestion of Vélib' station data. Two DAGs orchestrate the full flow from API fetch to analytics-ready tables.

---

### Architecture

**dag_velib_station_status_ingestion** — every 15 minutes:
1. `src/fetch_velib_data.py` — calls the Vélib' public API, writes raw CSVs to `data/station_status/raw/YYYY/MM/DD/`
2. `src/enrich_velib_station_info.py` — joins raw status with static station metadata
3. `scripts/upload_to_s3.sh` — syncs raw data to S3 (`velib-airflow-<region>-<account_id>`)

**dag_velib_station_status_weekly_pipeline** — weekly at 00:05 (Monday):
1. dbt incremental run — `mart_station_status` reads from `station_status_raw`, appends snapshots since the last partition to the partitioned Parquet table. If triggered outside Monday, data is appended up to the moment of the run (not up to the end of the week).
2. Telegram success notification via `utils/telegram_notifier.py`

**Infrastructure** (provisioned via Terraform in `terraform/`): S3 bucket, Glue crawler, Athena database.

**Alerting**: task failures → email via Mailjet (`utils/alerting.py`, Airflow Variable `ALERT_EMAILS`).

---

### Environment configuration

A `.env` file is required at the project root (not tracked by Git):

```env
TELEGRAM_BOT_TOKEN=<YOUR_TELEGRAM_BOT_TOKEN>
TELEGRAM_CHAT_ID=<YOUR_TELEGRAM_CHAT_ID>

EMAIL_ADDRESS_RECEIVER=<YOUR_EMAIL_ADDRESS_RECEIVER>
EMAIL_ADDRESS_SENDER=<YOUR_EMAIL_ADDRESS_SENDER>

AWS_PROFILE=<YOUR_AWS_PROFILE>
AWS_REGION=<YOUR_AWS_REGION>
```

---

### Setup

```bash
make create-env               # create .venv/ with Python 3.10.14 via uv
make install-requirements     # install main dependencies
make install-requirements-dev # install dev dependencies (pytest, ruff, dbt-athena…)
make deploy-dags              # symlink dags/ into ~/airflow/dags/
```

---

### Author

Allister K.

---

### License

MIT
