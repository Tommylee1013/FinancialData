from __future__ import annotations

import duckdb
import numpy as np


SERIES_TABLES = [
    ("market.index_data", "close"), ("market.volatility_data", "close"),
    ("market.fx_data", "close"), ("fixed_income.fixed_income_data", "value"),
    ("freight.freight_data", "value"), ("industry.index_data", "value"),
    ("behavior.behavior_data", "value"), ("macro.macro_data", "actual"),
]

TOOL_DEFINITIONS = [
    {"type": "function", "name": "search_instruments", "description": "Search the FinDash instrument catalog by symbol or name.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}}, "required": ["query"], "additionalProperties": False}},
    {"type": "function", "name": "get_financial_series", "description": "Load a financial time series from the read-only FinDash DuckDB.",
     "parameters": {"type": "object", "properties": {"symbol": {"type": "string"}, "limit": {"type": "integer", "minimum": 2, "maximum": 1000}}, "required": ["symbol"], "additionalProperties": False}},
    {"type": "function", "name": "get_market_snapshot", "description": "Get the latest and previous observations for multiple symbols.",
     "parameters": {"type": "object", "properties": {"symbols": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 20}}, "required": ["symbols"], "additionalProperties": False}},
]


class FinancialTools:
    def __init__(self, database_path):
        self.database_path = str(database_path)

    def _connect(self):
        return duckdb.connect(self.database_path, read_only=True)

    def search_instruments(self, query, limit=10):
        with self._connect() as con:
            rows = con.execute("""
              select symbol, name, asset_class, category, country, unit, frequency
              from metadata.instrument_master
              where lower(symbol) like ? or lower(name) like ?
              order by case when lower(symbol)=? then 0 else 1 end, symbol limit ?
            """, [f"%{query.lower()}%", f"%{query.lower()}%", query.lower(), min(limit, 20)]).fetchall()
        keys = ["symbol", "name", "asset_class", "category", "country", "unit", "frequency"]
        return [dict(zip(keys, row)) for row in rows]

    def get_financial_series(self, symbol, limit=240):
        symbol = symbol.upper().strip()
        with self._connect() as con:
            for table, field in SERIES_TABLES:
                exists = con.execute(f"select count(*) from {table} where symbol=? and {field} is not null", [symbol]).fetchone()[0]
                if exists:
                    rows = con.execute(f"""select base_date, {field} from {table} where symbol=? and {field} is not null
                                          order by base_date desc, release_date desc, time desc limit ?""",
                                       [symbol, min(limit, 1000)]).fetchall()
                    return {"symbol": symbol, "table": table, "observations":
                            [{"date": row[0], "value": row[1]} for row in reversed(rows)]}
        return {"symbol": symbol, "error": "Series not found"}

    def get_market_snapshot(self, symbols):
        results = []
        for symbol in symbols[:20]:
            series = self.get_financial_series(symbol, 2)
            observations = series.get("observations", [])
            if observations:
                latest, previous = observations[-1], observations[-2] if len(observations) > 1 else observations[-1]
                change = latest["value"] - previous["value"]
                results.append({"symbol": symbol.upper(), "date": latest["date"], "value": latest["value"],
                                "change": change, "change_pct": change / previous["value"] * 100 if previous["value"] else 0})
            else:
                results.append({"symbol": symbol.upper(), "error": "Series not found"})
        return results

    def quantify_risk(self, symbol, limit=250, confidence=0.95, window=20):
        series = self.get_financial_series(symbol, min(max(int(limit), 30), 1000))
        observations = series.get("observations", [])
        values = np.asarray([float(row["value"]) for row in observations], dtype=float)
        values = values[np.isfinite(values)]
        if len(values) < 30:
            return {"symbol": symbol.upper(), "error": "At least 31 valid observations are required"}
        returns = np.diff(values) / values[:-1]
        returns = returns[np.isfinite(returns)]
        confidence = min(max(float(confidence), 0.90), 0.99)
        window = min(max(int(window), 5), len(returns))
        threshold = np.quantile(returns, 1 - confidence)
        tail = returns[returns <= threshold]
        wealth = np.cumprod(1 + returns)
        drawdown = wealth / np.maximum.accumulate(wealth) - 1
        rolling_std = np.asarray([np.std(returns[max(0, i-window+1):i+1], ddof=1)
                                  for i in range(window-1, len(returns))])
        return {"symbol": symbol.upper(), "source": series.get("table"),
                "start": observations[0]["date"], "end": observations[-1]["date"],
                "observations": int(len(returns)), "confidence": confidence,
                "dailyVolatilityPct": float(np.std(returns, ddof=1) * 100),
                "annualizedVolatilityPct": float(np.std(returns, ddof=1) * np.sqrt(252) * 100),
                "rollingStdLatestPct": float(rolling_std[-1] * 100) if len(rolling_std) else None,
                "historicalVaRPct": float(-threshold * 100),
                "historicalCVaRPct": float(-np.mean(tail) * 100) if len(tail) else float(-threshold * 100),
                "maxDrawdownPct": float(np.min(drawdown) * 100)}

    def execute(self, name, arguments):
        if name == "search_instruments": return self.search_instruments(**arguments)
        if name == "get_financial_series": return self.get_financial_series(**arguments)
        if name == "get_market_snapshot": return self.get_market_snapshot(**arguments)
        return {"error": f"Unknown tool: {name}"}
