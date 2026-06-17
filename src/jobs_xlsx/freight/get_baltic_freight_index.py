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
    / "baltic dry index.xlsx"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "freight"
    / "baltic_index.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/baltic_freight.log",
)


# ============================================================
# Metadata
# ============================================================

BALTIC_SYMBOL_INFO = pd.DataFrame(
    [
        {
            "symbol": "BDI",
            "symbol_raw": "BDI",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Dry Index",
            "release_time": "13:00:00",
        },
        {
            "symbol": "BSI",
            "symbol_raw": "BSI",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Supramax Index",
            "release_time": "13:00:00",
        },
        {
            "symbol": "BCI",
            "symbol_raw": "BCI",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Capesize Index",
            "release_time": "13:00:00",
        },
        {
            "symbol": "BCTI",
            "symbol_raw": "BCTI",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Clean Tanker Index",
            "release_time": "16:00:00",
        },
        {
            "symbol": "BPI",
            "symbol_raw": "BPI",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Panamax Index",
            "release_time": "13:00:00",
        },
        {
            "symbol": "BHSI",
            "symbol_raw": "BHSI",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Handysize Index",
            "release_time": "13:00:00",
        },
        {
            "symbol": "BLNG",
            "symbol_raw": "BLNG",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic LNG Index",
            "release_time": "11:00:00",
        },
        {
            "symbol": "BLPG",
            "symbol_raw": "BLPG",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic LPG Index",
            "release_time": "16:00:00",
        },
        {
            "symbol": "FBX",
            "symbol_raw": "FBX",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Freightos Baltic Index",
            "release_time": "14:00:00",
        },
        {
            "symbol": "BDTI",
            "symbol_raw": "BDTI",
            "exchange": "BALTIC",
            "country": "United Kingdom",
            "name": "Baltic Dirty Tanker Index",
            "release_time": "16:00:00",
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


def transform_baltic_freight_data(
    df: pd.DataFrame,
    symbol_info: pd.DataFrame = BALTIC_SYMBOL_INFO,
) -> pd.DataFrame:
    """
    Transforms Baltic freight index data from wide format
    into normalized value-based time-series format.

    Important:
    - release time is assigned by symbol using Baltic metadata.
    - time_zone is preserved from the Excel file because it already reflects
      UTC+0 / UTC+1 according to London daylight-saving time.
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

    required_metadata_columns = {
        "symbol",
        "exchange",
        "country",
        "release_time",
    }

    missing_metadata_columns = (
        required_metadata_columns
        - set(symbol_info.columns)
    )

    if missing_metadata_columns:
        raise ValueError(
            "Required Baltic metadata columns are missing: "
            f"{sorted(missing_metadata_columns)}"
        )

    symbol_info = symbol_info.copy()

    symbol_info["symbol"] = (
        symbol_info["symbol"]
        .astype("string")
        .str.strip()
    )

    symbol_info["exchange"] = (
        symbol_info["exchange"]
        .astype("string")
        .str.strip()
    )

    symbol_info["country"] = (
        symbol_info["country"]
        .astype("string")
        .str.strip()
    )

    symbol_info["release_time"] = (
        symbol_info["release_time"]
        .astype("string")
        .str.strip()
    )

    duplicated_metadata_symbols = symbol_info[
        symbol_info.duplicated(
            subset=["symbol"],
            keep=False,
        )
    ]

    if not duplicated_metadata_symbols.empty:
        raise ValueError(
            "Duplicate symbols detected in Baltic metadata.\n"
            f"{duplicated_metadata_symbols}"
        )

    symbol_columns = [
        column
        for column in data.columns
        if column not in DATE_COLUMNS
    ]

    if not symbol_columns:
        raise ValueError(
            "No freight symbol columns were found."
        )

    symbol_columns = [
        str(column).strip()
        for column in symbol_columns
    ]

    valid_symbols = set(
        symbol_info["symbol"].astype(str)
    )

    unknown_symbols = sorted(
        set(symbol_columns)
        - valid_symbols
    )

    if unknown_symbols:
        raise ValueError(
            "Symbols are not defined in Baltic metadata: "
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
                "release_time",
            ]
        ],
        how="left",
        on="symbol",
        validate="many_to_one",
    )

    unmapped_symbols = (
        long_df.loc[
            long_df["exchange"].isna()
            | long_df["country"].isna()
            | long_df["release_time"].isna(),
            "symbol",
        ]
        .drop_duplicates()
        .tolist()
    )

    if unmapped_symbols:
        raise ValueError(
            "Failed to map Baltic metadata for symbols: "
            f"{unmapped_symbols}"
        )

    # --------------------------------------------------------
    # Only overwrite release time by symbol.
    # Keep Excel time_zone as-is: UTC+0 / UTC+1.
    # --------------------------------------------------------

    long_df["time"] = long_df["release_time"]

    long_df["time"] = (
        pd.to_datetime(
            long_df["time"],
            format="%H:%M:%S",
            errors="raise",
        )
        .dt.strftime("%H:%M:%S")
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
            "Duplicate Baltic freight rows detected.\n"
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

def collect_baltic_freight_data() -> None:
    """
    Reads the first sheet of the Baltic freight Excel file,
    transforms it into normalized value format,
    and saves it as Parquet.
    """

    LOGGER.info(
        "Baltic freight data job started | input_path=%s",
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

    transformed_data = transform_baltic_freight_data(
        raw_data
    )

    if transformed_data.empty:
        raise ValueError(
            "No rows remained after Baltic freight transformation."
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
        "Baltic freight Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(transformed_data),
    )


if __name__ == "__main__":
    collect_baltic_freight_data()