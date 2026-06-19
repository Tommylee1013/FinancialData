from pathlib import Path

import pandas as pd
from tqdm import tqdm
from tvDatafeed import Interval

from src.dataloader.meta_info import get_master_table
from src.dataloader.data_downloader import get_data_from_tradingview
from src.utils.log import setup_logger


# ============================================================
# Const Values
# ============================================================

OUTPUT_PATH = Path(
    "data_lake/raw/fx/currency.parquet"
)

LOGGER = setup_logger(
    name="currencies_job",
    log_path="logs/jobs/currencies.log",
)

N_BARS = 13000
VERBOSE = True
NUM_TRIALS = 5

# tvDatafeed가 현재 PC 기준 KST naive datetime으로 반환되는 상황을 전제로 함
SOURCE_TIME_ZONE = "Asia/Seoul"
RELEASE_TIME_ZONE = "UTC+09:00"


# ============================================================
# TradingView Exchange Resolver
# ============================================================

def resolve_tv_exchange(
    symbol_raw: str,
    exchange: str,
) -> str:
    """
    metadata의 EXCHANGE와 tvDatafeed 호출용 exchange를 분리합니다.

    예:
    - DB/metadata상 EXCHANGE = ICE
    - TradingView/tvDatafeed 호출용 exchange = FX_IDC

    TradingView 화면에서 ICE로 보이는 FX spot은
    tvDatafeed에서는 보통 FX_IDC로 조회해야 합니다.
    """

    symbol_raw = str(symbol_raw).strip().upper()
    exchange = str(exchange).strip().upper()

    # FX spot의 ICE/IDC composite feed
    if exchange == "ICE":
        return "FX_IDC"

    return exchange


# ============================================================
# Daily Calendar Rule
# ============================================================

def get_daily_calendar_rule(
    symbol_raw: str,
    tv_exchange: str,
) -> dict[str, object]:
    """
    TradingView daily index는 장 시작 timestamp이므로
    release_date/time으로 사용하지 않습니다.

    여기서는 장마감 기준으로 release_date/time/time_zone을 부여합니다.

    반환값
    ------
    base_date_offset_days:
        tvDatafeed daily index의 날짜에서 base_date를 보정하는 일수

    release_date_offset_days:
        base_date에서 release_date를 보정하는 일수

    release_time:
        장마감 기준 확정 시간

    release_time_zone:
        release_time의 시간대
    """

    symbol_raw = str(symbol_raw).strip().upper()
    tv_exchange = str(tv_exchange).strip().upper()

    # --------------------------------------------------------
    # TVC
    # 관측:
    # - daily timestamp가 KST 기준 전일 21:00 근처로 찍힘
    # - 18일 데이터 장마감은 19일 06:15 KST로 판단
    # 처리:
    # - source timestamp date + 1일 = base_date
    # - base_date + 1일 06:15 KST = release datetime
    # --------------------------------------------------------
    if tv_exchange == "TVC":
        return {
            "base_date_offset_days": 1,
            "release_date_offset_days": 1,
            "release_time": "06:15:00",
            "release_time_zone": RELEASE_TIME_ZONE,
        }

    # --------------------------------------------------------
    # ICEUS / DXY 계열
    # 관측:
    # - DXY daily timestamp가 KST 기준 당일 08:00 근처
    # - 18일 데이터 장마감은 19일 07:00 KST로 판단
    # --------------------------------------------------------
    if tv_exchange == "ICEUS" or symbol_raw in {"DXY", "USDX"}:
        return {
            "base_date_offset_days": 0,
            "release_date_offset_days": 1,
            "release_time": "07:00:00",
            "release_time_zone": RELEASE_TIME_ZONE,
        }

    # --------------------------------------------------------
    # FX_IDC
    # 관측:
    # - FX_IDC daily timestamp가 KST 기준 당일 07:00 근처
    # - 24시간 FX spot이지만 daily 확정 기준은
    #   base_date + 1일 07:00 KST로 통일
    # --------------------------------------------------------
    if tv_exchange == "FX_IDC":
        return {
            "base_date_offset_days": 0,
            "release_date_offset_days": 1,
            "release_time": "07:00:00",
            "release_time_zone": RELEASE_TIME_ZONE,
        }

    raise ValueError(
        "정의되지 않은 TradingView daily calendar rule입니다. "
        f"symbol_raw={symbol_raw}, tv_exchange={tv_exchange}"
    )


# ============================================================
# Metadata
# ============================================================

