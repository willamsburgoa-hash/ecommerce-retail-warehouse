-- Scaffold example. Replace with real staging models that select from source('bronze', ...).
-- Kept so the template's `dbt build` and CI are green out of the box.
select
    id,
    lower(category) as category,
    cast(amount as double) as amount,
    status
from {{ ref('example_seed') }}
