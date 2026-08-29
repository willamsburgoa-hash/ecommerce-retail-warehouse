-- Grain: one row per (cohort_month, month_offset). A customer's cohort is the
-- month of their first order; month_offset counts whole months from that first
-- order to any later order. retention_rate = active_customers / cohort_customers.
-- Olist is almost entirely single-purchase, so offsets > 0 are very thin.

with person_orders as (
    select
        c.customer_unique_id,
        o.order_id,
        date_trunc('month', o.purchased_at) as order_month
    from {{ ref('fct_orders') }} as o
    join {{ ref('stg_customers') }} as c on c.customer_id = o.customer_id
    where o.purchased_at is not null
),

first_order as (
    select
        customer_unique_id,
        min(order_month) as cohort_month
    from person_orders
    group by customer_unique_id
),

cohort_size as (
    select
        cohort_month,
        count(distinct customer_unique_id) as cohort_customers
    from first_order
    group by cohort_month
),

orders_with_offset as (
    select
        f.cohort_month,
        po.customer_unique_id,
        date_diff('month', f.cohort_month, po.order_month) as month_offset
    from person_orders as po
    join first_order as f on f.customer_unique_id = po.customer_unique_id
)

select
    date_format(o.cohort_month, '%Y-%m') || '-m' || cast(o.month_offset as varchar) as cohort_key,
    cast(o.cohort_month as date)                                                    as cohort_month,
    o.month_offset,
    cs.cohort_customers,
    count(distinct o.customer_unique_id)                                            as active_customers,
    round(
        1.0 * count(distinct o.customer_unique_id) / cs.cohort_customers, 4
    )                                                                              as retention_rate
from orders_with_offset as o
join cohort_size as cs on cs.cohort_month = o.cohort_month
group by o.cohort_month, o.month_offset, cs.cohort_customers
