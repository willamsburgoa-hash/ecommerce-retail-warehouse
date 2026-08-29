-- One row per payment on an order (orders can split across methods).
-- Grain: order_id + payment_sequential. Source: bronze `order_payments`.

with source as (
    select * from {{ source('olist', 'order_payments') }}
)

select
    order_id || '-' || cast(payment_sequential as varchar) as payment_key,
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
from source
