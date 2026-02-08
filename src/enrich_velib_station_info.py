# src/enrich_velib_station_info.py

import logging
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def download_file(url, output_file):
    os.makedirs(output_file.parent, exist_ok=True)
    try:
        logging.info(f"Downloading {output_file.name} from {url}")
        response = requests.get(url)
        response.raise_for_status()

        with open(output_file, "wb") as f:
            f.write(response.content)

        logging.info(f"File downloaded and saved under '{output_file}' successfully.")

    except requests.RequestException as e:
        logging.error(f"An error occurred during the download: {e}")


def download_geojson_data(OTHERS_DIR):
    if "communes-ile-de-france.geojson" and "paris_arrondissements.geojson" not in os.listdir(OTHERS_DIR):
        logging.info(f"Geodata not found in {OTHERS_DIR}, downloading...")
        # Communes de l'Ile de France
        url = "https://www.data.gouv.fr/fr/datasets/r/723193a8-ac82-4da3-a261-2265e0f4969f"
        output_file = Path(OTHERS_DIR) / "communes-ile-de-france.geojson"
        download_file(url, output_file)

        # Arrondissements de Paris
        url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson?lang=fr&timezone=Europe%2FBerlin"
        output_file = Path(OTHERS_DIR) / "paris_arrondissements.geojson"
        download_file(url, output_file)
    else:
        logging.info(f"Geodata found in {OTHERS_DIR}")


def enrich_station_info_data(df_station_info_path, DATA_DIR, OTHERS_DIR):
    download_geojson_data(OTHERS_DIR)

    shapefile_communes = gpd.read_file(Path(OTHERS_DIR) / "communes-ile-de-france.geojson")
    geodf_communes = gpd.GeoDataFrame(shapefile_communes, geometry=shapefile_communes["geometry"])
    geodf_communes = geodf_communes[["com_name_upper", "geometry"]]
    geodf_communes = geodf_communes.rename({"com_name_upper": "commune"}, axis=1)
    # print(geodf_communes.head())

    # DATA_DIR / "station_info" / "velib_station_info.csv"
    df = pd.read_csv(df_station_info_path)
    # print(df.head())

    gdf_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
    # print(gdf_points.head())
    # S'assurer que les deux GeoDataFrames ont le même CRS
    # ou CRS de geodf_communes si différent
    gdf_points = gdf_points.set_crs("EPSG:4326")
    geodf_communes = geodf_communes.set_crs("EPSG:4326")

    # Spatial join : chaque point récupère la commune dans laquelle il tombe
    gdf_points_with_commune = gpd.sjoin(
        gdf_points,
        geodf_communes[["commune", "geometry"]],
        how="left",
        predicate="within",
    )

    # Résultat : une nouvelle colonne 'commune' est ajoutée
    # gdf_points_with_commune
    shapefile_arrondissements = gpd.read_file(Path(OTHERS_DIR) / "paris_arrondissements.geojson")
    # shapefile_arrondissements.shape)
    shapefile_arrondissements = shapefile_arrondissements[["c_ar", "geometry"]]
    shapefile_arrondissements = shapefile_arrondissements.rename({"c_ar": "arrondissement"}, axis=1)
    # shapefile_arrondissements
    gdf_points_with_commune = gdf_points_with_commune.set_crs("EPSG:4326")
    shapefile_arrondissements = shapefile_arrondissements.set_crs("EPSG:4326")
    # Supprimer l'ancienne colonne index_right pour éviter le conflit
    gdf_points_with_commune = gdf_points_with_commune.drop(columns=["index_right"])

    # Spatial join pour récupérer l'arrondissement
    gdf_points_with_commune_arrondissements = gpd.sjoin(
        gdf_points_with_commune,
        shapefile_arrondissements[["arrondissement", "geometry"]],
        how="left",
        predicate="within",
    )

    gdf_points_with_commune_arrondissements = gdf_points_with_commune_arrondissements.drop(columns=["index_right"])
    gdf_points_with_commune_arrondissements["arrondissement"] = gdf_points_with_commune_arrondissements[
        "arrondissement"
    ].astype(str)
    gdf_points_with_commune_arrondissements["arrondissement"] = gdf_points_with_commune_arrondissements[
        "arrondissement"
    ].str.replace(".0", "")
    # gdf_points_with_commune_arrondissements.head()

    def get_commune_arrondissement(row):
        if row["commune"] == "PARIS":
            return row["commune"] + " - " + row["arrondissement"]
        else:
            return row["commune"]

    gdf_points_with_commune_arrondissements["commune_arrondissement"] = gdf_points_with_commune_arrondissements.apply(
        get_commune_arrondissement, axis=1
    )
    gdf_points_with_commune_arrondissements["commune_arrondissement"] = gdf_points_with_commune_arrondissements[
        "commune_arrondissement"
    ].replace("PARIS - nan", "PARIS - 12")
    gdf_points_with_commune_arrondissements = gdf_points_with_commune_arrondissements.drop(columns=["geometry"])

    gdf_points_with_commune_arrondissements.sort_values(by="stationCode", inplace=True)
    gdf_points_with_commune_arrondissements.to_csv(
        Path(DATA_DIR) / "station_info" / "velib_station_info_enriched.csv", index=False
    )

    return gdf_points_with_commune_arrondissements


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    OTHERS_DIR = DATA_DIR / "others"
    OTHERS_DIR.mkdir(parents=True, exist_ok=True)
    df_station_info_path = DATA_DIR / "station_info" / "velib_station_info.csv"
    enrich_station_info_data(df_station_info_path, DATA_DIR, OTHERS_DIR)
