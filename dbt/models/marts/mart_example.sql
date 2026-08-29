-- Scaffold mart. Replace with real fct_/dim_/mart_ models.
select
    category,
    count(*)          as orders,
    sum(amount)       as revenue,
    avg(amount)       as avg_order_value
from {{ ref('stg_example') }}
where status <> 'canceled'
group by 1
