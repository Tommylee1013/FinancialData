from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

SCHEMA = "fed_policy"
PRICE_COLUMNS = ["base_date", "release_date", "time", "time_zone", "symbol", "exchange", "country", "open", "high", "low", "close"]


class FedPolicyRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def connect(self, read_only: bool = False):
        return duckdb.connect(str(self.database_path), read_only=read_only)

    def initialize(self, connection) -> None:
        connection.execute(f"create schema if not exists {SCHEMA}")
        for table in ("fed_funds_futures", "effective_fed_funds_rate"):
            connection.execute(f"""create table if not exists {SCHEMA}.{table} (
                base_date date not null, release_date date not null, time time not null,
                time_zone varchar not null, symbol varchar not null, exchange varchar not null,
                country varchar not null, open double, high double, low double, close double
            )""")
        connection.execute(f"""create table if not exists {SCHEMA}.meeting_probabilities (
            base_date date not null, release_date date not null, time time not null, time_zone varchar not null,
            meeting_date date not null, contract_symbol varchar not null, scenario_bp integer not null,
            probability double not null, futures_price double, implied_rate double, effective_rate double
        )""")

    def meeting_dates(self, connection, start: str | None = None, extra_dates: list[str] | None = None) -> list[pd.Timestamp]:
        query = "select distinct base_date from macro.macro_data where upper(symbol) = 'FDTR'"
        params = []
        if start:
            query += " and base_date >= ?"; params.append(start)
        dates = [pd.Timestamp(row[0]) for row in connection.execute(query + " order by base_date", params).fetchall()]
        dates.extend(pd.Timestamp(value) for value in (extra_dates or []))
        return sorted(set(dates))

    def replace_prices(self, connection, table: str, frame: pd.DataFrame) -> int:
        if frame.empty: return 0
        missing = set(PRICE_COLUMNS) - set(frame.columns)
        if missing: raise ValueError(f"Missing price columns: {sorted(missing)}")
        connection.register("fed_price_frame", frame[PRICE_COLUMNS])
        try:
            connection.execute(f"delete from {SCHEMA}.{table} where symbol in (select distinct symbol from fed_price_frame)")
            connection.execute(f"insert into {SCHEMA}.{table} select * from fed_price_frame")
        finally:
            connection.unregister("fed_price_frame")
        return len(frame)

    def replace_probabilities(self, connection, frame: pd.DataFrame) -> int:
        if frame.empty: return 0
        connection.register("fed_probability_frame", frame)
        try:
            connection.execute(f"delete from {SCHEMA}.meeting_probabilities where meeting_date in (select distinct meeting_date from fed_probability_frame)")
            connection.execute(f"insert into {SCHEMA}.meeting_probabilities select * from fed_probability_frame")
        finally:
            connection.unregister("fed_probability_frame")
        return len(frame)
