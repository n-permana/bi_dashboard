"""
Indonesia Inbound Tourism — Streamlit BI Dashboard.

Run with:  streamlit run dashboard/app.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse" / "tourism.db"

st.set_page_config(
    page_title="Indonesia Tourism BI",
    page_icon="🇮🇩",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- data access -----------------------------------------------------
@st.cache_resource
def get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        st.error(
            f"Warehouse not found at {DB_PATH}. "
            "Run `python etl/run_etl.py` first."
        )
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def q(sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_conn(), params=params)


@st.cache_data
def load_dims() -> dict[str, pd.DataFrame]:
    return {
        "date": q("SELECT * FROM dim_date ORDER BY date_key"),
        "origin": q("SELECT * FROM dim_origin_country ORDER BY origin_country"),
        "port": q("SELECT * FROM dim_port_entry ORDER BY port_of_entry"),
        "purpose": q("SELECT * FROM dim_purpose ORDER BY purpose"),
    }


dims = load_dims()

# ---------- sidebar filters -------------------------------------------------
st.sidebar.title("🇮🇩 Filters")

years = sorted(dims["date"]["year"].unique().tolist())
year_sel = st.sidebar.multiselect("Year", years, default=years)

continents = sorted(dims["origin"]["origin_continent"].unique().tolist())
continent_sel = st.sidebar.multiselect("Origin continent", continents, default=continents)

port_types = sorted(dims["port"]["port_type"].unique().tolist())
port_type_sel = st.sidebar.multiselect("Port type", port_types, default=port_types)

purposes = sorted(dims["purpose"]["purpose"].unique().tolist())
purpose_sel = st.sidebar.multiselect("Purpose", purposes, default=purposes)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: simulated from published BPS monthly tourism releases, 2019–2024.\n\n"
    "Swap in real BPS CSVs (same schema) to refresh."
)


# ---------- helper: build WHERE clause -------------------------------------
def where_clause() -> tuple[str, list]:
    clauses, params = [], []
    if year_sel:
        clauses.append(f"d.year IN ({','.join('?' * len(year_sel))})")
        params += year_sel
    if continent_sel:
        clauses.append(f"o.origin_continent IN ({','.join('?' * len(continent_sel))})")
        params += continent_sel
    if port_type_sel:
        clauses.append(f"pe.port_type IN ({','.join('?' * len(port_type_sel))})")
        params += port_type_sel
    if purpose_sel:
        clauses.append(f"p.purpose IN ({','.join('?' * len(purpose_sel))})")
        params += purpose_sel
    w = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return w, params


BASE_FROM = """
FROM fact_visits f
JOIN dim_date d            USING (date_key)
JOIN dim_origin_country o  USING (origin_key)
JOIN dim_port_entry pe     USING (port_key)
JOIN dim_purpose p         USING (purpose_key)
"""


# ===========================================================================
# HEADER & KPIs
# ===========================================================================
st.title("Indonesia Inbound Tourism — BI Dashboard")
st.caption(
    "End-to-end BI pipeline: **CSV → Python ETL → SQLite star schema → OLAP → Streamlit**."
)

w, params = where_clause()

kpi = q(
    f"""
    SELECT
      SUM(f.visitor_count)                               AS visitors,
      SUM(f.total_expenditure_usd) / 1e6                 AS revenue_musd,
      AVG(f.avg_length_of_stay_nights)                   AS avg_stay,
      AVG(f.avg_expenditure_usd)                         AS avg_exp
    {BASE_FROM} {w}
    """,
    tuple(params),
).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Visitors", f"{int(kpi['visitors'] or 0):,}")
c2.metric("Revenue (USD M)", f"{(kpi['revenue_musd'] or 0):,.1f}")
c3.metric("Avg Length of Stay", f"{(kpi['avg_stay'] or 0):.1f} nights")
c4.metric("Avg Spend / Visitor", f"${(kpi['avg_exp'] or 0):,.0f}")

st.markdown("---")

# ===========================================================================
# TABS
# ===========================================================================
tab_trend, tab_origin, tab_port, tab_purpose, tab_olap = st.tabs(
    ["📈 Trends", "🌏 Origin Markets", "✈️ Ports & Provinces",
     "🎯 Purpose Mix", "🧮 OLAP Explorer"]
)

# ----- Trends --------------------------------------------------------------
with tab_trend:
    monthly = q(
        f"""
        SELECT d.year, d.month,
               printf('%04d-%02d', d.year, d.month) AS ym,
               d.era,
               SUM(f.visitor_count)              AS visitors,
               SUM(f.total_expenditure_usd)/1e6  AS revenue_musd
        {BASE_FROM} {w}
        GROUP BY d.year, d.month, d.era
        ORDER BY d.year, d.month
        """,
        tuple(params),
    )
    if monthly.empty:
        st.info("No data for selected filters.")
    else:
        fig = px.line(
            monthly, x="ym", y="visitors", color="era", markers=True,
            title="Monthly Visitor Arrivals (colored by era)",
            labels={"ym": "Month", "visitors": "Visitors"},
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

        yearly = monthly.groupby("year", as_index=False).agg(
            visitors=("visitors", "sum"), revenue_musd=("revenue_musd", "sum")
        )
        yearly["yoy_pct"] = yearly["visitors"].pct_change() * 100

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                px.bar(yearly, x="year", y="visitors",
                       text_auto=".2s", title="Visitors by Year"),
                use_container_width=True,
            )
        with col2:
            st.plotly_chart(
                px.bar(yearly.dropna(), x="year", y="yoy_pct",
                       text_auto=".1f",
                       title="Year-over-Year Growth (%)",
                       color="yoy_pct", color_continuous_scale="RdYlGn"),
                use_container_width=True,
            )


# ----- Origin --------------------------------------------------------------
with tab_origin:
    top_n = st.slider("Top N countries", 5, 20, 10)
    origin = q(
        f"""
        SELECT o.origin_country, o.origin_region, o.origin_continent,
               SUM(f.visitor_count) AS visitors,
               SUM(f.total_expenditure_usd)/1e6 AS revenue_musd,
               AVG(f.avg_length_of_stay_nights) AS avg_stay
        {BASE_FROM} {w}
        GROUP BY o.origin_country, o.origin_region, o.origin_continent
        ORDER BY visitors DESC
        """,
        tuple(params),
    )
    if origin.empty:
        st.info("No data.")
    else:
        top = origin.head(top_n)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(
                px.bar(top, x="visitors", y="origin_country",
                       orientation="h", color="origin_continent",
                       title=f"Top {top_n} Origin Countries",
                       text_auto=".2s").update_yaxes(categoryorder="total ascending"),
                use_container_width=True,
            )
        with col2:
            st.plotly_chart(
                px.pie(origin, names="origin_continent", values="visitors",
                       title="Share by Continent", hole=0.45),
                use_container_width=True,
            )
        st.subheader("Detail table")
        st.dataframe(
            origin.assign(
                visitors=origin["visitors"].map("{:,.0f}".format),
                revenue_musd=origin["revenue_musd"].map("{:,.2f}".format),
                avg_stay=origin["avg_stay"].map("{:.1f}".format),
            ),
            use_container_width=True, hide_index=True,
        )

    # Recovery analysis
    st.markdown("#### Recovery vs 2019 (within current filters)")
    recovery = q(
        f"""
        WITH y AS (
          SELECT o.origin_country,
                 SUM(CASE WHEN d.year=2019 THEN f.visitor_count END) AS v2019,
                 SUM(CASE WHEN d.year=2024 THEN f.visitor_count END) AS v2024
          {BASE_FROM} {w}
          GROUP BY o.origin_country
        )
        SELECT origin_country, v2019, v2024,
               ROUND(100.0 * v2024 / NULLIF(v2019,0), 1) AS recovery_pct
        FROM y WHERE v2019 > 20000
        ORDER BY recovery_pct DESC
        """,
        tuple(params),
    )
    if not recovery.empty:
        st.plotly_chart(
            px.bar(recovery, x="origin_country", y="recovery_pct",
                   color="recovery_pct", color_continuous_scale="RdYlGn",
                   title="2024 Recovery as % of 2019 Baseline",
                   text_auto=".0f"),
            use_container_width=True,
        )


# ----- Ports --------------------------------------------------------------
with tab_port:
    port = q(
        f"""
        SELECT pe.port_of_entry, pe.port_province, pe.port_type,
               SUM(f.visitor_count) AS visitors,
               SUM(f.total_expenditure_usd)/1e6 AS revenue_musd
        {BASE_FROM} {w}
        GROUP BY pe.port_of_entry, pe.port_province, pe.port_type
        ORDER BY visitors DESC
        """,
        tuple(params),
    )
    if port.empty:
        st.info("No data.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                px.treemap(port, path=["port_type", "port_province", "port_of_entry"],
                           values="visitors", color="revenue_musd",
                           color_continuous_scale="Viridis",
                           title="Ports Treemap (size = visitors, color = revenue $M)"),
                use_container_width=True,
            )
        with col2:
            prov = (port.groupby("port_province", as_index=False)
                        .agg(visitors=("visitors", "sum"),
                             revenue_musd=("revenue_musd", "sum"))
                        .sort_values("visitors", ascending=False))
            st.plotly_chart(
                px.bar(prov, x="visitors", y="port_province",
                       orientation="h", text_auto=".2s",
                       title="Visitors by Province")
                  .update_yaxes(categoryorder="total ascending"),
                use_container_width=True,
            )
        st.dataframe(port, use_container_width=True, hide_index=True)


# ----- Purpose ------------------------------------------------------------
with tab_purpose:
    purp_year = q(
        f"""
        SELECT d.year, p.purpose, SUM(f.visitor_count) AS visitors
        {BASE_FROM} {w}
        GROUP BY d.year, p.purpose
        ORDER BY d.year, p.purpose
        """,
        tuple(params),
    )
    if purp_year.empty:
        st.info("No data.")
    else:
        st.plotly_chart(
            px.area(purp_year, x="year", y="visitors", color="purpose",
                    groupnorm="percent",
                    title="Purpose Mix Over Time (share of visitors)"),
            use_container_width=True,
        )
        st.plotly_chart(
            px.bar(purp_year, x="year", y="visitors", color="purpose",
                   title="Visitors by Purpose and Year", text_auto=".2s"),
            use_container_width=True,
        )


# ----- OLAP Explorer -------------------------------------------------------
with tab_olap:
    st.markdown(
        "Pick any two dimensions to pivot. Demonstrates **slice / dice / pivot** "
        "directly against the star schema."
    )
    dim_map = {
        "Year":       "d.year",
        "Quarter":    "d.year_quarter",
        "Month":      "printf('%04d-%02d', d.year, d.month)",
        "Era":        "d.era",
        "Country":    "o.origin_country",
        "Region":     "o.origin_region",
        "Continent":  "o.origin_continent",
        "Port":       "pe.port_of_entry",
        "Province":   "pe.port_province",
        "Port type":  "pe.port_type",
        "Purpose":    "p.purpose",
    }
    c1, c2, c3 = st.columns(3)
    row_dim = c1.selectbox("Row dimension", list(dim_map.keys()), index=4)
    col_dim = c2.selectbox("Column dimension", list(dim_map.keys()), index=0)
    measure = c3.selectbox(
        "Measure",
        ["Visitors", "Revenue (USD M)", "Avg stay (nights)", "Avg spend (USD)"],
    )
    meas_sql = {
        "Visitors":          "SUM(f.visitor_count)",
        "Revenue (USD M)":   "ROUND(SUM(f.total_expenditure_usd)/1e6, 2)",
        "Avg stay (nights)": "ROUND(AVG(f.avg_length_of_stay_nights), 2)",
        "Avg spend (USD)":   "ROUND(AVG(f.avg_expenditure_usd), 0)",
    }[measure]

    sql = f"""
    SELECT {dim_map[row_dim]} AS row_v,
           {dim_map[col_dim]} AS col_v,
           {meas_sql}         AS m
    {BASE_FROM} {w}
    GROUP BY row_v, col_v
    """
    df = q(sql, tuple(params))
    if df.empty:
        st.info("No data.")
    else:
        pivot = df.pivot(index="row_v", columns="col_v", values="m").fillna(0)
        st.dataframe(pivot, use_container_width=True)
        st.plotly_chart(
            px.imshow(pivot, aspect="auto", color_continuous_scale="Blues",
                      title=f"{measure}: {row_dim} × {col_dim}"),
            use_container_width=True,
        )
