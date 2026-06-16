from __future__ import annotations

from datetime import time
from pathlib import Path

import pandas as pd

from src.utils.log import setup_logger


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path.cwd()

METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "metadata.xlsx"
)

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "industry"
    / "cfm"
    / "Index.xlsx"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "industry"
    / "index"
    / "cfm_price_index.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/cfm_price_index.log",
)


# ============================================================
# Constants
# ============================================================

SHEET_NAME = "Index"

INDEX_COLUMN_NAME_MAP = {
    "DRAM Index": "CFM DRAM Price Index",
    "NAND Index": "CFM NAND Price Index",
}

DATE_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
]

OUTPUT_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "value",
]


# ============================================================
# Text normalization
# ============================================================

def normalize_text_value(
    value: object,
) -> str:
    """
    Normalizes text values.
    """

    if pd.isna(value):
        return ""

    return (
        str(value)
        .replace("\xa0", " ")
        .replace("μ", "µ")
        .strip()
    )


def normalize_match_key(
    value: object,
) -> str:
    """
    Produces case-insensitive and whitespace-normalized matching key.
    """

    return " ".join(
        normalize_text_value(value)
        .lower()
        .split()
    )


def normalize_column_name(
    column_name: object,
) -> str:
    """
    Normalizes Excel column names to lowercase snake_case.
    """

    return (
        normalize_text_value(column_name)
        .lower()
        .replace(" ", "_")
    )


# ============================================================
# Metadata
# ============================================================

