"""
Load stage.

Creates/refreshes the SQLite data warehouse using sql/schema.sql,
then bulk-inserts processed dimension and fact tables.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse" / "tourism.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"


def load(tables: dict[str, pd.DataFrame]) -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_PATH.read_text()

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema_sql)
        # order matters: dims before fact
        load_order = [
            "dim_date",
            "dim_origin_country",
            "dim_port_entry",
            "dim_purpose",
            "fact_visits",
        ]
        for name in load_order:
            df = tables[name]
            df.to_sql(name, conn, if_exists="append", index=False)
            print(f"[load] inserted {len(df):,} rows into {name}")
        conn.commit()

    print(f"[load] warehouse ready at {DB_PATH}")
    return DB_PATH
