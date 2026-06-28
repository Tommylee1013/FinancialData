from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

try:
    from src.utils.log import setup_logger
except Exception:  # pragma: no cover
    import logging

    def setup_logger(name: str, log_path: str | None = None) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

            if log_path:
                Path(log_path).parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_path, encoding="utf-8")
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        return logger


# ============================================================
# Constants
# ============================================================

PROJECT_ROOT = Path.cwd()

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

DEFAULT_COLUMN_MAP = {
    "Base Date": "base_date",
    "Release Date": "release_date",
    "Time": "time",
    "Time Zone": "time_zone",
}


# ============================================================
# Path / Config
# ============================================================

def resolve_path(path_value: str | Path) -> Path:
    """
    Resolve path from project root when a relative path is given.
    """

    path = Path(path_value)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path


def load_yaml(config_path: str | Path) -> dict[str, Any]:
    """
    Load YAML configuration.
    """

    path = resolve_path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"YAML config file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(
            "YAML config must be a dictionary at the top level."
        )

    return config


def build_logger(config: dict[str, Any]):
    """
    Build logger from YAML job.log_path.
    """

    job_config = config.get("job", {})
    log_path = job_config.get(
        "log_path",
        "logs/jobs/excel_wide_value_loader.log",
    )

    return setup_logger(
        name=__name__,
        log_path=log_path,
    )


# ============================================================
# Validation
# ============================================================

def validate_config(config: dict[str, Any]) -> None:
    """
    Validate YAML structure.

    Required YAML structure:

    job:
      output_path: ...
      duplicate_strategy: error

    sources:
      - file_name: ...
        sheet_name: ...
        exchange: ...
        country: ...
    """

    job_config = config.get("job")
    if not isinstance(job_config, dict):
        raise ValueError(
            "YAML must contain job section."
        )

    if "output_path" not in job_config:
        raise ValueError(
            "YAML job section must contain output_path."
        )

    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError(
            "YAML must contain non-empty sources list."
        )

    required_source_fields = {
        "file_name",
        "sheet_name",
        "exchange",
        "country",
    }

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(
                f"Each item in sources must be a dictionary. index={index}"
            )

        missing_fields = required_source_fields - set(source)

        if missing_fields:
            raise ValueError(
                f"Source config is missing required fields. "
                f"index={index}, missing={sorted(missing_fields)}"
            )


# ============================================================
# Transform Helpers
# ============================================================

