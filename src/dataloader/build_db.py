from pathlib import Path

import duckdb
import pandas as pd

from src.utils.log import setup_logger


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path.cwd()

DATABASE_PATH = (
    PROJECT_ROOT
    / "database"
    / "alternative_data.duckdb"
)

METADATA_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "metadata.xlsx"
)

INDEX_DATA_PATH = (
    PROJECT_ROOT
    / "data_warehouse"
    / "raw"
    / "index"
)

MACRO_DATA_PATH = (
    PROJECT_ROOT
    / "data_warehouse"
    / "raw"
    / "macro"
)

FREIGHT_DATA_PATH = (
    PROJECT_ROOT
    / "data_warehouse"
    / "raw"
    / "freight"
)

VOLATILITY_DATA_PATH = (
    PROJECT_ROOT
    / "data_warehouse"
    /"raw"
    / "risk"
)

INDUSTRY_DATA_PATH = (
    PROJECT_ROOT
    / "data_warehouse"
    / "raw"
    /"industry"
    /'components'
)

INDUSTRY_INDEX_DATA_PATH = (
    PROJECT_ROOT
    / "data_warehouse"
    / 'raw'
    /'industry'
    / 'index'
)

FX_INDEX_DATA_PATH = (
    PROJECT_ROOT
    / "data_warehouse"
    / 'raw'
    /'fx'
)

FIXED_INCOME_DATA_PATH = (
    PROJECT_ROOT
    / "data_warehouse"
    / 'raw'
    /'fixed_income'
)

FIXED_INCOME_INDEX_DATA_PATH = FIXED_INCOME_DATA_PATH / "index"

BEHAVIOR_DATA_PATH = (PROJECT_ROOT
    / "data_warehouse"
    / 'raw'
    / 'behavior'
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/build_duckdb.log",
)


# ============================================================
# Table names
# ============================================================

METADATA_TABLE = "metadata.instrument_master"
INDEX_TABLE = "market.index_data"
MACRO_TABLE = "macro.macro_data"
FREIGHT_TABLE = "freight.freight_data"
VOLATILITY_TABLE = "market.volatility_data"
INDUSTRY_TABLE = 'industry.components_data'
INDUSTRY_INDEX_TABLE = 'industry.index_data'
FX_TABLE = 'market.fx_data'
FIXED_INCOME_TABLE = 'fixed_income.fixed_income_data'
FIXED_INCOME_INDEX_TABLE = 'fixed_income.index_data'
BEHAVIOR_TABLE = 'behavior.behavior_data'

# ============================================================
# Expected columns
# ============================================================

INDEX_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

MACRO_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "actual",
    "forecast",
    "previous",
    'preliminary_release'
]

FREIGHT_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "value",
]

VOLATILITY_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

INDUSTRY_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "item",
    'value'
]

INDUSTRY_INDEX_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    'value'
]

FX_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "open",
    "high",
    "low",
    "close",
    "volume",
]

FIXED_INCOME_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    'value'
]

FIXED_INCOME_INDEX_COLUMNS = INDEX_COLUMNS

BEHAVIOR_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    'value'
]

# A release can have multiple observations for the same base date. Keep the
# release timestamp in those keys; industry components also need their item.
TABLE_KEYS = {
    METADATA_TABLE: ("id",),
    INDEX_TABLE: ("base_date", "symbol", "exchange"),
    MACRO_TABLE: ("base_date", "release_date", "time", "symbol", "exchange"),
    FREIGHT_TABLE: ("base_date", "release_date", "time", "symbol", "exchange"),
    VOLATILITY_TABLE: ("base_date", "symbol", "exchange"),
    INDUSTRY_TABLE: ("base_date", "release_date", "time", "symbol", "exchange", "item"),
    INDUSTRY_INDEX_TABLE: ("base_date", "symbol", "exchange"),
    FX_TABLE: ("base_date", "symbol", "exchange"),
    FIXED_INCOME_TABLE: ("base_date", "symbol", "exchange"),
    FIXED_INCOME_INDEX_TABLE: ("base_date", "symbol", "exchange"),
    BEHAVIOR_TABLE: ("base_date", "release_date", "time", "symbol", "exchange"),
}

