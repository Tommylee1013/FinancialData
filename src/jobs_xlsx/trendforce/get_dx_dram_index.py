from __future__ import annotations

from datetime import time
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
    / "industry"
    / "TrendForce"
    / "Index.xlsx"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "industry"
    / "index"
    / "dxi.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/trendforce_dxi.log",
)


# ============================================================
# Constants
# ============================================================

SHEET_NAME = "DXI"

SYMBOL = "DXI"
EXCHANGE = "DRAMEXCHANGE"
COUNTRY = "Taiwan"

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
# Helpers
# ============================================================

def normalize_column_name(
    column_name: object,
) -> str:
    """
    Normalizes Excel column names to lowercase snake_case.
    """

    normalized = (
        str(column_name)
        .strip()
        .lower()
        .replace(" ", "_")
    )

    return normalized


def parse_time_series(
    values: pd.Series,
) -> pd.Series:
    """
    Parses Excel time values safely.

    Handles:
        - datetime.time
        - pandas Timestamp / datetime
        - strings like 18:10:00
        - strings like 18:10
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

def transform_dxi_index_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transforms DRAMExchange DXI data into normalized
    index schema.

    Input:
        Base Date, Release Date, Time, Time Zone, DXI, Volume

    Output:
        base_date, release_date, time, time_zone,
        symbol, exchange, country, value
    """

    data = df.copy()

    data.columns = [
        normalize_column_name(column)
        for column in data.columns
    ]

    required_columns = {
        "base_date",
        "release_date",
        "time",
        "time_zone",
        "dxi",
    }

    missing_columns = (
        required_columns
        - set(data.columns)
    )

    if missing_columns:
        raise ValueError(
            "Required columns are missing from DXI data: "
            f"{sorted(missing_columns)}"
        )

    data["base_date"] = pd.to_datetime(
        data["base_date"],
        errors="raise",
    ).dt.normalize()

    data["release_date"] = pd.to_datetime(
        data["release_date"],
        errors="raise",
    ).dt.normalize()

    data["time"] = parse_time_series(
        data["time"]
    )

    data["time_zone"] = (
        data["time_zone"]
        .astype("string")
        .str.strip()
    )

    data["symbol"] = SYMBOL
    data["exchange"] = EXCHANGE
    data["country"] = COUNTRY

    data["value"] = pd.to_numeric(
        data["dxi"],
        errors="coerce",
    )

    data = data[
        OUTPUT_COLUMNS
    ]

    data = data.dropna(
        subset=[
            "value",
        ]
    )

    duplicated_rows = data[
        data.duplicated(
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
            "Duplicate DXI rows detected.\n"
            f"{duplicated_rows}"
        )

    data = (
        data.sort_values(
            by=[
                "base_date",
                "release_date",
                "time",
                "symbol",
            ]
        )
        .reset_index(drop=True)
    )

    return data


# ============================================================
# Main job
# ============================================================

def collect_dxi_index_data() -> None:
    """
    Reads TrendForce Index.xlsx / DXI sheet,
    transforms DXI into normalized index schema,
    and saves it as Parquet.
    """

    LOGGER.info(
        "DXI data job started | input_path=%s | sheet=%s",
        INPUT_PATH,
        SHEET_NAME,
    )

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input Excel file not found: {INPUT_PATH}"
        )

    raw_data = pd.read_excel(
        INPUT_PATH,
        sheet_name=SHEET_NAME,
        header=0,
    )

    LOGGER.info(
        "DXI Excel sheet loaded | rows=%d | columns=%d",
        raw_data.shape[0],
        raw_data.shape[1],
    )

    transformed_data = transform_dxi_index_data(
        raw_data
    )

    if transformed_data.empty:
        raise ValueError(
            "No rows remained after DXI transformation."
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
        "DXI Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(transformed_data),
    )


if __name__ == "__main__":
    collect_dxi_index_data()