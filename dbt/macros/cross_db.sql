{#
  Small cross-engine shims so the same models run on Athena (Trino SQL, prod)
  and DuckDB (CI, from the committed seed slice - no cloud creds).
#}

{% macro parse_ts(col) -%}
    {%- if target.type == 'athena' -%}
        date_parse(nullif({{ col }}, ''), '%Y-%m-%d %H:%i:%s')
    {%- else -%}
        try_cast(nullif(cast({{ col }} as varchar), '') as timestamp)
    {%- endif -%}
{%- endmacro %}


{% macro month_key(col) -%}
    {%- if target.type == 'athena' -%}
        date_format({{ col }}, '%Y-%m')
    {%- else -%}
        strftime({{ col }}, '%Y-%m')
    {%- endif -%}
{%- endmacro %}
