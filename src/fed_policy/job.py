from __future__ import annotations

import argparse
from datetime import time
from pathlib import Path

import pandas as pd
from tvDatafeed import TvDatafeed

from .contracts import contract_symbol
from .downloader import fetch_daily
from .model import calculate_meeting_probabilities
from .repository import FedPolicyRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = PROJECT_ROOT / "database" / "alternative_data.duckdb"


def run(database: Path, start: str, n_bars: int, extra_meetings: list[str]) -> dict:
    repository = FedPolicyRepository(database)
    read_connection = repository.connect(read_only=True)
    try: meetings = repository.meeting_dates(read_connection, start=start, extra_dates=extra_meetings)
    finally: read_connection.close()
    if not meetings: raise ValueError("No FDTR meeting dates found for the requested period")

    tv = TvDatafeed()
    effr = fetch_daily(tv, "EFFR", "FRED", n_bars=n_bars)
    contracts = []
    for symbol in sorted({contract_symbol(meeting) for meeting in meetings}):
        try: contracts.append(fetch_daily(tv, symbol, "CBOT", n_bars=n_bars))
        except RuntimeError as error: print(f"[WARN] {error}")
    futures = pd.concat(contracts, ignore_index=True) if contracts else pd.DataFrame()

    write_connection = repository.connect()
    try:
        write_connection.execute("begin transaction"); repository.initialize(write_connection)
        effr_rows = repository.replace_prices(write_connection, "effective_fed_funds_rate", effr)
        futures_rows = repository.replace_prices(write_connection, "fed_funds_futures", futures)
        probabilities = []
        effr_series = effr.set_index(pd.to_datetime(effr["base_date"]))["close"] * (100 if effr["close"].abs().median() < 1 else 1)
        for meeting in meetings:
            symbol = contract_symbol(meeting)
            contract = futures[futures["symbol"] == symbol] if not futures.empty else pd.DataFrame()
            if contract.empty: continue
            close = contract.set_index(pd.to_datetime(contract["base_date"]))["close"]
            result = calculate_meeting_probabilities(close, effr_series, meeting)
            if result.empty: continue
            result.insert(1, "release_date", result["base_date"]); result.insert(2, "time", time(0, 0))
            result.insert(3, "time_zone", "UTC"); result.insert(5, "contract_symbol", symbol)
            probabilities.append(result)
        probability_frame = pd.concat(probabilities, ignore_index=True) if probabilities else pd.DataFrame()
        probability_rows = repository.replace_probabilities(write_connection, probability_frame)
        write_connection.execute("commit")
    except Exception:
        write_connection.execute("rollback"); raise
    finally: write_connection.close()
    return {"meetings": len(meetings), "contracts": len(contracts), "effr_rows": effr_rows,
            "futures_rows": futures_rows, "probability_rows": probability_rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Fed funds futures and calculate FOMC decision probabilities")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--start", default="2020-01-01", help="Earliest FDTR meeting date")
    parser.add_argument("--n-bars", type=int, default=5000)
    parser.add_argument("--meeting", action="append", default=[], help="Optional future FOMC decision date; repeatable")
    args = parser.parse_args()
    print(run(args.database, args.start, args.n_bars, args.meeting))


if __name__ == "__main__": main()