def get_currency_symbol_info() -> pd.DataFrame:
    """
    외환 데이터의 TradingView 조회 정보와
    내부 표준 SYMBOL 정보를 반환합니다.

    반환 컬럼
    ----------
    symbol:
        내부 저장용 표준 심볼

    symbol_raw:
        TradingView 조회용 원본 심볼

    exchange:
        내부 저장용 exchange/provider

    tv_exchange:
        tvDatafeed 조회용 exchange

    country:
        내부 저장용 국가/지역
    """

    data = get_master_table().copy()

    required_columns = [
        "SYMBOL",
        "SYMBOL_RAW",
        "EXCHANGE",
        "ASSET_CLASS",
        "INSTRUMENT_TYPE",
        "SOURCE",
    ]

    missing_required_columns = sorted(
        set(required_columns) - set(data.columns)
    )

    if missing_required_columns:
        raise ValueError(
            "master table에 필수 컬럼이 없습니다: "
            f"{missing_required_columns}"
        )

    selected_columns = [
        "SYMBOL",
        "SYMBOL_RAW",
        "EXCHANGE",
    ]

    if "COUNTRY" in data.columns:
        selected_columns.append("COUNTRY")

    sub = data[
        (data["ASSET_CLASS"] == "Foreign Exchange")
        & (data["INSTRUMENT_TYPE"].isin(["INDEX", "SPOT"]))
        & (data["SOURCE"] == "TRADINGVIEW")
    ][selected_columns].copy()

    rename_columns = {
        "SYMBOL": "symbol",
        "SYMBOL_RAW": "symbol_raw",
        "EXCHANGE": "exchange",
    }

    if "COUNTRY" in sub.columns:
        rename_columns["COUNTRY"] = "country"

    sub = sub.rename(columns=rename_columns)

    if "country" not in sub.columns:
        sub["country"] = pd.NA

    # 문자열 정리
    for column in [
        "symbol",
        "symbol_raw",
        "exchange",
        "country",
    ]:
        sub[column] = (
            sub[column]
            .astype("string")
            .str.strip()
        )

    # tvDatafeed 조회용 exchange 생성
    sub["tv_exchange"] = [
        resolve_tv_exchange(
            symbol_raw=symbol_raw,
            exchange=exchange,
        )
        for symbol_raw, exchange in zip(
            sub["symbol_raw"],
            sub["exchange"],
        )
    ]

    sub["tv_exchange"] = (
        sub["tv_exchange"]
        .astype("string")
        .str.strip()
    )

    # 필수값 누락 검증
    missing_rows = sub[
        sub[
            [
                "symbol",
                "symbol_raw",
                "exchange",
                "tv_exchange",
            ]
        ].isna().any(axis=1)
    ]

    if not missing_rows.empty:
        raise ValueError(
            "SYMBOL, SYMBOL_RAW, EXCHANGE 또는 tv_exchange가 "
            "비어 있는 외환 항목이 있습니다.\n"
            f"{missing_rows}"
        )

    # SYMBOL_RAW가 중복이면 현재 get_data_from_tradingview 반환 구조에서
    # 원본 심볼 기준 매핑이 애매해지므로 금지
    duplicated_raw = sub[
        sub["symbol_raw"].duplicated(keep=False)
    ]

    if not duplicated_raw.empty:
        raise ValueError(
            "중복된 SYMBOL_RAW가 존재합니다.\n"
            f"{duplicated_raw}"
        )

    return sub.reset_index(drop=True)


# ============================================================
# Transform
# ============================================================

