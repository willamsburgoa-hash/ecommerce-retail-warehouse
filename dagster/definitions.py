"""Dagster pipeline for P1: ingest -> Glue tables -> dbt build, on a daily schedule.

Each asset shells out to the same script you would run by hand, so there is a
single source of truth. Env vars come from the process environment: docker-compose
passes `.env`; `dagster dev` inherits your shell (use `dotenv run -- dagster dev`).
"""

import subprocess
import sys
from pathlib import Path

from dagster import (
    AssetExecutionContext,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
)

ROOT = Path(__file__).resolve().parents[1]


def _run(context: AssetExecutionContext, *cmd: str, cwd: Path | None = None) -> None:
    context.log.info("running: %s (cwd=%s)", " ".join(cmd), cwd or ROOT)
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


@asset
def raw_ingested(context: AssetExecutionContext) -> None:
    """Olist source -> S3 raw/ CSV + bronze/ Parquet (partitioned by ingest_date)."""
    _run(context, sys.executable, "scripts/ingest.py")


@asset(deps=[raw_ingested])
def glue_tables(context: AssetExecutionContext) -> None:
    """Create / repair the bronze external tables in the Glue Data Catalog."""
    _run(context, sys.executable, "scripts/create_glue_tables.py")


@asset(deps=[glue_tables])
def dbt_build(context: AssetExecutionContext) -> None:
    """dbt build: staging + marts, plus every data test."""
    _run(context, "dbt", "build", "--profiles-dir", ".", cwd=ROOT / "dbt")


retail_pipeline = define_asset_job("retail_pipeline", selection="*")

daily_schedule = ScheduleDefinition(
    job=retail_pipeline,
    cron_schedule="0 6 * * *",  # 06:00 UTC daily
    execution_timezone="UTC",
)

defs = Definitions(
    assets=[raw_ingested, glue_tables, dbt_build],
    jobs=[retail_pipeline],
    schedules=[daily_schedule],
)
