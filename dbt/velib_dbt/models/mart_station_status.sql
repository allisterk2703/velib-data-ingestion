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
            AND (
                extract(YEAR FROM updated_at),
                extract(MONTH FROM updated_at),
                extract(DAY FROM updated_at)
            ) >= (
                SELECT
                    t.year,
                    t.month,
                    t.day
                FROM {{ this }} AS t
                ORDER BY t.year DESC, t.month DESC, t.day DESC
                LIMIT 1
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
