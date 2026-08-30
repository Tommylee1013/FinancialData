from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


ASSETS = {
    "us_eq": {"name": "US Equities", "ticker": "SPX", "assetClass": "Market", "table": "market.index_data", "symbol": "SP500", "field": "close", "region": "United States", "color": "#1A56DB"},
    "kr_eq": {"name": "Korea Equities", "ticker": "KOSPI", "assetClass": "Market", "table": "market.index_data", "symbol": "KOSPI", "field": "close", "region": "South Korea", "color": "#3B82F6"},
    "jp_eq": {"name": "Japan Equities", "ticker": "N225", "assetClass": "Market", "table": "market.index_data", "symbol": "NI225", "field": "close", "region": "Japan", "color": "#60A5FA"},
    "cn_eq": {"name": "China Equities", "ticker": "CSI300", "assetClass": "Market", "table": "market.index_data", "symbol": "CSI300", "field": "close", "region": "China", "color": "#F59E0B"},
    "us_small": {"name": "US Small Cap", "ticker": "RUS2000", "assetClass": "Market", "table": "market.index_data", "symbol": "RUS2000", "field": "close", "region": "United States", "color": "#06B6D4"},
    "semi": {"name": "Semiconductors", "ticker": "SOX", "assetClass": "Market", "table": "market.index_data", "symbol": "SOX", "field": "close", "region": "United States", "color": "#8B5CF6"},
    "reit": {"name": "US Real Estate", "ticker": "SPX RE", "assetClass": "Market", "table": "market.index_data", "symbol": "SPX50060", "field": "close", "region": "United States", "color": "#A855F7"},
    "kr_bond_3y": {"name": "Korea Treasury 3Y", "ticker": "KTB 3Y", "assetClass": "Bond", "table": "fixed_income.fixed_income_data", "symbol": "KTB03", "field": "value", "transform": "yield", "duration": 2.7, "region": "South Korea", "color": "#22C55E"},
    "kr_bond_10y": {"name": "Korea Treasury 10Y", "ticker": "KTB 10Y", "assetClass": "Bond", "table": "fixed_income.fixed_income_data", "symbol": "KTB10", "field": "value", "transform": "yield", "duration": 8.2, "region": "South Korea", "color": "#15803D"},
    "dxy": {"name": "US Dollar Index", "ticker": "DXY", "assetClass": "FX", "table": "market.fx_data", "symbol": "DXY", "field": "close", "region": "FX", "color": "#16A34A"},
    "jxy": {"name": "Japanese Yen Index", "ticker": "JXY", "assetClass": "FX", "table": "market.fx_data", "symbol": "JXY", "field": "close", "region": "FX", "color": "#E11D48"},
    "exy": {"name": "Euro Currency Index", "ticker": "EXY", "assetClass": "FX", "table": "market.fx_data", "symbol": "EXY", "field": "close", "region": "FX", "color": "#0EA5E9"},
}


class AllocationData:
    def __init__(self, database_path: Path | str):
        self.database_path = str(database_path)
        self.assets = dict(ASSETS)
        self._load_market_universe()

    def _load_market_universe(self):
        known_symbols = {meta["symbol"] for meta in self.assets.values() if meta.get("table") == "market.index_data"}
        palette = ["#2563EB", "#7C3AED", "#0891B2", "#D97706", "#DC2626", "#059669", "#4F46E5", "#C026D3"]
        with duckdb.connect(self.database_path, read_only=True) as con:
            rows = con.execute("""
              select d.symbol, count(*) as observations, any_value(m.name) as instrument_name,
                     any_value(m.country) as instrument_country, any_value(m.category) as instrument_category
              from market.index_data d left join metadata.instrument_master m using(symbol)
              where d.close is not null group by d.symbol having count(*) >= 60 order by d.symbol
            """).fetchall()
        for index, (symbol, _, name, country, category) in enumerate(rows):
            if symbol in known_symbols:
                continue
            asset_id = f"market_{symbol.lower()}"
            self.assets[asset_id] = {"name": name or symbol, "ticker": symbol, "assetClass": "Market",
                                     "table": "market.index_data", "symbol": symbol, "field": "close",
                                     "region": country or "Global", "category": category or "Equity Index",
                                     "color": palette[index % len(palette)]}

    def universe(self):
        visible = ("name", "ticker", "assetClass", "region", "category", "color")
        rows = [{"id": asset_id, **{key: meta.get(key) for key in visible}} for asset_id, meta in self.assets.items()]
        return sorted(rows, key=lambda row: ({"Market": 0, "Bond": 1, "FX": 2}.get(row["assetClass"], 9), row["region"], row["name"]))

    def prices(self, asset_ids, lookback_years=5):
        unknown = set(asset_ids) - set(self.assets)
        if unknown:
            raise ValueError(f"Unknown assets: {', '.join(sorted(unknown))}")
        frames = []
        with duckdb.connect(self.database_path, read_only=True) as con:
            for asset_id in asset_ids:
                meta = self.assets[asset_id]
                rows = con.execute(f"""
                  select base_date, {meta['field']} from {meta['table']}
                  where symbol=? and {meta['field']} is not null
                  order by base_date
                """, [meta["symbol"]]).fetchall()
                if len(rows) < 60:
                    raise ValueError(f"Insufficient observations for {meta['ticker']}")
                frame = pd.DataFrame(rows, columns=["date", asset_id]).drop_duplicates("date", keep="last").set_index("date")
                if meta.get("transform") == "yield":
                    yields = frame[asset_id].astype(float) / 100
                    bond_returns = -float(meta["duration"]) * yields.diff() + yields.shift(1) / 252
                    frame[asset_id] = 100 * (1 + bond_returns.fillna(0)).cumprod()
                frames.append(frame)
        prices = pd.concat(frames, axis=1).sort_index().ffill(limit=10)
        prices.index = pd.to_datetime(prices.index)
        if lookback_years:
            cutoff = prices.index.max() - pd.DateOffset(years=int(lookback_years))
            prices = prices.loc[prices.index >= cutoff]
        prices = prices.dropna()
        if len(prices) < 60:
            raise ValueError("Selected assets do not have enough overlapping history")
        returns = prices.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).dropna()
        return prices, returns
