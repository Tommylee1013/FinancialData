# src/jobs_tv/commodity/get_commodity_index.py

import pandas as pd

from pathlib import Path
from tvDatafeed import Interval

from src.dataloader.meta_info import get_master_table
from src.dataloader.data_downloader import get_data_from_tradingview
from src.utils.log import setup_logger


# ============================================================
# Const Values
# ============================================================

OUTPUT_PATH = Path(
    "data_lake/raw/commodity/index/commodity_index.parquet"
)

LOGGER = setup_logger(
    name="commodity_index_job",
    log_path="logs/jobs/commodity_index.log",
)

N_BARS = 13000
VERBOSE = True
NUM_TRIALS = 5

EXCLUDED_SYMBOLS = {
    "DJCI",
}


# ============================================================
# Metadata
# ============================================================

def get_commodity_symbol_info() -> pd.DataFrame:
    """
    Commodity Index의 TradingView 조회 정보와
    내부 표준 SYMBOL 정보를 반환합니다.

    조건
    ----------
    ASSET_CLASS == Commodity
    INSTRUMENT_TYPE == INDEX
    SYMBOL != DJCI

    반환 컬럼
    ----------
    symbol:
        내부 저장용 표준 심볼

    symbol_raw:
        TradingView 조회용 원본 심볼

    exchange:
        TradingView 조회용 거래소

    country:
        국가
    """

    data = get_master_table().copy()

    sub = data[
        (data["ASSET_CLASS"] == "Commodity")
        & (data["INSTRUMENT_TYPE"] == "INDEX")
        & (~data["SYMBOL"].isin(EXCLUDED_SYMBOLS))
    ][
        [
            "SYMBOL",
            "SYMBOL_RAW",
            "EXCHANGE",
            "COUNTRY",
            "NAME",
        ]
    ].copy()

    sub = sub.rename(
        columns={
            "SYMBOL": "symbol",
            "SYMBOL_RAW": "symbol_raw",
            "EXCHANGE": "exchange",
            "COUNTRY": "country",
            "NAME": "name",
        }
    )

    for column in [
        "symbol",
        "symbol_raw",
        "exchange",
        "country",
        "name",
    ]:
        sub[column] = (
            sub[column]
            .astype("string")
            .str.strip()
        )

    sub["symbol"] = sub["symbol"].str.upper()
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
            "SYMBOL, SYMBOL_RAW, EXCHANGE 또는 COUNTRY가 "
            "비어 있는 Commodity Index 항목이 있습니다.\n"
            f"{missing_rows}"
        )

    empty_rows = sub[
        (sub["symbol"] == "")
        | (sub["symbol_raw"] == "")
        | (sub["exchange"] == "")
        | (sub["country"] == "")
    ]

    if not empty_rows.empty:
        raise ValueError(
            "SYMBOL, SYMBOL_RAW, EXCHANGE 또는 COUNTRY가 "
            "빈 문자열인 Commodity Index 항목이 있습니다.\n"
            f"{empty_rows}"
        )

    duplicated_symbol = sub[
        sub["symbol"].duplicated(keep=False)
    ]

    if not duplicated_symbol.empty:
        raise ValueError(
            "중복된 내부 SYMBOL이 존재합니다.\n"
            f"{duplicated_symbol}"
        )

    duplicated_raw = sub[
        sub["symbol_raw"].duplicated(keep=False)
    ]

    if not duplicated_raw.empty:
        raise ValueError(
            "중복된 SYMBOL_RAW가 존재합니다.\n"
            f"{duplicated_raw}"
        )

    LOGGER.info(
        "Commodity index metadata loaded | symbols=%d | excluded_symbols=%s",
        len(sub),
        sorted(EXCLUDED_SYMBOLS),
    )

    return sub.reset_index(drop=True)


# ============================================================
# Transform
# ============================================================

