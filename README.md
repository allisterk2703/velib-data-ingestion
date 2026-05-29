# velib-data-ingestion

Apache Airflow pipeline for near-real-time ingestion of Vélib' station data. Two DAGs orchestrate the full flow from API fetch to analytics-ready tables.

---

### Architecture

**dag_velib_station_status_ingestion** — every 15 minutes:
1. `src/fetch_velib_data.py` — calls the Vélib' public API, writes raw CSVs to `data/station_status/raw/YYYY/MM/DD/`
2. `src/enrich_velib_station_info.py` — spatial join with communes (data.gouv.fr) and arrondissements (opendata.paris.fr) GeoJSON files
3. `scripts/upload_to_s3.sh` — syncs raw data to S3 (`velib-data-ingestion-<account_id>-<region>`)

**dag_velib_station_status_weekly_pipeline** — weekly at 00:05 (Monday):
1. dbt incremental run — `mart_station_status` reads from `station_status_raw`, appends snapshots since the last partition to the partitioned Parquet table. If triggered outside Monday, data is appended up to the moment of the run (not up to the end of the week).
2. Telegram success notification via `utils/telegram_notifier.py`

**dbt models** (`dbt/velib_data_ingestion_dbt/`):
- `models/marts/mart_station_status.sql` — incremental append, partitioned by year/month/day, filters on quarter-hour timestamps (0, 15, 30, 45 min)
- `models/sandbox/bikes_by_station.sql` — aggregation table (dev exploration)
- Two targets: `dev` (Athena database `allister_sandbox`) and `prod` (database `velib_data_ingestion`)

**Infrastructure** (provisioned via Terraform in `terraform/`): S3 bucket, Glue crawler, Athena database, two external Glue tables (`station_status_raw`, `station_info`).

**Alerting**: task failures → email via Airflow's `send_email()` (`utils/alerting.py`, Airflow Variable `ALERT_EMAILS`).

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

Pre-commit hooks (ruff lint/format) are configured in `.pre-commit-config.yaml`. Install with:

```bash
pre-commit install
```

CI runs on every push and PR (`.github/workflows/ci.yml`): lint, format check, pytest.

---

### Git workflow

`main` is protected. All work happens on `dev` (or feature branches), merged into `main` via PRs using **rebase merge** (no merge commits).

After merging a PR, sync `dev`:

```bash
git pull origin main && git push origin dev --force-with-lease
```

---

### Author

Allister Kohn

---

### License

MIT
