-- Grain: one row per customer_unique_id (the stable person key; Olist issues a
-- fresh customer_id per order). Geography is taken from the person's most recent
-- order. lifetime_value = gross order_total across all of the person's orders.

with customers as (
    select * from {{ ref('stg_customers') }}
),

person_orders as (
    select
        c.customer_unique_id,
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,
        o.order_id,
        o.is_delivered,
        o.purchased_at,
        o.order_total
    from {{ ref('fct_orders') }} as o
    join customers as c on c.customer_id = o.customer_id
),

latest_geo as (
    select
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        row_number() over (
            partition by customer_unique_id
            order by purchased_at desc, order_id
        ) as rn
    from person_orders
)

select
    po.customer_unique_id,
    g.customer_zip_code_prefix,
    g.customer_city,
    g.customer_state,

    count(distinct po.order_id)                                        as order_count,
    count(distinct po.order_id) filter (where po.is_delivered)         as delivered_order_count,
    count(distinct po.order_id) > 1                                    as is_repeat_customer,

    min(po.purchased_at)                                               as first_order_at,
    max(po.purchased_at)                                               as last_order_at,
    date_diff('day', min(po.purchased_at), max(po.purchased_at))       as customer_tenure_days,

    round(sum(po.order_total), 2)                                      as lifetime_value,
    round(sum(po.order_total) / count(distinct po.order_id), 2)        as avg_order_value
from person_orders as po
join latest_geo as g
    on g.customer_unique_id = po.customer_unique_id and g.rn = 1
group by
    po.customer_unique_id,
    g.customer_zip_code_prefix,
    g.customer_city,
    g.customer_state
