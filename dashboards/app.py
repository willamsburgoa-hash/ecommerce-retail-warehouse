"""P1 dashboard - Brazilian e-commerce retail warehouse KPIs.

Reads the gold marts from AWS Athena (awswrangler) by default. Set
DASHBOARD_ENGINE=duckdb (or run with no AWS creds) to read a local
dbt/ci.duckdb built by the CI sample instead.

    streamlit run dashboards/app.py
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

SCHEMA = os.getenv("DBT_SCHEMA", "retail")
WORKGROUP = os.getenv("ATHENA_WORKGROUP", "de-portfolio")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "dbt/ci.duckdb")


def _use_duckdb() -> bool:
    engine = os.getenv("DASHBOARD_ENGINE", "").lower()
    if engine:
        return engine == "duckdb"
    has_aws = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE")
    return not has_aws and os.path.exists(DUCKDB_PATH)


@st.cache_data(ttl=300)
def q(sql: str) -> pd.DataFrame:
    sql = sql.format(schema=SCHEMA)
    if _use_duckdb():
        import duckdb

        return duckdb.connect(DUCKDB_PATH, read_only=True).execute(sql).df()
    import awswrangler as wr

    return wr.athena.read_sql_query(
        sql, database=SCHEMA, workgroup=WORKGROUP, ctas_approach=False
    )


st.set_page_config(page_title="Retail warehouse - KPIs", layout="wide")
st.title("Brazilian e-commerce - retail warehouse KPIs")
st.caption(
    f"Source: {'DuckDB (CI sample)' if _use_duckdb() else 'AWS Athena'} - schema `{SCHEMA}`"
)

head = q(
    """
    select count(*) as orders,
           round(sum(order_total), 2) as gmv,
           round(avg(order_total), 2) as avg_order_value
    from {schema}.fct_orders
    """
).iloc[0]
repeat = q(
    """
    select round(100.0 * avg(case when is_repeat_customer then 1 else 0 end), 2) as repeat_pct,
           round(avg(lifetime_value), 2) as avg_ltv
    from {schema}.dim_customers
    """
).iloc[0]
delivery = q(
    """
    select round(avg(delivery_delay_days), 2) as avg_delay_days,
           round(100.0 * avg(case when is_on_time then 1 else 0 end), 1) as on_time_pct
    from {schema}.fct_delivery_performance
    """
).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Orders", f"{int(head['orders']):,}")
c2.metric(
    "GMV (BRL)",
    f"{head['gmv']:,.0f}",
    help=f"Avg order value {head['avg_order_value']:,.2f}",
)
c3.metric(
    "Repeat customers",
    f"{repeat['repeat_pct']:.1f}%",
    help=f"Avg LTV {repeat['avg_ltv']:,.0f}",
)
c4.metric(
    "On-time delivery",
    f"{delivery['on_time_pct']:.1f}%",
    delta=f"{delivery['avg_delay_days']:+.1f} d vs promised",
    delta_color="off",
)

st.subheader("Revenue by product category (top 15)")
cat = q(
    """
    select coalesce(t.product_category_name_english,
                    p.product_category_name, 'unknown') as category,
           round(sum(i.price), 2) as revenue
    from {schema}.stg_order_items i
    join {schema}.stg_products p on p.product_id = i.product_id
    left join {schema}.stg_product_category_translation t
           on t.product_category_name = p.product_category_name
    group by 1
    order by revenue desc
    limit 15
    """
)
st.bar_chart(cat.set_index("category")["revenue"], horizontal=True)

st.subheader("Mean delivery delay by customer state (negative = early)")
state = q(
    """
    select customer_state,
           round(avg(delivery_delay_days), 1) as avg_delay_days
    from {schema}.fct_delivery_performance
    group by 1
    order by avg_delay_days desc
    """
)
st.bar_chart(state.set_index("customer_state")["avg_delay_days"])

st.subheader("Monthly retention cohorts - repurchase rate by month offset")
coh = q(
    """
    select cohort_month, month_offset, retention_rate
    from {schema}.mart_retention_cohorts
    where month_offset between 1 and 12
    """
)
coh["month_offset"] = coh["month_offset"].astype("int64")
coh["cohort_month"] = pd.to_datetime(coh["cohort_month"]).dt.strftime("%Y-%m")
pivot = coh.pivot(
    index="cohort_month", columns="month_offset", values="retention_rate"
).sort_index()

_vmax = float(pivot.max().max())
if pd.isna(_vmax) or _vmax == 0:
    _vmax = 1.0


def _heat(v: float) -> str:
    if pd.isna(v):
        return ""
    a = min(v / _vmax, 1.0) * 0.75
    return f"background-color: rgba(33, 102, 172, {a:.3f})"


st.dataframe(
    pivot.style.format("{:.2%}", na_rep="").map(_heat),
    use_container_width=True,
)
st.caption("Olist is almost entirely single-purchase - repurchase stays well under 1%.")
