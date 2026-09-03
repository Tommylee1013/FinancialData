from __future__ import annotations

import time

import pandas as pd
from tvDatafeed import Interval, TvDatafeed


def fetch_daily(tv: TvDatafeed, symbol: str, exchange: str, n_bars: int = 5000, retries: int = 5) -> pd.DataFrame:
    error = None
    for attempt in range(retries):
        try:
            raw = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=n_bars)
            if raw is None or raw.empty: raise ValueError("TradingView returned no data")
            return normalize_ohlc(raw, symbol, exchange)
        except Exception as exc:
            error = exc
            if attempt + 1 < retries: time.sleep(1.0)
    raise RuntimeError(f"Unable to download {exchange}:{symbol} after {retries} attempts") from error


def normalize_ohlc(raw: pd.DataFrame, symbol: str, exchange: str) -> pd.DataFrame:
    frame = raw.copy(); frame.columns = [str(column).lower() for column in frame.columns]
    index = pd.to_datetime(frame.index)
    if index.tz is not None: index = index.tz_convert("UTC").tz_localize(None)
    zone = "America/Chicago" if exchange.upper() == "CBOT" else "UTC"
    output = pd.DataFrame({
        "base_date": index.date, "release_date": index.date, "time": index.time,
        "time_zone": zone, "symbol": symbol, "exchange": exchange.upper(), "country": "United States",
        "open": frame["open"].to_numpy(), "high": frame["high"].to_numpy(),
        "low": frame["low"].to_numpy(), "close": frame["close"].to_numpy(),
    })
    return output.drop_duplicates(["base_date", "symbol", "exchange"], keep="last").sort_values("base_date")
