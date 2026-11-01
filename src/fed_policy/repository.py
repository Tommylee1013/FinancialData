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

    def _merge_frame(self, connection, table: str, frame: pd.DataFrame, keys: tuple[str, ...]) -> int:
        if frame.empty:
            return 0

        columns = [(row[0], row[1]) for row in connection.execute(f"DESCRIBE {SCHEMA}.{table}").fetchall()]
        expected = {name for name, _ in columns}
        missing = expected - set(frame.columns)
        if missing:
            raise ValueError(f"{table}: missing columns: {sorted(missing)}")

        def quote(name: str) -> str:
            return '"' + name.replace('"', '""') + '"'

        source_name = "_fed_incoming_frame"
        stage = "_fed_incoming_batch"
        connection.register(source_name, frame)
        try:
            projection = ", ".join(
                f"CAST({quote(name)} AS {dtype}) AS {quote(name)}" for name, dtype in columns
            )
            connection.execute(f"CREATE TEMP TABLE {stage} AS SELECT {projection} FROM {source_name}")
            try:
                key_columns = ", ".join(quote(key) for key in keys)
                null_check = " OR ".join(f"{quote(key)} IS NULL" for key in keys)
                if connection.execute(f"SELECT 1 FROM {stage} WHERE {null_check} LIMIT 1").fetchone():
                    raise ValueError(f"{table}: incoming data has a null key")
                if connection.execute(
                    f"SELECT 1 FROM {stage} GROUP BY {key_columns} HAVING COUNT(*) > 1 LIMIT 1"
                ).fetchone():
                    raise ValueError(f"{table}: incoming data has duplicate keys")
                if connection.execute(
                    f"SELECT 1 FROM {SCHEMA}.{table} GROUP BY {key_columns} HAVING COUNT(*) > 1 LIMIT 1"
                ).fetchone():
                    raise ValueError(f"{table}: existing data has duplicate keys; merge is unsafe")

                join = " AND ".join(f"target.{quote(key)} = source.{quote(key)}" for key in keys)
                nonkeys = [name for name, _ in columns if name not in keys]
                changed = " OR ".join(
                    f"target.{quote(name)} IS DISTINCT FROM source.{quote(name)}" for name in nonkeys
                )
                assignments = ", ".join(
                    f"{quote(name)} = source.{quote(name)}" for name in nonkeys
                )
                connection.execute(f"""
                    MERGE INTO {SCHEMA}.{table} AS target USING {stage} AS source ON {join}
                    WHEN MATCHED AND ({changed}) THEN UPDATE SET {assignments}
                    WHEN NOT MATCHED THEN INSERT BY NAME
                """)
            finally:
                connection.execute(f"DROP TABLE {stage}")
        finally:
            connection.unregister(source_name)
        return len(frame)

    def upsert_prices(self, connection, table: str, frame: pd.DataFrame) -> int:
        if table not in ("effective_fed_funds_rate", "fed_funds_futures"):
            raise ValueError(f"Unknown Fed policy price table: {table}")
        if frame.empty:
            return 0
        missing = set(PRICE_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError(f"Missing price columns: {sorted(missing)}")
        return self._merge_frame(connection, table, frame, ("base_date", "symbol", "exchange"))

    def upsert_probabilities(self, connection, frame: pd.DataFrame) -> int:
        return self._merge_frame(
            connection, "meeting_probabilities", frame,
            ("base_date", "meeting_date", "contract_symbol", "scenario_bp"),
        )
