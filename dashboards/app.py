"""Minimal Streamlit dashboard skeleton.

Point it at the gold marts (Athena via `awswrangler`, Databricks via `databricks-sql-connector`,
or a local DuckDB file in CI). Replace the demo query with real KPIs.
"""
import os

import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Portfolio project", layout="wide")
st.title("<project-name> — KPIs")


@st.cache_data(ttl=300)
def load_marts() -> pd.DataFrame:
    db = os.getenv("DUCKDB_PATH", "dbt/ci.duckdb")
    if os.path.exists(db):
        con = duckdb.connect(db, read_only=True)
        return con.execute("select * from marts.mart_example").df()
    return pd.DataFrame({"category": ["books", "electronics"], "revenue": [21.5, 249.89]})


df = load_marts()

c1, c2, c3 = st.columns(3)
c1.metric("Categories", len(df))
c2.metric("Total revenue", f"{df['revenue'].sum():,.2f}")
c3.metric("Top category", df.loc[df["revenue"].idxmax(), "category"])

st.bar_chart(df.set_index("category")["revenue"])
st.dataframe(df, use_container_width=True)