def transform_commodity_index_data(
    df: pd.DataFrame,
    symbol_mapping: dict[str, str],
    exchange_mapping: dict[str, str],
    country_mapping: dict[str, str],
) -> pd.DataFrame:
    """
    TradingView Commodity Index 데이터를 DB 적재용 Long Form으로 변환합니다.

    TradingView에서 조회된 SYMBOL_RAW를
    metadata의 내부 표준 SYMBOL로 치환합니다.

    입력 구조
    ----------
    index:
        DatetimeIndex 또는 날짜로 변환 가능한 Index

    columns:
        MultiIndex
        Level 0 = TradingView 원본 심볼, 즉 SYMBOL_RAW
        Level 1 = open, high, low, close, volume

    출력 컬럼
    ----------
    base_date, release_date, time, time_zone,
    symbol, exchange, country,
    open, high, low, close, volume
    """

    if df.empty:
        raise ValueError(
            "TradingView에서 반환된 Commodity Index 데이터가 비어 있습니다."
        )

    if not isinstance(df.columns, pd.MultiIndex):
        raise TypeError(
            "df.columns는 MultiIndex여야 합니다. "
            "Level 0은 SYMBOL_RAW, Level 1은 OHLCV여야 합니다."
        )

    required_fields = {
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    df = df.copy()

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
        df.columns
        .get_level_values(0)
        .astype(str)
        .str.strip()
        .str.upper()
    )

    fields = (
        df.columns
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
            "metadata에서 매핑할 수 없는 SYMBOL_RAW가 있습니다: "
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

    df.columns = pd.MultiIndex.from_arrays(
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
        df.columns.get_level_values("field")
    )

    missing_fields = required_fields - available_fields

    if missing_fields:
        raise ValueError(
            "필수 OHLCV 컬럼이 없습니다: "
            f"{sorted(missing_fields)}"
        )

    df.index = pd.to_datetime(
        df.index,
        errors="raise",
    ).normalize()

    df.index.name = "base_date"

    long_df = (
        df.stack(
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

    # Commodity index 대부분은 TradingView상 미국 기준 지수/CFD 계열이므로
    # New York 16:00 기준으로 정규화
    market_close_datetime = (
        pd.to_datetime(
            long_df["base_date"],
            errors="raise",
        ).dt.normalize()
        + pd.Timedelta(hours=16)
    )

    market_close_datetime = (
        market_close_datetime
        .dt.tz_localize(
            "America/New_York",
            ambiguous="raise",
            nonexistent="raise",
        )
    )

    long_df["time"] = market_close_datetime.dt.time

    long_df["time_zone"] = market_close_datetime.map(
        lambda value: (
            f"UTC"
            f"{int(value.utcoffset().total_seconds() // 3600):+d}"
        )
    )

    output_columns = [
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

    long_df = long_df[output_columns]

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]:
        long_df[column] = pd.to_numeric(
            long_df[column],
            errors="coerce",
        )

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
            "중복된 Commodity Index 행이 존재합니다.\n"
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
# Main Job
# ============================================================

def collect_commodity_index_data() -> None:
    """
    Commodity Index 데이터를 TradingView에서 수집하여
    Parquet 파일로 저장합니다.

    주의
    ----------
    TradingView 조회:
        SYMBOL_RAW 사용

    저장:
        내부 SYMBOL 사용

    제외:
        DJCI
    """

    LOGGER.info(
        "Starting download commodity index data."
    )

    symbol_info = get_commodity_symbol_info()

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
        "Commodity index download target prepared | tickers=%d | exchanges=%s",
        len(tickers),
        sorted(set(exchanges)),
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

    cleansing_data = transform_commodity_index_data(
        df=data,
        symbol_mapping=symbol_mapping,
        exchange_mapping=exchange_mapping,
        country_mapping=country_mapping,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cleansing_data.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    LOGGER.info(
        "All commodity index data has been downloaded | output_path=%s | rows=%d | symbols=%d",
        OUTPUT_PATH,
        len(cleansing_data),
        cleansing_data["symbol"].nunique(),
    )


if __name__ == "__main__":
    collect_commodity_index_data()