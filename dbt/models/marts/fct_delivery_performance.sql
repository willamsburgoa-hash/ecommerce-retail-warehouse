-- Grain: one row per delivered order (needs both an actual and an estimated
-- delivery date). Positive delay = late. primary_category / primary_seller_state
-- are the category / seller state of the highest-value line in the order.

with orders as (
    select
        order_id,
        customer_id,
        purchased_at,
        estimated_delivery_at,
        delivered_to_customer_at,
        estimated_days,
        delivered_days
    from {{ ref('fct_orders') }}
    where is_delivered
      and delivered_to_customer_at is not null
      and estimated_delivery_at is not null
),

customer_geo as (
    select customer_id, customer_state
    from {{ ref('stg_customers') }}
),

order_category as (
    select order_id, product_category_name as primary_category
    from (
        select
            i.order_id,
            p.product_category_name,
            row_number() over (
                partition by i.order_id
                order by sum(i.price) desc, p.product_category_name
            ) as rn
        from {{ ref('stg_order_items') }} as i
        join {{ ref('stg_products') }} as p on p.product_id = i.product_id
        group by i.order_id, p.product_category_name
    )
    where rn = 1
),

order_seller_state as (
    select order_id, seller_state as primary_seller_state
    from (
        select
            i.order_id,
            s.seller_state,
            row_number() over (
                partition by i.order_id
                order by sum(i.price) desc, s.seller_state
            ) as rn
        from {{ ref('stg_order_items') }} as i
        join {{ ref('stg_sellers') }} as s on s.seller_id = i.seller_id
        group by i.order_id, s.seller_state
    )
    where rn = 1
)

select
    o.order_id,
    o.customer_id,
    cg.customer_state,
    oc.primary_category,
    oss.primary_seller_state,

    o.purchased_at,
    o.estimated_delivery_at,
    o.delivered_to_customer_at,

    o.delivered_days                                                          as actual_days,
    o.estimated_days,
    date_diff('day', o.estimated_delivery_at, o.delivered_to_customer_at)     as delivery_delay_days,
    date_diff('day', o.estimated_delivery_at, o.delivered_to_customer_at) <= 0 as is_on_time,
    date_diff('day', o.estimated_delivery_at, o.delivered_to_customer_at) > 0  as is_late
from orders as o
left join customer_geo as cg on cg.customer_id = o.customer_id
left join order_category as oc on oc.order_id = o.order_id
left join order_seller_state as oss on oss.order_id = o.order_id
