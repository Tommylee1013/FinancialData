from __future__ import annotations

import numpy as np
import pandas as pd

from allocation.algorithms import estimates, optimize_black_litterman, optimize_hrp, optimize_mvo, optimize_nco
from allocation.data import AllocationData


FREQUENCIES = {"monthly", "quarterly", "semiannual", "annual"}


class WalkForwardBacktester:
    def __init__(self, database_path):
        self.data = AllocationData(database_path)

    def _weights(self, method, returns, asset_ids, params, risk_free):
        mu, cov = estimates(returns, params.get("covEstimator", "sample"))
        if method == "mvo":
            return optimize_mvo(mu, cov, params.get("objective", "max_sharpe"), params.get("riskAversion", 2), risk_free,
                                params.get("minWeight", 0), params.get("maxWeight", 1), params.get("longOnly", True))
        if method == "hrp":
            return optimize_hrp(returns, params.get("linkage", "ward"), params.get("distanceMetric", "pearson"))
        if method == "nco":
            return optimize_nco(returns, params.get("nClusters", 3), params.get("withinCluster", "mvo"),
                                params.get("covEstimator", "sample"), risk_free)[0]
        if method == "bl":
            return optimize_black_litterman(returns, params.get("views", []), asset_ids, params.get("delta", 2.5),
                                            params.get("tau", 0.05), risk_free, params.get("objective", "max_sharpe"))
        raise ValueError(f"Unknown method: {method}")

    @staticmethod
    def _metrics(returns, risk_free):
        returns = np.asarray(returns, dtype=float); wealth = np.cumprod(1 + returns)
        years = max(len(returns) / 252, 1 / 252); cagr = wealth[-1] ** (1 / years) - 1
        volatility = np.std(returns, ddof=1) * np.sqrt(252)
        drawdown = wealth / np.maximum.accumulate(wealth) - 1
        return {"cagr": float(cagr * 100), "volatility": float(volatility * 100),
                "sharpe": float((cagr - risk_free) / volatility if volatility else 0),
                "maxDrawdown": float(drawdown.min() * 100), "totalReturn": float((wealth[-1] - 1) * 100)}

    def run(self, request):
        asset_ids = request.get("assetIds") or []
        if len(asset_ids) < 2: raise ValueError("Select at least two assets")
        frequency = request.get("rebalance", "quarterly")
        if frequency not in FREQUENCIES: raise ValueError("Unsupported rebalancing frequency")
        method = request.get("method", "mvo"); params = request.get("params") or {}
        risk_free = float(request.get("riskFreeRate", 3.5)) / 100
        training_days = int(request.get("trainingDays", 504)); history_years = int(request.get("historyYears", 10))
        transaction_cost = float(request.get("transactionCostBps", 10)) / 10000
        _, returns = self.data.prices(asset_ids, history_years)
        if frequency == "monthly": periods = [f"{date.year}-{date.month:02d}" for date in returns.index]
        elif frequency == "quarterly": periods = [f"{date.year}-Q{date.quarter}" for date in returns.index]
        elif frequency == "semiannual": periods = [f"{date.year}-H{1 if date.month <= 6 else 2}" for date in returns.index]
        else: periods = [str(date.year) for date in returns.index]
        candidate_dates = returns.groupby(periods).head(1).index
        first_oos_date = returns.index[training_days]
        rebalance_dates = [first_oos_date] + [date for date in candidate_dates if date > first_oos_date]
        if len(rebalance_dates) < 2: raise ValueError("Insufficient history for walk-forward backtesting")
        portfolio = pd.Series(index=returns.index, dtype=float); benchmark = returns.mean(axis=1)
        previous = np.zeros(len(asset_ids)); weights_history = []; total_turnover = 0.0
        for index, date in enumerate(rebalance_dates):
            location = returns.index.get_loc(date); train = returns.iloc[max(0, location - training_days):location]
            weights = self._weights(method, train, asset_ids, params, risk_free)
            turnover = float(np.abs(weights - previous).sum()) if previous.any() else 1.0
            total_turnover += turnover; end = rebalance_dates[index + 1] if index + 1 < len(rebalance_dates) else returns.index[-1] + pd.Timedelta(days=1)
            mask = (returns.index >= date) & (returns.index < end); period_returns = returns.loc[mask].values @ weights
            if len(period_returns): period_returns[0] -= turnover * transaction_cost
            portfolio.loc[mask] = period_returns
            weights_history.append({"date": str(date.date()), "turnover": turnover,
                                    "weights": dict(zip(asset_ids, map(float, weights)))})
            previous = weights
        portfolio = portfolio.dropna(); benchmark = benchmark.loc[portfolio.index]
        portfolio_wealth = (1 + portfolio).cumprod(); benchmark_wealth = (1 + benchmark).cumprod()
        portfolio_dd = portfolio_wealth / portfolio_wealth.cummax() - 1
        series = [{"date": str(date.date()), "portfolio": float(portfolio_wealth.loc[date] * 100),
                   "benchmark": float(benchmark_wealth.loc[date] * 100), "drawdown": float(portfolio_dd.loc[date] * 100)}
                  for date in portfolio.index]
        return {"series": series, "portfolioMetrics": self._metrics(portfolio.values, risk_free),
                "benchmarkMetrics": self._metrics(benchmark.values, risk_free), "weightsHistory": weights_history,
                "summary": {"method": method, "rebalance": frequency, "trainingDays": training_days,
                            "transactionCostBps": transaction_cost * 10000, "rebalanceCount": len(weights_history),
                            "averageTurnover": total_turnover / len(weights_history), "start": series[0]["date"], "end": series[-1]["date"]}}
