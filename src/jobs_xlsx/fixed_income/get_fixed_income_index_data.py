from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.jobs_xlsx.market.get_market_index_data import (
    load_config,
    resolve_path,
    transform_market_index,
)
from src.utils.log import setup_logger


def collect_fixed_income_index_data(config_path: str | Path) -> pd.DataFrame:
    """Load configured bond-index workbooks into fixed-income OHLCV parquet."""
    config = load_config(config_path)
    job = config["job"]
    logger = setup_logger(
        name=__name__,
        log_path=job.get("log_path", "logs/jobs/fixed_income_index_excel_loader.log"),
    )
    frames: list[pd.DataFrame] = []
    for source in config["sources"]:
        input_path = resolve_path(source["file_name"])
        raw = pd.read_excel(
            input_path,
            sheet_name=source["sheet_name"],
            header=source.get("header", 0),
            skiprows=source.get("skiprows"),
        )
        frames.append(transform_market_index(
            raw,
            symbol=source["symbol"],
            exchange=source["exchange"],
            country=source["country"],
            value_column=source.get("value_column"),
        ))

    result = pd.concat(frames, ignore_index=True)
    duplicate_key = ["base_date", "symbol", "exchange"]
    duplicates = result[result.duplicated(duplicate_key, keep=False)]
    strategy = job.get("duplicate_strategy", "error")
    if not duplicates.empty:
        if strategy == "error":
            raise ValueError(f"Duplicate bond-index rows detected.\n{duplicates.head(100)}")
        result = result.drop_duplicates(
            duplicate_key,
            keep="first" if strategy == "keep_first" else "last",
        )

    result = result.sort_values(["symbol", "base_date", "release_date", "time"]).reset_index(drop=True)
    output_path = resolve_path(job["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output_path, index=False)
    logger.info(
        "Fixed-income index Parquet saved | output=%s | rows=%d | symbols=%d",
        output_path, len(result), result["symbol"].nunique(),
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load configured fixed-income indices into Parquet.")
    parser.add_argument("config_path", nargs="?", default="config/fixed_income_index_jobs.yaml")
    args = parser.parse_args()
    collect_fixed_income_index_data(args.config_path)
