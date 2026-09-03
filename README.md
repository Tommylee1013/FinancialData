# FinancialData

FinancialData is a local-first financial data platform and research terminal built around DuckDB. It brings market prices, macroeconomic releases, fixed income, foreign exchange, industry indicators, supply-chain data, sentiment, and portfolio analytics into one consistent data model and a professional web dashboard.

The project was created as a personal research system: raw observations are collected from multiple sources, standardized with shared metadata and timestamps, stored locally, and exposed for analysis without depending on a hosted database.

## Data coverage

- **Equities and indices** — major US, Korean, Japanese, Chinese, Hong Kong, and European indices, regional benchmarks, and detailed sector indices.
- **Foreign exchange** — major currency pairs and currency indices, including dollar, yen, euro, pound, and other regional currency series.
- **Fixed income** — US and Korean government yields, yield curves, and maturity-level rate histories.
- **Macroeconomics** — inflation, labor, growth, manufacturing, trade, liquidity, and central-bank-related indicators across multiple countries.
- **Volatility and sentiment** — VIX-family indices, MOVE, SKEW, VKOSPI, NKVI, CNN Fear & Greed, AAII sentiment, and NAAIM exposure where available.
- **Commodities** — energy, precious and industrial metals, agricultural products, and broad commodity indices.
- **Supply chain and freight** — BDI, BCI, BHSI, BDTI, CCFI, SCFI, WCI, air freight, rail, LNG, and LPG shipping indicators.
- **Industry data** — semiconductor and memory pricing, materials, energy, manufacturing, and other industry-specific series, including unified average/high/low observations.
- **Federal Reserve policy** — Fed funds futures, effective fed funds rates, FOMC meeting dates sourced from FDTR, and modeled meeting-by-meeting target-rate probabilities.

## Data design principles

Data from different providers rarely arrives in the same shape. The ingestion layer therefore makes datasets comparable and traceable before they reach the dashboard.

- `METADATA.xlsx` is the master catalog for symbols, names, countries, asset classes, categories, units, frequencies, and sources.
- Every observation follows shared temporal fields such as `base_date`, `release_date`, `time`, and `time_zone` where applicable.
- Price-like instruments use consistent OHLC fields, while indicators preserve their reported values and release information.
- Asset classes and countries are normalized so newly added datasets can appear in the correct dashboard section.
- Data is stored in domain-specific DuckDB schemas and standardized Parquet datasets rather than one flat table.
- Collection and presentation are separated; the dashboard reads the analytical database in read-only mode.
- Historical observations are retained. Charts receive the complete available history while opening on a practical recent window where appropriate.
- Credentials remain local under `config/` or environment variables and should never be committed.

## FinDash

FinDash is the React/Vite interface for exploring the database. It currently includes:

- **Overview** — global ticker tape, cross-market snapshots, key macro signals, and compact market monitoring.
- **Market** — country tabs, indices and sectors, TradingView-style candlestick charts, 5-day moving average, 20-day Bollinger Bands, volatility, and sentiment.
- **Fixed Income** — country-based yield curves and instrument detail pages.
- **Foreign Exchange** — regional and country filters, searchable instruments, market statistics, and full-history OHLC charts.
- **Supply Chain** — indicator- and country-based organization, group comparisons, freight signals, and a global map.
- **Macro** — country and topic classification, releases, historical charts, custom date ranges, and indicator detail pages.
- **Commodities** — category views, price histories, cross-commodity signals, and detail pages.
- **Industry** — organized industry groups, comparison charts, and consolidated average/high/low histories.
- **FedWatch** — FOMC meeting selection, cut/hold/hike probabilities, target-rate scenarios, probability history, implied rates, and Fed funds futures charts.
- **Asset Allocation** — Markowitz mean variance, minimum variance, maximum Sharpe, HRP, NCO, and Black–Litterman using eligible Market, Bond, and FX assets.
- **Portfolio Research** — allocation metrics, efficient frontier, correlation heatmap, correlation-distance tree network, and walk-forward backtesting with selectable rebalancing.
- **AI Research** — a research agent with persisted conversations and allowlisted, read-only access to financial data.

Major series have dedicated detail views with real dates, adaptive Y-axis scaling, full available history, predefined ranges, and custom date selection.

## Architecture

```text
FinancialData/
├── FinDash/          # React frontend and local API server
├── src/
│   ├── dataloader/   # Data ingestion and normalization
│   ├── jobs_api/     # API-based collection jobs
│   ├── jobs_xlsx/    # Spreadsheet ingestion jobs
│   ├── service/      # Domain data services
│   ├── indicators/   # Analytical indicators
│   ├── fed_policy/   # Fed futures and policy probabilities
│   ├── allocation/   # Portfolio optimization engines
│   ├── backtest/     # Walk-forward backtesting
│   └── agent/        # AI research agent
├── catalogs/         # Dataset catalogs
├── config/           # Job configuration and local credentials
├── data_lake/        # Standardized Parquet datasets
├── database/         # DuckDB and conversation storage
├── logs/             # Collection and build logs
└── METADATA.xlsx     # Instrument master metadata
```

## Running FinDash

Open two terminals from the project root:

```bash
cd FinDash
npm install
npm run api
```

```bash
cd FinDash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The API runs at `http://127.0.0.1:8787` and reads `database/alternative_data.duckdb` in read-only mode. Set `FINDASH_DB_PATH` to use a different database.

## Adding data

When introducing a series, add or update its entry in `METADATA.xlsx`, preserve the shared time fields, place it in the appropriate domain schema, and confirm its unit and frequency before rebuilding the master table. This lets the API and dashboard classify the series without page-specific hard-coding.

Portfolio inputs are intentionally restricted to investable Market, Bond, and FX series. Macroeconomic, sentiment, volatility, and analytical indices remain available for research but are excluded from direct allocation.

## Status

FinancialData is an actively evolving personal research platform focused on reliable local data ownership, broad cross-asset coverage, transparent analytics, and turning a growing historical database into a practical daily research workflow.
