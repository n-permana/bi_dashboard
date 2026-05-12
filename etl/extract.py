"""
Extract stage.

Generates raw CSVs that mimic the schema of BPS monthly tourism releases,
calibrated to published annual totals and top-origin shares (2019-2024).

Real-world usage: replace generate_raw_data() with scrapers / API calls
that deposit CSVs with the same schema in data/raw/.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# Top origin countries with approximate 2019 share of total arrivals (BPS).
ORIGIN_COUNTRIES = [
    ("Malaysia",   "ASEAN",           "Asia",    0.175),
    ("Singapore",  "ASEAN",           "Asia",    0.120),
    ("China",      "East Asia",       "Asia",    0.130),
    ("Australia",  "Oceania",         "Oceania", 0.090),
    ("Timor-Leste","ASEAN",           "Asia",    0.080),
    ("India",      "South Asia",      "Asia",    0.040),
    ("Japan",      "East Asia",       "Asia",    0.030),
    ("South Korea","East Asia",       "Asia",    0.025),
    ("USA",        "North America",   "Americas",0.025),
    ("UK",         "Europe",          "Europe",  0.020),
    ("Germany",    "Europe",          "Europe",  0.015),
    ("France",     "Europe",          "Europe",  0.015),
    ("Netherlands","Europe",          "Europe",  0.012),
    ("Philippines","ASEAN",           "Asia",    0.018),
    ("Thailand",   "ASEAN",           "Asia",    0.015),
    ("Taiwan",     "East Asia",       "Asia",    0.015),
    ("Saudi Arabia","Middle East",    "Asia",    0.012),
    ("Russia",     "Europe",          "Europe",  0.010),
    ("Canada",     "North America",   "Americas",0.008),
    ("Others",     "Other",           "Other",   0.145),
]

# Ports of entry with approximate share (BPS: Ngurah Rai dominant for leisure,
# Soekarno-Hatta for business, land borders for Timor-Leste/Malaysia).
PORTS = [
    ("Ngurah Rai",       "Bali",             "Air",  0.40),
    ("Soekarno-Hatta",   "DKI Jakarta",      "Air",  0.22),
    ("Batam",            "Kepulauan Riau",   "Sea",  0.13),
    ("Juanda",           "Jawa Timur",       "Air",  0.04),
    ("Kualanamu",        "Sumatera Utara",   "Air",  0.03),
    ("Tanjung Uban",     "Kepulauan Riau",   "Sea",  0.03),
    ("Entikong",         "Kalimantan Barat", "Land", 0.02),
    ("Atambua (Motaain)","NTT",              "Land", 0.04),
    ("Sam Ratulangi",    "Sulawesi Utara",   "Air",  0.015),
    ("Yogyakarta",       "DI Yogyakarta",    "Air",  0.015),
    ("Lombok",           "NTB",              "Air",  0.015),
    ("Others",           "Lainnya",          "Mixed",0.055),
]

PURPOSES = [
    ("Leisure",  0.65),
    ("Business", 0.20),
    ("Official", 0.05),
    ("Education",0.03),
    ("Religious",0.04),
    ("Other",    0.03),
]

# Annual total arrivals (BPS published figures, rounded, in millions).
ANNUAL_TOTALS = {
    2019: 16_106_954,
    2020: 4_052_923,
    2021: 1_557_530,
    2022: 5_470_000,
    2023: 11_677_000,
    2024: 13_900_000,  # projected / partial
}

# Seasonality multiplier per month (peaks Jul-Aug & Dec).
SEASONALITY = np.array(
    [0.85, 0.80, 0.90, 0.95, 1.00, 1.05, 1.20, 1.25, 1.00, 1.00, 0.95, 1.15]
)
SEASONALITY = SEASONALITY / SEASONALITY.mean()


def _month_weights(year: int) -> np.ndarray:
    """Pandemic distortion: flatten 2020 after Mar, near-zero 2021 H1."""
    w = SEASONALITY.copy()
    if year == 2020:
        w[2:] *= np.linspace(0.15, 0.05, 10)  # collapse after March
    elif year == 2021:
        w[:6] *= 0.05
        w[6:] *= np.linspace(0.1, 0.3, 6)
    return w / w.sum()


def generate_raw_data(seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for year, total in ANNUAL_TOTALS.items():
        month_w = _month_weights(year)
        for m_idx, mw in enumerate(month_w, start=1):
            month_total = total * mw
            # allocate across origin × port × purpose with Dirichlet noise
            for country, region, continent, c_share in ORIGIN_COUNTRIES:
                c_total = month_total * c_share * rng.uniform(0.85, 1.15)
                # country-specific port bias: Australians via Bali, Malaysians via Batam, etc.
                port_bias = np.array([p[3] for p in PORTS], dtype=float)
                if country == "Australia":
                    port_bias = port_bias * np.array(
                        [3.0, 0.5, 0.3, 0.8, 0.3, 0.3, 0.2, 0.2, 0.4, 1.0, 1.2, 0.8]
                    )
                elif country == "Malaysia":
                    port_bias = port_bias * np.array(
                        [0.6, 0.8, 2.5, 0.5, 1.5, 2.0, 3.0, 0.3, 0.5, 0.4, 0.2, 0.8]
                    )
                elif country == "China":
                    port_bias = port_bias * np.array(
                        [2.2, 1.2, 0.5, 0.8, 0.3, 0.3, 0.1, 0.2, 0.8, 1.0, 0.7, 0.5]
                    )
                elif country == "Timor-Leste":
                    port_bias = port_bias * np.array(
                        [0.05, 0.2, 0.05, 0.05, 0.05, 0.05, 0.05, 8.0, 0.05, 0.05, 0.1, 0.3]
                    )
                port_bias = port_bias / port_bias.sum()
                port_alloc = rng.dirichlet(port_bias * 50 + 0.5) * c_total

                # purpose bias per country
                purpose_bias = np.array([p[1] for p in PURPOSES], dtype=float)
                if country in ("Singapore", "Japan", "South Korea"):
                    purpose_bias = purpose_bias * np.array([0.7, 2.0, 1.2, 0.8, 0.5, 1.0])
                elif country == "Saudi Arabia":
                    purpose_bias = purpose_bias * np.array([0.3, 0.5, 0.5, 0.5, 6.0, 0.5])
                elif country == "India":
                    purpose_bias = purpose_bias * np.array([1.1, 1.4, 0.8, 1.0, 0.7, 1.0])
                purpose_bias = purpose_bias / purpose_bias.sum()

                for port_idx, port_count in enumerate(port_alloc):
                    if port_count < 1:
                        continue
                    purp_alloc = rng.dirichlet(purpose_bias * 30 + 0.5) * port_count
                    port_name, province, port_type, _ = PORTS[port_idx]
                    for purp_idx, purp_count in enumerate(purp_alloc):
                        if purp_count < 1:
                            continue
                        purpose_name, _ = PURPOSES[purp_idx]
                        # length of stay & expenditure depend on purpose/origin
                        base_los = {
                            "Leisure": 8.5, "Business": 4.0, "Official": 5.0,
                            "Education": 30.0, "Religious": 7.0, "Other": 6.0,
                        }[purpose_name]
                        base_exp = {
                            "Leisure": 1400, "Business": 1800, "Official": 1600,
                            "Education": 2500, "Religious": 1200, "Other": 1100,
                        }[purpose_name]
                        if continent == "Europe":
                            base_los *= 1.3; base_exp *= 1.2
                        if country == "Australia":
                            base_los *= 0.9; base_exp *= 1.0
                        if country == "Malaysia":
                            base_los *= 0.6; base_exp *= 0.7
                        los = max(1.0, rng.normal(base_los, base_los * 0.15))
                        exp = max(100.0, rng.normal(base_exp, base_exp * 0.20))
                        rows.append({
                            "year": year,
                            "month": m_idx,
                            "origin_country": country,
                            "origin_region": region,
                            "origin_continent": continent,
                            "port_of_entry": port_name,
                            "port_province": province,
                            "port_type": port_type,
                            "purpose": purpose_name,
                            "visitor_count": int(round(purp_count)),
                            "avg_length_of_stay_nights": round(los, 2),
                            "avg_expenditure_usd": round(exp, 2),
                        })

    df = pd.DataFrame(rows)
    # Split into two raw files to simulate multi-source extraction.
    arrivals_cols = [
        "year", "month", "origin_country", "origin_region", "origin_continent",
        "port_of_entry", "port_province", "port_type", "purpose", "visitor_count",
    ]
    profile_cols = [
        "year", "month", "origin_country", "port_of_entry", "purpose",
        "avg_length_of_stay_nights", "avg_expenditure_usd",
    ]
    df[arrivals_cols].to_csv(RAW_DIR / "arrivals_monthly.csv", index=False)
    df[profile_cols].to_csv(RAW_DIR / "visitor_profile_monthly.csv", index=False)
    print(f"[extract] wrote {len(df):,} raw rows to {RAW_DIR}")


def extract() -> dict[str, pd.DataFrame]:
    """Read raw CSVs. Generates them first if missing."""
    arrivals_path = RAW_DIR / "arrivals_monthly.csv"
    profile_path = RAW_DIR / "visitor_profile_monthly.csv"
    if not arrivals_path.exists() or not profile_path.exists():
        generate_raw_data()
    arrivals = pd.read_csv(arrivals_path)
    profile = pd.read_csv(profile_path)
    print(f"[extract] loaded arrivals={len(arrivals):,}, profile={len(profile):,}")
    return {"arrivals": arrivals, "profile": profile}


if __name__ == "__main__":
    generate_raw_data()
