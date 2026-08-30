from __future__ import annotations

import numpy as np

from .algorithms import estimates, optimize_black_litterman, optimize_hrp, optimize_mvo, optimize_nco
from .data import AllocationData


class AllocationService:
    def __init__(self, database_path): self.data = AllocationData(database_path)

    def universe(self): return self.data.universe()

    def optimize(self, request):
        asset_ids = request.get("assetIds") or []
        if len(asset_ids) < 2: raise ValueError("Select at least two assets")
        method = request.get("method", "mvo"); params = request.get("params") or {}
        risk_free = float(request.get("riskFreeRate", 3.5)) / 100
        prices, returns = self.data.prices(asset_ids, request.get("lookbackYears", 5))
        mu, cov = estimates(returns, params.get("covEstimator", "sample"))
        clusters = None
        if method == "mvo":
            weights = optimize_mvo(mu, cov, params.get("objective", "mean_variance"), params.get("riskAversion", 2), risk_free,
                                   params.get("minWeight", 0), params.get("maxWeight", 1), params.get("longOnly", True))
        elif method == "hrp": weights = optimize_hrp(returns, params.get("linkage", "ward"), params.get("distanceMetric", "pearson"))
        elif method == "nco": weights, clusters = optimize_nco(returns, params.get("nClusters", 3), params.get("withinCluster", "mvo"), params.get("covEstimator", "sample"), risk_free)
        elif method == "bl": weights = optimize_black_litterman(returns, params.get("views", []), asset_ids, params.get("delta", 2.5), params.get("tau", 0.05), risk_free, params.get("objective", "max_sharpe"))
        else: raise ValueError(f"Unknown method: {method}")
        portfolio = returns.values @ weights
        annual_return = float(np.mean(portfolio) * 252); annual_vol = float(np.std(portfolio, ddof=1) * np.sqrt(252))
        wealth = np.cumprod(1 + portfolio); drawdowns = wealth / np.maximum.accumulate(wealth) - 1
        downside = portfolio[portfolio < 0]; sortino_den = np.std(downside, ddof=1) * np.sqrt(252) if len(downside) > 1 else np.nan
        losses = -portfolio; var = float(np.quantile(losses, .95)); tail = losses[losses >= var]
        metrics = {"ret": annual_return * 100, "vol": annual_vol * 100,
                   "sharpe": (annual_return - risk_free) / annual_vol if annual_vol else 0,
                   "maxDD": float(drawdowns.min() * 100), "calmar": annual_return / abs(drawdowns.min()) if drawdowns.min() else 0,
                   "sortino": (annual_return - risk_free) / sortino_den if sortino_den and np.isfinite(sortino_den) else 0,
                   "var95": -var * np.sqrt(21) * 100, "cvar95": -float(tail.mean() if len(tail) else var) * np.sqrt(21) * 100,
                   "rf": risk_free * 100}
        asset_stats = {asset_id: {"expectedReturn": float(mu[i] * 100), "volatility": float(np.sqrt(cov[i, i]) * 100)} for i, asset_id in enumerate(asset_ids)}
        frontier = []
        for target in np.linspace(float(mu.min()), float(mu.max()), 30):
            try:
                w = optimize_mvo(mu, cov, "min_variance", risk_free=risk_free, target_return=target)
                frontier.append({"x": float(np.sqrt(w @ cov @ w) * 100), "y": float(w @ mu * 100)})
            except ValueError: pass
        return {"method": method, "weights": dict(zip(asset_ids, map(float, weights))), "metrics": metrics,
                "correlation": returns.corr().fillna(0).values.tolist(), "frontier": frontier, "assetStats": asset_stats,
                "clusters": clusters, "sample": {"start": str(returns.index.min()), "end": str(returns.index.max()), "observations": len(returns)}}
