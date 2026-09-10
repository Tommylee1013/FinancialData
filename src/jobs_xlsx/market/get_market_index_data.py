from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.utils.log import setup_logger


PROJECT_ROOT = Path.cwd()
DATE_COLUMNS = ["base_date", "release_date", "time", "time_zone"]
PRICE_COLUMNS = ["open", "high", "low", "close"]
OUTPUT_COLUMNS = DATE_COLUMNS + ["symbol", "exchange", "country"] + PRICE_COLUMNS + ["volume"]


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_config(config_path: str | Path) -> dict[str, Any]:
    path = resolve_path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Market index config not found: {path}")
    with path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict) or not isinstance(config.get("job"), dict):
        raise ValueError("Config must contain a job section.")
    if not isinstance(config.get("sources"), list) or not config["sources"]:
        raise ValueError("Config must contain a non-empty sources list.")
    if "output_path" not in config["job"]:
        raise ValueError("job.output_path is required.")
    required = {"file_name", "sheet_name", "symbol", "exchange", "country"}
    for index, source in enumerate(config["sources"]):
        missing = required - set(source)
        if missing:
            raise ValueError(f"Source {index} is missing fields: {sorted(missing)}")
    return config


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in data.columns
    ]
    return data


def coerce_time(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.time
    return pd.to_datetime(series.astype(str), errors="raise").dt.time


def transform_market_index(
    frame: pd.DataFrame,
    *,
    symbol: str,
    exchange: str,
    country: str,
    value_column: str | None = None,
) -> pd.DataFrame:
    """Normalize one Excel sheet/column to market.index_data OHLCV format."""
    data = normalize_columns(frame)
    missing_dates = set(DATE_COLUMNS) - set(data.columns)
    if missing_dates:
        raise ValueError(f"Required date/time columns are missing: {sorted(missing_dates)}")

    normalized_value_column = str(value_column).strip().lower().replace(" ", "_") if value_column else None
    if normalized_value_column:
        if normalized_value_column not in data.columns:
            raise ValueError(f"Configured value_column is missing: {value_column}")
        data["close"] = data[normalized_value_column]

    if "close" not in data.columns:
        raise ValueError("The sheet must contain close or a configured value_column.")

    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    for column in ("open", "high", "low"):
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce").fillna(data["close"])
        else:
            data[column] = data["close"]
    # Keep every candle internally valid without changing the source workbook.
    # This also handles occasional vendor rows with swapped high/low values.
    price_boundaries = data[["open", "high", "low", "close"]]
    data["high"] = price_boundaries.max(axis=1)
    data["low"] = price_boundaries.min(axis=1)
    if "volume" in data.columns:
        data["volume"] = pd.to_numeric(data["volume"], errors="coerce").fillna(0.0)
    else:
        data["volume"] = 0.0

    data["base_date"] = pd.to_datetime(data["base_date"], errors="raise").dt.normalize()
    data["release_date"] = pd.to_datetime(data["release_date"], errors="raise").dt.normalize()
    data["time"] = coerce_time(data["time"])
    data["time_zone"] = data["time_zone"].astype("string").str.strip().str.upper()
    data["symbol"] = str(symbol).strip().upper()
    data["exchange"] = str(exchange).strip().upper()
    data["country"] = str(country).strip()

    data = data[OUTPUT_COLUMNS].dropna(subset=["base_date", "release_date", "close"])
    duplicate_key = ["base_date", "symbol", "exchange"]
    duplicates = data[data.duplicated(duplicate_key, keep=False)]
    if not duplicates.empty:
        raise ValueError(f"Duplicate market index rows detected for {symbol}.\n{duplicates.head(100)}")
    return data.sort_values(["symbol", "base_date", "release_date", "time"]).reset_index(drop=True)


def collect_market_index_data(config_path: str | Path) -> pd.DataFrame:
    config = load_config(config_path)
    job = config["job"]
    logger = setup_logger(
        name=__name__,
        log_path=job.get("log_path", "logs/jobs/market_index_excel_loader.log"),
    )
    frames: list[pd.DataFrame] = []
    logger.info("Market index Excel job started | config=%s", resolve_path(config_path))

    for source in config["sources"]:
        input_path = resolve_path(source["file_name"])
        if not input_path.exists():
            raise FileNotFoundError(f"Input Excel file not found: {input_path}")
        raw = pd.read_excel(
            input_path,
            sheet_name=source["sheet_name"],
            header=source.get("header", 0),
            skiprows=source.get("skiprows"),
        )
        transformed = transform_market_index(
            raw,
            symbol=source["symbol"],
            exchange=source["exchange"],
            country=source["country"],
            value_column=source.get("value_column"),
        )
        frames.append(transformed)
        logger.info(
            "Market index source loaded | file=%s | sheet=%s | symbol=%s | rows=%d",
            input_path, source["sheet_name"], source["symbol"], len(transformed),
        )

    result = pd.concat(frames, ignore_index=True)
    duplicate_key = ["base_date", "symbol", "exchange"]
    duplicates = result[result.duplicated(duplicate_key, keep=False)]
    strategy = job.get("duplicate_strategy", "error")
    if not duplicates.empty:
        if strategy == "error":
            raise ValueError(f"Duplicate rows detected after combining sources.\n{duplicates.head(100)}")
        if strategy not in {"keep_first", "keep_last"}:
            raise ValueError("duplicate_strategy must be error, keep_first, or keep_last.")
        result = result.drop_duplicates(duplicate_key, keep="first" if strategy == "keep_first" else "last")

    result = result.sort_values(["symbol", "base_date", "release_date", "time"]).reset_index(drop=True)
    output_path = resolve_path(job["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_path, index=False)
    logger.info(
        "Market index Parquet saved | output=%s | rows=%d | symbols=%d",
        output_path, len(result), result["symbol"].nunique(),
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load configured Excel market indices into Parquet.")
    parser.add_argument("config_path", nargs="?", default="config/market_index_jobs.yaml")
    args = parser.parse_args()
    collect_market_index_data(args.config_path)
