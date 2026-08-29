"""Register the bronze Parquet layer as Glue / Athena external tables.

Runs every statement in ``sql/ddl_bronze.sql`` through Athena, then
``MSCK REPAIR TABLE`` to discover the ``ingest_date`` partitions, then a
``COUNT(*)`` smoke test per table.

    python scripts/create_glue_tables.py
    python scripts/create_glue_tables.py --recreate   # DROP then CREATE
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import awswrangler as wr
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DDL_FILE = ROOT / "sql" / "ddl_bronze.sql"

TABLES = [
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "customers",
    "products",
    "sellers",
    "geolocation",
    "product_category_translation",
]


def _env() -> tuple[str, str, str]:
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        sys.exit("S3_BUCKET not set — fill .env from `terraform output` (block B2).")
    database = os.environ.get("GLUE_DATABASE", "retail")
    workgroup = os.environ.get("ATHENA_WORKGROUP", "de-portfolio")
    return bucket, database, workgroup


def _sql(statement: str, database: str, workgroup: str) -> None:
    wr.athena.start_query_execution(
        sql=statement, database=database, workgroup=workgroup, wait=True
    )


def _statements(bucket: str) -> list[str]:
    raw = DDL_FILE.read_text(encoding="utf-8").replace("__BUCKET__", bucket)
    body = "\n".join(ln for ln in raw.splitlines() if not ln.lstrip().startswith("--"))
    return [s.strip() for s in body.split(";") if s.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="Create the bronze Glue tables.")
    ap.add_argument("--recreate", action="store_true", help="DROP each table first")
    args = ap.parse_args()

    bucket, database, workgroup = _env()
    statements = _statements(bucket)
    print(f"{len(statements)} DDL statements -> {database} (workgroup {workgroup})")

    if args.recreate:
        for table in TABLES:
            _sql(f"DROP TABLE IF EXISTS {database}.{table}", database, workgroup)
        print(f"dropped {len(TABLES)} tables")

    for i, statement in enumerate(statements, start=1):
        try:
            _sql(statement, database, workgroup)
        except Exception as exc:  # surface which statement broke, then stop
            sys.exit(f"DDL #{i} failed: {exc}\n---\n{statement}\n---")
    print(f"created {len(statements)} tables")

    print("repairing partitions + row counts:")
    for table in TABLES:
        _sql(f"MSCK REPAIR TABLE {database}.{table}", database, workgroup)
        df = wr.athena.read_sql_query(
            f"SELECT count(*) AS n FROM {database}.{table}",
            database=database,
            workgroup=workgroup,
            ctas_approach=False,
        )
        print(f"  {table:<30} {int(df['n'].iloc[0]):>10,} rows")

    print("done.")


if __name__ == "__main__":
    main()
