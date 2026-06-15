from pathlib import Path

import pandas as pd
from tvDatafeed import Interval

from src.dataloader.data_downloader import get_data_from_tradingview
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

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "risk"
    / "volatility.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/volatility.log",
)


# ============================================================
# Const Values
# ============================================================

N_BARS = 13000
VERBOSE = True
NUM_TRIALS = 5

EXCLUDED_COUNTRIES = {
    "Europe",
    "Japan",
}

TARGET_SYMBOLS = {
    "VIX",
    "VVIX",
    "GAMMA",
    "SKEW",
    "VXN",
    "VSTOXX",
    "NKVI",
    "VHSI",
    "VKOSPI",
    "VXEEM",
    "MOVE",
    "GVZ",
    "VXGDX",
    "VXSLV",
    "OVX",
    "BITVX",
}

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
    )

    return metadata


def get_volatility_symbol_info() -> pd.DataFrame:
    """
    Returns TradingView query information for volatility index data.

    SYMBOL_RAW is used for TradingView requests.
    SYMBOL is used for the final saved Parquet symbol.
    """

    metadata = load_metadata()

    required_columns = {
        "asset_class",
        "category",
        "instrument_type",
        "symbol",
        "symbol_raw",
        "exchange",
        "country",
    }

    missing_columns = required_columns - set(metadata.columns)

    if missing_columns:
        raise ValueError(
            "Required metadata columns are missing: "
            f"{sorted(missing_columns)}"
        )

    for column in required_columns:
        metadata[column] = (
            metadata[column]
            .astype("string")
            .str.strip()
        )

    symbol_upper = metadata["symbol"].str.upper()

    sub = metadata[
        (metadata["asset_class"].str.upper() == "RISK")
        & (metadata["instrument_type"].str.upper() == "INDEX")
        & symbol_upper.isin(TARGET_SYMBOLS)
        & ~metadata["country"].isin(EXCLUDED_COUNTRIES)
    ][
        [
            "symbol",
            "symbol_raw",
            "exchange",
            "country",
        ]
    ].copy()

    if sub.empty:
        raise ValueError(
            "No volatility symbols found in metadata."
        )

    sub["symbol"] = sub["symbol"].str.upper()
    sub["symbol_raw"] = sub["symbol_raw"].str.upper()
    sub["exchange"] = sub["exchange"].str.upper()

    missing_rows = sub[
        sub[
            [
                "symbol",
                "symbol_raw",
                "exchange",
                "country",
            ]
        ].isna().any(axis=1)
    ]

    if not missing_rows.empty:
        raise ValueError(
            "Missing SYMBOL, SYMBOL_RAW, EXCHANGE, or COUNTRY "
            "in volatility metadata.\n"
            f"{missing_rows}"
        )

    duplicated_raw = sub[
        sub["symbol_raw"].duplicated(keep=False)
    ]

    if not duplicated_raw.empty:
        raise ValueError(
            "Duplicate SYMBOL_RAW values detected in volatility metadata.\n"
            f"{duplicated_raw}"
        )

    LOGGER.info(
        "Volatility metadata loaded | symbols=%d | excluded_countries=%s",
        len(sub),
        sorted(EXCLUDED_COUNTRIES),
    )

    return sub.reset_index(drop=True)


# ============================================================
# Time handling
# ============================================================

def get_market_close_datetime(
    base_date: pd.Series,
    exchange: pd.Series,
    country: pd.Series,
) -> pd.Series:
    """
    Builds timezone-aware market close datetimes.

    Rules
    -----
    United States:
        16:15 New York time.
        DST is handled by America/New_York.

    Hong Kong:
        16:10 Hong Kong time.

    South Korea:
        15:30 Seoul time.
    """

    result = pd.Series(
        index=base_date.index,
        dtype="object",
    )

    base_date = pd.to_datetime(
        base_date,
        errors="raise",
    ).dt.normalize()

    exchange = (
        exchange
        .astype("string")
        .str.strip()
        .str.upper()
    )

    country = (
        country
        .astype("string")
        .str.strip()
    )

    us_mask = country.eq("United States")
    hk_mask = country.eq("Hong Kong")
    kr_mask = country.eq("South Korea")

    if us_mask.any():
        us_dt = (
            base_date.loc[us_mask]
            + pd.Timedelta(hours=16, minutes=15)
        )

        result.loc[us_mask] = (
            us_dt
            .dt.tz_localize(
                "America/New_York",
                ambiguous="raise",
                nonexistent="raise",
            )
        )

    if hk_mask.any():
        hk_dt = (
            base_date.loc[hk_mask]
            + pd.Timedelta(hours=16, minutes=10)
        )

        result.loc[hk_mask] = (
            hk_dt
            .dt.tz_localize(
                "Asia/Hong_Kong",
                ambiguous="raise",
                nonexistent="raise",
            )
        )

    if kr_mask.any():
        kr_dt = (
            base_date.loc[kr_mask]
            + pd.Timedelta(hours=15, minutes=30)
        )

        result.loc[kr_mask] = (
            kr_dt
            .dt.tz_localize(
                "Asia/Seoul",
                ambiguous="raise",
                nonexistent="raise",
            )
        )

    undefined_rows = result[result.isna()]

    if not undefined_rows.empty:
        undefined_cases = (
            pd.DataFrame(
                {
                    "exchange": exchange.loc[undefined_rows.index],
                    "country": country.loc[undefined_rows.index],
                }
            )
            .drop_duplicates()
            .to_dict("records")
        )

        raise ValueError(
            "Market close time rule is not defined for: "
            f"{undefined_cases}"
        )

    return result


