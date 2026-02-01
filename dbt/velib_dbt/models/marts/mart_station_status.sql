{{ config(
    materialized='incremental',
    incremental_strategy='append',
    file_format='parquet',
    partitioned_by=['year', 'month', 'day']
) }}

WITH raw AS (

    SELECT
        stationcode,
        num_bikes_available,
        num_docks_available,
        is_working,
        num_mechanical_bikes_available,
        num_ebike_bikes_available,
        updated_at,

        extract(HOUR FROM updated_at) AS "hour",
        extract(MINUTE FROM updated_at) AS "minute",

        extract(YEAR FROM updated_at) AS "year",
        extract(MONTH FROM updated_at) AS "month",
        extract(DAY FROM updated_at) AS "day"

    FROM {{ source('velib', 'station_status_raw') }}

    WHERE
        extract(MINUTE FROM updated_at) IN (0, 15, 30, 45)

    {% if is_incremental() %}
      and (
            extract(year from updated_at),
            extract(month from updated_at),
            extract(day from updated_at)
          ) >= (
            select year, month, day
            from {{ this }}
            order by year desc, month desc, day desc
            limit 1
          )
    {% endif %}

)

SELECT
    stationcode,
    num_bikes_available,
    num_docks_available,
    is_working,
    num_mechanical_bikes_available,
    num_ebike_bikes_available,
    updated_at,
    "hour",
    "minute",
    "year",
    "month",
    "day"
FROM raw
