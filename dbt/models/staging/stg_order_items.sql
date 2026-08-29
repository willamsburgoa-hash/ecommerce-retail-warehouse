-- One row per item within an order. Grain: order_id + order_item_id.
-- Source: bronze `order_items` (keys land as string, measures already double).

with source as (
    select * from {{ source('olist', 'order_items') }}
)

select
    order_id || '-' || cast(order_item_id as varchar)               as order_item_key,
    order_id,
    order_item_id,
    product_id,
    seller_id,
    date_parse(nullif(shipping_limit_date, ''), '%Y-%m-%d %H:%i:%s') as shipping_limit_at,
    price,
    freight_value
from source
