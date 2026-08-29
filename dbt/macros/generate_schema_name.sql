{#
  Keep every layer (bronze sources, stg_* views, marts tables) in the single
  Glue database `retail` (= target schema), distinguished by table-name prefix.
  This avoids dbt-athena auto-creating `retail_staging` / `retail_marts`, which
  Terraform does not manage and `terraform destroy` would leave orphaned.
  The `+schema:` keys in dbt_project.yml are therefore inert.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ target.schema | trim }}
{%- endmacro %}
