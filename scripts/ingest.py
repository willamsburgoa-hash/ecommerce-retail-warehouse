"""Ingestion skeleton: fetch a source, land it in S3 raw/, convert to bronze/ parquet.

Replace `fetch_source()` per project (CSV download, paginated REST API, SPARQL, GDELT files).
The retry + logging + S3 layout are meant to be reused as-is.
"""
from __future__ import annotations

import io
import logging
import os
from datetime import date

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger("ingest")

RUN_DATE = date.today().isoformat()


def _bucket() -> str:
    return os.environ["S3_BUCKET"]


def _s3():
    return boto3.client("s3")


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30))
def fetch_source() -> pd.DataFrame:
    """TODO: implement per project. Must return a tidy DataFrame."""
    raise NotImplementedError("Implement fetch_source() for this project")


def put_raw(body: bytes, key: str) -> None:
    bucket = _bucket()
    _s3().put_object(Bucket=bucket, Key=f"raw/{key}", Body=body)
    log.info("wrote s3://%s/raw/%s (%d bytes)", bucket, key, len(body))


def put_bronze(df: pd.DataFrame, name: str) -> None:
    bucket = _bucket()
    table = pa.Table.from_pandas(df, preserve_index=False)
    buf = io.BytesIO()
    pq.write_table(table, buf, compression="snappy")
    key = f"bronze/{name}/ingest_date={RUN_DATE}/{name}.parquet"
    _s3().put_object(Bucket=bucket, Key=key, Body=buf.getvalue())
    log.info("wrote s3://%s/%s (%d rows)", bucket, key, len(df))


def main() -> None:
    log.info("ingest start | bucket=%s | run_date=%s", _bucket(), RUN_DATE)
    df = fetch_source()
    put_raw(df.to_csv(index=False).encode(), f"source/{RUN_DATE}.csv")
    put_bronze(df, "source")
    log.info("ingest done")


if __name__ == "__main__":
    main()
