# Financial Data

A private financial data infrastructure project for collecting, standardizing, storing, and analyzing market, macro, industry, freight, commodity, and alternative datasets.

This repository is designed as a local research database and Python analytics library. The long-term goal is to make financial data easy to retrieve through service classes such as `PriceService`, `MacroService`, `IndustryService`, and `FreightService`, while also providing reusable tools for technical indicators, factor analysis, portfolio allocation, and macro-financial research.

---

## 1. Project Overview

This project is not just a collection of Excel files. It is intended to become a structured financial data platform with the following layers:

```text
raw source files (excel, tradingview api, yfinance api etc.)
    ↓
python etl jobs
    ↓
parquet data lake
    ↓
duckdb database
    ↓
python service layer
    ↓
research, dashboards, allocation models, and reports
```

The database currently focuses on:

```text
- market data
- macroeconomic indicators
- freight and shipping indicators
- commodity indices and futures
- industry indicators
- semiconductor data
- automobile data
- real estate data
- volatility and risk indicators
- alternative datasets
```

The metadata master currently contains hundreds of data items across major asset and alternative-data categories, including `commodity`, `freight`, `equity`, `industry`, `macro`, and `risk`.

---

## 2. Design Principles

### 2.1 metadata first

Every dataset should be described before it is used.

The project uses a master metadata table to define:

```text
- internal id
- asset class
- category
- sub-category
- instrument type
- symbol
- raw symbol
- exchange
- country
- name
- unit
- frequency
- source
- url
```

This makes the database easier to maintain as the number of datasets grows.

### 2.2 raw data is preserved

Raw files should be kept as close as possible to the original source format. Cleansed data should be saved separately.

Recommended structure:

```text
data/
    raw manually collected or source-specific files

data_lake/
    raw/
        standardized parquet files
    refined/
        cleaned and merged datasets
```

### 2.3 long-form storage, wide-form analysis

Database tables should generally store data in long form:

```text
base_date | release_date | symbol | value
```

Analysis can then pivot the data into wide form when needed:

```text
date | bdi | bsi | bcti | fbx | ...
```

This keeps the database normalized while still allowing easy modeling in Python.

### 2.4 release timing matters

For macro and alternative data, the project stores:

```text
base_date
release_date
time
time_zone
```

This is important for avoiding look-ahead bias. A value should only be used after it was actually released and observable.

### 2.5 services should hide database complexity

Users should not need to write raw SQL every time. Future service classes will provide simple Python interfaces such as:

```python
freight = FreightService(db_path="alternative_data.duckdb")
df = freight.get_series(symbols=["BDI", "FBX"], start="2020-01-01")
```

---

## 3. Database Architecture

The project uses DuckDB as the local analytical database engine.

A typical fully qualified table name follows this pattern:

```text
catalog.schema.table
```

Example:

```sql
select *
from alternative_data.freight.freight_data;
```

---

## 4. Core Tables

### 4.1 freight data

Table:

```text
alternative_data.freight.freight_data
```

Columns:

```text
base_date
release_date
time
time_zone
symbol
exchange
country
value
```

Description:

```text
freight_data stores time-series values for freight and shipping-related indices.
examples include bdi, bsi, bci, bcti, bpi, bhsi, blng, blpg, fbx, and bdti.
```

Logical key:

```text
base_date + symbol + exchange
```

For datasets with multiple releases per base date, use:

```text
base_date + release_date + time + symbol + exchange
```

### 4.2 macro data

Recommended table:

```text
alternative_data.macro.macro_data
```

Recommended columns:

```text
base_date
release_date
time
time_zone
symbol
exchange
country
actual
forecast
previous
preliminary_release
```

Purpose:

```text
macro_data stores scheduled economic releases, including actual, forecast, previous, and preliminary release values.
```

For indicators with preliminary, revised, and final releases, the same `base_date` may appear multiple times with different `release_date` values.

Recommended logical key:

```text
base_date + release_date + time + symbol + exchange
```

almost macroeconomic data derived from investing.com

### 4.3 master metadata

Recommended table:

```text
alternative_data.metadata.data_master
```

Recommended columns:

```text
id
asset_class
category
sub_category
instrument_type
symbol
symbol_raw
exchange
country
name
name_kr
unit
frequency
source
url
```

Purpose:

```text
data_master defines what each dataset is, where it comes from, how often it updates, and how it should be interpreted.
```

---

## 5. Data Dictionary Convention

Each major data table should have a corresponding dictionary table.

Examples:

```text
freight.freight_data       → freight.freight_dictionary
macro.macro_data           → macro.macro_dictionary
industry.industry_data     → industry.industry_dictionary
price.price_data           → price.price_dictionary
metadata.data_master       → metadata.data_master_dictionary
```

---

## 6. SQL Style Guide

Use lowercase SQL keywords for readability.

Preferred:

```sql
select *
from alternative_data.freight.freight_data
order by release_date;
```

Avoid:

```sql
SELECT *
FROM alternative_data.freight.freight_data
ORDER BY release_date;
```

---

## 7. Python Service Layer

The planned service layer will provide a clean interface for retrieving data from DuckDB.

### 7.1 PriceService

Purpose:

```text
retrieve price, index, futures, fx, and market data.
```

