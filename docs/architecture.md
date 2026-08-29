# Architecture

## Overview

One paragraph: the business question, the shape of the data, why this design.

## Diagram

```mermaid
flowchart LR
    subgraph Sources
      A[Public dataset / REST API / GDELT files]
    end
    subgraph Ingest
      B[ingest.py in Docker]
    end
    subgraph Lake
      C[(S3 raw)]
      D[(bronze / Delta bronze)]
    end
    subgraph Transform
      E[Athena / Spark]
      F[dbt: staging -> marts]
    end
    subgraph Serve
      G[Streamlit / Databricks SQL dashboard]
    end
    O[Dagster / Lakeflow Job]

    A --> B --> C --> D --> E --> F --> G
    O -.schedule.-> B
    O -.schedule.-> F
```

## Data model

- **bronze**: raw, typed-as-string, partitioned by `ingest_date`.
- **silver / staging**: typed, deduped, cleaned; one model per source entity.
- **gold / marts**: business entities — `fct_*`, `dim_*`, `mart_*`.

## Design decisions

| Decision | Why | Trade-off |
|---|---|---|
| Athena over a warehouse | free-tier friendly, no cluster to run | slower, no constraints |
| dbt for transforms | tests + docs + lineage for free | another tool to learn |
| Small data slice | Databricks Free Edition quota | not a scale demo |

## Cost

How the design stays at ~$0 and how it's verified (Budget alarm, `terraform destroy`, data size).
