import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

actual_datetime = datetime.now().replace(second=0, microsecond=0)
actual_datetime_str = actual_datetime.strftime("%Y-%m-%d %H:%M:%S")


def create_folder(data_dir, year, month, day):
    folder_path = data_dir / f"{year}/{month}/{day}"
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def fetch_station_status(folder_path):
    folder_path = folder_path / "raw"

    logging.info("Fetching station status")
    url = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        logging.error(f"Error fetching station status: {response.status_code}")
        return None

    stations_status = response.json()["data"]["stations"]
    formatted_time = actual_datetime_str.replace(" ", "_").replace(":", "-")
    folder_path = create_folder(
        folder_path,
        actual_datetime.year,
        f"{actual_datetime.month:02}",
        f"{actual_datetime.day:02}",
    )
    df = pd.DataFrame(stations_status)
    df = df[["stationCode", "num_bikes_available", "num_bikes_available_types", "num_docks_available", "is_returning"]]

    if df["stationCode"].isna().sum() == df.shape[0]:
        logging.error("stationCode column only has nulls")
        return None

    df["stationCode"] = df["stationCode"].astype(float).astype("Int64")

    def extract_bike_counts(bike_list):
        mechanical = sum(b.get("mechanical", 0) for b in bike_list)
        ebike = sum(b.get("ebike", 0) for b in bike_list)
        return pd.Series([mechanical, ebike])

    df[["num_mechanical_bikes_available", "num_ebike_bikes_available"]] = df["num_bikes_available_types"].apply(
        extract_bike_counts
    )
    df = df.rename(columns={"is_returning": "is_working"})
    df = df.drop(columns=["num_bikes_available_types"])
    df["updated_at"] = pd.to_datetime(actual_datetime_str).strftime("%Y-%m-%d %H:%M:%S")

    output_file = folder_path / f"velib_data_{formatted_time}.csv"
    df.to_csv(output_file, index=False)
    logging.info(f"Data saved in {output_file}")

    return df


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data" / "station_status"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    logging.info("Fetching station status...")
    fetch_station_status(DATA_DIR)
    logging.info("Done.")
