# velib-data-ingestion

This repository contains an Apache Airflow pipeline designed to ingest Vélib’ station status data every 15 minutes.

The pipeline automatically fetches real-time station status data from the Vélib’ API and stores it in a raw data layer, partitioned by date, following this structure:

`data/station_status/raw/YYYY/MM/DD/`

The collected data is intended to serve as a foundation for downstream analytics, batch processing, and machine learning workflows.

---

### Environment configuration

This project requires a `.env` file located at the root of the repository.  
This file is not tracked by Git and must be created manually.

Example `.env` file:

```env
TELEGRAM_BOT_TOKEN=<YOUR_TELEGRAM_BOT_TOKEN>
TELEGRAM_CHAT_ID=<YOUR_TELEGRAM_CHAT_ID>

EMAIL_ADDRESS_RECEIVER=<YOUR_EMAIL_ADDRESS_RECEIVER>
EMAIL_ADDRESS_SENDER=<YOUR_EMAIL_ADDRESS_SENDER>
MAILJET_API_KEY=<YOUR_MAILJET_API_KEY>
MAILJET_SECRET_KEY=<YOUR_MAILJET_SECRET_KEY>

AWS_PROFILE=<YOUR_AWS_PROFILE>
```

These variables are used for alerting, notifications, and AWS authentication.

---

### Author

Allister K.

---

### License

This project is licensed under the MIT License.