# ============================================================
# Utility functions
# ============================================================

def get_parquet_files(
    directory: Path,
) -> list[Path]:
    """
    Recursively returns all Parquet files under the target directory.
    """

    if not directory.exists():
        raise FileNotFoundError(
            f"Data directory not found: {directory}"
        )

    parquet_files = sorted(
        directory.rglob("*.parquet")
    )

    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet files found in: {directory}"
        )

    return parquet_files


def validate_parquet_columns(
    parquet_files: list[Path],
    required_columns: list[str],
    data_type_name: str,
) -> None:
    """
    Validates that every Parquet file contains all required columns.
    """

    required_column_set = set(required_columns)

    for file_path in parquet_files:
        columns = (
            pd.read_parquet(file_path)
            .columns
            .tolist()
        )

        normalized_columns = {
            str(column).strip().lower()
            for column in columns
        }

        missing_columns = (
            required_column_set
            - normalized_columns
        )

        if missing_columns:
            raise ValueError(
                f"Required columns are missing from "
                f"{data_type_name} data_lake.\n"
                f"File: {file_path}\n"
                f"Missing columns: {sorted(missing_columns)}"
            )

    LOGGER.info(
        "Parquet schema validation completed | "
        "data_type=%s | files=%d",
        data_type_name,
        len(parquet_files),
    )