def transform_currency_data(
    df: pd.DataFrame,
    symbol_mapping: dict[str, str],
    exchange_mapping: dict[str, str],
    tv_exchange_mapping: dict[str, str],
    country_mapping: dict[str, str],
) -> pd.DataFrame:
    """
    TradingView 외환 데이터를 DB 적재용 Long Form으로 변환합니다.

    중요
    ----
    TradingView daily index는 장 시작 timestamp이므로
    release_date/time으로 사용하지 않습니다.

    처리 방식
    ---------
    1. tvDatafeed index는 source_timestamp로 보존하되,
       output에는 넣지 않습니다.
    2. source별 rule로 base_date를 보정합니다.
    3. 장마감 기준 release_date/time/time_zone을 부여합니다.

    입력 구조
    ----------
    index:
        DatetimeIndex 또는 날짜로 변환 가능한 Index

    columns:
        MultiIndex
        Level 0 = TradingView 원본 심볼(SYMBOL_RAW)
        Level 1 = open, high, low, close, volume

    출력 컬럼
    ----------
    base_date, release_date, time, time_zone,
    symbol, exchange, country,
    open, high, low, close, volume
    """

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
        str(raw_symbol).strip().upper(): str(symbol).strip()
        for raw_symbol, symbol in symbol_mapping.items()
    }

    normalized_exchange_mapping = {
        str(raw_symbol).strip().upper(): str(exchange).strip().upper()
        for raw_symbol, exchange in exchange_mapping.items()
    }

    normalized_tv_exchange_mapping = {
        str(raw_symbol).strip().upper(): str(tv_exchange).strip().upper()
        for raw_symbol, tv_exchange in tv_exchange_mapping.items()
    }

    normalized_country_mapping = {
        str(raw_symbol).strip().upper(): (
            pd.NA
            if pd.isna(country)
            else str(country).strip()
        )
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

    # metadata에 존재하지 않는 TradingView 심볼 검증
    unmapped_symbols = sorted(
        set(raw_symbols) - set(normalized_symbol_mapping)
    )

    if unmapped_symbols:
        raise ValueError(
            "metadata에서 매핑할 수 없는 SYMBOL_RAW가 있습니다: "
            f"{unmapped_symbols}"
        )

    # SYMBOL_RAW → 내부 표준 SYMBOL / exchange / tv_exchange
    mapped_symbols = [
        normalized_symbol_mapping[raw_symbol]
        for raw_symbol in raw_symbols
    ]

    mapped_exchanges = [
        normalized_exchange_mapping[raw_symbol]
        for raw_symbol in raw_symbols
    ]

    mapped_tv_exchanges = [
        normalized_tv_exchange_mapping[raw_symbol]
        for raw_symbol in raw_symbols
    ]

    mapped_countries = [
        normalized_country_mapping.get(raw_symbol, pd.NA)
        for raw_symbol in raw_symbols
    ]

    df.columns = pd.MultiIndex.from_arrays(
        [
            mapped_symbols,
            raw_symbols,
            mapped_exchanges,
            mapped_tv_exchanges,
            mapped_countries,
            fields,
        ],
        names=[
            "symbol",
            "symbol_raw",
            "exchange",
            "tv_exchange",
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

    # --------------------------------------------------------
    # tvDatafeed index 처리
    # --------------------------------------------------------
    # 현재 관측상 tvDatafeed daily index가 KST naive datetime으로 찍힘.
    # 하지만 이 값은 release time이 아니라 장 시작 timestamp임.
    # 따라서 source_timestamp로만 취급하고,
    # base_date 산출에만 사용합니다.
    # --------------------------------------------------------
    source_index = pd.DatetimeIndex(
        pd.to_datetime(
            df.index,
            errors="raise",
        )
    )

    if source_index.tz is not None:
        source_index = (
            source_index
            .tz_convert(SOURCE_TIME_ZONE)
            .tz_localize(None)
        )

    df.index = source_index
    df.index.name = "source_timestamp"

    long_df = (
        df.stack(
            level=[
                "symbol",
                "symbol_raw",
                "exchange",
                "tv_exchange",
                "country",
            ],
            future_stack=True,
        )
        .reset_index()
    )

    # 모든 OHLCV 값이 결측인 행 제거
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

    # --------------------------------------------------------
    # source별 calendar rule 적용
    # --------------------------------------------------------
    rules = [
        get_daily_calendar_rule(
            symbol_raw=symbol_raw,
            tv_exchange=tv_exchange,
        )
        for symbol_raw, tv_exchange in zip(
            long_df["symbol_raw"],
            long_df["tv_exchange"],
        )
    ]

    rule_df = pd.DataFrame(rules)

    long_df = pd.concat(
        [
            long_df.reset_index(drop=True),
            rule_df.reset_index(drop=True),
        ],
        axis=1,
    )

    source_date = (
        pd.to_datetime(long_df["source_timestamp"])
        .dt.normalize()
    )

    long_df["base_date"] = (
        source_date
        + pd.to_timedelta(
            long_df["base_date_offset_days"],
            unit="D",
        )
    ).dt.date

    long_df["release_date"] = (
        pd.to_datetime(long_df["base_date"])
        + pd.to_timedelta(
            long_df["release_date_offset_days"],
            unit="D",
        )
    ).dt.date

    long_df["time"] = long_df["release_time"]
    long_df["time_zone"] = long_df["release_time_zone"]

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

    long_df = (
        long_df.sort_values(
            by=[
                "base_date",
                "symbol",
                "exchange",
            ],
        )
        .reset_index(drop=True)
    )

    return long_df


# ============================================================
# Main Job
# ============================================================

def collect_currency_data() -> None:
    LOGGER.info(
        "starting download currency data."
    )

    symbol_info = get_currency_symbol_info()

    # TradingView에서는 SYMBOL_RAW + tv_exchange로 조회
    tickers = symbol_info["symbol_raw"].tolist()
    exchanges = symbol_info["tv_exchange"].tolist()

    # 저장 시 SYMBOL_RAW를 내부 표준 SYMBOL로 치환하기 위한 매핑
    symbol_mapping = dict(
        zip(
            symbol_info["symbol_raw"],
            symbol_info["symbol"],
        )
    )

    # 저장용 exchange
    exchange_mapping = dict(
        zip(
            symbol_info["symbol_raw"],
            symbol_info["exchange"],
        )
    )

    # 조회용 exchange / calendar rule 판정용
    tv_exchange_mapping = dict(
        zip(
            symbol_info["symbol_raw"],
            symbol_info["tv_exchange"],
        )
    )

    country_mapping = dict(
        zip(
            symbol_info["symbol_raw"],
            symbol_info["country"],
        )
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

    cleansing_data = transform_currency_data(
        df=data,
        symbol_mapping=symbol_mapping,
        exchange_mapping=exchange_mapping,
        tv_exchange_mapping=tv_exchange_mapping,
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
        "All currency data has been downloaded."
    )


if __name__ == "__main__":
    collect_currency_data()