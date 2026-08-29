-- Customer reviews. One row per review; review_id is NOT unique in the source
-- (some ids repeat and a few orders have more than one review).
-- Source: bronze `order_reviews`.

with source as (
    select * from {{ source('olist', 'order_reviews') }}
)

select
    review_id,
    order_id,
    review_score,
    nullif(trim(review_comment_title), '')                             as review_title,
    nullif(trim(review_comment_message), '')                           as review_message,
    date_parse(nullif(review_creation_date, ''), '%Y-%m-%d %H:%i:%s')  as review_created_at,
    date_parse(nullif(review_answer_timestamp, ''), '%Y-%m-%d %H:%i:%s') as review_answered_at
from source
