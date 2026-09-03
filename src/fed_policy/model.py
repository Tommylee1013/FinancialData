from __future__ import annotations

import numpy as np
import pandas as pd


def month_weights(meeting_date: str | pd.Timestamp) -> tuple[int, int, int]:
    meeting = pd.Timestamp(meeting_date)
    start = meeting.replace(day=1)
    days = (start + pd.offsets.MonthEnd(0) - start).days + 1
    before = (meeting - start).days
    return days, before, days - before


def calculate_meeting_probabilities(
    futures_close: pd.Series,
    effective_rate: pd.Series,
    meeting_date: str | pd.Timestamp,
    scenarios_bp: tuple[int, ...] = (-100, -75, -50, -25, 0, 25, 50, 75, 100),
    moving_average_window: int = 5,
    smooth_last_days: int = 20,
) -> pd.DataFrame:
    """Convert a meeting-month ZQ contract into discrete policy-move probabilities."""
    meeting = pd.Timestamp(meeting_date).normalize()
    prices = futures_close.dropna().sort_index().copy()
    prices.index = pd.to_datetime(prices.index).normalize()
    rates = effective_rate.dropna().sort_index().copy()
    rates.index = pd.to_datetime(rates.index).normalize()
    rates = rates.reindex(prices.index, method="ffill")
    valid = rates.notna() & (prices.index <= meeting)
    prices, rates = prices[valid], rates[valid]
    if prices.empty:
        return pd.DataFrame()

    expiry = meeting.replace(day=1) + pd.offsets.BMonthEnd(0)
    smoothed = prices.rolling(max(1, moving_average_window), min_periods=1).mean()
    days_to_expiry = pd.Series((expiry - prices.index).days, index=prices.index)
    used = prices.where(days_to_expiry > smooth_last_days, smoothed)
    total_days, before_days, after_days = month_weights(meeting)
    scenarios = np.asarray(scenarios_bp, dtype=float)
    result = []

    for observation_date, price in used.items():
        current_rate = float(rates.loc[observation_date])
        implied_rate = 100.0 - float(price)
        scenario_rates = current_rate + scenarios / 100.0
        monthly_rates = (before_days * current_rate + after_days * scenario_rates) / total_days
        order = np.argsort(monthly_rates)
        ordered_rates = monthly_rates[order]
        probabilities = np.zeros(len(scenarios))
        if implied_rate <= ordered_rates[0]:
            probabilities[order[0]] = 1.0
        elif implied_rate >= ordered_rates[-1]:
            probabilities[order[-1]] = 1.0
        else:
            lower = int(np.searchsorted(ordered_rates, implied_rate) - 1)
            upper = lower + 1
            weight_upper = (implied_rate - ordered_rates[lower]) / (ordered_rates[upper] - ordered_rates[lower])
            probabilities[order[lower]] = 1.0 - weight_upper
            probabilities[order[upper]] = weight_upper
        for scenario, probability in zip(scenarios.astype(int), probabilities):
            result.append({"base_date": observation_date.date(), "meeting_date": meeting.date(),
                           "scenario_bp": int(scenario), "probability": float(probability),
                           "futures_price": float(price), "implied_rate": implied_rate,
                           "effective_rate": current_rate})
    return pd.DataFrame(result)
