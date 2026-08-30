# FinDash Walk-Forward Backtesting

The backtester uses only information available before each rebalance date:

1. Load a trailing 504-observation training window.
2. Re-estimate the selected allocation model.
3. Hold the resulting weights until the next monthly, quarterly, semiannual, or annual rebalance.
4. Deduct turnover-based transaction costs at each rebalance.
5. Compare against an equal-weight buy-and-rebalance benchmark.

The implementation is managed independently under `src/backtest` and reuses the production algorithms in `src/allocation`.
