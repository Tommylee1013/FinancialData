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
    / "Baltic air freight index.xlsx"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "freight"
    / "baltic_air_freight_index.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/baltic_air_freight.log",
)


# ============================================================
# Metadata
# ============================================================

BALTIC_AIR_FREIGHT_SYMBOL_INFO = pd.DataFrame(
    [
        {
            "symbol": "BAI00",
            "symbol_raw": "BAI00",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Air Freight Index",
        },
        {
            "symbol": "BAI20",
            "symbol_raw": "BAI20",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Air Freight Index Route 20",
        },
        {
            "symbol": "BAI30",
            "symbol_raw": "BAI30",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Air Freight Index Route 30",
        },
        {
            "symbol": "BAI40",
            "symbol_raw": "BAI40",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Air Freight Index Route 40",
        },
        {
            "symbol": "BAI50",
            "symbol_raw": "BAI50",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Air Freight Index Route 50",
        },
        {
            "symbol": "BAI60",
            "symbol_raw": "BAI60",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Air Freight Index Route 60",
        },
        {
            "symbol": "BAI80",
            "symbol_raw": "BAI80",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Air Freight Index Route 80",
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
    Normalizes fixed date/time columns while preserving symbol columns.
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


def transform_baltic_air_freight_data(
    df: pd.DataFrame,
    symbol_info: pd.DataFrame = BALTIC_AIR_FREIGHT_SYMBOL_INFO,
) -> pd.DataFrame:
    """
    Transforms Baltic air freight index data from wide format
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

    symbol_columns = [
        column
        for column in data.columns
        if column not in DATE_COLUMNS
    ]

    if not symbol_columns:
        raise ValueError(
            "No Baltic air freight symbol columns were found."
        )

    valid_symbols = set(
        symbol_info["symbol"].astype(str)
    )

    unknown_symbols = sorted(
        set(symbol_columns)
        - valid_symbols
    )

    if unknown_symbols:
        raise ValueError(
            "Symbols are not defined in Baltic air freight metadata: "
            f"{unknown_symbols}"
        )

    long_df = data.melt(
        id_vars=DATE_COLUMNS,
        value_vars=symbol_columns,
        var_name="symbol",
        value_name="value",
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
            "Duplicate Baltic air freight rows detected.\n"
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

def collect_baltic_air_freight_data() -> None:
    """
    Reads the first sheet of the Baltic air freight Excel file,
    transforms it into normalized value format,
    and saves it as Parquet.
    """

    LOGGER.info(
        "Baltic air freight data job started | input_path=%s",
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

    transformed_data = transform_baltic_air_freight_data(
        raw_data
    )

    if transformed_data.empty:
        raise ValueError(
            "No rows remained after Baltic air freight transformation."
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
        "Baltic air freight Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(transformed_data),
    )


if __name__ == "__main__":
    collect_baltic_air_freight_data()