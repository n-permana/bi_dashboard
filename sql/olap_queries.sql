-- =============================================================
-- OLAP operations over the Indonesia Tourism star schema.
-- Each section demonstrates a canonical OLAP concept.
-- =============================================================

-- -------------------------------------------------------------
-- 1. ROLL-UP  (month -> quarter -> year -> era)
-- -------------------------------------------------------------
-- 1a. Arrivals by era (highest level)
SELECT d.era, SUM(f.visitor_count) AS total_visitors
FROM fact_visits f JOIN dim_date d USING (date_key)
GROUP BY d.era
ORDER BY total_visitors DESC;

-- 1b. Arrivals by year
SELECT d.year, SUM(f.visitor_count) AS total_visitors,
       ROUND(SUM(f.total_expenditure_usd) / 1e6, 2) AS revenue_musd
FROM fact_visits f JOIN dim_date d USING (date_key)
GROUP BY d.year ORDER BY d.year;

-- 1c. Arrivals by year-quarter
SELECT d.year_quarter, SUM(f.visitor_count) AS total_visitors
FROM fact_visits f JOIN dim_date d USING (date_key)
GROUP BY d.year_quarter ORDER BY d.year_quarter;


-- -------------------------------------------------------------
-- 2. DRILL-DOWN  (continent -> region -> country)
-- -------------------------------------------------------------
-- 2a. By continent in 2024
SELECT o.origin_continent, SUM(f.visitor_count) AS visitors
FROM fact_visits f
JOIN dim_date d USING (date_key)
JOIN dim_origin_country o USING (origin_key)
WHERE d.year = 2024
GROUP BY o.origin_continent ORDER BY visitors DESC;

-- 2b. Drill down Asia -> regions
SELECT o.origin_region, SUM(f.visitor_count) AS visitors
FROM fact_visits f
JOIN dim_date d USING (date_key)
JOIN dim_origin_country o USING (origin_key)
WHERE d.year = 2024 AND o.origin_continent = 'Asia'
GROUP BY o.origin_region ORDER BY visitors DESC;

-- 2c. Drill down ASEAN -> countries
SELECT o.origin_country, SUM(f.visitor_count) AS visitors
FROM fact_visits f
JOIN dim_date d USING (date_key)
JOIN dim_origin_country o USING (origin_key)
WHERE d.year = 2024 AND o.origin_region = 'ASEAN'
GROUP BY o.origin_country ORDER BY visitors DESC;


-- -------------------------------------------------------------
-- 3. SLICE  (fix one dimension value, look at remainder)
-- -------------------------------------------------------------
-- Slice: Bali only, monthly trend by purpose
SELECT d.year, d.month, p.purpose, SUM(f.visitor_count) AS visitors
FROM fact_visits f
JOIN dim_date d USING (date_key)
JOIN dim_port_entry pe USING (port_key)
JOIN dim_purpose p USING (purpose_key)
WHERE pe.port_province = 'Bali'
GROUP BY d.year, d.month, p.purpose
ORDER BY d.year, d.month;


-- -------------------------------------------------------------
-- 4. DICE  (filter on multiple dimensions)
-- -------------------------------------------------------------
-- Dice: Australian & Chinese leisure visitors via air ports, 2023-2024
SELECT d.year_quarter, o.origin_country, pe.port_of_entry,
       SUM(f.visitor_count) AS visitors,
       ROUND(AVG(f.avg_length_of_stay_nights), 2) AS avg_stay
FROM fact_visits f
JOIN dim_date d USING (date_key)
JOIN dim_origin_country o USING (origin_key)
JOIN dim_port_entry pe USING (port_key)
JOIN dim_purpose p USING (purpose_key)
WHERE o.origin_country IN ('Australia', 'China')
  AND pe.port_type = 'Air'
  AND p.purpose = 'Leisure'
  AND d.year IN (2023, 2024)
GROUP BY d.year_quarter, o.origin_country, pe.port_of_entry
ORDER BY d.year_quarter, o.origin_country, visitors DESC;


-- -------------------------------------------------------------
-- 5. PIVOT  (origin x year, visitors)
-- -------------------------------------------------------------
SELECT o.origin_country,
       SUM(CASE WHEN d.year = 2019 THEN f.visitor_count END) AS y2019,
       SUM(CASE WHEN d.year = 2020 THEN f.visitor_count END) AS y2020,
       SUM(CASE WHEN d.year = 2021 THEN f.visitor_count END) AS y2021,
       SUM(CASE WHEN d.year = 2022 THEN f.visitor_count END) AS y2022,
       SUM(CASE WHEN d.year = 2023 THEN f.visitor_count END) AS y2023,
       SUM(CASE WHEN d.year = 2024 THEN f.visitor_count END) AS y2024
FROM fact_visits f
JOIN dim_date d USING (date_key)
JOIN dim_origin_country o USING (origin_key)
GROUP BY o.origin_country
ORDER BY y2024 DESC;


-- -------------------------------------------------------------
-- 6. RECOVERY RATIO 2024 vs 2019  (analytical KPI)
-- -------------------------------------------------------------
WITH y AS (
    SELECT o.origin_country,
           SUM(CASE WHEN d.year = 2019 THEN f.visitor_count END) AS v2019,
           SUM(CASE WHEN d.year = 2024 THEN f.visitor_count END) AS v2024
    FROM fact_visits f
    JOIN dim_date d USING (date_key)
    JOIN dim_origin_country o USING (origin_key)
    GROUP BY o.origin_country
)
SELECT origin_country, v2019, v2024,
       ROUND(100.0 * v2024 / NULLIF(v2019, 0), 1) AS recovery_pct
FROM y
WHERE v2019 > 50000
ORDER BY recovery_pct DESC;


-- -------------------------------------------------------------
-- 7. TOP-N PORTS BY REVENUE, current year
-- -------------------------------------------------------------
SELECT pe.port_of_entry, pe.port_province,
       SUM(f.visitor_count) AS visitors,
       ROUND(SUM(f.total_expenditure_usd) / 1e6, 2) AS revenue_musd
FROM fact_visits f
JOIN dim_date d USING (date_key)
JOIN dim_port_entry pe USING (port_key)
WHERE d.year = 2024
GROUP BY pe.port_of_entry, pe.port_province
ORDER BY revenue_musd DESC
LIMIT 10;
