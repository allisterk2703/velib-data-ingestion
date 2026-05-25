{{ config(materialized='table') }}

SELECT
    stationcode,
    AVG(num_bikes_available) AS avg_bikes_available,
    AVG(num_docks_available) AS avg_docks_available,
    AVG(num_ebike_bikes_available) AS avg_ebikes_available,
    COUNT(*) AS nb_snapshots
FROM {{ source('velib_data_ingestion', 'station_status_raw') }}
WHERE is_working = 1
GROUP BY stationcode
ORDER BY avg_bikes_available DESC