def normalize_metadata_columns(
    metadata: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalizes metadata column names to lowercase snake_case
    and trims string values.
    """

    metadata = metadata.copy()

    metadata.columns = (
        metadata.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    string_columns = metadata.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in string_columns:
        metadata[column] = (
            metadata[column]
            .astype("string")
            .str.strip()
        )

        metadata[column] = metadata[column].replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "<NA>": pd.NA,
            }
        )

    return metadata


def build_parquet_path_list(
    parquet_files: list[Path],
) -> str:
    """
    Builds a DuckDB-compatible SQL list of Parquet file paths.
    """

    escaped_paths = [
        file_path
        .resolve()
        .as_posix()
        .replace("'", "''")
        for file_path in parquet_files
    ]

    return "[" + ", ".join(
        f"'{path}'"
        for path in escaped_paths
    ) + "]"


def upsert_table(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    source_query: str,
) -> int:
    """Merge a validated batch without removing rows absent from the source."""

    stage = "_incoming_build_batch"
    keys = TABLE_KEYS[table]

    def quote(name: str) -> str:
        return '"' + name.replace('"', '""') + '"'

    connection.execute(f"CREATE TEMP TABLE {stage} AS {source_query}")
    try:
        source_columns = [row[:2] for row in connection.execute(f"DESCRIBE {stage}").fetchall()]
        names = [name for name, _ in source_columns]
        if not set(keys).issubset(names):
            raise ValueError(f"{table}: source is missing key columns {set(keys) - set(names)}")

        null_check = " OR ".join(f"{quote(key)} IS NULL" for key in keys)
        if connection.execute(f"SELECT 1 FROM {stage} WHERE {null_check} LIMIT 1").fetchone():
            raise ValueError(f"{table}: incoming data has a null key; existing data was not changed")

        key_columns = ", ".join(quote(key) for key in keys)
        if connection.execute(
            f"SELECT 1 FROM {stage} GROUP BY {key_columns} HAVING COUNT(*) > 1 LIMIT 1"
        ).fetchone():
            raise ValueError(f"{table}: incoming data has duplicate keys; existing data was not changed")

        schema, name = table.split(".", 1)
        exists = connection.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_schema = ? AND table_name = ?",
            [schema, name],
        ).fetchone()

        if not exists:
            connection.execute(f"CREATE TABLE {table} AS SELECT * FROM {stage}")
            inserted = connection.execute(f"SELECT COUNT(*) FROM {stage}").fetchone()[0]
            LOGGER.info("Table initialized | table=%s | inserted=%d", table, inserted)
        else:
            target_columns = [row[:2] for row in connection.execute(f"DESCRIBE {table}").fetchall()]
            if source_columns != target_columns:
                raise ValueError(
                    f"{table}: source/target schemas differ; refusing to replace the table. "
                    f"source={source_columns}, target={target_columns}"
                )
            if connection.execute(
                f"SELECT 1 FROM {table} GROUP BY {key_columns} HAVING COUNT(*) > 1 LIMIT 1"
            ).fetchone():
                raise ValueError(f"{table}: existing data has duplicate keys; merge is unsafe")

            join = " AND ".join(
                f"target.{quote(key)} = source.{quote(key)}" for key in keys
            )
            nonkeys = [column for column in names if column not in keys]
            changed = " OR ".join(
                f"target.{quote(column)} IS DISTINCT FROM source.{quote(column)}"
                for column in nonkeys
            )
            assignments = ", ".join(
                f"{quote(column)} = source.{quote(column)}" for column in nonkeys
            )
            inserted, updated = connection.execute(f"""
                SELECT
                    COUNT(*) FILTER (WHERE target.{quote(keys[0])} IS NULL),
                    COUNT(*) FILTER (WHERE target.{quote(keys[0])} IS NOT NULL AND ({changed}))
                FROM {stage} AS source
                LEFT JOIN {table} AS target ON {join}
            """).fetchone()
            connection.execute(f"""
                MERGE INTO {table} AS target USING {stage} AS source ON {join}
                WHEN MATCHED AND ({changed}) THEN UPDATE SET {assignments}
                WHEN NOT MATCHED THEN INSERT BY NAME
            """)
            LOGGER.info(
                "Table merged | table=%s | inserted=%d | updated=%d | unchanged=%d",
                table, inserted, updated,
                connection.execute(f"SELECT COUNT(*) FROM {stage}").fetchone()[0] - inserted - updated,
            )

        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        connection.execute(f"DROP TABLE {stage}")


# ============================================================
# Schema creation
# ============================================================

def create_schemas(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """
    Creates the required DuckDB schemas.
    """

    connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS metadata
        """
    )

    connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS market
        """
    )

    connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS macro
        """
    )

    connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS freight
        """
    )

    # add code from here (create schema)

    connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS industry
        """
    )

    connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS fixed_income
        """
    )

    connection.execute(
        """
        CREATE SCHEMA IF NOT EXISTS behavior
        """
    )

    LOGGER.info(
        "DuckDB schemas created or verified | "
        "schemas=metadata,market,macro,freight,industry,fixed_income,behavior"
    )


# ============================================================
# Table builders
# ============================================================

def create_metadata_table(
    connection: duckdb.DuckDBPyConnection,
) -> int:
    """
    Creates metadata.instrument_master from data_lake/metadata.xlsx.
    """

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {METADATA_PATH}"
        )

    LOGGER.info(
        "Loading metadata Excel file | path=%s",
        METADATA_PATH,
    )

    metadata = pd.read_excel(
        METADATA_PATH,
        sheet_name="Master",
    )

    metadata = normalize_metadata_columns(
        metadata
    )

    if metadata.empty:
        raise ValueError(
            "The Master sheet in metadata.xlsx is empty."
        )

    connection.register(
        "metadata_dataframe",
        metadata,
    )

    try:
        row_count = upsert_table(
            connection, METADATA_TABLE, "SELECT * FROM metadata_dataframe"
        )

    finally:
        connection.unregister(
            "metadata_dataframe"
        )

    LOGGER.info(
        "Metadata table synchronized | "
        "table=%s | rows=%d",
        METADATA_TABLE,
        row_count,
    )

    return row_count


def create_index_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all Index Parquet files into market.index_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(open AS DOUBLE) AS open,
            CAST(high AS DOUBLE) AS high,
            CAST(low AS DOUBLE) AS low,
            CAST(close AS DOUBLE) AS close,
            CAST(volume AS DOUBLE) AS volume
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, INDEX_TABLE, query)

    LOGGER.info(
        "Index table synchronized | "
        "table=%s | files=%d | rows=%d",
        INDEX_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count


def create_macro_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all Macro Parquet files into macro.macro_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(actual AS DOUBLE) AS actual,
            CAST(forecast AS DOUBLE) AS forecast,
            CAST(previous AS DOUBLE) AS previous,
            CAST(preliminary_release as boolean) as preliminary_release,
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, MACRO_TABLE, query)

    LOGGER.info(
        "Macro table synchronized | "
        "table=%s | files=%d | rows=%d",
        MACRO_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count


def create_freight_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all Freight Parquet files into freight.freight_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(value AS DOUBLE) AS value
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, FREIGHT_TABLE, query)

    LOGGER.info(
        "Freight table synchronized | "
        "table=%s | files=%d | rows=%d",
        FREIGHT_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count

def create_volatility_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all volatility Parquet files into market.volatility_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(open AS DOUBLE) AS open,
            CAST(high AS DOUBLE) AS high,
            CAST(low AS DOUBLE) AS low,
            CAST(close AS DOUBLE) AS close,
            CAST(volume AS DOUBLE) AS volume
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, VOLATILITY_TABLE, query)

    LOGGER.info(
        "Volatility Index table synchronized | "
        "table=%s | files=%d | rows=%d",
        VOLATILITY_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count

# add codes from here (functions)

def create_industry_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all Industry Parquet files into industry.industry_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(item AS VARCHAR) AS item,
            CAST(value AS DOUBLE) AS value,
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, INDUSTRY_TABLE, query)

    LOGGER.info(
        "Industry Components table synchronized | "
        "table=%s | files=%d | rows=%d",
        INDUSTRY_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count

def create_industry_index_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all Industry Parquet files into industry.industry_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(value AS DOUBLE) AS value,
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, INDUSTRY_INDEX_TABLE, query)

    LOGGER.info(
        "Industry Index table synchronized | "
        "table=%s | files=%d | rows=%d",
        INDUSTRY_INDEX_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count

def create_fx_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all FX Parquet files into market.fx_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(open AS DOUBLE) AS open,
            CAST(high AS DOUBLE) AS high,
            CAST(low AS DOUBLE) AS low,
            CAST(close AS DOUBLE) AS close,
            CAST(volume AS DOUBLE) AS volume
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, FX_TABLE, query)

    LOGGER.info(
        "FX table synchronized | "
        "table=%s | files=%d | rows=%d",
        FX_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count

def create_fixed_income_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all Industry Parquet files into industry.industry_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(value AS DOUBLE) AS value,
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, FIXED_INCOME_TABLE, query)

    LOGGER.info(
        "Fixed Income table synchronized | "
        "table=%s | files=%d | rows=%d",
        FIXED_INCOME_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count


def create_fixed_income_index_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """Combine bond-index OHLCV parquet files into fixed_income.index_data."""
    parquet_paths = build_parquet_path_list(parquet_files)
    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(open AS DOUBLE) AS open,
            CAST(high AS DOUBLE) AS high,
            CAST(low AS DOUBLE) AS low,
            CAST(close AS DOUBLE) AS close,
            CAST(volume AS DOUBLE) AS volume
        FROM read_parquet({parquet_paths}, union_by_name = TRUE)
    """
    row_count = upsert_table(connection, FIXED_INCOME_INDEX_TABLE, query)
    LOGGER.info("Fixed-income index table synchronized | table=%s | files=%d | rows=%d",
                FIXED_INCOME_INDEX_TABLE, len(parquet_files), row_count)
    return row_count

