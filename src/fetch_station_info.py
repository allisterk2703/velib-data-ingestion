import logging
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def fetch_station_info(output_dir):
    logging.info("Fetching station information")
    url = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json"
    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        logging.error(f"Error fetching station information: {response.status_code}")
        return None

    stations_info = response.json()["data"]["stations"]
    df = pd.DataFrame(stations_info)[["stationCode", "name", "lat", "lon", "capacity"]]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "velib_station_info.csv"
    df.to_csv(output_file, index=False)
    logging.info(f"Station info saved in {output_file}")

    return df


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data" / "station_info"

    logging.info("Fetching station info...")
    fetch_station_info(DATA_DIR)
    logging.info("Done.")
