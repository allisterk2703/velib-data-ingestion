import logging
from datetime import datetime, timezone

from utils.telegram_notifier import send_telegram_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    send_telegram_message(f"This is a test message sent at {now}.")
