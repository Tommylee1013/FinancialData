from __future__ import annotations

from datetime import time
from pathlib import Path

import pandas as pd

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

INPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "industry"
    / "cfm"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "industry"
    / "components"
    / "cfm_components.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/cfm_industry.log",
)


# ============================================================
# Workbook configuration
# ============================================================

WORKBOOK_CONFIGS = [
    {
        "file_name": "DDR.xlsx",
        "category": "DRAM",
        "sub_category": "DDR",
        "mode": "price_sheet",
        "skip_sheets": {"fig", "info"},
    },
    {
        "file_name": "RDIMM.xlsx",
        "category": "DRAM",
        "sub_category": "Module",
        "mode": "price_sheet",
        "skip_sheets": {"fig", "info"},
    },
    {
        "file_name": "LPDDR.xlsx",
        "category": "DRAM",
        "sub_category": "Mobile DDR",
        "mode": "price_sheet",
        "skip_sheets": {"fig", "info"},
    },
    {
        "file_name": "Flash Wafer.xlsx",
        "category": "Flash Memory",
        "sub_category": "Wafer",
        "mode": "wafer_sheet",
        "skip_sheets": {"fig", "info"},
    },
    {
        "file_name": "Channel SSD.xlsx",
        "category": "Flash Memory",
        "sub_category": "SSD",
        "mode": "price_sheet",
        "skip_sheets": {"fig", "info"},
    },
    {
        "file_name": "OEM SSD.xlsx",
        "category": "Flash Memory",
        "sub_category": "SSD",
        "mode": "price_sheet",
        "skip_sheets": {"fig", "info"},
    },
    {
        "file_name": "Flash Card.xlsx",
        "category": "Flash Memory",
        "sub_category": "Micro SD",
        "mode": "price_sheet",
        "skip_sheets": {"fig", "info"},
    },
    {
        "file_name": "eMMC.xlsx",
        "category": "Flash Memory",
        "sub_category": "Embedded Storage",
        "mode": "price_sheet",
        "skip_sheets": {"fig", "info"},
    },
    {
        "file_name": "eMCP.xlsx",
        "category": "Flash Memory",
        "sub_category": "Embedded Storage",
        "mode": "price_sheet",
        "skip_sheets": {"fig", "info"},
    },
]


# ============================================================
# Columns
# ============================================================

DATE_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
]

ID_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
]

OUTPUT_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "item",
    "value",
]


# ============================================================
# Text normalization
# ============================================================

def normalize_text_value(
    value: object,
) -> str:
    """
    Normalizes text values for stable Excel-to-metadata matching.
    """

    if pd.isna(value):
        return ""

    return (
        str(value)
        .replace("\xa0", " ")
        .replace("μ", "µ")
        .strip()
    )


def normalize_match_key(
    value: object,
) -> str:
    """
    Produces case-insensitive and whitespace-normalized matching key.

    This intentionally lowercases names because CFM sheets sometimes use:
        1TB / 1Tb
        512GB / 512Gb
        LPDDR4X 64GB / LPDDR4X 64Gb
    """

    return " ".join(
        normalize_text_value(value)
        .lower()
        .split()
    )


def normalize_column_name(
    column_name: object,
) -> str:
    """
    Normalizes Excel column names to lowercase snake_case.
    """

    return (
        normalize_text_value(column_name)
        .lower()
        .replace(" ", "_")
    )


def normalize_sheet_name_for_matching(
    sheet_name: str,
) -> str:
    """
    Normalizes CFM sheet names before matching to metadata.name.
    """

    return normalize_text_value(sheet_name)


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
        .str.replace(" ", "_", regex=False)
    )

    string_columns = metadata.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in string_columns:
        metadata[column] = (
            metadata[column]
            .astype("string")
            .str.strip()
        )

    return metadata


