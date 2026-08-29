-- One row per customer_id (order-scoped in Olist). customer_unique_id is the
-- stable person key used for retention / LTV. Source: bronze `customers`.

with source as (
    select * from {{ source('olist', 'customers') }}
)

select
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    trim(customer_city) as customer_city,
    customer_state
from source
