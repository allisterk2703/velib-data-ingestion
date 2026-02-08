# src/compile_yesterday_raw_files.py

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DATA_DIR = Path("data")


def create_folder(year, month):
    folder_path = DATA_DIR / "station_status" / "clean" / f"{year}/{month:02}"
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def load_yesterday_velib_data(data_dir: Path) -> pd.DataFrame:
    # Calcul de la date de la veille
    yesterday = datetime.now() - timedelta(days=1)
    y, m, d = yesterday.year, yesterday.month, yesterday.day

    # Construction du chemin de la veille
    yesterday_dir = data_dir / "station_status" / "raw" / f"{y}" / f"{m:02}" / f"{d:02}"
    logging.info(f"Looking for files in: {yesterday_dir}")

    if not yesterday_dir.exists():
        logging.warning(f"No directory found for {yesterday_dir}")
        return pd.DataFrame()

    # Liste des CSVs de la veille
    all_csvs = [
        f for f in yesterday_dir.glob("*.csv") if "velib_station_info" not in f.name and "full_velib_data" not in f.name
    ]
    logging.info(f"{len(all_csvs)} CSV files found for {yesterday_dir}")

    df_list = []
    for file in sorted(all_csvs):
        try:
            df = pd.read_csv(file)
            df["updated_at"] = pd.to_datetime(df["updated_at"])
            df_list.append(df)
        except Exception as e:
            logging.error(f"Error in {file}: {e}")

    if not df_list:
        return pd.DataFrame()

    df_all = pd.concat(df_list, ignore_index=True)
    df_all = df_all.sort_values(by=["updated_at"])

    return df_all


if __name__ == "__main__":
    logging.info("STARTED COMPILING YESTERDAY FILES...")
    df = load_yesterday_velib_data(DATA_DIR)
    yesterday = datetime.now() - timedelta(days=1)
    folder_path = create_folder(yesterday.year, yesterday.month)
    if not df.empty:
        df.to_csv(folder_path / f"velib_{yesterday.strftime('%Y-%m-%d')}.csv", index=False)
        filename = folder_path / f"velib_{yesterday.strftime('%Y-%m-%d')}.csv"
        logging.info(f"Saved to {filename}")
    else:
        logging.warning("No data compiled")
    logging.info("COMPILING YESTERDAY FILES COMPLETED")
