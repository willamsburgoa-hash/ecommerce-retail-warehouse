"""Ingest the Olist e-commerce dataset into the S3 data lake.

Layout written per table:
    raw/olist/<table>/<table>.csv                              -- source CSV, as-is
    bronze/<table>/ingest_date=<YYYY-MM-DD>/<table>.parquet     -- snappy Parquet

Source resolution (``--source``, default ``auto``):
    auto    the full dataset if ``data/olist/`` is populated or KAGGLE_USERNAME /
            KAGGLE_KEY are set (downloaded on first run), otherwise the slice
    sample  always the committed slice in ``data/olist_sample/``
    full    always the full Kaggle dataset (downloaded into ``data/olist/`` if missing)

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --source sample
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("ingest")

RUN_DATE = date.today().isoformat()

ROOT = Path(__file__).resolve().parents[1]
FULL_DIR = ROOT / "data" / "olist"
SAMPLE_DIR = ROOT / "data" / "olist_sample"

KAGGLE_DATASET = "olistbr/brazilian-ecommerce"

# Kaggle file name -> clean table name. Must match scripts/make_sample.py (FILES).
KAGGLE_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "product_category_translation": "product_category_name_translation.csv",
}


def _bucket() -> str:
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        sys.exit("S3_BUCKET is not set. Copy .env.example to .env and fill it in (block B2).")
    return bucket


def _s3():
    return boto3.client("s3")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def _download_full() -> None:
    """Download + unzip the full Kaggle dataset into data/olist/."""
    FULL_DIR.mkdir(parents=True, exist_ok=True)
    log.info("downloading %s -> %s", KAGGLE_DATASET, FULL_DIR)
    subprocess.run(
        [
            sys.executable, "-m", "kaggle", "datasets", "download",
            "-d", KAGGLE_DATASET, "-p", str(FULL_DIR), "--unzip",
        ],
        check=True,
    )


def _resolve_tables(source: str) -> dict[str, Path]:
    """Return ``{table_name: csv_path}`` for the chosen source."""
    have_full = all((FULL_DIR / f).exists() for f in KAGGLE_FILES.values())
    creds = bool(os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"))
    use_full = source == "full" or (source == "auto" and (have_full or creds))

    if use_full and not have_full:
        try:
            _download_full()
            have_full = True
        except (subprocess.CalledProcessError, FileNotFoundError, ImportError) as exc:
            if source == "full":
                sys.exit(f"Kaggle download failed: {exc}")
            log.warning("Kaggle download failed (%s); using the local slice instead", exc)
            use_full = False

    if use_full:
        return {table: FULL_DIR / fname for table, fname in KAGGLE_FILES.items()}

    csvs = sorted(SAMPLE_DIR.glob("*.csv"))
    if not csvs:
        sys.exit(
            f"No CSVs in {SAMPLE_DIR}. Run `python scripts/make_sample.py` (block B3), "
            "or use --source full with KAGGLE_USERNAME / KAGGLE_KEY set."
        )
    return {path.stem: path for path in csvs}


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30))
def _put(key: str, body: bytes) -> None:
    _s3().put_object(Bucket=_bucket(), Key=key, Body=body)


def _arrow_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Object columns mixing str and NaN break pyarrow; turn NaN into None."""
    obj_cols = df.select_dtypes(include=["object", "string"]).columns
    if len(obj_cols):
        df = df.copy()
        df[obj_cols] = df[obj_cols].where(df[obj_cols].notna(), None)
    return df


def put_raw(table: str, csv_bytes: bytes) -> str:
    key = f"raw/olist/{table}/{table}.csv"
    _put(key, csv_bytes)
    log.info("wrote s3://%s/%s (%d bytes)", _bucket(), key, len(csv_bytes))
    return key


def put_bronze(table: str, df: pd.DataFrame) -> str:
    buf = io.BytesIO()
    _arrow_safe(df).to_parquet(buf, engine="pyarrow", compression="snappy", index=False)
    key = f"bronze/{table}/ingest_date={RUN_DATE}/{table}.parquet"
    _put(key, buf.getvalue())
    log.info("wrote s3://%s/%s (%d rows)", _bucket(), key, len(df))
    return key


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest Olist into S3 raw/ + bronze/.")
    ap.add_argument("--source", choices=["auto", "sample", "full"], default="auto")
    args = ap.parse_args()

    bucket = _bucket()
    tables = _resolve_tables(args.source)
    log.info(
        "ingest start | bucket=%s | run_date=%s | tables=%d", bucket, RUN_DATE, len(tables)
    )

    summary: list[tuple[str, int, str, str]] = []
    try:
        for table, path in tables.items():
            df = pd.read_csv(path)
            raw_key = put_raw(table, path.read_bytes())
            bronze_key = put_bronze(table, df)
            summary.append((table, len(df), raw_key, bronze_key))
    except (NoCredentialsError, ClientError, BotoCoreError) as exc:
        sys.exit(
            f"S3 upload failed ({type(exc).__name__}): {exc}\n"
            "Check AWS credentials (`aws configure`) and S3_BUCKET in .env."
        )

    log.info("ingest done | tables=%d", len(summary))
    print(f"\n{'table':<28} {'rows':>8}  s3 keys")
    for table, rows, raw_key, bronze_key in summary:
        print(f"{table:<28} {rows:>8,}  {raw_key}")
        print(f"{'':<28} {'':>8}  {bronze_key}")


if __name__ == "__main__":
    main()
