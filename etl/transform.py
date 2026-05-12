"""
Transform stage.

- Cleans raw data (null handling, type coercion, dedup, range validation).
- Joins arrivals + visitor profile.
- Builds conformed dimension tables and fact table in star-schema shape.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


def _clean(df: pd.DataFrame, name: str) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    # basic range checks
    if "year" in df.columns:
        df = df[df["year"].between(2019, 2024)]
    if "month" in df.columns:
        df = df[df["month"].between(1, 12)]
    if "visitor_count" in df.columns:
        df = df[df["visitor_count"] >= 0]
    # trim strings
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()
    print(f"[transform] {name}: {before:,} -> {len(df):,} rows after cleaning")
    return df


def build_dimensions_and_fact(
    arrivals: pd.DataFrame, profile: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    arrivals = _clean(arrivals, "arrivals")
    profile = _clean(profile, "profile")

    # ---- dim_date -----------------------------------------------------------
    dates = arrivals[["year", "month"]].drop_duplicates().sort_values(["year", "month"])
    dates["date_key"] = dates["year"] * 100 + dates["month"]
    dates["month_name"] = pd.to_datetime(dates["month"], format="%m").dt.strftime("%b")
    dates["quarter"] = ((dates["month"] - 1) // 3 + 1).map(lambda q: f"Q{q}")
    dates["year_quarter"] = dates["year"].astype(str) + "-" + dates["quarter"]

    def era(y: int) -> str:
        if y == 2019:
            return "Pre-Pandemic"
        if y in (2020, 2021):
            return "Pandemic"
        return "Recovery"

    dates["era"] = dates["year"].apply(era)
    dim_date = dates[
        ["date_key", "year", "quarter", "year_quarter", "month", "month_name", "era"]
    ].reset_index(drop=True)

    # ---- dim_origin_country -------------------------------------------------
    dim_origin = (
        arrivals[["origin_country", "origin_region", "origin_continent"]]
        .drop_duplicates()
        .sort_values("origin_country")
        .reset_index(drop=True)
    )
    dim_origin.insert(0, "origin_key", range(1, len(dim_origin) + 1))

    # ---- dim_port_entry -----------------------------------------------------
    dim_port = (
        arrivals[["port_of_entry", "port_province", "port_type"]]
        .drop_duplicates()
        .sort_values("port_of_entry")
        .reset_index(drop=True)
    )
    dim_port.insert(0, "port_key", range(1, len(dim_port) + 1))

    # ---- dim_purpose --------------------------------------------------------
    dim_purpose = (
        arrivals[["purpose"]]
        .drop_duplicates()
        .sort_values("purpose")
        .reset_index(drop=True)
    )
    dim_purpose.insert(0, "purpose_key", range(1, len(dim_purpose) + 1))

    # ---- fact_visits --------------------------------------------------------
    merged = arrivals.merge(
        profile,
        on=["year", "month", "origin_country", "port_of_entry", "purpose"],
        how="left",
    )
    # impute any missing profile metrics with group medians
    for col in ["avg_length_of_stay_nights", "avg_expenditure_usd"]:
        merged[col] = merged.groupby("purpose")[col].transform(
            lambda s: s.fillna(s.median())
        )
        merged[col] = merged[col].fillna(merged[col].median())

    merged["date_key"] = merged["year"] * 100 + merged["month"]
    merged = merged.merge(dim_origin[["origin_key", "origin_country"]], on="origin_country")
    merged = merged.merge(dim_port[["port_key", "port_of_entry"]], on="port_of_entry")
    merged = merged.merge(dim_purpose[["purpose_key", "purpose"]], on="purpose")

    merged["total_expenditure_usd"] = (
        merged["visitor_count"] * merged["avg_expenditure_usd"]
    ).round(2)

    fact = (
        merged.groupby(
            ["date_key", "origin_key", "port_key", "purpose_key"], as_index=False
        )
        .agg(
            visitor_count=("visitor_count", "sum"),
            avg_length_of_stay_nights=("avg_length_of_stay_nights", "mean"),
            avg_expenditure_usd=("avg_expenditure_usd", "mean"),
            total_expenditure_usd=("total_expenditure_usd", "sum"),
        )
    )
    fact["avg_length_of_stay_nights"] = fact["avg_length_of_stay_nights"].round(2)
    fact["avg_expenditure_usd"] = fact["avg_expenditure_usd"].round(2)
    fact.insert(0, "visit_id", range(1, len(fact) + 1))

    print(
        f"[transform] dim_date={len(dim_date)}, dim_origin={len(dim_origin)}, "
        f"dim_port={len(dim_port)}, dim_purpose={len(dim_purpose)}, fact={len(fact):,}"
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dim_date.to_csv(PROCESSED_DIR / "dim_date.csv", index=False)
    dim_origin.to_csv(PROCESSED_DIR / "dim_origin_country.csv", index=False)
    dim_port.to_csv(PROCESSED_DIR / "dim_port_entry.csv", index=False)
    dim_purpose.to_csv(PROCESSED_DIR / "dim_purpose.csv", index=False)
    fact.to_csv(PROCESSED_DIR / "fact_visits.csv", index=False)

    return {
        "dim_date": dim_date,
        "dim_origin_country": dim_origin,
        "dim_port_entry": dim_port,
        "dim_purpose": dim_purpose,
        "fact_visits": fact,
    }
