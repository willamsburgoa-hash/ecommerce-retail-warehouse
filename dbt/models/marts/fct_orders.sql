-- Grain: one row per order. Order economics (items, freight, payments) plus
-- delivery timing. Built from the staging layer.

with orders as (
    select * from {{ ref('stg_orders') }}
),

items as (
    select
        order_id,
        count(*)          as item_count,
        sum(price)         as items_total,
        sum(freight_value) as freight_total
    from {{ ref('stg_order_items') }}
    group by order_id
),

payments as (
    select
        order_id,
        sum(payment_value) as payment_total
    from {{ ref('stg_order_payments') }}
    group by order_id
)

select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_status = 'delivered'                                   as is_delivered,

    o.purchased_at,
    o.approved_at,
    o.delivered_to_carrier_at,
    o.delivered_to_customer_at,
    o.estimated_delivery_at,

    coalesce(i.item_count, 0)                                      as item_count,
    coalesce(i.items_total, 0.0)                                   as items_total,
    coalesce(i.freight_total, 0.0)                                 as freight_total,
    coalesce(i.items_total, 0.0) + coalesce(i.freight_total, 0.0)  as order_total,
    coalesce(p.payment_total, 0.0)                                 as payment_total,

    date_diff('day', o.purchased_at, o.delivered_to_customer_at)   as delivered_days,
    date_diff('day', o.purchased_at, o.estimated_delivery_at)      as estimated_days
from orders as o
left join items as i on i.order_id = o.order_id
left join payments as p on p.order_id = o.order_id
