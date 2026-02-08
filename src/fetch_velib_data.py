# src/fetch_velib_data.py

import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

actual_datetime = datetime.now()
actual_datetime = actual_datetime.replace(second=0, microsecond=0)
actual_datetime_str = actual_datetime.strftime("%Y-%m-%d %H:%M:%S")


def create_folder(DATA_DIR, year, month, day):
    folder_path = DATA_DIR / f"{year}/{month}/{day}"
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


def fetch_station_info(folder_path):
    # --- Station Information ---
    logging.info("Fetching station information")
    url_info = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json"
    response_info = requests.get(url_info, timeout=10)

    if response_info.status_code == 200:
        data_info = response_info.json()
        stations_info = data_info["data"]["stations"]
        df_station_info = pd.DataFrame(stations_info)
        df_station_info = df_station_info[["stationCode", "name", "lat", "lon", "capacity"]]
        os.makedirs(folder_path, exist_ok=True)
        df_station_info.to_csv(folder_path / "velib_station_info.csv", index=False)
        logging.info(f"Station info saved in {folder_path / 'station_info' / 'velib_station_info.csv'}")
    else:
        logging.error(f"Error fetching station information: {response_info.status_code}")
        return None

    return df_station_info


def is_summer(elem):
    return elem in [6, 7, 8]


def fetch_station_status(folder_path):
    folder_path = folder_path / "raw"

    # --- Station Status ---
    logging.info("Fetching station status")
    url_status = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
    response_status = requests.get(url_status, timeout=10)

    if response_status.status_code == 200:
        data_status = response_status.json()
        stations_status = data_status["data"]["stations"]
        formatted_time = actual_datetime_str.replace(" ", "_").replace(":", "-")
        folder_path = create_folder(
            folder_path,
            actual_datetime.year,
            f"{actual_datetime.month:02}",
            f"{actual_datetime.day:02}",
        )
        df_dispos = pd.DataFrame(stations_status)
        df_dispos = df_dispos[
            [
                "stationCode",
                "num_bikes_available",
                "num_bikes_available_types",
                "num_docks_available",
                "is_returning",
            ]
        ]
        if df_dispos["stationCode"].isna().sum() == df_dispos.shape[0]:
            logging.error("stationCode column only has nulls")
            return None
        else:
            df_dispos["stationCode"] = df_dispos["stationCode"].astype(float).astype("Int64")

    else:
        logging.error(f"Error fetching station status: {response_status.status_code}")
        return None

    def extract_bike_counts(bike_list):
        mechanical = 0
        ebike = 0
        for bike in bike_list:
            mechanical += bike.get("mechanical", 0)
            ebike += bike.get("ebike", 0)
        return pd.Series([mechanical, ebike])

    df_dispos[["num_mechanical_bikes_available", "num_ebike_bikes_available"]] = df_dispos[
        "num_bikes_available_types"
    ].apply(extract_bike_counts)

    df_dispos = df_dispos.rename({"is_returning": "is_working"}, axis=1)
    df_dispos = df_dispos.drop(columns=["num_bikes_available_types"])

    df_dispos["updated_at"] = pd.to_datetime(actual_datetime_str)
    df_dispos["updated_at"] = df_dispos["updated_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # --- Save Output ---
    output_file = folder_path / f"velib_data_{formatted_time}.csv"
    df_dispos.to_csv(output_file, index=False)
    logging.info(f"Data saved in {output_file}")

    return df_dispos


def run(folder_path_status, folder_path_info):
    logging.info(f"Folder path status = {folder_path_status}")
    logging.info(f"Folder path info = {folder_path_info}")

    folder_path_status.mkdir(parents=True, exist_ok=True)
    folder_path_info.mkdir(parents=True, exist_ok=True)

    df_station_info = fetch_station_info(folder_path_info)
    df_station_status = fetch_station_status(folder_path_status)

    return df_station_info, df_station_status


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent

    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    DATA_DIR_STATION_INFO = DATA_DIR / "station_info"
    DATA_DIR_STATION_INFO.mkdir(parents=True, exist_ok=True)

    DATA_DIR_STATION_STATUS = DATA_DIR / "station_status"
    DATA_DIR_STATION_STATUS.mkdir(parents=True, exist_ok=True)

    logging.info("STARTED FETCHING STATION STATUS...")
    df_station_info, df_station_status = run(DATA_DIR_STATION_STATUS, DATA_DIR_STATION_INFO)
    logging.info("FETCHING STATION STATUS COMPLETED")