def normalize_columns(
    df: pd.DataFrame,
    column_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Normalize only fixed date/time columns.

    Symbol columns are preserved as the Excel column names.
    """

    data = df.copy()

    effective_column_map = DEFAULT_COLUMN_MAP.copy()

    if column_map:
        effective_column_map.update(column_map)

    data = data.rename(columns=effective_column_map)

    data.columns = [
        str(column).strip()
        for column in data.columns
    ]

    return data


def coerce_time_series(series: pd.Series) -> pd.Series:
    """
    Convert time-like values to python time objects.
    """

    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.time

    return pd.to_datetime(
        series.astype(str),
        errors="raise",
    ).dt.time


def transform_wide_value_sheet(
    df: pd.DataFrame,
    *,
    exchange: str,
    country: str,
    column_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Transform one Excel wide-format sheet into normalized long format.

    Input columns must include:
    - Base Date
    - Release Date
    - Time
    - Time Zone
    - symbol columns

    Output columns:
    - base_date
    - release_date
    - time
    - time_zone
    - symbol
    - exchange
    - country
    - value
    """

    data = normalize_columns(
        df,
        column_map=column_map,
    )

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
            "No symbol columns were found."
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

    long_df["time"] = coerce_time_series(
        long_df["time"]
    )

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

    long_df["exchange"] = str(exchange).strip()

    long_df["country"] = str(country).strip()

    long_df["value"] = pd.to_numeric(
        long_df["value"],
        errors="coerce",
    )

    long_df = long_df[OUTPUT_COLUMNS]

    long_df = long_df.dropna(
        subset=["value"]
    )

    return long_df


# ============================================================
# Duplicate Handling
# ============================================================

def handle_duplicates(
    df: pd.DataFrame,
    *,
    duplicate_strategy: str,
) -> pd.DataFrame:
    """
    Handle duplicated rows by full observation key.

    This loader does not collapse rows with the same base_date.
    If the same base_date has different release_date/time, it is treated
    as a different released observation and preserved.

    Supported strategies:
    - error
    - keep_first
    - keep_latest_release
    """

    key_columns = [
        "base_date",
        "release_date",
        "time",
        "time_zone",
        "symbol",
        "exchange",
    ]

    duplicated_mask = df.duplicated(
        subset=key_columns,
        keep=False,
    )

    if not duplicated_mask.any():
        return df

    duplicated_rows = df.loc[
        duplicated_mask
    ].copy()

    if duplicate_strategy == "error":
        raise ValueError(
            "Duplicate rows detected by full observation key: "
            "base_date, release_date, time, time_zone, symbol, exchange.\n"
            f"{duplicated_rows.sort_values(key_columns).head(100)}"
        )

    if duplicate_strategy == "keep_first":
        return (
            df.drop_duplicates(
                subset=key_columns,
                keep="first",
            )
            .reset_index(drop=True)
        )

    if duplicate_strategy == "keep_latest_release":
        return (
            df.sort_values(
                by=[
                    "base_date",
                    "release_date",
                    "time",
                    "time_zone",
                    "symbol",
                    "exchange",
                ]
            )
            .drop_duplicates(
                subset=key_columns,
                keep="last",
            )
            .reset_index(drop=True)
        )

    raise ValueError(
        "Invalid duplicate_strategy. "
        "Use one of: error, keep_first, keep_latest_release."
    )


# ============================================================
# Main Loader
# ============================================================

def collect_freights_data(
    config_path: str | Path,
) -> pd.DataFrame:
    """
    Read Excel sheets defined in YAML, transform them to long format,
    and save the result as one Parquet file.

    YAML source unit:
    - file_name
    - sheet_name
    - exchange
    - country
    """

    config = load_yaml(config_path)

    validate_config(config)

    logger = build_logger(config)

    job_config = config["job"]
    sources = config["sources"]

    output_path = resolve_path(
        job_config["output_path"]
    )

    duplicate_strategy = job_config.get(
        "duplicate_strategy",
        "error",
    )

    global_column_map = config.get(
        "column_map",
        {},
    ) or {}

    logger.info(
        "Excel wide value loader started | config_path=%s",
        config_path,
    )

    frames: list[pd.DataFrame] = []

    for source in sources:
        input_path = resolve_path(
            source["file_name"]
        )

        sheet_name = source["sheet_name"]
        exchange = source["exchange"]
        country = source["country"]

        header = source.get(
            "header",
            0,
        )

        skiprows = source.get(
            "skiprows",
            None,
        )

        source_column_map = global_column_map.copy()
        source_column_map.update(
            source.get("column_map", {}) or {}
        )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input Excel file not found: {input_path}"
            )

        logger.info(
            "Loading Excel sheet | file=%s | sheet=%s | exchange=%s | country=%s",
            input_path,
            sheet_name,
            exchange,
            country,
        )

        raw_data = pd.read_excel(
            input_path,
            sheet_name=sheet_name,
            header=header,
            skiprows=skiprows,
        )

        logger.info(
            "Excel sheet loaded | file=%s | sheet=%s | rows=%d | columns=%d",
            input_path,
            sheet_name,
            raw_data.shape[0],
            raw_data.shape[1],
        )

        transformed_data = transform_wide_value_sheet(
            raw_data,
            exchange=exchange,
            country=country,
            column_map=source_column_map,
        )

        if transformed_data.empty:
            logger.warning(
                "No rows remained after transform | file=%s | sheet=%s",
                input_path,
                sheet_name,
            )
            continue

        frames.append(transformed_data)

    if not frames:
        raise ValueError(
            "No rows remained after all Excel transformations."
        )

    final_data = pd.concat(
        frames,
        ignore_index=True,
    )

    before_rows = len(final_data)

    final_data = handle_duplicates(
        final_data,
        duplicate_strategy=duplicate_strategy,
    )

    after_rows = len(final_data)

    if after_rows < before_rows:
        logger.warning(
            "Duplicate rows handled | strategy=%s | before=%d | after=%d | dropped=%d",
            duplicate_strategy,
            before_rows,
            after_rows,
            before_rows - after_rows,
        )

    final_data = (
        final_data.sort_values(
            by=[
                "base_date",
                "release_date",
                "time",
                "symbol",
                "exchange",
            ]
        )
        .reset_index(drop=True)
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        final_data.to_parquet(
            output_path,
            index=False,
        )
    except ImportError as error:
        raise ImportError(
            "Parquet save requires pyarrow or fastparquet. "
            "Install one of them: pip install pyarrow"
        ) from error

    logger.info(
        "Parquet saved | output_path=%s | rows=%d | symbols=%d",
        output_path,
        len(final_data),
        final_data["symbol"].nunique(),
    )

    return final_data


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Load Excel wide value sheets into normalized long-form Parquet."
        )
    )

    parser.add_argument(
        "config_path",
        help="Path to YAML config file.",
    )

    args = parser.parse_args()

    collect_freights_data(
        args.config_path,
    )