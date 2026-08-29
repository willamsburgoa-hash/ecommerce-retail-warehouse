-- Bronze layer: external tables over the Parquet written by scripts/ingest.py.
-- Deliberately near-raw: timestamp-like columns stay `string` (dbt staging casts
-- them in block B7+), and the product_* measures are `double` because the source
-- has null gaps. Partitioned by ingest_date (Hive-style path from ingest.py);
-- run `MSCK REPAIR TABLE` after create to register partitions.
-- __BUCKET__ is substituted by scripts/create_glue_tables.py from $S3_BUCKET.

CREATE EXTERNAL TABLE IF NOT EXISTS retail.orders (
  order_id string,
  customer_id string,
  order_status string,
  order_purchase_timestamp string,
  order_approved_at string,
  order_delivered_carrier_date string,
  order_delivered_customer_date string,
  order_estimated_delivery_date string
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/orders/'
TBLPROPERTIES ('classification' = 'parquet');

CREATE EXTERNAL TABLE IF NOT EXISTS retail.order_items (
  order_id string,
  order_item_id bigint,
  product_id string,
  seller_id string,
  shipping_limit_date string,
  price double,
  freight_value double
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/order_items/'
TBLPROPERTIES ('classification' = 'parquet');

CREATE EXTERNAL TABLE IF NOT EXISTS retail.order_payments (
  order_id string,
  payment_sequential bigint,
  payment_type string,
  payment_installments bigint,
  payment_value double
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/order_payments/'
TBLPROPERTIES ('classification' = 'parquet');

CREATE EXTERNAL TABLE IF NOT EXISTS retail.order_reviews (
  review_id string,
  order_id string,
  review_score bigint,
  review_comment_title string,
  review_comment_message string,
  review_creation_date string,
  review_answer_timestamp string
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/order_reviews/'
TBLPROPERTIES ('classification' = 'parquet');

CREATE EXTERNAL TABLE IF NOT EXISTS retail.customers (
  customer_id string,
  customer_unique_id string,
  customer_zip_code_prefix bigint,
  customer_city string,
  customer_state string
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/customers/'
TBLPROPERTIES ('classification' = 'parquet');

CREATE EXTERNAL TABLE IF NOT EXISTS retail.products (
  product_id string,
  product_category_name string,
  product_name_lenght double,
  product_description_lenght double,
  product_photos_qty double,
  product_weight_g double,
  product_length_cm double,
  product_height_cm double,
  product_width_cm double
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/products/'
TBLPROPERTIES ('classification' = 'parquet');

CREATE EXTERNAL TABLE IF NOT EXISTS retail.sellers (
  seller_id string,
  seller_zip_code_prefix bigint,
  seller_city string,
  seller_state string
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/sellers/'
TBLPROPERTIES ('classification' = 'parquet');

CREATE EXTERNAL TABLE IF NOT EXISTS retail.geolocation (
  geolocation_zip_code_prefix bigint,
  geolocation_lat double,
  geolocation_lng double,
  geolocation_city string,
  geolocation_state string
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/geolocation/'
TBLPROPERTIES ('classification' = 'parquet');

CREATE EXTERNAL TABLE IF NOT EXISTS retail.product_category_translation (
  product_category_name string,
  product_category_name_english string
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://__BUCKET__/bronze/product_category_translation/'
TBLPROPERTIES ('classification' = 'parquet');
