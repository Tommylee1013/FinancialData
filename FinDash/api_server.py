#!/usr/bin/env python3
"""Read-only local API for the FinDash frontend."""

from __future__ import annotations

import json
import os
from datetime import date, datetime, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import duckdb


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("FINDASH_DB_PATH", ROOT.parent / "database" / "alternative_data.duckdb"))
HOST = os.environ.get("FINDASH_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("FINDASH_API_PORT", "8787"))


MARKETS = {
    "SP500": ("sp500", "S&P 500", "US", "🇺🇸"),
    "NASDAQ": ("nasdaq", "NASDAQ", "US", "🇺🇸"),
    "DJI": ("dow", "Dow Jones", "US", "🇺🇸"),
    "KOSPI": ("kospi", "KOSPI", "KR", "🇰🇷"),
    "KOSDAQ": ("kosdaq", "KOSDAQ", "KR", "🇰🇷"),
    "NKY": ("nikkei", "Nikkei 225", "JP", "🇯🇵"),
    "TOPIX": ("topix", "TOPIX", "JP", "🇯🇵"),
    "DAX": ("dax", "DAX", "DE", "🇩🇪"),
    "UKX": ("ftse", "FTSE 100", "GB", "🇬🇧"),
    "CAC": ("cac", "CAC 40", "FR", "🇫🇷"),
    "HSI": ("hsi", "Hang Seng", "HK", "🇭🇰"),
    "SHSZ300": ("csi300", "CSI 300", "CN", "🇨🇳"),
}

VOLATILITY = {
    "VIX": ("vix", "VIX", "S&P 500 Volatility"),
    "VKOSPI": ("vkospi", "VKOSPI", "KOSPI Volatility"),
    "V2X": ("vstoxx", "VSTOXX", "Euro Stoxx 50 Volatility"),
    "JNIV": ("nkvi", "NKVI", "Nikkei 225 Volatility"),
    "RVX": ("rvx", "RVX", "Russell 2000 Volatility"),
    "MOVE": ("move", "MOVE", "US Bond Market Volatility"),
}

MACRO = {
    "CPIYOY": ("uscpi", "US CPI", "US Consumer Price Index", "%", "inflation"),
    "CPURNSA": ("uscorecpi", "US Core CPI", "US Core CPI", "%", "inflation"),
    "PPIACO": ("usppi", "US PPI", "US Producer Price Index", "%", "inflation"),
    "JPCPIYOY": ("jpcpi", "JP CPI", "Japan CPI", "%", "inflation"),
    "CPICEMU": ("eucpi", "EU CPI", "EU CPI", "%", "inflation"),
    "KRCPIYOY": ("krcpi", "KR CPI", "Korea CPI", "%", "inflation"),
    "NAPMPMI": ("uspmi", "US ISM PMI", "US ISM Manufacturing PMI", "", "pmi"),
    "CPMINDX": ("cnpmi", "CN PMI", "China Manufacturing PMI", "", "pmi"),
}

COMMODITIES = {
    "CL": ("wti", "WTI Crude", "Energy", "USD/bbl"),
    "BRN": ("brent", "Brent Crude", "Energy", "USD/bbl"),
    "NG": ("natgas", "Natural Gas", "Energy", "USD/MMBtu"),
    "GC": ("gold", "Gold", "Precious Metals", "USD/troy oz"),
    "SI": ("silver", "Silver", "Precious Metals", "USD/troy oz"),
    "HG": ("copper", "Copper", "Base Metals", "USD/lb"),
    "LMAHDS03": ("alum", "Aluminium", "Base Metals", "USD/MT"),
    "TIO1": ("iron", "Iron Ore", "Industrial", "USD/MT"),
}

FREIGHT = {
    "BDI": ("bdi", "BDI", "Baltic Dry Index", "Dry Bulk Freight"),
    "SCFI": ("scfi", "SCFI", "Shanghai Containerized Freight Index", "Shanghai Container Freight"),
    "CCFI": ("ccfi", "CCFI", "China Containerized Freight Index", "China Container Freight"),
    "WCI": ("wci", "WCI", "World Container Index (Drewry)", "Global Container Freight ($/FEU)"),
    "FBX": ("fbx", "FBX", "Freightos Baltic Index", "Global Container Freight ($/FEU)"),
    "HARPEX": ("harpex", "HARPEX", "Harper Petersen Charter Rates Index", "Container Charter Rate"),
}

INDUSTRY = {
    "DXI": ("dram", "DRAMExchange Index", "Semiconductors", "Index"),
    "CFMDRAM": ("cfmdram", "CFM DRAM Price Index", "Semiconductors", "Index"),
    "CSUSHPINSA": ("cshome", "CS Home Price Idx", "Real Estate", "Index"),
    "LTC": ("lithi", "Lithium Carbonate", "Materials", "USD/MT"),
    "CO": ("cobalt", "Cobalt", "Materials", "USD/MT"),
}

US_YIELDS = [("USGG1M", "1M"), ("USGG3M", "3M"), ("USGG6M", "6M"), ("USGG12M", "1Y"),
             ("USGG2YR", "2Y"), ("USGG3YR", "3Y"), ("USGG5YR", "5Y"), ("USGG7YR", "7Y"),
             ("USGG10YR", "10Y"), ("USGG20YR", "20Y"), ("USGG30YR", "30Y")]
KR_YIELDS = [("KTB01", "1Y"), ("KTB02", "2Y"), ("KTB03", "3Y"), ("KTB05", "5Y"),
             ("KTB07", "7Y"), ("KTB10", "10Y"), ("KTB20", "20Y"), ("KTB30", "30Y")]

SECTORS = {
    "US": {
        "SPX50010": ("Energy", "Energy"), "SPX50015": ("Materials", "Materials"),
        "SPX50020": ("Industrials", "Industrials"), "SPX50025": ("Consumer Discretionary", "Consumer"),
        "SPX50030": ("Consumer Staples", "Consumer"), "SPX50035": ("Health Care", "Health Care"),
        "SPX50040": ("Financials", "Financials"), "SPX50045": ("Information Technology", "Technology"),
        "SPX50050": ("Communication Services", "Communication"), "SPX50055": ("Utilities", "Utilities"),
        "SPX50060": ("Real Estate", "Real Estate"),
    },
    "KR": {
        "KRXSECTOR20": ("Communication Services", "Communication"), "KRXSECTOR18": ("Consumer Discretionary", "Consumer"),
        "KRXSECTOR19": ("Consumer Staples", "Consumer"), "KRXSECTOR6": ("Energy", "Energy"),
        "KRXSECTOR4": ("Financials", "Financials"), "KRXSECTOR3": ("Health Care", "Health Care"),
        "KRXSECTOR1": ("Industrials", "Industrials"), "KRXSECTOR21": ("Information Technology", "Technology"),
        "KRXSECTOR7": ("Materials", "Materials"), "KRXSECTOR22": ("Utilities", "Utilities"),
    },
    "JP": {
        "T17ISO": ("Communication Services", "Communication"), "T17RT": ("Consumer Discretionary", "Consumer"),
        "T17FD": ("Consumer Staples", "Consumer"), "T17ER": ("Energy", "Energy"),
        "T17FIN": ("Financials", "Financials"), "T17PHR": ("Health Care", "Health Care"),
        "T17CWT": ("Industrials", "Industrials"), "T17EAPI": ("Information Technology", "Technology"),
        "T17SNM": ("Materials", "Materials"), "T17RE": ("Real Estate", "Real Estate"),
        "T17EPG": ("Utilities", "Utilities"),
    },
    "CN": {
        "CSI30050": ("Communication Services", "Communication"), "CSI30025": ("Consumer Discretionary", "Consumer"),
        "CSI30030": ("Consumer Staples", "Consumer"), "CSI30010": ("Energy", "Energy"),
        "CSI30040": ("Financials", "Financials"), "CSI30035": ("Health Care", "Health Care"),
        "CSI30020": ("Industrials", "Industrials"), "CSI30045": ("Information Technology", "Technology"),
        "CSI30015": ("Materials", "Materials"), "CSI30060": ("Real Estate", "Real Estate"),
        "CSI30055": ("Utilities", "Utilities"),
    },
}


def _json_default(value):
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def _ohlcv(con, table: str, mapping: dict, periods: int = 365) -> list[dict]:
    symbols = list(mapping)
    rows = con.execute(f"""
        with ranked as (
          select *, row_number() over (partition by symbol order by base_date desc, release_date desc, time desc) rn
          from {table} where symbol in (select unnest(?)) and close is not null
        ) select symbol, base_date, open, high, low, close, volume
          from ranked where rn <= ? order by symbol, base_date
    """, [symbols, periods]).fetchall()
    grouped = {}
    for symbol, base_date, op, hi, lo, close, volume in rows:
        grouped.setdefault(symbol, []).append((base_date, op, hi, lo, close, volume))
    result = []
    for symbol, meta in mapping.items():
        series = grouped.get(symbol, [])
        if not series:
            continue
        latest, previous = series[-1], series[-2] if len(series) > 1 else series[-1]
        value, prev = latest[4], previous[4]
        change = value - prev
        item = {"id": meta[0], "name": meta[1], "value": value, "change": change,
                "changePct": change / prev * 100 if prev else 0, "prev": prev,
                "high": latest[2] if latest[2] is not None else value,
                "low": latest[3] if latest[3] is not None else value,
                "volume": f"{latest[5]:,.0f}" if latest[5] is not None else "—",
                "trend": [{"t": i, "date": row[0], "v": row[4]} for i, row in enumerate(series) if row[4] is not None],
                "ohlc": [{"time": row[0], "open": row[1], "high": row[2], "low": row[3], "close": row[4]}
                         for row in series if all(value is not None for value in row[1:5])],
                "asOf": latest[0]}
        if len(meta) >= 3:
            if len(meta) == 4 and len(meta[2]) <= 2:
                item.update(country=meta[2], flag=meta[3])
            else:
                item.update(desc=meta[2])
        result.append(item)
    return result


def _values(con, table: str, mapping: dict, periods: int = 365) -> list[dict]:
    rows = con.execute(f"""
        with ranked as (
          select *, row_number() over (partition by symbol order by base_date desc, release_date desc, time desc) rn
          from {table} where symbol in (select unnest(?)) and value is not null
        ) select symbol, base_date, value from ranked where rn <= ? order by symbol, base_date
    """, [list(mapping), periods]).fetchall()
    grouped = {}
    for symbol, base_date, value in rows:
        grouped.setdefault(symbol, []).append((base_date, value))
    result = []
    for symbol, meta in mapping.items():
        series = grouped.get(symbol, [])
        if not series:
            continue
        value = series[-1][1]
        prev = series[-2][1] if len(series) > 1 else value
        change = value - prev
        item = {"id": meta[0], "name": meta[1], "value": value, "change": change,
                "changePct": change / prev * 100 if prev else 0,
                "high": max(x[1] for x in series), "low": min(x[1] for x in series),
                "trend": [{"t": i, "date": x[0], "v": x[1]} for i, x in enumerate(series)], "asOf": series[-1][0]}
        if len(meta) == 4:
            item.update(category=meta[2], unit=meta[3])
        result.append(item)
    return result


def _macro(con) -> list[dict]:
    rows = con.execute("""
      with ranked as (
        select *, row_number() over (partition by symbol order by base_date desc, release_date desc, time desc) rn
        from macro.macro_data where symbol in (select unnest(?)) and actual is not null
      ) select symbol, base_date, actual, forecast, previous from ranked where rn <= 120 order by symbol, base_date
    """, [list(MACRO)]).fetchall()
    grouped = {}
    for row in rows:
        grouped.setdefault(row[0], []).append(row[1:])
    out = []
    for symbol, meta in MACRO.items():
        series = grouped.get(symbol, [])
        if not series:
            continue
        latest = series[-1]
        historical_previous = series[-2][1] if len(series) > 1 else latest[1]
        previous = latest[3] if latest[3] is not None else historical_previous
        forecast = latest[2] if latest[2] is not None else previous
        scale = 100 if meta[4] == "inflation" and abs(latest[1]) <= 1 else 1
        out.append({"id": meta[0], "name": meta[1], "desc": meta[2], "unit": meta[3], "type": meta[4],
                    "value": latest[1] * scale, "forecast": forecast * scale, "prev": previous * scale,
                    "period": latest[0].strftime("%b %Y"),
                    "trend": [{"t": i, "date": x[0], "v": x[1] * scale} for i, x in enumerate(series) if x[1] is not None]})
    return out


def _yield_curve(con, mapping) -> list[dict]:
    rows = con.execute("""
      with ranked as (
       select symbol, base_date, value, row_number() over(partition by symbol order by base_date desc, release_date desc, time desc) rn
       from fixed_income.fixed_income_data where symbol in (select unnest(?)) and value is not null
      ) select symbol, base_date, value, rn from ranked where rn <= 365 order by symbol, base_date
    """, [[x[0] for x in mapping]]).fetchall()
    values = {}
    trends = {}
    for symbol, base_date, value, rank in rows:
        values.setdefault(symbol, {})[rank] = value
        trends.setdefault(symbol, []).append({"date": base_date, "v": value})
    return [{"tenor": tenor, "yield": values[symbol][1], "prev": values[symbol].get(2, values[symbol][1]), "trend": trends[symbol]}
            for symbol, tenor in mapping if symbol in values and 1 in values[symbol]]


def _sector_data(con) -> dict[str, list[dict]]:
    output = {}
    for country, mapping in SECTORS.items():
        raw_mapping = {symbol: (f"sector-{country.lower()}-{symbol.lower()}", name, category, "Index")
                       for symbol, (name, category) in mapping.items()}
        rows = _ohlcv(con, "market.index_data", raw_mapping, 365)
        for row in rows:
            row.update(country=country, symbol=next((s for s, meta in raw_mapping.items() if meta[0] == row["id"]), ""))
        output[country] = rows
    return output


def _sentiment(con) -> dict:
    symbols = ["CNNFNGI", "AAIIBULL", "AAIINEUT", "AAIIBEAR", "NAAIMAVG"]
    rows = con.execute("""
      with ranked as (
        select symbol, base_date, value,
               row_number() over(partition by symbol order by base_date desc, release_date desc, time desc) rn
        from behavior.behavior_data where symbol in (select unnest(?)) and value is not null
      ) select symbol, base_date, value, rn from ranked where rn <= 2
    """, [symbols]).fetchall()
    values = {}
    for symbol, base_date, value, rank in rows:
        values.setdefault(symbol, {})[rank] = (value, base_date)
    def latest(symbol, scale=1):
        current = values.get(symbol, {}).get(1)
        previous = values.get(symbol, {}).get(2, current)
        return ((current[0] * scale if current else None), (previous[0] * scale if previous else None),
                (current[1] if current else None))
    fng, fng_prev, fng_date = latest("CNNFNGI")
    naaim, naaim_prev, naaim_date = latest("NAAIMAVG")
    bull, _, aaii_date = latest("AAIIBULL", 100)
    neutral, _, _ = latest("AAIINEUT", 100)
    bear, _, _ = latest("AAIIBEAR", 100)
    label = "Unavailable" if fng is None else ("Extreme Fear" if fng < 25 else "Fear" if fng < 45 else "Neutral" if fng < 55 else "Greed" if fng < 75 else "Extreme Greed")
    return {
        "fng": {"value": fng, "prev": fng_prev, "label": label, "asOf": fng_date, "connected": fng is not None},
        "aaii": {"bullish": bull, "neutral": neutral, "bearish": bear, "asOf": aaii_date,
                 "connected": all(v is not None for v in (bull, neutral, bear))},
        "naaim": {"value": naaim, "prev": naaim_prev, "change": naaim - naaim_prev if naaim is not None and naaim_prev is not None else None,
                  "asOf": naaim_date, "connected": naaim is not None},
        "putcall": {"value": None, "connected": False, "reason": "Series not available in DuckDB"},
    }


def dashboard_payload() -> dict:
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"DuckDB not found: {DB_PATH}")
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        industry = _values(con, "industry.index_data", INDUSTRY)
        for item in industry:
            meta = next(v for v in INDUSTRY.values() if v[0] == item["id"])
            item.update(category=meta[2], unit=meta[3])
        freight = _values(con, "freight.freight_data", FREIGHT, 365)
        for item in freight:
            meta = next(v for v in FREIGHT.values() if v[0] == item["id"])
            item.update(fullName=meta[2], desc=meta[3])
        return {"source": str(DB_PATH), "updatedAt": datetime.now().isoformat(timespec="seconds"),
                "marketIndices": _ohlcv(con, "market.index_data", MARKETS),
                "volatilityIndices": _ohlcv(con, "market.volatility_data", VOLATILITY),
                "sectorDataByCountry": _sector_data(con), "sentimentData": _sentiment(con),
                "macroVariables": _macro(con),
                "commodities": _values(con, "industry.index_data", COMMODITIES),
                "freightIndices": freight, "industryData": industry,
                "yieldCurveUS": _yield_curve(con, US_YIELDS), "yieldCurveKR": _yield_curve(con, KR_YIELDS)}
    finally:
        con.close()


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict):
        body = json.dumps(payload, default=_json_default, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/health":
                self._send(200, {"ok": DB_PATH.is_file(), "database": str(DB_PATH)})
            elif path == "/api/dashboard":
                self._send(200, dashboard_payload())
            else:
                self._send(404, {"error": "Not found"})
        except Exception as exc:
            self._send(500, {"error": str(exc)})

    def log_message(self, fmt, *args):
        print(f"[FinDash API] {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    print(f"FinDash API: http://{HOST}:{PORT}")
    print(f"DuckDB (read-only): {DB_PATH}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
