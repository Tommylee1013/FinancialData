from pathlib import Path

import pandas as pd

from src.utils.log import setup_logger


# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path.cwd()

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "volatility"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "risk"
    / "volatility_excel.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/nkvi_vstoxx_volatility.log",
)


# ============================================================
# Metadata
# ============================================================

VOLATILITY_SYMBOL_INFO = pd.DataFrame(
    [
        {
            "file_name": "NKVI.xlsx",
            "sheet_name": "NKVI",
            "symbol": "NKVI",
            "exchange": "OSE",
            "country": "Japan",
            "name": "NIKKEI Average Volatility Index",
        },
        {
            "file_name": "VSTOXX.xlsx",
            "sheet_name": "VSTOXX",
            "symbol": "VSTOXX",
            "exchange": "STOXX",
            "country": "Europe",
            "name": "EUROSTOXX 50 Volatility Index",
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

VALUE_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
]

OUTPUT_COLUMNS = [
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


# ============================================================
# Transform
# ============================================================

def normalize_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalizes NKVI / VSTOXX Excel columns into volatility_data format.
    """

    data = df.copy()

    data = data.rename(
        columns={
            "Base Date": "base_date",
            "Release Date": "release_date",
            "Time": "time",
            "Time Zone": "time_zone",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    data.columns = [
        str(column).strip().lower()
        for column in data.columns
    ]

    return data


def transform_volatility_data(
    df: pd.DataFrame,
    symbol: str,
    exchange: str,
    country: str,
) -> pd.DataFrame:
    """
    Transforms a single volatility index Excel sheet into normalized
    volatility_data format.

    NKVI and VSTOXX do not have meaningful traded volume,
    so volume is filled with 0.
    """

    data = normalize_columns(df)

    required_columns = set(
        DATE_COLUMNS
        + VALUE_COLUMNS
    )

    missing_columns = (
        required_columns
        - set(data.columns)
    )

    if missing_columns:
        raise ValueError(
            "Required volatility columns are missing: "
            f"{sorted(missing_columns)}"
        )

    data = data[
        DATE_COLUMNS
        + VALUE_COLUMNS
    ].copy()

    data["base_date"] = pd.to_datetime(
        data["base_date"],
        errors="raise",
    ).dt.normalize()

    data["release_date"] = pd.to_datetime(
        data["release_date"],
        errors="raise",
    ).dt.normalize()

    data["time"] = pd.to_datetime(
        data["time"].astype(str),
        errors="raise",
    ).dt.time

    data["time_zone"] = (
        data["time_zone"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    data["symbol"] = str(symbol).strip().upper()
    data["exchange"] = str(exchange).strip().upper()
    data["country"] = str(country).strip()

    for column in VALUE_COLUMNS:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    data["volume"] = 0

    data = data[OUTPUT_COLUMNS]

    data = data.dropna(
        subset=VALUE_COLUMNS,
        how="all",
    )

    duplicated_rows = data[
        data.duplicated(
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
            f"Duplicate volatility rows detected for symbol={symbol}.\n"
            f"{duplicated_rows}"
        )

    data = (
        data.sort_values(
            by=[
                "base_date",
                "symbol",
            ]
        )
        .reset_index(drop=True)
    )

    return data


def transform_excel_volatility_data(
    symbol_info: pd.DataFrame = VOLATILITY_SYMBOL_INFO,
) -> pd.DataFrame:
    """
    Reads NKVI and VSTOXX Excel files, transforms them into volatility_data
    format, and concatenates them into one DataFrame.
    """

    frames: list[pd.DataFrame] = []

    for row in symbol_info.to_dict("records"):
        input_path = (
            INPUT_DIR
            / row["file_name"]
        )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input Excel file not found: {input_path}"
            )

        LOGGER.info(
            "Volatility Excel loading | symbol=%s | input_path=%s",
            row["symbol"],
            input_path,
        )

        raw_data = pd.read_excel(
            input_path,
            sheet_name=row["sheet_name"],
        )

        LOGGER.info(
            "Volatility Excel loaded | symbol=%s | rows=%d | columns=%d",
            row["symbol"],
            raw_data.shape[0],
            raw_data.shape[1],
        )

        transformed_data = transform_volatility_data(
            df=raw_data,
            symbol=row["symbol"],
            exchange=row["exchange"],
            country=row["country"],
        )

        frames.append(transformed_data)

    if not frames:
        raise ValueError(
            "No volatility data was transformed."
        )

    result = pd.concat(
        frames,
        axis=0,
        ignore_index=True,
    )

    duplicated_rows = result[
        result.duplicated(
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
            "Duplicate volatility rows detected after concat.\n"
            f"{duplicated_rows}"
        )

    result = (
        result.sort_values(
            by=[
                "base_date",
                "symbol",
            ]
        )
        .reset_index(drop=True)
    )

    return result


# ============================================================
# Main job
# ============================================================

def collect_volatility_data_from_excel() -> None:
    """
    Reads NKVI and VSTOXX Excel files from data/volatility,
    transforms them into volatility_data column structure,
    and saves the result as Parquet.
    """

    LOGGER.info(
        "NKVI / VSTOXX volatility data job started | input_dir=%s",
        INPUT_DIR,
    )

    transformed_data = transform_excel_volatility_data()

    if transformed_data.empty:
        raise ValueError(
            "No rows remained after NKVI / VSTOXX volatility transformation."
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
        "NKVI / VSTOXX volatility Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(transformed_data),
    )


if __name__ == "__main__":
    collect_volatility_data_from_excel()