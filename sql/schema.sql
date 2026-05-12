-- Star schema DDL for the Indonesia Inbound Tourism data warehouse.
-- Target: SQLite (portable, file-based).

DROP TABLE IF EXISTS fact_visits;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_origin_country;
DROP TABLE IF EXISTS dim_port_entry;
DROP TABLE IF EXISTS dim_purpose;

CREATE TABLE dim_date (
    date_key      INTEGER PRIMARY KEY,   -- YYYYMM
    year          INTEGER NOT NULL,
    quarter       TEXT    NOT NULL,
    year_quarter  TEXT    NOT NULL,
    month         INTEGER NOT NULL,
    month_name    TEXT    NOT NULL,
    era           TEXT    NOT NULL        -- Pre-Pandemic / Pandemic / Recovery
);

CREATE TABLE dim_origin_country (
    origin_key       INTEGER PRIMARY KEY,
    origin_country   TEXT NOT NULL UNIQUE,
    origin_region    TEXT NOT NULL,       -- ASEAN, East Asia, Europe, ...
    origin_continent TEXT NOT NULL
);

CREATE TABLE dim_port_entry (
    port_key        INTEGER PRIMARY KEY,
    port_of_entry   TEXT NOT NULL UNIQUE,
    port_province   TEXT NOT NULL,
    port_type       TEXT NOT NULL         -- Air / Sea / Land / Mixed
);

CREATE TABLE dim_purpose (
    purpose_key INTEGER PRIMARY KEY,
    purpose     TEXT NOT NULL UNIQUE
);

CREATE TABLE fact_visits (
    visit_id                 INTEGER PRIMARY KEY,
    date_key                 INTEGER NOT NULL REFERENCES dim_date(date_key),
    origin_key               INTEGER NOT NULL REFERENCES dim_origin_country(origin_key),
    port_key                 INTEGER NOT NULL REFERENCES dim_port_entry(port_key),
    purpose_key              INTEGER NOT NULL REFERENCES dim_purpose(purpose_key),
    visitor_count            INTEGER NOT NULL,
    avg_length_of_stay_nights REAL,
    avg_expenditure_usd      REAL,
    total_expenditure_usd    REAL
);

CREATE INDEX idx_fact_date    ON fact_visits(date_key);
CREATE INDEX idx_fact_origin  ON fact_visits(origin_key);
CREATE INDEX idx_fact_port    ON fact_visits(port_key);
CREATE INDEX idx_fact_purpose ON fact_visits(purpose_key);
