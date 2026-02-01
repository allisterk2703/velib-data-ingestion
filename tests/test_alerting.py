import logging
import os
from datetime import datetime, timezone

from airflow.utils.email import send_email
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv(override=True)

if __name__ == "__main__":
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    send_email(
        to=str(os.getenv("EMAIL_ADDRESS_RECEIVER")),
        subject="Airflow Alerts - Test email",
        html_content=f"This is a test email sent at {now}.",
    )
