"""Build a small, referentially-consistent slice of the Olist dataset.

Reads the full Kaggle dump from ``data/olist/`` and writes a few-thousand-row
sample to ``data/olist_sample/``. That slice is committed to the repo so CI and
``docker compose up`` can run the whole pipeline with no credentials.

Usage
-----
    python scripts/make_sample.py                 # 2500 orders, seed 42
    python scripts/make_sample.py --n-orders 1500 --seed 7

Get the full dataset first (one of):
    # Kaggle CLI  (needs ~/.kaggle/kaggle.json or KAGGLE_USERNAME / KAGGLE_KEY)
    uv pip install kaggle
    kaggle datasets download -d olistbr/brazilian-ecommerce -p data/olist --unzip

    # or download the zip from
    #   https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
    # and unzip it into data/olist/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "olist"
OUT_DIR = ROOT / "data" / "olist_sample"

# Kaggle file name -> clean table name used everywhere downstream (S3, Glue, dbt).
FILES = {
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

MAX_BYTES = 5 * 1024 * 1024  # keep the committed slice under 5 MiB


def load_raw() -> dict[str, pd.DataFrame]:
    missing = [f for f in FILES.values() if not (RAW_DIR / f).exists()]
    if missing:
        print(f"Missing files in {RAW_DIR}:", *missing, sep="\n  ")
        print(
            "\nGet the full dataset first:\n"
            "  uv pip install kaggle\n"
            "  kaggle datasets download -d olistbr/brazilian-ecommerce "
            "-p data/olist --unzip\n"
            "or unzip the Kaggle zip into data/olist/.",
        )
        sys.exit(1)
    return {name: pd.read_csv(RAW_DIR / fname) for name, fname in FILES.items()}


def build_sample(
    raw: dict[str, pd.DataFrame], n_orders: int, seed: int
) -> dict[str, pd.DataFrame]:
    orders_full = raw["orders"]
    n = min(n_orders, len(orders_full))
    orders = orders_full.sample(n=n, random_state=seed).reset_index(drop=True)

    order_ids = set(orders["order_id"])
    customer_ids = set(orders["customer_id"])

    items = raw["order_items"]
    order_items = items[items["order_id"].isin(order_ids)].copy()
    pays = raw["order_payments"]
    order_payments = pays[pays["order_id"].isin(order_ids)].copy()
    revs = raw["order_reviews"]
    order_reviews = revs[revs["order_id"].isin(order_ids)].copy()

    product_ids = set(order_items["product_id"])
    seller_ids = set(order_items["seller_id"])

    cust = raw["customers"]
    customers = cust[cust["customer_id"].isin(customer_ids)].copy()
    prod = raw["products"]
    products = prod[prod["product_id"].isin(product_ids)].copy()
    sell = raw["sellers"]
    sellers = sell[sell["seller_id"].isin(seller_ids)].copy()

    # Dimensions. Keep the whole (tiny) translation table. Raw Olist has many
    # lat/lng points per zip prefix; keep one row per prefix so the prefix is a
    # clean join key and the slice stays small.
    translation = raw["product_category_translation"].copy()
    zips = set(customers["customer_zip_code_prefix"]) | set(
        sellers["seller_zip_code_prefix"]
    )
    geo = raw["geolocation"]
    geolocation = (
        geo[geo["geolocation_zip_code_prefix"].isin(zips)]
        .drop_duplicates(subset="geolocation_zip_code_prefix", keep="first")
        .copy()
    )

    return {
        "orders": orders,
        "order_items": order_items,
        "order_payments": order_payments,
        "order_reviews": order_reviews,
        "customers": customers,
        "products": products,
        "sellers": sellers,
        "geolocation": geolocation,
        "product_category_translation": translation,
    }


def check_integrity(s: dict[str, pd.DataFrame]) -> bool:
    def subset(child: str, ckey: str, parent: str, pkey: str) -> bool:
        return set(s[child][ckey]) <= set(s[parent][pkey])

    checks = {
        "order_items.order_id -> orders": subset(
            "order_items", "order_id", "orders", "order_id"
        ),
        "order_payments.order_id -> orders": subset(
            "order_payments", "order_id", "orders", "order_id"
        ),
        "order_reviews.order_id -> orders": subset(
            "order_reviews", "order_id", "orders", "order_id"
        ),
        "orders.customer_id -> customers": subset(
            "orders", "customer_id", "customers", "customer_id"
        ),
        "order_items.product_id -> products": subset(
            "order_items", "product_id", "products", "product_id"
        ),
        "order_items.seller_id -> sellers": subset(
            "order_items", "seller_id", "sellers", "seller_id"
        ),
    }
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    return all(checks.values())


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Slice the Olist dataset into data/olist_sample/."
    )
    ap.add_argument("--n-orders", type=int, default=2500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    raw = load_raw()
    sample = build_sample(raw, args.n_orders, args.seed)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nWriting slice to {OUT_DIR} (seed={args.seed}):")
    total = 0
    for name, df in sample.items():
        path = OUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        size = path.stat().st_size
        total += size
        print(f"  {name:<28} {len(df):>7,} rows  {size / 1024:>9.1f} KiB")
    print(f"  {'TOTAL':<28} {'':>7}        {total / 1024 / 1024:>9.2f} MiB")

    print("\nReferential integrity:")
    ok = check_integrity(sample)
    if not ok:
        sys.exit("Integrity check failed.")
    if total > MAX_BYTES:
        sys.exit(f"Slice is {total / 1024 / 1024:.2f} MiB (> 5 MiB). Lower --n-orders.")
    print("\nOK. Commit data/olist_sample/*.csv")


if __name__ == "__main__":
    main()
