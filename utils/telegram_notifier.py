import logging
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = Path(__file__).resolve().parents[1]
DOTENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=DOTENV_PATH, override=True)


def send_telegram_message(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"

    if not bot_token or not chat_id:
        logging.error("Token or Chat ID missing")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=payload)
        logging.info(f"Telegram message '{message}' sent successfully")
        return True
    except Exception as e:
        logging.error(f"Erreur Telegram : {e}")
        return False
