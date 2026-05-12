"""Quick OLAP smoke-test against the warehouse. Used to ground insights."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DB = Path(__file__).resolve().parents[1] / "warehouse" / "tourism.db"

QUERIES = {
    "Yearly totals": """
        SELECT d.year,
               SUM(f.visitor_count) AS visitors,
               ROUND(SUM(f.total_expenditure_usd)/1e6, 1) AS rev_musd
        FROM fact_visits f JOIN dim_date d USING(date_key)
        GROUP BY d.year ORDER BY d.year
    """,
    "Top 10 origins 2024": """
        SELECT o.origin_country, SUM(f.visitor_count) AS visitors
        FROM fact_visits f
        JOIN dim_date d USING(date_key)
        JOIN dim_origin_country o USING(origin_key)
        WHERE d.year = 2024
        GROUP BY o.origin_country ORDER BY visitors DESC LIMIT 10
    """,
    "Recovery 2024 vs 2019": """
        WITH y AS (
          SELECT o.origin_country,
                 SUM(CASE WHEN d.year=2019 THEN f.visitor_count END) AS v2019,
                 SUM(CASE WHEN d.year=2024 THEN f.visitor_count END) AS v2024
          FROM fact_visits f
          JOIN dim_date d USING(date_key)
          JOIN dim_origin_country o USING(origin_key)
          GROUP BY o.origin_country
        )
        SELECT origin_country, v2019, v2024,
               ROUND(100.0 * v2024 / NULLIF(v2019, 0), 1) AS rec_pct
        FROM y WHERE v2019 > 50000 ORDER BY rec_pct DESC
    """,
    "Top ports 2024": """
        SELECT pe.port_of_entry, pe.port_province,
               SUM(f.visitor_count) AS visitors,
               ROUND(SUM(f.total_expenditure_usd)/1e6, 1) AS rev_musd
        FROM fact_visits f
        JOIN dim_date d USING(date_key)
        JOIN dim_port_entry pe USING(port_key)
        WHERE d.year = 2024
        GROUP BY pe.port_of_entry, pe.port_province
        ORDER BY visitors DESC LIMIT 8
    """,
    "Purpose mix 2024": """
        SELECT p.purpose, SUM(f.visitor_count) AS visitors
        FROM fact_visits f
        JOIN dim_date d USING(date_key)
        JOIN dim_purpose p USING(purpose_key)
        WHERE d.year = 2024
        GROUP BY p.purpose ORDER BY visitors DESC
    """,
}


def main() -> None:
    with sqlite3.connect(DB) as conn:
        for title, sql in QUERIES.items():
            print(f"--- {title} ---")
            print(pd.read_sql(sql, conn).to_string(index=False))
            print()


if __name__ == "__main__":
    main()
