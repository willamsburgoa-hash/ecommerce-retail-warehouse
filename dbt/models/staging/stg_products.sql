-- Product catalog. Grain: product_id. Source: bronze `products`.
-- ~610 rows have no category and no dimensions (kept as NULL).
-- Fixes the source's misspelled `lenght` columns.

with source as (
    select * from {{ source('olist', 'products') }}
)

select
    product_id,
    product_category_name,
    product_name_lenght        as product_name_length,
    product_description_lenght as product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
from source