def load_metadata(
    metadata_path: Path = METADATA_PATH,
) -> pd.DataFrame:
    """
    Loads metadata.xlsx and normalizes column names.
    """

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {metadata_path}"
        )

    metadata = pd.read_excel(
        metadata_path,
        sheet_name="Master",
        dtype="string",
    )

    metadata.columns = (
        metadata.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    string_columns = metadata.select_dtypes(
        include=[
            "object",
            "string",
        ]
    ).columns

    for column in string_columns:
        metadata[column] = (
            metadata[column]
            .astype("string")
            .str.strip()
        )

    return metadata


def get_cfm_index_symbol_info() -> pd.DataFrame:
    """
    Loads CFM index metadata rows only.

    Expected metadata examples:
        Industry DRAM         INDEX CFMDRAMPI ...
        Industry Flash Memory INDEX CFMNANDPI ...
    """

    metadata = load_metadata()

    required_columns = {
        "asset_class",
        "category",
        "instrument_type",
        "symbol",
        "exchange",
        "country",
        "name",
    }

    missing_columns = required_columns - set(metadata.columns)

    if missing_columns:
        raise ValueError(
            "Required metadata columns are missing: "
            f"{sorted(missing_columns)}"
        )

    symbol_info = metadata[
        (metadata["asset_class"].str.upper() == "INDUSTRY")
        & (metadata["exchange"].str.upper() == "CFM")
        & (metadata["instrument_type"].str.upper() == "INDEX")
    ][
        [
            "category",
            "instrument_type",
            "symbol",
            "exchange",
            "country",
            "name",
        ]
    ].copy()

    if symbol_info.empty:
        raise ValueError(
            "No CFM index metadata rows found."
        )

    symbol_info["category"] = (
        symbol_info["category"]
        .astype("string")
        .str.strip()
    )

    symbol_info["instrument_type"] = (
        symbol_info["instrument_type"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    symbol_info["symbol"] = (
        symbol_info["symbol"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    symbol_info["exchange"] = (
        symbol_info["exchange"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    symbol_info["country"] = (
        symbol_info["country"]
        .astype("string")
        .str.strip()
    )

    symbol_info["name"] = symbol_info["name"].map(
        normalize_text_value
    )

    symbol_info["match_name"] = symbol_info["name"].map(
        normalize_match_key
    )

    missing_rows = symbol_info[
        symbol_info[
            [
                "symbol",
                "exchange",
                "country",
                "name",
                "match_name",
            ]
        ].isna().any(axis=1)
    ]

    if not missing_rows.empty:
        raise ValueError(
            "CFM index metadata contains missing values.\n"
            f"{missing_rows}"
        )

    duplicated_names = symbol_info[
        symbol_info["match_name"].duplicated(keep=False)
    ]

    if not duplicated_names.empty:
        raise ValueError(
            "Duplicate CFM index metadata names detected.\n"
            f"{duplicated_names.sort_values(by=['match_name', 'symbol'])}"
        )

    duplicated_symbols = symbol_info[
        symbol_info["symbol"].duplicated(keep=False)
    ]

    if not duplicated_symbols.empty:
        raise ValueError(
            "Duplicate CFM index metadata symbols detected.\n"
            f"{duplicated_symbols.sort_values(by=['symbol', 'name'])}"
        )

    LOGGER.info(
        "CFM index metadata loaded | symbols=%d",
        len(symbol_info),
    )

    return symbol_info.reset_index(drop=True)


def map_index_name_to_symbol(
    metadata_name: str,
    symbol_info: pd.DataFrame,
) -> dict:
    """
    Maps CFM index metadata name to symbol information.
    """

    match_name = normalize_match_key(
        metadata_name
    )

    matched = symbol_info[
        symbol_info["match_name"].eq(match_name)
    ]

    if matched.empty:
        available_names = (
            symbol_info["name"]
            .dropna()
            .drop_duplicates()
            .sort_values()
            .tolist()
        )

        raise ValueError(
            "CFM index name is not mapped in metadata.name | "
            f"name={metadata_name}\n"
            f"Available names: {available_names}"
        )

    if len(matched) > 1:
        raise ValueError(
            "Multiple CFM index metadata rows matched one name.\n"
            f"name={metadata_name}\n"
            f"{matched}"
        )

    row = matched.iloc[0]

    return {
        "symbol": str(row["symbol"]).strip().upper(),
        "exchange": str(row["exchange"]).strip().upper(),
        "country": str(row["country"]).strip(),
    }


# ============================================================
# Time parser
# ============================================================

def parse_time_series(
    values: pd.Series,
) -> pd.Series:
    """
    Parses Excel time values safely.
    """

    def parse_one(value: object) -> time:
        if isinstance(value, time):
            return value

        if pd.isna(value):
            raise ValueError(
                "Missing time value detected."
            )

        if isinstance(value, pd.Timestamp):
            return value.time()

        parsed = pd.to_datetime(
            str(value),
            format="%H:%M:%S",
            errors="coerce",
        )

        if pd.isna(parsed):
            parsed = pd.to_datetime(
                str(value),
                format="%H:%M",
                errors="coerce",
            )

        if pd.isna(parsed):
            raise ValueError(
                f"Failed to parse time value: {value}"
            )

        return parsed.time()

    return values.map(parse_one)


# ============================================================
# Transform
# ============================================================

def normalize_date_time_columns(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalizes Base Date, Release Date, Time, Time Zone columns.
    """

    result = data.copy()

    result.columns = [
        normalize_column_name(column)
        for column in result.columns
    ]

    required_columns = {
        "base_date",
        "release_date",
        "time",
        "time_zone",
    }

    missing_columns = required_columns - set(result.columns)

    if missing_columns:
        raise ValueError(
            "Required date/time columns are missing from CFM index data: "
            f"{sorted(missing_columns)}"
        )

    result["base_date"] = pd.to_datetime(
        result["base_date"],
        errors="raise",
    ).dt.normalize()

    result["release_date"] = pd.to_datetime(
        result["release_date"],
        errors="raise",
    ).dt.normalize()

    result["time"] = parse_time_series(
        result["time"]
    )

    result["time_zone"] = (
        result["time_zone"]
        .astype("string")
        .str.strip()
    )

    return result


def transform_cfm_price_index_data(
    df: pd.DataFrame,
    symbol_info: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transforms CFM price index Excel data.

    Input:
        Base Date, Release Date, Time, Time Zone, DRAM Index, NAND Index

    Output:
        base_date, release_date, time, time_zone,
        symbol, exchange, country, value
    """

    data = normalize_date_time_columns(
        df
    )

    transformed_parts = []

    for source_column, metadata_name in INDEX_COLUMN_NAME_MAP.items():
        normalized_source_column = normalize_column_name(
            source_column
        )

        if normalized_source_column not in data.columns:
            raise ValueError(
                "Required CFM index column is missing: "
                f"{source_column}"
            )

        mapped = map_index_name_to_symbol(
            metadata_name=metadata_name,
            symbol_info=symbol_info,
        )

        part = data[
            [
                "base_date",
                "release_date",
                "time",
                "time_zone",
                normalized_source_column,
            ]
        ].copy()

        part = part.rename(
            columns={
                normalized_source_column: "value",
            }
        )

        part["symbol"] = mapped["symbol"]
        part["exchange"] = mapped["exchange"]
        part["country"] = mapped["country"]

        part["value"] = pd.to_numeric(
            part["value"],
            errors="coerce",
        )

        part = part[
            OUTPUT_COLUMNS
        ]

        transformed_parts.append(
            part
        )

    result = pd.concat(
        transformed_parts,
        ignore_index=True,
    )

    result = result.dropna(
        subset=[
            "value",
        ]
    )

    duplicated_rows = result[
        result.duplicated(
            subset=[
                "base_date",
                "release_date",
                "time",
                "symbol",
                "exchange",
            ],
            keep=False,
        )
    ]

    if not duplicated_rows.empty:
        raise ValueError(
            "Duplicate CFM price index rows detected.\n"
            f"{duplicated_rows}"
        )

    result = (
        result.sort_values(
            by=[
                "base_date",
                "release_date",
                "time",
                "symbol",
            ]
        )
        .reset_index(drop=True)
    )

    return result


# ============================================================
# Main job
# ============================================================

def collect_cfm_price_index_data() -> None:
    """
    Reads CFM Index.xlsx,
    transforms CFM DRAM Price Index and CFM NAND Price Index,
    and saves them as Parquet.
    """

    LOGGER.info(
        "CFM price index data job started | input_path=%s | metadata_path=%s",
        INPUT_PATH,
        METADATA_PATH,
    )

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input Excel file not found: {INPUT_PATH}"
        )

    symbol_info = get_cfm_index_symbol_info()

    raw_data = pd.read_excel(
        INPUT_PATH,
        sheet_name=SHEET_NAME,
        header=0,
    )

    LOGGER.info(
        "CFM price index Excel sheet loaded | rows=%d | columns=%d",
        raw_data.shape[0],
        raw_data.shape[1],
    )

    transformed_data = transform_cfm_price_index_data(
        df=raw_data,
        symbol_info=symbol_info,
    )

    if transformed_data.empty:
        raise ValueError(
            "No rows remained after CFM price index transformation."
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    transformed_data.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    LOGGER.info(
        "CFM price index Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(transformed_data),
    )


if __name__ == "__main__":
    collect_cfm_price_index_data()