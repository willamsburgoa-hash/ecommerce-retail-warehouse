"""Dagster skeleton for the AWS projects (P1, P2).

Wire real assets: an ingestion asset that runs scripts/ingest.py, then a dbt asset built from
dagster-dbt, then a daily schedule over the job. Kept minimal so `dagster dev` starts clean.
"""
from __future__ import annotations

import subprocess

from dagster import (
    AssetExecutionContext,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
)


@asset
def raw_ingested(context: AssetExecutionContext) -> None:
    """Run the ingestion script."""
    context.log.info("running scripts/ingest.py")
    subprocess.run(["python", "scripts/ingest.py"], check=True)


@asset(deps=[raw_ingested])
def dbt_built(context: AssetExecutionContext) -> None:
    """Run `dbt build` (swap for dagster-dbt's dbt_assets for real lineage)."""
    subprocess.run(["dbt", "build", "--profiles-dir", "."], cwd="dbt", check=True)


pipeline_job = define_asset_job("pipeline_job", selection="*")

daily_schedule = ScheduleDefinition(
    job=pipeline_job,
    cron_schedule="0 6 * * *",  # 06:00 UTC daily
)

defs = Definitions(
    assets=[raw_ingested, dbt_built],
    jobs=[pipeline_job],
    schedules=[daily_schedule],
)
