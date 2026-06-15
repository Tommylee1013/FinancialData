import pandas as pd
import yfinance as yf

from pathlib import Path

from src.dataloader.meta_info import get_master_table
from src.utils.log import setup_logger


# ============================================================
# Const Values
# ============================================================

OUTPUT_PATH = Path(
    "data_lake/raw/index/yfinance_index.parquet"
)

LOGGER = setup_logger(
    name="yfinance_index_job",
    log_path="logs/jobs/yfinance_index.log",
)

START_DATE = "1900-01-01"
END_DATE = None
AUTO_ADJUST = False
GROUP_BY = "ticker"
THREADS = True

YFINANCE_EXCHANGE = "INDEX"

TARGET_SYMBOLS = {
    "SP500",
    "SPX50010",
    "SPX50015",
    "SPX50020",
    "SPX50025",
    "SPX50030",
    "SPX50035",
    "SPX50040",
    "SPX50045",
    "SPX50050",
    "SPX50055",
    "SPX50060",
    "NI225",
    "RUS1000",
    "RUS2000",
    "RUS3000",
}


# ============================================================
# Metadata
# ============================================================

def get_yfinance_symbol_info() -> pd.DataFrame:
    """
    yfinance 지수 데이터 조회 정보와 내부 표준 SYMBOL 정보를 반환합니다.

    조건
    ----------
    ASSET_CLASS == Equity
    INSTRUMENT_TYPE == INDEX
    EXCHANGE == INDEX
    SYMBOL in TARGET_SYMBOLS

    반환 컬럼
    ----------
    symbol:
        내부 저장용 표준 심볼

    symbol_raw:
        yfinance 조회용 원본 심볼

    exchange:
        metadata상 exchange

    country:
        국가
    """

    data = get_master_table().copy()

    sub = data[
        (data["ASSET_CLASS"] == "Equity")
        & (data["INSTRUMENT_TYPE"] == "INDEX")
        & (data["EXCHANGE"] == YFINANCE_EXCHANGE)
        & (data["SYMBOL"].isin(TARGET_SYMBOLS))
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
            "비어 있는 yfinance 지수 항목이 있습니다.\n"
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
            "빈 문자열인 yfinance 지수 항목이 있습니다.\n"
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

    missing_target_symbols = sorted(
        TARGET_SYMBOLS - set(sub["symbol"])
    )

    if missing_target_symbols:
        raise ValueError(
            "metadata에서 찾을 수 없는 TARGET_SYMBOLS가 있습니다.\n"
            f"{missing_target_symbols}"
        )

    LOGGER.info(
        "yfinance index metadata loaded | symbols=%d",
        len(sub),
    )

    return (
        sub.sort_values(
            by=[
                "symbol",
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# yfinance Downloader
# ============================================================

def download_yfinance_data(
    tickers: list[str],
) -> pd.DataFrame:
    """
    yfinance에서 OHLCV 데이터를 다운로드합니다.

    반환 구조
    ----------
    columns:
        MultiIndex
        level 0 = ticker
        level 1 = open, high, low, close, volume
    """

    if not tickers:
        raise ValueError(
            "yfinance tickers list is empty."
        )

    LOGGER.info(
        "yfinance download started | tickers=%d",
        len(tickers),
    )

    data = yf.download(
        tickers=tickers,
        start=START_DATE,
        end=END_DATE,
        auto_adjust=AUTO_ADJUST,
        group_by=GROUP_BY,
        threads=THREADS,
        progress=True,
    )

    if data is None or data.empty:
        raise ValueError(
            "yfinance returned empty data."
        )

    data = data.copy()

    # 단일 ticker일 경우 yfinance가 단일 컬럼으로 반환할 수 있음.
    # 이 job은 다중 ticker 기준이지만 방어적으로 처리.
    if not isinstance(data.columns, pd.MultiIndex):
        if len(tickers) != 1:
            raise TypeError(
                "yfinance columns are not MultiIndex, "
                "but multiple tickers were requested."
            )

        ticker = tickers[0]

        data.columns = pd.MultiIndex.from_product(
            [
                [ticker],
                data.columns,
            ],
            names=[
                "ticker",
                "field",
            ],
        )

    # yfinance 버전에 따라 group_by='ticker'여도
    # column level 순서가 (Price, Ticker)로 올 수 있어 보정
    level_0_values = set(
        data.columns.get_level_values(0).astype(str)
    )

    level_1_values = set(
        data.columns.get_level_values(1).astype(str)
    )

    ticker_set = set(
        map(
            str,
            tickers,
        )
    )

    ohlcv_like = {
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume",
    }

    if not ticker_set.intersection(level_0_values) and ticker_set.intersection(level_1_values):
        data.columns = data.columns.swaplevel(0, 1)

    data = data.sort_index(axis=1)

    # field lowercase 정규화
    tickers_level = (
        data.columns
        .get_level_values(0)
        .astype(str)
        .str.strip()
    )

    fields_level = (
        data.columns
        .get_level_values(1)
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    data.columns = pd.MultiIndex.from_arrays(
        [
            tickers_level,
            fields_level,
        ],
        names=[
            "ticker",
            "field",
        ],
    )

    # Adj Close는 저장하지 않음
    keep_fields = {
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    data = data.loc[
        :,
        data.columns.get_level_values("field").isin(keep_fields),
    ]

    LOGGER.info(
        "yfinance download completed | rows=%d | columns=%d",
        data.shape[0],
        data.shape[1],
    )

    return data


# ============================================================
# Transform
# ============================================================

def transform_yfinance_index_data(
    df: pd.DataFrame,
    symbol_mapping: dict[str, str],
    exchange_mapping: dict[str, str],
    country_mapping: dict[str, str],
) -> pd.DataFrame:
    """
    yfinance 지수 데이터를 DB 적재용 Long Form으로 변환합니다.

    yfinance에서 조회된 SYMBOL_RAW를
    metadata의 내부 표준 SYMBOL로 치환합니다.

    입력 구조
    ----------
    index:
        DatetimeIndex 또는 날짜로 변환 가능한 Index

    columns:
        MultiIndex
        Level 0 = yfinance 원본 심볼, 즉 SYMBOL_RAW
        Level 1 = open, high, low, close, volume

    출력 컬럼
    ----------
    base_date, release_date, time, time_zone,
    symbol, exchange, country,
    open, high, low, close, volume
    """

    if df.empty:
        raise ValueError(
            "yfinance에서 반환된 지수 데이터가 비어 있습니다."
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
            "중복된 yfinance index 행이 존재합니다.\n"
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

def collect_yfinance_index_data() -> None:
    """
    yfinance 지수 데이터를 수집하여 Parquet 파일로 저장합니다.

    주의
    ----------
    yfinance 조회:
        SYMBOL_RAW 사용

    저장:
        내부 SYMBOL 사용
    """

    LOGGER.info(
        "Starting download yfinance index data."
    )

    symbol_info = get_yfinance_symbol_info()

    tickers = symbol_info["symbol_raw"].tolist()

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
        "yfinance index download target prepared | tickers=%d",
        len(tickers),
    )

    data = download_yfinance_data(
        tickers=tickers,
    )

    cleansing_data = transform_yfinance_index_data(
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
        "All yfinance index data has been downloaded | output_path=%s | rows=%d | symbols=%d",
        OUTPUT_PATH,
        len(cleansing_data),
        cleansing_data["symbol"].nunique(),
    )


if __name__ == "__main__":
    collect_yfinance_index_data()