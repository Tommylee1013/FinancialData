# FinDash Allocation Engine

Real portfolio optimization using read-only series from `alternative_data.duckdb`.

The eligible universe is restricted to Market, Bond, and FX assets. Non-investable analytical series such as macro, industry, volatility, and freight indices are excluded. Government yield series are converted to approximate bond total returns using carry plus a duration-based price change before optimization.

The Market universe is discovered dynamically from every `market.index_data` symbol with at least 60 observations and enriched with the instrument metadata catalog. The UI therefore expands automatically when a new eligible equity index is loaded into DuckDB.

- Markowitz: mean–variance, minimum variance, and maximum Sharpe
- HRP: hierarchical clustering and recursive bisection
- NCO: clustered inner/outer optimization with sample, Ledoit–Wolf, or OAS covariance
- Black–Litterman: equilibrium returns blended with confidence-weighted absolute views

The frontend sends asset IDs and parameters to `/api/allocation/optimize`. Results include weights, realized sample statistics, correlation, efficient frontier, and the exact data window used.
