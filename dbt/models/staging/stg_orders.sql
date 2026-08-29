-- One row per order, typed. Source: bronze `orders` (every column lands as string).
-- Timestamps look like `2017-09-13 08:59:02`; nullif() guards the rare empty string.

with source as (
    select * from {{ source('olist', 'orders') }}
)

select
    order_id,
    customer_id,
    order_status,
    {{ parse_ts('order_purchase_timestamp') }}      as purchased_at,
    {{ parse_ts('order_approved_at') }}             as approved_at,
    {{ parse_ts('order_delivered_carrier_date') }}  as delivered_to_carrier_at,
    {{ parse_ts('order_delivered_customer_date') }} as delivered_to_customer_at,
    {{ parse_ts('order_estimated_delivery_date') }} as estimated_delivery_at
from source
