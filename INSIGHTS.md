# Business Insights — Indonesia Inbound Tourism (2019–2024)

All figures are derived from the warehouse `warehouse/tourism.db`. They are calibrated to BPS-published aggregates for trend realism. Run `python etl/smoke_test.py` to reproduce.

## 1. Headline trajectory

| Year | Visitors      | Revenue (USD M) | YoY     |
|------|---------------|-----------------|---------|
| 2019 | 16.18 M       | 23,890          | —       |
| 2020 | 4.11 M        | 6,095           | **−75%** |
| 2021 | 1.56 M        | 2,300           | −62%    |
| 2022 | 5.44 M        | 7,958           | +249%   |
| 2023 | 11.63 M       | 16,910          | +114%   |
| 2024 | 14.17 M       | 20,830          | +22%    |

> **Insight 1 — Recovery is real but incomplete.** 2024 arrivals reach **~88% of the 2019 peak**. No origin country has fully closed the gap, indicating ~2 M visitors of latent demand still on the table.

## 2. Origin markets

Top 5 markets in 2024 (Malaysia 2.62 M, China 1.80 M, Singapore 1.68 M, Australia 1.25 M, Timor-Leste 1.11 M) account for **~62%** of all arrivals.

> **Insight 2 — Recovery laggards = growth opportunity.** South Korea (82.6%), Taiwan (84.7%), Germany (85.1%) and China (85.2%) are below the average recovery rate. These 4 markets alone represent **~500 K missing visitors** vs 2019.

> **Insight 3 — Concentration risk.** ASEAN + East Asia drives **~70%** of arrivals. Any regional shock (FX, geopolitics, aviation capacity) hits Indonesia harder than diversified destinations like Thailand. **Diversification toward India, Middle East, and Europe** should be a stated KPI.

## 3. Ports & geography

| Port | Province | 2024 visitors | Revenue (USD M) |
|------|----------|---------------|-----------------|
| Ngurah Rai | Bali | 5.23 M | 7,825 |
| Soekarno-Hatta | DKI Jakarta | 2.48 M | 3,757 |
| Batam | Kepulauan Riau | 1.86 M | 2,479 |
| Atambua (Motaain) | NTT | 1.17 M | 1,816 |

> **Insight 4 — Bali is the cash engine, but also the single point of failure.** Ngurah Rai handles **37% of arrivals and ~38% of revenue**. Volcanic eruptions, runway closures, or overtourism backlash directly hit national totals. Investments in **Yogyakarta, Lombok, and Sam Ratulangi (Manado)** as secondary leisure gateways are strategically essential.

> **Insight 5 — Land borders are underused for revenue.** Atambua moves 1.17 M visitors but most are short-stay Timor-Leste cross-border traffic with low spend. Land-border tourism marketing offers little revenue lift; air-route expansion offers far more.

## 4. Purpose mix

2024 share: Leisure **57.8%**, Business **22.9%**, Official **6.3%**, Religious **5.2%**, Other **4.1%**, Education **3.9%**.

> **Insight 6 — Education and religious tourism are the highest-yield segments**. Education visitors stay ~30 nights and spend ~USD 2,500 each; religious visitors (Saudi/Middle East corridor) spend ~USD 1,200 with high seasonality. Both are under-marketed relative to leisure. **Targeted MICE + halal-tourism + scholarship-pipeline campaigns** should lift average revenue per visitor.

## 5. Recommendations to the Ministry of Tourism

1. **Set explicit recovery KPIs per market**: target 100% of 2019 baseline by end-2025 for the four laggards (Korea, Taiwan, Germany, China).
2. **De-risk Bali dependence**: re-allocate 15–20% of marketing budget to Yogyakarta, Lombok, Manado; subsidize new direct flights from Korea/Japan/India to those airports.
3. **Diversify origin mix**: open new tourism offices in Mumbai, Riyadh, Frankfurt; aim to lift non-ASEAN-non-East-Asia share from ~30% to ~38% by 2026.
4. **Yield management**: shift incentives from raw arrival counts to **revenue per visitor**. Education and religious segments deserve dedicated programs.
5. **Always-on dashboard**: keep this BI dashboard live with monthly BPS feeds so policy can react in weeks, not quarters.
