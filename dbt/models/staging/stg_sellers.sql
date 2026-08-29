-- Seller catalog. Grain: seller_id. Source: bronze `sellers`.

with source as (
    select * from {{ source('olist', 'sellers') }}
)

select
    seller_id,
    seller_zip_code_prefix,
    trim(seller_city) as seller_city,
    seller_state
from source
