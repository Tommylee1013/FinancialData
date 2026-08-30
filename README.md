# FinancialData 

Local financial-data platform and research dashboard built around DuckDB. It collects and standardizes market, fixed-income, FX, macro, commodity, freight, industry, volatility, and alternative datasets, then exposes them through a professional web interface.

## What is included

- **FinDash** — React/Vite dashboard with overview, market, fixed income, supply chain, macro, commodities, industry, asset allocation, and AI research pages.
- **Local data platform** — metadata-driven ETL jobs, Parquet data lake, and read-only DuckDB analytics.
- **Interactive research** — detail pages, adjustable date ranges, TradingView-style market charts, technical indicators, yield curves, sentiment, sector views, and global ticker tape.
- **Portfolio allocation** — Markowitz MVO (mean variance, minimum variance, maximum Sharpe), HRP, NCO, and Black–Litterman using eligible Market, Bond, and FX data.
- **Risk analytics** — efficient frontier, allocation metrics, correlation heatmap, correlation-distance minimum-spanning tree, and walk-forward backtesting with selectable rebalancing frequency.
- **AI Research** — isolated research-agent backend with persisted conversations and allowlisted, read-only financial-data tools.

## Project structure

```text
FinancialData/
├── FinDash/          # React frontend and local API server
├── src/
│   ├── dataloader/   # Data ingestion and normalization
│   ├── jobs_api/     # API-based collection jobs
│   ├── jobs_xlsx/    # Spreadsheet ingestion jobs
│   ├── service/      # Data access services
│   ├── indicators/   # Analytical indicators
│   ├── allocation/   # Portfolio optimization engines
│   ├── backtest/     # Walk-forward backtesting
│   └── agent/        # AI research agent
├── data_lake/        # Standardized Parquet datasets
├── database/         # DuckDB and chat-history storage
├── config/           # Local configuration and API keys
└── METADATA.xlsx     # Dataset master metadata
```

## Run FinDash

Open two terminals:

```bash
cd FinDash
npm install
npm run api
```

```bash
cd FinDash
npm run dev
```

Then open `http://localhost:5173`. The API runs at `http://127.0.0.1:8787` and reads `database/alternative_data.duckdb` in read-only mode. Use `FINDASH_DB_PATH` to override the database location.

## Notes

- Update `METADATA.xlsx` when adding datasets so categories, names, units, countries, and routing remain complete.
- Portfolio inputs are restricted to investable Market, Bond, and FX series; macro and analytical indices are excluded.
- Keep API credentials local under `config/` or environment variables. Do not commit secrets or generated database files.
- Component-specific details are documented in `src/agent`, `src/allocation`, `src/backtest`, and `FinDash`.
