-- One row per order, typed. Source: bronze `orders` (every column lands as string).
-- Timestamps look like `2017-09-13 08:59:02`; nullif() guards the rare empty string.

with source as (
    select * from {{ source('olist', 'orders') }}
)

select
    order_id,
    customer_id,
    order_status,
    date_parse(nullif(order_purchase_timestamp, ''), '%Y-%m-%d %H:%i:%s')      as purchased_at,
    date_parse(nullif(order_approved_at, ''), '%Y-%m-%d %H:%i:%s')             as approved_at,
    date_parse(nullif(order_delivered_carrier_date, ''), '%Y-%m-%d %H:%i:%s')  as delivered_to_carrier_at,
    date_parse(nullif(order_delivered_customer_date, ''), '%Y-%m-%d %H:%i:%s') as delivered_to_customer_at,
    date_parse(nullif(order_estimated_delivery_date, ''), '%Y-%m-%d %H:%i:%s') as estimated_delivery_at
from source
