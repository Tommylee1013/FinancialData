from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.optimize import minimize
from scipy.spatial.distance import squareform
from sklearn.cluster import AgglomerativeClustering
from sklearn.covariance import LedoitWolf, OAS

TRADING_DAYS = 252

def estimates(returns: pd.DataFrame, estimator="sample"):
    mu = returns.mean().values * TRADING_DAYS
    if estimator == "ledoit": cov = LedoitWolf().fit(returns).covariance_ * TRADING_DAYS
    elif estimator == "oas": cov = OAS().fit(returns).covariance_ * TRADING_DAYS
    else: cov = returns.cov().values * TRADING_DAYS
    return mu, cov


def _bounds(n, min_weight=0.0, max_weight=1.0, long_only=True):
    lower = max(0.0, min_weight) if long_only else min_weight
    if lower * n > 1 + 1e-9 or max_weight * n < 1 - 1e-9:
        raise ValueError("Weight constraints are infeasible for the selected asset count")
    return [(lower, max_weight)] * n


def optimize_mvo(mu, cov, objective="mean_variance", risk_aversion=2.0, risk_free=0.035,
                 min_weight=0.0, max_weight=1.0, long_only=True, target_return=None):
    n = len(mu); x0 = np.repeat(1 / n, n); bounds = _bounds(n, min_weight, max_weight, long_only)
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    if target_return is not None:
        constraints.append({"type": "eq", "fun": lambda w: float(w @ mu) - target_return})
    def variance(w): return float(w @ cov @ w)
    if objective == "min_variance" or target_return is not None: fun = variance
    elif objective == "max_sharpe": fun = lambda w: -float((w @ mu - risk_free) / max(np.sqrt(variance(w)), 1e-12))
    else: fun = lambda w: float(0.5 * risk_aversion * variance(w) - w @ mu)
    result = minimize(fun, x0, method="SLSQP", bounds=bounds, constraints=constraints,
                      options={"maxiter": 1000, "ftol": 1e-11})
    if not result.success: raise ValueError(f"Optimization failed: {result.message}")
    weights = np.clip(result.x, bounds[0][0], bounds[0][1]); return weights / weights.sum()


def optimize_hrp(returns, method="ward", metric="pearson"):
    corr = returns.corr(method=metric).fillna(0).values
    distance = np.sqrt(np.clip((1 - corr) / 2, 0, 1))
    condensed = squareform(distance, checks=False)
    order = leaves_list(linkage(condensed, method=method))
    cov = returns.cov().values * TRADING_DAYS
    weights = np.ones(len(order)); clusters = [list(order)]
    def cluster_variance(indices):
        sub = cov[np.ix_(indices, indices)]; inv = 1 / np.clip(np.diag(sub), 1e-12, None); w = inv / inv.sum()
        return float(w @ sub @ w)
    while clusters:
        next_clusters = []
        for cluster in clusters:
            if len(cluster) <= 1: continue
            split = len(cluster) // 2; left, right = cluster[:split], cluster[split:]
            left_var, right_var = cluster_variance(left), cluster_variance(right)
            alpha = 1 - left_var / (left_var + right_var)
            weights[left] *= alpha; weights[right] *= 1 - alpha
            next_clusters.extend([left, right])
        clusters = next_clusters
    return weights / weights.sum()


def optimize_nco(returns, n_clusters=3, within="mvo", estimator="sample", risk_free=0.035):
    n = returns.shape[1]; n_clusters = max(2, min(int(n_clusters), n))
    corr = returns.corr().fillna(0).values; distance = np.sqrt(np.clip((1 - corr) / 2, 0, 1))
    labels = AgglomerativeClustering(n_clusters=n_clusters, metric="precomputed", linkage="average").fit_predict(distance)
    inner = np.zeros((n, n_clusters))
    for cluster in range(n_clusters):
        members = np.where(labels == cluster)[0]; sub = returns.iloc[:, members]; mu, cov = estimates(sub, estimator)
        if within == "equal": local = np.repeat(1 / len(members), len(members))
        elif within == "ivp":
            inv = 1 / np.clip(np.diag(cov), 1e-12, None); local = inv / inv.sum()
        else: local = optimize_mvo(mu, cov, "max_sharpe", risk_free=risk_free)
        inner[members, cluster] = local
    cluster_returns = pd.DataFrame(returns.values @ inner, index=returns.index)
    cluster_mu, cluster_cov = estimates(cluster_returns, estimator)
    outer = optimize_mvo(cluster_mu, cluster_cov, "min_variance", risk_free=risk_free)
    weights = inner @ outer; return weights / weights.sum(), labels.tolist()


def optimize_black_litterman(returns, views, asset_ids, delta=2.5, tau=0.05, risk_free=0.035, objective="max_sharpe"):
    _, cov = estimates(returns, "ledoit"); n = len(asset_ids); market = np.repeat(1 / n, n)
    pi = delta * cov @ market
    valid = [view for view in views if view.get("assetId") in asset_ids]
    if valid:
        p = np.zeros((len(valid), n)); q = np.zeros(len(valid)); omega = np.zeros((len(valid), len(valid)))
        for row, view in enumerate(valid):
            idx = asset_ids.index(view["assetId"]); p[row, idx] = 1
            magnitude = float(view.get("magnitude", 0)) / 100
            q[row] = magnitude if view.get("direction") == "up" else -magnitude
            confidence = np.clip(float(view.get("confidence", 50)) / 100, 0.01, 0.99)
            omega[row, row] = float(p[row] @ (tau * cov) @ p[row]) * (1 - confidence) / confidence
        tau_cov_inv = np.linalg.pinv(tau * cov); omega_inv = np.linalg.pinv(omega)
        posterior_cov = np.linalg.pinv(tau_cov_inv + p.T @ omega_inv @ p)
        posterior = posterior_cov @ (tau_cov_inv @ pi + p.T @ omega_inv @ q)
    else: posterior = pi
    return optimize_mvo(posterior, cov, objective, risk_aversion=delta, risk_free=risk_free)