def create_behavior_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_files: list[Path],
) -> int:
    """
    Combines all Industry Parquet files into behavior.behavior_data.
    """

    parquet_paths = build_parquet_path_list(
        parquet_files
    )

    query = f"""
        SELECT
            CAST(base_date AS DATE) AS base_date,
            CAST(release_date AS DATE) AS release_date,
            CAST(time AS TIME) AS time,
            CAST(time_zone AS VARCHAR) AS time_zone,
            CAST(symbol AS VARCHAR) AS symbol,
            CAST(exchange AS VARCHAR) AS exchange,
            CAST(country AS VARCHAR) AS country,
            CAST(value AS DOUBLE) AS value,
        FROM read_parquet(
            {parquet_paths},
            union_by_name = TRUE
        )
    """

    row_count = upsert_table(connection, BEHAVIOR_TABLE, query)

    LOGGER.info(
        "Behavior table synchronized | "
        "table=%s | files=%d | rows=%d",
        BEHAVIOR_TABLE,
        len(parquet_files),
        row_count,
    )

    return row_count

# ============================================================
# Database validation
# ============================================================

def validate_database(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """
    Performs basic data_lake-quality validation after table creation.
    """

    index_null_keys = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {INDEX_TABLE}
        WHERE base_date IS NULL
           OR symbol IS NULL
        """
    ).fetchone()[0]

    macro_null_keys = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {MACRO_TABLE}
        WHERE base_date IS NULL
           OR release_date IS NULL
           OR symbol IS NULL
        """
    ).fetchone()[0]

    freight_null_keys = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {FREIGHT_TABLE}
        WHERE base_date IS NULL
           OR release_date IS NULL
           OR symbol IS NULL
        """
    ).fetchone()[0]

    volatility_null_keys = connection.execute(
        f"""
            SELECT COUNT(*)
            FROM {VOLATILITY_TABLE}
            WHERE base_date IS NULL
               OR symbol IS NULL
            """
    ).fetchone()[0]

    # add codes from here (null keys)

    industry_null_keys = connection.execute(
        f"""
            SELECT COUNT(*)
            FROM {INDUSTRY_TABLE}
            WHERE base_date IS NULL
               OR symbol IS NULL
            """
    ).fetchone()[0]

    industry_index_null_keys = connection.execute(
        f"""
                SELECT COUNT(*)
                FROM {INDUSTRY_INDEX_TABLE}
                WHERE base_date IS NULL
                   OR symbol IS NULL
            """
    ).fetchone()[0]

    fx_null_keys = connection.execute(
        f"""
                    SELECT COUNT(*)
                    FROM {FX_TABLE}
                    WHERE base_date IS NULL
                       OR symbol IS NULL
                """
    ).fetchone()[0]

    fixed_income_null_keys = connection.execute(
        f"""
                    SELECT COUNT(*)
                    FROM {FIXED_INCOME_TABLE}
                    WHERE base_date IS NULL
                       OR symbol IS NULL
                """
    ).fetchone()[0]

    behavior_null_keys = connection.execute(
        f"""
                        SELECT COUNT(*)
                        FROM {BEHAVIOR_TABLE}
                        WHERE base_date IS NULL
                           OR symbol IS NULL
                    """
    ).fetchone()[0]

    index_duplicates = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT
                base_date,
                symbol,
                exchange,
                COUNT(*) AS row_count
            FROM {INDEX_TABLE}
            GROUP BY
                base_date,
                symbol,
                exchange
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    macro_duplicates = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT
                base_date,
                release_date,
                time,
                symbol,
                exchange,
                COUNT(*) AS row_count
            FROM {MACRO_TABLE}
            GROUP BY
                base_date,
                release_date,
                time,
                symbol,
                exchange
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    freight_duplicates = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT
                base_date,
                release_date,
                time,
                symbol,
                exchange,
                COUNT(*) AS row_count
            FROM {FREIGHT_TABLE}
            GROUP BY
                base_date,
                release_date,
                time,
                symbol,
                exchange
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    volatility_duplicates = connection.execute(
        f"""
            SELECT COUNT(*)
            FROM (
                SELECT
                    base_date,
                    symbol,
                    exchange,
                    COUNT(*) AS row_count
                FROM {VOLATILITY_TABLE}
                GROUP BY
                    base_date,
                    symbol,
                    exchange
                HAVING COUNT(*) > 1
            )
            """
    ).fetchone()[0]

    # add codes from here (duplicates)

    industry_duplicates = connection.execute(
        f"""
                SELECT COUNT(*)
                FROM (
                    SELECT
                        base_date,
                        release_date,
                        time,
                        symbol,
                        exchange,
                        item,
                        COUNT(*) AS row_count
                    FROM {INDUSTRY_TABLE}
                    GROUP BY
                        base_date,
                        release_date,
                        time,
                        symbol,
                        exchange,
                        item
                    HAVING COUNT(*) > 1
                )
                """
    ).fetchone()[0]

    industry_index_duplicates = connection.execute(
        f"""
            select count(*)
            from (
                select base_date, symbol, exchange,
                count(*) as row_count
                from {INDUSTRY_INDEX_TABLE}
                group by base_date, symbol, exchange
                having count(*) > 1
            )
        """
    ).fetchone()[0]

    fx_duplicates = connection.execute(
        f"""
                SELECT COUNT(*)
                FROM (
                    SELECT
                        base_date,
                        symbol,
                        exchange,
                        COUNT(*) AS row_count
                    FROM {FX_TABLE}
                    GROUP BY
                        base_date,
                        symbol,
                        exchange
                    HAVING COUNT(*) > 1
                )
                """
    ).fetchone()[0]

    fixed_income_duplicates = connection.execute(
        f"""
                select count(*)
                from (
                    select base_date, symbol, exchange,
                    count(*) as row_count
                    from {FIXED_INCOME_TABLE}
                    group by base_date, symbol, exchange
                    having count(*) > 1
                )
            """
    ).fetchone()[0]

    behavior_duplicates = connection.execute(
        f"""
                    select count(*)
                    from (
                    select base_date, release_date, time, symbol, exchange,
                        count(*) as row_count
                        from {BEHAVIOR_TABLE}
                    group by base_date, release_date, time, symbol, exchange
                        having count(*) > 1
                    )
                """
    ).fetchone()[0]

    if index_null_keys > 0:
        raise ValueError(
            "The index table contains "
            f"{index_null_keys:,} rows with a null "
            "base_date or symbol."
        )

    if macro_null_keys > 0:

        LOGGER.error(
            "Invalid macro rows:\n%s",
            connection.execute(
                f"""
                    SELECT *
                    FROM {MACRO_TABLE}
                    WHERE base_date IS NULL
                       OR release_date IS NULL
                       OR symbol IS NULL
                    """
            ).fetchdf().to_string(index=False),
        )

        raise ValueError(
            "The macro table contains "
            f"{macro_null_keys:,} rows with a null "
            "base_date, release_date, or symbol."
        )

    if freight_null_keys > 0:
        raise ValueError(
            "The freight table contains "
            f"{freight_null_keys:,} rows with a null "
            "base_date, release_date, or symbol."
        )

    if volatility_null_keys > 0:
        raise ValueError(
            "The volatility index table contains "
            f"{volatility_null_keys:,} rows with a null "
            "base_date or symbol."
        )

    # add codes from here

    if industry_null_keys > 0:
        raise ValueError(
            "The industry components table contains "
            f"{industry_null_keys:,} rows with a null "
            "base_date or symbol."
        )

    if industry_index_null_keys > 0 :
        raise ValueError(
            "The industry index table contains "
            f"{industry_index_null_keys:,} rows with a null "
            "base_date or symbol."
        )

    if fx_null_keys > 0:
        raise ValueError(
            "The FX table contains "
            f"{fx_null_keys:,} rows with a null "
            "base_date or symbol."
        )

    if fixed_income_null_keys > 0 :
        raise ValueError(
            "The fixed income table contains "
            f"{fixed_income_null_keys:,} rows with a null "
            "base_date or symbol."
        )

    if behavior_null_keys > 0 :
        raise ValueError(
            "The behavior table contains "
            f"{behavior_null_keys:,} rows with a null "
            "base_date or symbol."
        )

    if index_duplicates > 0:
        LOGGER.warning(
            "Duplicate index keys detected | "
            "duplicate_groups=%d",
            index_duplicates,
        )

    if macro_duplicates > 0:
        LOGGER.warning(
            "Duplicate macro keys detected | "
            "duplicate_groups=%d",
            macro_duplicates,
        )

    if freight_duplicates > 0:
        LOGGER.warning(
            "Duplicate freight keys detected | "
            "duplicate_groups=%d",
            freight_duplicates,
        )

    if volatility_duplicates > 0:
        LOGGER.warning(
            "Duplicate volatility index keys detected | "
            "duplicate_groups=%d",
            volatility_duplicates,
        )

    # add codes from here

    if industry_duplicates > 0:
        LOGGER.warning(
            "Duplicate industry component keys detected | "
            "duplicate_groups=%d",
            industry_duplicates,
        )

    if industry_index_duplicates > 0:
        LOGGER.warning(
            "Duplicate industry index keys detected | "
            "duplicate_groups=%d",
            industry_index_duplicates,
        )

    if fx_duplicates > 0:
        LOGGER.warning(
            "Duplicate FX keys detected | "
            "duplicate_groups=%d",
            fx_duplicates,
        )

    if fixed_income_duplicates > 0:
        LOGGER.warning(
            "Duplicate fixed income keys detected | "
            "duplicate_groups=%d",
            fixed_income_duplicates,
        )

    if behavior_duplicates > 0:
        LOGGER.warning(
            "Duplicate behavior keys detected | "
            "duplicate_groups=%d",
            behavior_duplicates,
        )

    # add codes from here

    LOGGER.info(
        "Database validation completed | "
        "index_null_keys=%d | "
        "macro_null_keys=%d | "
        "freight_null_keys=%d | "
        "volatility_null_keys=%d | "
        "industry_null_keys=%d | "
        'industry_index_null_keys=%d | '
        'fx_null_keys=%d | '
        'fixed_income_null_key=%d | '
        'behavior_null_keys=%d | '
        "index_duplicate_groups=%d | "
        "macro_duplicate_groups=%d | "
        "freight_duplicate_groups=%d"
        "volatility_duplicate_groups=%d | "
        "industury_duplicate_groups=%d | "
        'industry_index_duplicates_groups=%d | '
        'fx_duplicates_groups=%d | '
        'fixed_income_duplicates_groups=%d | '
        'behavior_duplicates_groups=%d | ',
        index_null_keys,
        macro_null_keys,
        freight_null_keys,
        volatility_null_keys,
        industry_null_keys,
        industry_index_null_keys,
        fx_null_keys,
        fixed_income_null_keys,
        behavior_null_keys,
        index_duplicates,
        macro_duplicates,
        freight_duplicates,
        volatility_duplicates,
        industry_duplicates,
        industry_index_duplicates,
        fx_duplicates,
        fixed_income_duplicates,
        behavior_duplicates,
    )


# ============================================================
# Main job
# ============================================================

def build_duckdb() -> None:
    """
    Builds the metadata, market, macro, and freight DuckDB tables.
    """

    LOGGER.info(
        "DuckDB build job started | database=%s",
        DATABASE_PATH,
    )

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = None

    try:
        index_files = get_parquet_files(
            INDEX_DATA_PATH
        )

        macro_files = get_parquet_files(
            MACRO_DATA_PATH
        )

        freight_files = get_parquet_files(
            FREIGHT_DATA_PATH
        )

        volatility_files = get_parquet_files(
            VOLATILITY_DATA_PATH
        )

        # add codes from here (files input)

        industry_files = get_parquet_files(
            INDUSTRY_DATA_PATH
        )

        industry_index_files = get_parquet_files(
            INDUSTRY_INDEX_DATA_PATH
        )

        fx_files = get_parquet_files(
            FX_INDEX_DATA_PATH
        )

        fixed_income_files = [
            path for path in get_parquet_files(FIXED_INCOME_DATA_PATH)
            if FIXED_INCOME_INDEX_DATA_PATH not in path.parents
        ]

        fixed_income_index_files = get_parquet_files(
            FIXED_INCOME_INDEX_DATA_PATH
        )

        behavior_files = get_parquet_files(
            BEHAVIOR_DATA_PATH
        )

        LOGGER.info(
            "Parquet file discovery completed | "
            "index_files=%d | macro_files=%d | freight_files=%d | fixed_income_index_files=%d",
            len(index_files),
            len(macro_files),
            len(freight_files),
            len(fixed_income_index_files),
        )

        validate_parquet_columns(
            parquet_files=index_files,
            required_columns=INDEX_COLUMNS,
            data_type_name="index",
        )

        validate_parquet_columns(
            parquet_files=macro_files,
            required_columns=MACRO_COLUMNS,
            data_type_name="macro",
        )

        validate_parquet_columns(
            parquet_files=freight_files,
            required_columns=FREIGHT_COLUMNS,
            data_type_name="freight",
        )

        validate_parquet_columns(
            parquet_files=volatility_files,
            required_columns=VOLATILITY_COLUMNS,
            data_type_name="risk",
        )

        # add codes from here (validations)

        validate_parquet_columns(
            parquet_files=industry_files,
            required_columns=INDUSTRY_COLUMNS,
            data_type_name="industry",
        )

        validate_parquet_columns(
            parquet_files=industry_index_files,
            required_columns=INDUSTRY_INDEX_COLUMNS,
            data_type_name="industry",
        )

        validate_parquet_columns(
            parquet_files=fx_files,
            required_columns=FX_COLUMNS,
            data_type_name="fx"
        )

        validate_parquet_columns(
            parquet_files=fixed_income_files,
            required_columns=FIXED_INCOME_COLUMNS,
            data_type_name="fixed_income"
        )

        validate_parquet_columns(
            parquet_files=fixed_income_index_files,
            required_columns=FIXED_INCOME_INDEX_COLUMNS,
            data_type_name="fixed_income_index",
        )

        validate_parquet_columns(
            parquet_files=behavior_files,
            required_columns=BEHAVIOR_COLUMNS,
            data_type_name="behavior",
        )

        connection = duckdb.connect(
            str(DATABASE_PATH)
        )

        LOGGER.info(
            "DuckDB connection opened | database=%s",
            DATABASE_PATH,
        )

        connection.execute(
            "BEGIN TRANSACTION"
        )

        create_schemas(
            connection
        )

        metadata_rows = create_metadata_table(
            connection
        )

        index_rows = create_index_table(
            connection,
            parquet_files=index_files,
        )

        macro_rows = create_macro_table(
            connection,
            parquet_files=macro_files,
        )

        freight_rows = create_freight_table(
            connection,
            parquet_files=freight_files,
        )

        volatility_rows = create_volatility_table(
            connection,
            parquet_files=volatility_files,
        )

        # add codes from here
        industry_rows = create_industry_table(
            connection,
            parquet_files=industry_files,
        )

        industry_index_rows = create_industry_index_table(
            connection,
            parquet_files=industry_index_files,
        )

        fx_rows = create_fx_table(
            connection,
            parquet_files=fx_files,
        )

        fixed_income_rows = create_fixed_income_table(
            connection,
            parquet_files=fixed_income_files,
        )

        fixed_income_index_rows = create_fixed_income_index_table(
            connection,
            parquet_files=fixed_income_index_files,
        )

        behavior_rows = create_behavior_table(
            connection,
            parquet_files=behavior_files,
        )

        validate_database(
            connection
        )

        connection.execute(
            "COMMIT"
        )

        LOGGER.info(
            "DuckDB build job completed successfully | "
            "metadata_rows=%d | "
            "index_rows=%d | "
            "macro_rows=%d | "
            "freight_rows=%d | "
            "volatility_rows=%d | "
            "industry_rows=%d | "
            "industry_index_rows=%d | "
            'fx_index_rows=%d | fixed_income_rows=%d | '
            'behavior_rows=%d | behavior_rows=%d | '
            ,
            metadata_rows,
            index_rows,
            macro_rows,
            freight_rows,
            volatility_rows,
            industry_rows,
            industry_index_rows,
            fx_rows, fixed_income_rows, behavior_rows, behavior_rows,
        )

    except Exception:
        if connection is not None:
            try:
                connection.execute(
                    "ROLLBACK"
                )

                LOGGER.warning(
                    "DuckDB transaction rolled back."
                )

            except Exception:
                LOGGER.exception(
                    "DuckDB rollback failed."
                )

        LOGGER.exception(
            "DuckDB build job failed."
        )

        raise

    finally:
        if connection is not None:
            connection.close()

            LOGGER.info(
                "DuckDB connection closed."
            )


if __name__ == "__main__":
    build_duckdb()