Example interface:

```python
price = PriceService(db_path="database/alternative_data.duckdb")

df = price.get_price(
    symbols=["spy", "tlt", "gld"],
    start="2020-01-01",
    end="2026-12-31",
    field="close",
)
```

Planned methods:

```text
get_price()
get_ohlcv()
get_returns()
get_wide_price()
get_adjusted_price()
```

### 7.2 MacroService

Purpose:

```text
retrieve economic indicators with release-date awareness.
```

Example interface:

```python
macro = MacroService(db_path="database/alternative_data.duckdb")

df = macro.get_release(
    symbols=["cpi_yoy", "nfp", "unrate"],
    start="2015-01-01",
    use_release_date=True,
)
```

Planned methods:

```text
get_actual()
get_forecast()
get_surprise()
get_revision()
get_asof()
```

### 7.3 IndustryService

Purpose:

```text
retrieve industry-level indicators such as semiconductor, automobile, real estate, and supply-chain data.
```

Example interface:

```python
industry = IndustryService(db_path="database/alternative_data.duckdb")

df = industry.get_series(
    symbols=["dram_spot", "nand_spot", "muvvi"],
    start="2018-01-01",
)
```

Planned methods:

```text
get_series()
get_cycle_indicator()
get_sector_dashboard()
get_industry_momentum()
```

### 7.4 FreightService

Purpose:

```text
retrieve freight, shipping, rail, container, tanker, and bulk shipping indices.
```

Example interface:

```python
freight = FreightService(db_path="database/alternative_data.duckdb")

df = freight.get_series(
    symbols=["bdi", "fbx", "bcti"],
    start="2020-01-01",
    wide=True,
    ffill=True,
)
```

Planned methods:

```text
get_series()
get_wide()
get_ffill()
get_shipping_dashboard()
get_freight_momentum()
```

---

## 8. Planned Analytics Library

The project will include reusable research tools.

### 8.1 technical indicators

Planned module:

```text
src/indicators/technical.py
```

Planned functions:

```text
moving_average()
exponential_moving_average()
relative_strength_index()
macd()
bollinger_band()
z_score()
drawdown()
rolling_volatility()
```

### 8.2 factor and macro tools

Planned module:

```text
src/research/factor_model.py
```

Planned functions:

```text
standardize_factor()
winsorize_factor()
calculate_factor_return()
calculate_beta()
rolling_correlation()
lead_lag_analysis()
```

### 8.3 portfolio allocation

Planned module:

```text
src/portfolio/allocation.py
```

Planned models:

```text
equal weight
inverse volatility
risk parity
mean-variance optimization
black-litterman
hierarchical risk parity
nested clustered optimization
regime-based tactical allocation
```

### 8.4 scenario and stress testing

Planned module:

```text
src/research/scenario.py
```

Planned features:

```text
macro shock simulation
commodity shock analysis
freight shock analysis
inflation scenario analysis
fx stress scenario
rate shock scenario
```

---

## 9. ETL Convention

Every ETL job should follow this pattern:

```text
read source file
    ↓
normalize column names
    ↓
validate required columns
    ↓
convert date, time, numeric fields
    ↓
add metadata
    ↓
check duplicates
    ↓
save parquet
    ↓
load into duckdb
```

Recommended validation rules:

```text
- required columns must exist
- dates must be parseable
- numeric values must be coercible
- logical primary key must not be duplicated
- symbol must exist in metadata master
- source and frequency should be defined
```

---

## 10. Time and Release-Date Policy

The project distinguishes:

```text
base_date
release_date
time
time_zone
```

Definitions:

```text
base_date:
    reference period of the observation.

release_date:
    date when the value became observable.

time:
    local release time.

time_zone:
    utc offset or local timezone representation.
```

This is especially important for:

```text
- macroeconomic releases
- freight indices
- commodity indices
- market-sensitive alternative data
- backtesting
- event studies
```

---

## 11. Roadmap

### phase 1: data infrastructure

```text
- finish metadata master
- standardize raw parquet files
- create duckdb schemas
- create dictionary tables
- define logical keys
```

### phase 2: service layer

```text
- implement BaseService
- implement PriceService
- implement MacroService
- implement IndustryService
- implement FreightService
```

### phase 3: analytics library

```text
- technical indicators
- return calculation
- rolling statistics
- factor transformation
- macro surprise calculation
- release-aware as-of joins
```

### phase 4: portfolio and research tools

```text
- asset allocation modules
- risk models
- optimization
- regime classification
- scenario simulation
- dashboard-ready data marts
```

### phase 5: automation

```text
- scheduled ingestion jobs
- data quality checks
- logging and monitoring
- automatic parquet refresh
- automatic duckdb table refresh
```

---

## 12. Current Status

The project currently has:

```text
- metadata master file
- freight data transformation pipeline
- macro data transformation pipeline
- parquet-based raw data lake
- duckdb-based database structure
- dictionary-table convention
- release-date and release-time aware schema design
```

The next development priority is to formalize the Python service layer and make data access easier from notebooks, research scripts, and dashboards.

---

## Disclaimer

This project is for private financial research, data engineering practice, and personal investment research infrastructure. It is not investment advice and should not be used as the sole basis for trading or allocation decisions.
