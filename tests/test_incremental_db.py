import unittest
from datetime import date, time

import duckdb
import pandas as pd

from src.dataloader.build_db import upsert_table
from src.fed_policy.repository import FedPolicyRepository


class IncrementalBuildTests(unittest.TestCase):
    def setUp(self):
        self.connection = duckdb.connect()
        self.connection.execute("CREATE SCHEMA metadata")

    def tearDown(self):
        self.connection.close()

    def test_update_insert_and_preserve_absent_rows(self):
        table = "metadata.instrument_master"
        upsert_table(
            self.connection, table,
            "SELECT 1::BIGINT AS id, 'original'::VARCHAR AS name, 1.0::DOUBLE AS score "
            "UNION ALL SELECT 2, 'preserve', 2.0",
        )
        upsert_table(
            self.connection, table,
            "SELECT 1::BIGINT AS id, 'changed'::VARCHAR AS name, 1.0::DOUBLE AS score "
            "UNION ALL SELECT 3, 'new', 3.0",
        )
        self.assertEqual(
            self.connection.execute(f"SELECT id, name FROM {table} ORDER BY id").fetchall(),
            [(1, "changed"), (2, "preserve"), (3, "new")],
        )
        self.assertEqual(
            upsert_table(self.connection, table, "SELECT 1::BIGINT AS id, 'changed'::VARCHAR AS name, 1.0::DOUBLE AS score"),
            3,
        )

    def test_reject_duplicate_null_key_and_schema_change(self):
        table = "metadata.instrument_master"
        upsert_table(self.connection, table, "SELECT 1::BIGINT AS id, 'keep'::VARCHAR AS name")
        bad_sources = (
            "SELECT 1::BIGINT AS id, 'a'::VARCHAR AS name UNION ALL SELECT 1, 'b'",
            "SELECT NULL::BIGINT AS id, 'bad'::VARCHAR AS name",
            "SELECT 1::BIGINT AS id, 5::INTEGER AS name",
        )
        for source in bad_sources:
            with self.subTest(source=source), self.assertRaises(ValueError):
                upsert_table(self.connection, table, source)
        self.assertEqual(self.connection.execute(f"SELECT * FROM {table}").fetchall(), [(1, "keep")])

    def test_failed_batch_rolls_back_prior_table_changes(self):
        table = "metadata.instrument_master"
        upsert_table(self.connection, table, "SELECT 1::BIGINT AS id, 'keep'::VARCHAR AS name")
        self.connection.execute("BEGIN TRANSACTION")
        try:
            upsert_table(self.connection, table, "SELECT 1::BIGINT AS id, 'temporary'::VARCHAR AS name")
            with self.assertRaises(ValueError):
                upsert_table(self.connection, table, "SELECT 2::BIGINT AS id, 'a'::VARCHAR AS name UNION ALL SELECT 2, 'b'")
        finally:
            self.connection.execute("ROLLBACK")
        self.assertEqual(self.connection.execute(f"SELECT * FROM {table}").fetchall(), [(1, "keep")])


class FedPolicyUpsertTests(unittest.TestCase):
    def test_price_and_probability_rows_are_merged(self):
        connection = duckdb.connect()
        try:
            repository = FedPolicyRepository("unused.duckdb")
            repository.initialize(connection)
            price = dict(
                base_date=date(2024, 1, 1), release_date=date(2024, 1, 2),
                time=time(0), time_zone="UTC", symbol="EFFR", exchange="FRED",
                country="US", open=1.0, high=1.0, low=1.0, close=1.0,
            )
            repository.upsert_prices(connection, "effective_fed_funds_rate", pd.DataFrame([price]))
            second_price = dict(price, base_date=date(2024, 1, 2))
            repository.upsert_prices(connection, "effective_fed_funds_rate", pd.DataFrame([second_price]))
            price["close"] = 2.0
            repository.upsert_prices(connection, "effective_fed_funds_rate", pd.DataFrame([price]))
            self.assertEqual(
                connection.execute("SELECT COUNT(*), MAX(close) FROM fed_policy.effective_fed_funds_rate").fetchone(),
                (2, 2.0),
            )

            probability = dict(
                base_date=date(2024, 1, 1), release_date=date(2024, 1, 2),
                time=time(0), time_zone="UTC", meeting_date=date(2024, 1, 31),
                contract_symbol="ZQF24", scenario_bp=525, probability=0.5,
                futures_price=95.0, implied_rate=5.0, effective_rate=5.0,
            )
            repository.upsert_probabilities(connection, pd.DataFrame([probability]))
            probability["probability"] = 0.75
            repository.upsert_probabilities(connection, pd.DataFrame([probability]))
            self.assertEqual(
                connection.execute("SELECT COUNT(*), MAX(probability) FROM fed_policy.meeting_probabilities").fetchone(),
                (1, 0.75),
            )
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
