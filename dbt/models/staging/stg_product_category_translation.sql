-- Portuguese -> English category names. Grain: product_category_name.
-- Source: bronze `product_category_translation`. Note: 2 categories used by
-- products (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos) are absent
-- here -- surfaced as a warn-level relationships test on stg_products.

with source as (
    select * from {{ source('olist', 'product_category_translation') }}
)

select
    product_category_name,
    product_category_name_english
from source
