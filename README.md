# Indonesia Inbound Tourism — Business Intelligence Project

A complete BI solution covering **ETL → Data Warehouse (star schema) → OLAP → Dashboard → Insights**, using Indonesia's foreign visitor arrival data (2019–2024).

## Business Question
> How has inbound tourism to Indonesia evolved through the pre-pandemic, pandemic, and recovery periods, and which **origin markets, entry ports, and visit purposes** should the Ministry of Tourism prioritize for the next 12 months?

## Dataset
Monthly foreign visitor arrivals disaggregated by **origin country**, **port of entry**, and **purpose of visit**, 2019-01 to 2024-12.

Source pattern: Indonesian Central Bureau of Statistics (BPS) — [bps.go.id](https://www.bps.go.id/en/statistics-table/2/MTM1OSMy/international-visitor-arrivals-to-indonesia-by-nationality.html) and Ministry of Tourism monthly releases.

> **Note:** Raw CSVs in `data/raw/` are simulated at record level but calibrated to published BPS aggregates (total arrivals, top-10 origin shares, COVID drop magnitude, 2023 recovery rate). This keeps the project reproducible without scraping. Swap in real BPS CSVs with the same schema to run on actual data.

## Architecture

```
 raw CSVs ──► extract.py ──► transform.py ──► load.py ──► SQLite (star schema)
                                                              │
                                                              ▼
                                                     Streamlit dashboard
                                                     + OLAP SQL queries
```

## Star Schema
```
                     ┌──────────────┐
                     │   dim_date   │
                     └──────┬───────┘
                            │
  ┌──────────────┐   ┌──────▼──────┐   ┌──────────────────┐
  │ dim_origin_  ├──►│ fact_visits ├──►│ dim_port_entry   │
  │  country     │   │             │   │                  │
  └──────────────┘   └──────┬──────┘   └──────────────────┘
                            │
                     ┌──────▼───────┐
                     │ dim_purpose  │
                     └──────────────┘
```

**Measures (fact_visits):** `visitor_count`, `avg_length_of_stay_nights`, `avg_expenditure_usd`, `total_expenditure_usd`.

## Quick Start

```bash
# 1. Install deps (use a virtualenv)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Generate raw data + run full ETL
python etl/run_etl.py

# 3. Launch dashboard
streamlit run dashboard/app.py
```

## Deliverables
- **ETL pipeline** — `etl/` (pandas)
- **Data warehouse** — `warehouse/tourism.db` (SQLite star schema)
- **OLAP queries** — `sql/olap_queries.sql` (roll-up, drill-down, slice, dice, pivot)
- **Dashboard** — `dashboard/app.py` (Streamlit, interactive)
- **Insights** — `INSIGHTS.md`
- **Slides** — `slides/presentation.md` (Marp)

## Team
BINUS — Business Intelligence course, Semester 3.
