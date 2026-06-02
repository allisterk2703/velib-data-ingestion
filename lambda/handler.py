import io
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import boto3
import pandas as pd
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

VELIB_STATUS_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"


def fetch_and_transform() -> pd.DataFrame:
    response = requests.get(VELIB_STATUS_URL, timeout=10)
    response.raise_for_status()

    stations = response.json()["data"]["stations"]
    df = pd.DataFrame(stations)[
        ["stationCode", "num_bikes_available", "num_bikes_available_types", "num_docks_available", "is_returning"]
    ]

    if df["stationCode"].isna().all():
        raise ValueError("stationCode column is entirely null")

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

    now = datetime.now(tz=ZoneInfo("Europe/Paris")).replace(second=0, microsecond=0)
    df["updated_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
    return df, now


def handler(event, context):
    import os

    bucket = os.environ["S3_BUCKET"]

    df, now = fetch_and_transform()

    key = (
        f"station_status/raw/{now.year}/{now.month:02}/{now.day:02}/velib_data_{now.strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    )

    buf = io.StringIO()
    df.to_csv(buf, index=False)

    s3 = boto3.client("s3")
    s3.put_object(Bucket=bucket, Key=key, Body=buf.getvalue(), ContentType="text/csv")

    logger.info(f"Written {len(df)} rows to s3://{bucket}/{key}")
    return {"statusCode": 200, "key": key, "rows": len(df)}