def get_cfm_symbol_info() -> pd.DataFrame:
    """
    Loads CFM metadata rows.

    Matching key:
        Excel sheet name == metadata.name

    Saved symbol:
        metadata.symbol
    """

    metadata = load_metadata()

    required_columns = {
        "asset_class",
        "category",
        "sub_category",
        "instrument_type",
        "symbol",
        "exchange",
        "country",
        "name",
    }

    missing_columns = required_columns - set(metadata.columns)

    if missing_columns:
        raise ValueError(
            "Required metadata columns are missing: "
            f"{sorted(missing_columns)}"
        )

    symbol_info = metadata[
        (metadata["asset_class"].str.upper() == "INDUSTRY")
        & (metadata["exchange"].str.upper() == "CFM")
        & (metadata["instrument_type"].str.upper().isin(["SPOT", "INDEX"]))
    ][
        [
            "category",
            "sub_category",
            "instrument_type",
            "symbol",
            "exchange",
            "country",
            "name",
        ]
    ].copy()

    if symbol_info.empty:
        raise ValueError(
            "No CFM metadata rows found."
        )

    symbol_info["category"] = (
        symbol_info["category"]
        .astype("string")
        .str.strip()
    )

    symbol_info["sub_category"] = (
        symbol_info["sub_category"]
        .astype("string")
        .str.strip()
    )

    symbol_info["instrument_type"] = (
        symbol_info["instrument_type"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    symbol_info["symbol"] = (
        symbol_info["symbol"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    symbol_info["exchange"] = (
        symbol_info["exchange"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    symbol_info["country"] = (
        symbol_info["country"]
        .astype("string")
        .str.strip()
    )

    symbol_info["name"] = symbol_info["name"].map(
        normalize_text_value
    )

    symbol_info["match_name"] = symbol_info["name"].map(
        normalize_match_key
    )

    missing_rows = symbol_info[
        symbol_info[
            [
                "symbol",
                "exchange",
                "country",
                "name",
                "match_name",
            ]
        ].isna().any(axis=1)
    ]

    if not missing_rows.empty:
        raise ValueError(
            "CFM metadata contains missing symbol, exchange, country, or name values.\n"
            f"{missing_rows}"
        )

    empty_name_rows = symbol_info[
        symbol_info["match_name"].eq("")
    ]

    if not empty_name_rows.empty:
        raise ValueError(
            "CFM metadata contains empty name values.\n"
            f"{empty_name_rows}"
        )

    duplicated_symbols = symbol_info[
        symbol_info["symbol"].duplicated(keep=False)
    ]

    if not duplicated_symbols.empty:
        raise ValueError(
            "Duplicate CFM metadata symbols detected. "
            "Each CFM product must have a unique symbol.\n"
            f"{duplicated_symbols.sort_values(by=['symbol', 'name'])}"
        )

    LOGGER.info(
        "CFM metadata loaded | symbols=%d",
        len(symbol_info),
    )

    return symbol_info.reset_index(drop=True)


def get_scoped_symbol_info(
    symbol_info: pd.DataFrame,
    file_name: str,
    sheet_name: str,
    category: str | None,
    sub_category: str | None,
    instrument_type: str | None = "SPOT",
) -> pd.DataFrame:
    """
    Filters metadata by category, sub_category, and instrument_type.

    This prevents ambiguous matching if the same product name appears
    in different CFM product groups.
    """

    scoped = symbol_info.copy()

    if category is not None:
        scoped = scoped[
            scoped["category"].eq(category)
        ].copy()

    if sub_category is not None:
        scoped = scoped[
            scoped["sub_category"].eq(sub_category)
        ].copy()

    if instrument_type is not None:
        scoped = scoped[
            scoped["instrument_type"].eq(instrument_type)
        ].copy()

    if scoped.empty:
        raise ValueError(
            "No CFM metadata rows found for matching scope | "
            f"file={file_name} | sheet={sheet_name} | "
            f"category={category} | sub_category={sub_category} | "
            f"instrument_type={instrument_type}"
        )

    duplicated_names = scoped[
        scoped["match_name"].duplicated(keep=False)
    ]

    if not duplicated_names.empty:
        raise ValueError(
            "Duplicate CFM metadata names detected within matching scope. "
            "Matching would be ambiguous.\n"
            f"file={file_name} | sheet={sheet_name} | "
            f"category={category} | sub_category={sub_category} | "
            f"instrument_type={instrument_type}\n"
            f"{duplicated_names.sort_values(by=['match_name', 'symbol'])}"
        )

    return scoped.reset_index(drop=True)


def map_name_to_symbol(
    name: str,
    scoped_symbol_info: pd.DataFrame,
    file_name: str,
    sheet_name: str,
) -> dict:
    """
    Maps one Excel sheet name to metadata symbol information.
    """

    match_name = normalize_match_key(
        name
    )

    matched = scoped_symbol_info[
        scoped_symbol_info["match_name"].eq(match_name)
    ]

    if matched.empty:
        available_names = (
            scoped_symbol_info["name"]
            .dropna()
            .drop_duplicates()
            .sort_values()
            .tolist()
        )

        raise ValueError(
            "CFM Excel name is not mapped in metadata.name | "
            f"file={file_name} | sheet={sheet_name} | name={name}\n"
            f"Available names in scope: {available_names}"
        )

    if len(matched) > 1:
        raise ValueError(
            "Multiple CFM metadata rows matched one Excel name | "
            f"file={file_name} | sheet={sheet_name} | name={name}\n"
            f"{matched}"
        )

    row = matched.iloc[0]

    return {
        "symbol": str(row["symbol"]).strip().upper(),
        "exchange": str(row["exchange"]).strip().upper(),
        "country": str(row["country"]).strip(),
    }


# ============================================================
# Time parser
# ============================================================

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
# Common transform helpers
# ============================================================

def normalize_date_time_columns(
    data: pd.DataFrame,
    file_name: str,
    sheet_name: str,
) -> pd.DataFrame:
    """
    Normalizes Base Date, Release Date, Time, Time Zone columns.
    """

    result = data.copy()

    result.columns = [
        normalize_column_name(column)
        for column in result.columns
    ]

    required_columns = set(DATE_COLUMNS)

    missing_columns = required_columns - set(result.columns)

    if missing_columns:
        raise ValueError(
            "Required date/time columns are missing | "
            f"file={file_name} | sheet={sheet_name} | "
            f"missing={sorted(missing_columns)} | "
            f"columns={list(result.columns)}"
        )

    result["base_date"] = pd.to_datetime(
        result["base_date"],
        errors="raise",
    ).dt.normalize()

    result["release_date"] = pd.to_datetime(
        result["release_date"],
        errors="raise",
    ).dt.normalize()

    result["time"] = parse_time_series(
        result["time"]
    )

    result["time_zone"] = (
        result["time_zone"]
        .astype("string")
        .str.strip()
    )

    return result


def infer_item_columns(
    data: pd.DataFrame,
    file_name: str,
    sheet_name: str,
) -> list[str]:
    """
    Dynamically infers CFM item columns.

    Rule:
        All columns except date/time/id columns become item columns.

    Examples:
        DDR.xlsx:
            low, high, average

        Flash Wafer.xlsx:
            low, open, close
    """

    excluded_columns = set(ID_COLUMNS)

    item_columns = [
        column
        for column in data.columns
        if column not in excluded_columns
        and not str(column).lower().startswith("unnamed")
        and str(column).strip() != ""
    ]

    if not item_columns:
        raise ValueError(
            "No item columns detected | "
            f"file={file_name} | sheet={sheet_name} | "
            f"columns={list(data.columns)}"
        )

    return item_columns


def finalize_cfm_rows(
    data: pd.DataFrame,
    file_name: str,
    sheet_name: str,
) -> pd.DataFrame:
    """
    Converts dynamically detected CFM item columns into item/value long form.

    Rule:
        All non-date/id columns are converted into item/value rows.
    """

    result = data.copy()

    item_columns = infer_item_columns(
        data=result,
        file_name=file_name,
        sheet_name=sheet_name,
    )

    for column in item_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result = result[
        ID_COLUMNS
        + item_columns
    ]

    result = result.melt(
        id_vars=ID_COLUMNS,
        value_vars=item_columns,
        var_name="item",
        value_name="value",
    )

    result["item"] = (
        result["item"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    result["value"] = pd.to_numeric(
        result["value"],
        errors="coerce",
    )

    result = result.dropna(
        subset=[
            "value",
        ]
    )

    result = result[OUTPUT_COLUMNS]

    duplicated_rows = result[
        result.duplicated(
            subset=[
                "base_date",
                "release_date",
                "time",
                "symbol",
                "exchange",
                "item",
            ],
            keep=False,
        )
    ]

    if not duplicated_rows.empty:
        raise ValueError(
            "Duplicate CFM rows detected.\n"
            f"File: {file_name}\n"
            f"Sheet: {sheet_name}\n"
            f"{duplicated_rows}"
        )

    result = (
        result.sort_values(
            by=[
                "base_date",
                "release_date",
                "time",
                "symbol",
                "item",
            ]
        )
        .reset_index(drop=True)
    )

    return result


# ============================================================
# Transform sheets
# ============================================================

def transform_price_sheet(
    df: pd.DataFrame,
    file_name: str,
    sheet_name: str,
    category: str,
    sub_category: str,
    symbol_info: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transforms standard CFM price sheets.

    Input:
        Base Date, Release Date, Time, Time Zone, plus arbitrary value columns.

    Output:
        base_date, release_date, time, time_zone,
        symbol, exchange, country,
        item, value
    """

    data = normalize_date_time_columns(
        data=df,
        file_name=file_name,
        sheet_name=sheet_name,
    )

    scoped_symbol_info = get_scoped_symbol_info(
        symbol_info=symbol_info,
        file_name=file_name,
        sheet_name=sheet_name,
        category=category,
        sub_category=sub_category,
        instrument_type="SPOT",
    )

    product_name = normalize_sheet_name_for_matching(
        sheet_name
    )

    mapped = map_name_to_symbol(
        name=product_name,
        scoped_symbol_info=scoped_symbol_info,
        file_name=file_name,
        sheet_name=sheet_name,
    )

    data["symbol"] = mapped["symbol"]
    data["exchange"] = mapped["exchange"]
    data["country"] = mapped["country"]

    result = finalize_cfm_rows(
        data=data,
        file_name=file_name,
        sheet_name=sheet_name,
    )

    return result


def transform_wafer_sheet(
    df: pd.DataFrame,
    file_name: str,
    sheet_name: str,
    category: str,
    sub_category: str,
    symbol_info: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transforms CFM Flash Wafer sheets.

    Same dynamic item/value rule as transform_price_sheet.
    """

    data = normalize_date_time_columns(
        data=df,
        file_name=file_name,
        sheet_name=sheet_name,
    )

    scoped_symbol_info = get_scoped_symbol_info(
        symbol_info=symbol_info,
        file_name=file_name,
        sheet_name=sheet_name,
        category=category,
        sub_category=sub_category,
        instrument_type="SPOT",
    )

    product_name = normalize_sheet_name_for_matching(
        sheet_name
    )

    mapped = map_name_to_symbol(
        name=product_name,
        scoped_symbol_info=scoped_symbol_info,
        file_name=file_name,
        sheet_name=sheet_name,
    )

    data["symbol"] = mapped["symbol"]
    data["exchange"] = mapped["exchange"]
    data["country"] = mapped["country"]

    result = finalize_cfm_rows(
        data=data,
        file_name=file_name,
        sheet_name=sheet_name,
    )

    return result


# ============================================================
# Workbook reader
# ============================================================

def get_target_sheet_names(
    input_path: Path,
    config: dict,
) -> list[str]:
    """
    Returns target sheet names for one workbook.
    """

    excel_file = pd.ExcelFile(
        input_path
    )

    all_sheet_names = excel_file.sheet_names

    skip_sheets = {
        str(sheet_name).strip()
        for sheet_name in config.get("skip_sheets", set())
    }

    target_sheet_names = [
        sheet_name
        for sheet_name in all_sheet_names
        if str(sheet_name).strip() not in skip_sheets
    ]

    if not target_sheet_names:
        raise ValueError(
            f"No target sheets found | file={input_path.name}"
        )

    return target_sheet_names


def transform_workbook(
    config: dict,
    symbol_info: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transforms one CFM workbook.
    """

    file_name = config["file_name"]
    mode = config["mode"]
    input_path = INPUT_DIR / file_name

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input workbook not found: {input_path}"
        )

    target_sheet_names = get_target_sheet_names(
        input_path=input_path,
        config=config,
    )

    transformed_sheets = []

    for sheet_name in target_sheet_names:
        raw_sheet = pd.read_excel(
            input_path,
            sheet_name=sheet_name,
            header=0,
        )

        LOGGER.info(
            "CFM sheet loaded | file=%s | sheet=%s | mode=%s | rows=%d | columns=%d",
            file_name,
            sheet_name,
            mode,
            raw_sheet.shape[0],
            raw_sheet.shape[1],
        )

        if mode == "price_sheet":
            transformed_sheet = transform_price_sheet(
                df=raw_sheet,
                file_name=file_name,
                sheet_name=sheet_name,
                category=config["category"],
                sub_category=config["sub_category"],
                symbol_info=symbol_info,
            )

        elif mode == "wafer_sheet":
            transformed_sheet = transform_wafer_sheet(
                df=raw_sheet,
                file_name=file_name,
                sheet_name=sheet_name,
                category=config["category"],
                sub_category=config["sub_category"],
                symbol_info=symbol_info,
            )

        else:
            raise ValueError(
                f"Unsupported workbook mode: {mode}"
            )

        LOGGER.info(
            "CFM sheet transformed | file=%s | sheet=%s | rows=%d",
            file_name,
            sheet_name,
            len(transformed_sheet),
        )

        transformed_sheets.append(
            transformed_sheet
        )

    result = pd.concat(
        transformed_sheets,
        ignore_index=True,
    )

    duplicated_rows = result[
        result.duplicated(
            subset=[
                "base_date",
                "release_date",
                "time",
                "symbol",
                "exchange",
                "item",
            ],
            keep=False,
        )
    ]

    if not duplicated_rows.empty:
        raise ValueError(
            "Duplicate CFM rows detected after combining workbook sheets.\n"
            f"File: {file_name}\n"
            f"{duplicated_rows}"
        )

    result = (
        result.sort_values(
            by=[
                "base_date",
                "release_date",
                "time",
                "symbol",
                "item",
            ]
        )
        .reset_index(drop=True)
    )

    return result


# ============================================================
# Main job
# ============================================================

def collect_cfm_industry_data() -> None:
    """
    Reads all CFM industry workbooks,
    maps sheet names to metadata symbols,
    and saves one normalized Parquet file.
    """

    LOGGER.info(
        "CFM industry data job started | input_dir=%s | metadata_path=%s",
        INPUT_DIR,
        METADATA_PATH,
    )

    symbol_info = get_cfm_symbol_info()

    transformed_workbooks = []

    for config in WORKBOOK_CONFIGS:
        transformed_workbook = transform_workbook(
            config=config,
            symbol_info=symbol_info,
        )

        LOGGER.info(
            "CFM workbook transformed | file=%s | rows=%d",
            config["file_name"],
            len(transformed_workbook),
        )

        transformed_workbooks.append(
            transformed_workbook
        )

    result = pd.concat(
        transformed_workbooks,
        ignore_index=True,
    )

    duplicated_rows = result[
        result.duplicated(
            subset=[
                "base_date",
                "release_date",
                "time",
                "symbol",
                "exchange",
                "item",
            ],
            keep=False,
        )
    ]

    if not duplicated_rows.empty:
        raise ValueError(
            "Duplicate CFM rows detected after combining all workbooks.\n"
            f"{duplicated_rows}"
        )

    result = (
        result.sort_values(
            by=[
                "base_date",
                "release_date",
                "time",
                "symbol",
                "item",
            ]
        )
        .reset_index(drop=True)
    )

    if result.empty:
        raise ValueError(
            "No rows remained after CFM industry transformation."
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    LOGGER.info(
        "CFM industry Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(result),
    )


if __name__ == "__main__":
    collect_cfm_industry_data()