-- Lat/lng by zip-code prefix. The source has many points per prefix
-- (~1M rows / ~19k prefixes); collapse to one deterministic row per prefix so
-- it can be joined as a dimension from stg_customers / stg_sellers.
-- Grain: geolocation_zip_code_prefix. Source: bronze `geolocation`.

with source as (
    select * from {{ source('olist', 'geolocation') }}
),

dedup as (
    select
        geolocation_zip_code_prefix,
        geolocation_lat,
        geolocation_lng,
        trim(geolocation_city) as geolocation_city,
        geolocation_state,
        row_number() over (
            partition by geolocation_zip_code_prefix
            order by geolocation_lat, geolocation_lng
        ) as rn
    from source
)

select
    geolocation_zip_code_prefix,
    geolocation_lat,
    geolocation_lng,
    geolocation_city,
    geolocation_state
from dedup
where rn = 1