def format_utc_offset(
    timestamp: pd.Timestamp,
) -> str:
    """
    Converts a timezone-aware timestamp offset into UTC±H format.
    """

    offset_seconds = timestamp.utcoffset().total_seconds()
    offset_hours = int(offset_seconds // 3600)

    return f"UTC{offset_hours:+d}"


# ============================================================
# Transform
# ============================================================

def transform_volatility_data(
    df: pd.DataFrame,
    symbol_mapping: dict[str, str],
    exchange_mapping: dict[str, str],
    country_mapping: dict[str, str],
) -> pd.DataFrame:
    """
    Transforms TradingView volatility index data into normalized long form.

    Input columns:
        MultiIndex
        Level 0 = SYMBOL_RAW
        Level 1 = open, high, low, close, volume

    Output columns:
        base_date, release_date, time, time_zone,
        symbol, exchange, country,
        open, high, low, close, volume
    """

    if not isinstance(df.columns, pd.MultiIndex):
        raise TypeError(
            "df.columns must be a MultiIndex. "
            "Level 0 must be SYMBOL_RAW and Level 1 must be OHLCV."
        )

    required_fields = {
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    data = df.copy()

    normalized_symbol_mapping = {
        str(raw_symbol).strip().upper(): str(symbol).strip().upper()
        for raw_symbol, symbol in symbol_mapping.items()
    }

    normalized_exchange_mapping = {
        str(raw_symbol).strip().upper(): str(exchange).strip().upper()
        for raw_symbol, exchange in exchange_mapping.items()
    }

    normalized_country_mapping = {
        str(raw_symbol).strip().upper(): str(country).strip()
        for raw_symbol, country in country_mapping.items()
    }

    raw_symbols = (
        data.columns
        .get_level_values(0)
        .astype(str)
        .str.strip()
        .str.upper()
    )

    fields = (
        data.columns
        .get_level_values(1)
        .astype(str)
        .str.strip()
        .str.lower()
    )

    unmapped_symbols = sorted(
        set(raw_symbols)
        - set(normalized_symbol_mapping)
    )

    if unmapped_symbols:
        raise ValueError(
            "SYMBOL_RAW values are not mapped in metadata: "
            f"{unmapped_symbols}"
        )

    mapped_symbols = [
        normalized_symbol_mapping[raw_symbol]
        for raw_symbol in raw_symbols
    ]

    mapped_exchanges = [
        normalized_exchange_mapping[raw_symbol]
        for raw_symbol in raw_symbols
    ]

    mapped_countries = [
        normalized_country_mapping[raw_symbol]
        for raw_symbol in raw_symbols
    ]

    data.columns = pd.MultiIndex.from_arrays(
        [
            mapped_symbols,
            mapped_exchanges,
            mapped_countries,
            fields,
        ],
        names=[
            "symbol",
            "exchange",
            "country",
            "field",
        ],
    )

    available_fields = set(
        data.columns.get_level_values("field")
    )

    missing_fields = required_fields - available_fields

    if missing_fields:
        raise ValueError(
            "Required OHLCV fields are missing: "
            f"{sorted(missing_fields)}"
        )

    data.index = pd.to_datetime(
        data.index,
        errors="raise",
    ).normalize()

    data.index.name = "base_date"

    long_df = (
        data.stack(
            level=[
                "symbol",
                "exchange",
                "country",
            ],
            future_stack=True,
        )
        .reset_index()
    )

    long_df["release_date"] = long_df["base_date"]

    market_close_datetime = get_market_close_datetime(
        base_date=long_df["base_date"],
        exchange=long_df["exchange"],
        country=long_df["country"],
    )

    long_df["time"] = market_close_datetime.map(
        lambda value: value.time()
    )

    long_df["time_zone"] = market_close_datetime.map(
        format_utc_offset
    )

    long_df = long_df[OUTPUT_COLUMNS]

    long_df = long_df.dropna(
        how="all",
        subset=[
            "open",
            "high",
            "low",
            "close",
            "volume",
        ],
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
            "Duplicate volatility rows detected.\n"
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

def collect_volatility_data() -> None:
    """
    Collects volatility index data from TradingView and saves it as Parquet.
    """

    LOGGER.info(
        "Volatility data job started | metadata_path=%s",
        METADATA_PATH,
    )

    symbol_info = get_volatility_symbol_info()

    tickers = symbol_info["symbol_raw"].tolist()
    exchanges = symbol_info["exchange"].tolist()

    symbol_mapping = dict(
        zip(
            symbol_info["symbol_raw"],
            symbol_info["symbol"],
        )
    )

    exchange_mapping = dict(
        zip(
            symbol_info["symbol_raw"],
            symbol_info["exchange"],
        )
    )

    country_mapping = dict(
        zip(
            symbol_info["symbol_raw"],
            symbol_info["country"],
        )
    )

    LOGGER.info(
        "TradingView request prepared | tickers=%d",
        len(tickers),
    )

    data = get_data_from_tradingview(
        tickers=tickers,
        interval=Interval.in_daily,
        exchange=exchanges,
        n_bars=N_BARS,
        verbose=VERBOSE,
        num_trials=NUM_TRIALS,
        multi_level_index=True,
        tz_cleansing=True,
    )

    if data is None or data.empty:
        raise ValueError(
            "No data was returned from TradingView."
        )

    LOGGER.info(
        "TradingView data collected | rows=%d | columns=%d",
        data.shape[0],
        data.shape[1],
    )

    transformed_data = transform_volatility_data(
        df=data,
        symbol_mapping=symbol_mapping,
        exchange_mapping=exchange_mapping,
        country_mapping=country_mapping,
    )

    if transformed_data.empty:
        raise ValueError(
            "No rows remained after volatility data transformation."
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
        "Volatility Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(transformed_data),
    )


if __name__ == "__main__":
    collect_volatility_data()