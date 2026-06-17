from pathlib import Path
import pandas as pd

from src.utils.log import setup_logger

# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path.cwd()

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "freight"
    / "US Rail Traffic.xlsx"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "freight"
    / "us_rail_traffic.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/us_rail_freight.log",
)


# ============================================================
# Metadata
# ============================================================

US_RAIL_SYMBOL_INFO = pd.DataFrame(
    [
        {
            "column_name": "USRT",
            "symbol": "USRT",
            "symbol_raw": "USRT",
            "exchange": "AAR",
            "country": "United States",
            "name": "US Weekly Rail Traffic",
        },
    ]
)


# ============================================================
# Expected columns
# ============================================================

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
# Transform
# ============================================================

def normalize_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalizes fixed date/time columns while preserving data columns.
    """

    data = df.copy()

    data = data.rename(
        columns={
            "Base Date": "base_date",
            "Release Date": "release_date",
            "Time": "time",
            "Time Zone": "time_zone",
        }
    )

    data.columns = [
        str(column).strip()
        for column in data.columns
    ]

    return data


def transform_us_rail_freight_data(
    df: pd.DataFrame,
    symbol_info: pd.DataFrame = US_RAIL_SYMBOL_INFO,
) -> pd.DataFrame:
    """
    Transforms US weekly rail traffic data from wide format
    into normalized value-based time-series format.
    """

    data = normalize_columns(df)

    missing_date_columns = (
        set(DATE_COLUMNS)
        - set(data.columns)
    )

    if missing_date_columns:
        raise ValueError(
            "Required date/time columns are missing: "
            f"{sorted(missing_date_columns)}"
        )

    column_mapping = dict(
        zip(
            symbol_info["column_name"],
            symbol_info["symbol"],
        )
    )

    value_columns = [
        column
        for column in data.columns
        if column not in DATE_COLUMNS
    ]

    if not value_columns:
        raise ValueError(
            "No US rail traffic data columns were found."
        )

    unknown_columns = sorted(
        set(value_columns)
        - set(column_mapping)
    )

    if unknown_columns:
        raise ValueError(
            "Excel columns are not defined in US rail metadata: "
            f"{unknown_columns}"
        )

    long_df = data.melt(
        id_vars=DATE_COLUMNS,
        value_vars=value_columns,
        var_name="column_name",
        value_name="value",
    )

    long_df["symbol"] = (
        long_df["column_name"]
        .map(column_mapping)
    )

    unmapped_columns = (
        long_df.loc[
            long_df["symbol"].isna(),
            "column_name",
        ]
        .drop_duplicates()
        .tolist()
    )

    if unmapped_columns:
        raise ValueError(
            "Failed to map Excel columns to symbols: "
            f"{unmapped_columns}"
        )

    long_df["base_date"] = pd.to_datetime(
        long_df["base_date"],
        errors="raise",
    ).dt.normalize()

    long_df["release_date"] = pd.to_datetime(
        long_df["release_date"],
        errors="raise",
    ).dt.normalize()

    long_df["time"] = pd.to_datetime(
        long_df["time"].astype(str),
        errors="raise",
    ).dt.time

    long_df["time_zone"] = (
        long_df["time_zone"]
        .astype("string")
        .str.strip()
    )

    long_df["symbol"] = (
        long_df["symbol"]
        .astype("string")
        .str.strip()
    )

    long_df["value"] = pd.to_numeric(
        long_df["value"],
        errors="coerce",
    )

    long_df = long_df.merge(
        symbol_info[
            [
                "symbol",
                "exchange",
                "country",
            ]
        ],
        how="left",
        on="symbol",
        validate="many_to_one",
    )

    unmapped_symbols = (
        long_df.loc[
            long_df["exchange"].isna()
            | long_df["country"].isna(),
            "symbol",
        ]
        .drop_duplicates()
        .tolist()
    )

    if unmapped_symbols:
        raise ValueError(
            "Failed to map exchange or country for symbols: "
            f"{unmapped_symbols}"
        )

    long_df = long_df[OUTPUT_COLUMNS]

    long_df = long_df.dropna(
        subset=["value"]
    )

    duplicated_rows = long_df[
        long_df.duplicated(
            subset=[
                "base_date",
                "symbol",
                "exchange",
            ],
            keep=False,
        )
    ]

    if not duplicated_rows.empty:
        raise ValueError(
            "Duplicate US rail traffic rows detected.\n"
            f"{duplicated_rows}"
        )

    long_df = (
        long_df.sort_values(
            by=[
                "base_date",
                "symbol",
            ]
        )
        .reset_index(drop=True)
    )

    return long_df


# ============================================================
# Main job
# ============================================================

def collect_us_rail_freight_data() -> None:
    """
    Reads the first sheet of the US Rail Traffic Excel file,
    transforms it into normalized value format,
    and saves it as Parquet.
    """

    LOGGER.info(
        "US rail freight data job started | input_path=%s",
        INPUT_PATH,
    )

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input Excel file not found: {INPUT_PATH}"
        )

    raw_data = pd.read_excel(
        INPUT_PATH,
        sheet_name=0,
    )

    LOGGER.info(
        "Excel file loaded | rows=%d | columns=%d",
        raw_data.shape[0],
        raw_data.shape[1],
    )

    transformed_data = transform_us_rail_freight_data(
        raw_data
    )

    if transformed_data.empty:
        raise ValueError(
            "No rows remained after US rail traffic transformation."
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
        "US rail traffic Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(transformed_data),
    )


if __name__ == "__main__":
    collect_us_rail_freight_data()