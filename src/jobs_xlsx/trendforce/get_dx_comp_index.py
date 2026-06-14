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
    / "TrendForce"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data_lake"
    / "raw"
    / "industry"
    / "trendforce"
    / "components.parquet"
)

LOGGER = setup_logger(
    name=__name__,
    log_path="logs/jobs/trendforce_industry.log",
)


# ============================================================
# Workbook configuration
# ============================================================

WORKBOOK_CONFIGS = [
    {
        "file_name": "DRAM.xlsx",
        "category": "DRAM",
        "mode": "multi_field",
        "sheets": {
            "DRAM": "DDR",
            "DRAM Contract": "DDR",
            "Module": "Module",
            "GDDR": "GDDR",
        },
    },
    {
        "file_name": "NAND Flash.xlsx",
        "category": "Flash Memory",
        "mode": "multi_field",
        "sheets": {
            "Flash": "NAND",
            "Flash Contract": "NAND",
            "Wafer": "Wafer",
            "Memory Card": "Micro SD",
            "PC-Client OEM SSD": "SSD",
            "SSD Street": "SSD",
        },
    },
    {
        "file_name": "PV.xlsx",
        "category": "PV",
        "mode": "multi_field",
        "sheets": {
            "Polysilicon": "Polysilicon",
            "Wafer": "Wafer",
            "Cell": "Cell",
            "Module": "Module",
            "PV Glass": "PV Glass",
        },
    },
    {
        "file_name": "TFT LCD.xlsx",
        "category": "TFTLCD",
        "mode": "multi_field",
        "sheets": {
            "Large Size Panel": "Large Panel",
            "LCD Smartphone Panel": "Smartphone Panel",
            "Street": "LCD",
            "Large Size Panel Shipment": "Shipment",
        },
    },
    {
        "file_name": "Li-Ion Battery.xlsx",
        "category": "Battery",
        "mode": "single_value",
        "sheets": {
            "Battery Cell & Pack": None,
            "Precursor and Cathode Material": None,
            "Anode Material": "Anode Material",
            "Separator": "Separator",
            "Electrolyte": "Electrolyte",
            "Li & Co & Ni": "LiCoNi",
            "Other": "Other",
        },
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

VALUE_COLUMNS = [
    "high",
    "low",
    "average",
]

OUTPUT_COLUMNS = [
    "base_date",
    "release_date",
    "time",
    "time_zone",
    "symbol",
    "exchange",
    "country",
    "high",
    "low",
    "average",
]


# ============================================================
# Field mapping
# ============================================================

FIELD_MAPPING = {
    "high": "high",
    "low": "low",
    "average": "average",
    "avg": "average",
    "value": "average",
    "worldwide": "average",
    "worldwide area": "average",
    "worldwide (area)": "average",
}

SYMBOL_SUFFIX_BY_FIELD = {
    "worldwide": "W",
    "worldwide area": "WA",
    "worldwide (area)": "WA",
}

IGNORED_FIELDS = {
    "last avg",
    "last average",
    "last_average",
}


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
    Produces whitespace-normalized product-name matching key.
    """

    return " ".join(
        normalize_text_value(value).split()
    )


def normalize_field_key(
    field_name: object,
) -> str:
    """
    Normalizes raw Excel field names for field mapping and suffix rules.
    """

    normalized = (
        normalize_text_value(field_name)
        .lower()
        .replace("_", " ")
    )

    return " ".join(
        normalized.split()
    )


def normalize_field_name(
    field_name: object,
) -> str | None:
    """
    Maps Excel field names to output value columns.

    Last Avg is intentionally ignored.
    """

    field_key = normalize_field_key(field_name)

    if field_key in IGNORED_FIELDS:
        return None

    return FIELD_MAPPING.get(
        field_key
    )


def normalize_fixed_column_name(
    column_name: object,
) -> str:
    """
    Normalizes fixed date/time column names.
    """

    normalized = (
        normalize_text_value(column_name)
        .lower()
        .replace(" ", "_")
    )

    mapping = {
        "base_date": "base_date",
        "release_date": "release_date",
        "time": "time",
        "time_zone": "time_zone",
    }

    return mapping.get(
        normalized,
        normalize_text_value(column_name),
    )


# ============================================================
# Metadata
# ============================================================

def load_metadata(
    metadata_path: Path = METADATA_PATH,
) -> pd.DataFrame:
    """
    Loads metadata.xlsx and normalizes column names and string values.
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


def get_trendforce_symbol_info() -> pd.DataFrame:
    """
    Loads all TrendForce / DRAMExchange industry metadata.

    Matching key:
        Excel product name == metadata.name

    Saved symbol:
        metadata.symbol
    """

    metadata = load_metadata()

    required_columns = {
        "asset_class",
        "category",
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
        & (metadata["exchange"].str.upper() == "DRAMEXCHANGE")
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

    symbol_info["sub_category"] = (
        symbol_info["sub_category"]
        .astype("string")
        .str.strip()
    )

    if symbol_info.empty:
        raise ValueError(
            "No TrendForce metadata rows found."
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

    symbol_info["category"] = (
        symbol_info["category"]
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
            "Metadata contains missing symbol, exchange, country, or name values.\n"
            f"{missing_rows}"
        )

    empty_name_rows = symbol_info[
        symbol_info["match_name"].eq("")
    ]

    if not empty_name_rows.empty:
        raise ValueError(
            "Metadata contains empty name values.\n"
            f"{empty_name_rows}"
        )


    duplicated_symbols = symbol_info[
        symbol_info["symbol"].duplicated(keep=False)
    ]

    if not duplicated_symbols.empty:
        raise ValueError(
            "Duplicate metadata symbols detected. "
            "Each TrendForce product must have a unique symbol.\n"
            f"{duplicated_symbols.sort_values(by=['symbol', 'name'])}"
        )

    LOGGER.info(
        "TrendForce metadata loaded | symbols=%d",
        len(symbol_info),
    )

    return symbol_info.reset_index(drop=True)


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
# Excel reader
# ============================================================

def read_excel_sheet(
    input_path: Path,
    sheet_name: str,
    mode: str,
) -> pd.DataFrame:
    """
    Reads one TrendForce sheet.

    multi_field:
        two-row header
        level 0 = product name
        level 1 = high / low / average / worldwide / etc.

    single_value:
        one-row header
        columns = product names
    """

    if mode == "multi_field":
        data = pd.read_excel(
            input_path,
            sheet_name=sheet_name,
            header=[0, 1],
        )

    elif mode == "single_value":
        data = pd.read_excel(
            input_path,
            sheet_name=sheet_name,
            header=0,
        )

    else:
        raise ValueError(
            f"Unsupported workbook mode: {mode}"
        )

    LOGGER.info(
        "TrendForce sheet loaded | file=%s | sheet=%s | mode=%s | rows=%d | columns=%d",
        input_path.name,
        sheet_name,
        mode,
        data.shape[0],
        data.shape[1],
    )

    return data


# ============================================================
# Finalization
# ============================================================

def finalize_trendforce_rows(
    data: pd.DataFrame,
    file_name: str,
    sheet_name: str,
    category: str,
    sub_category: str | None,
    symbol_info: pd.DataFrame,
) -> pd.DataFrame:
    """
    Maps Excel product names to metadata symbols,
    applies symbol suffixes, and validates final rows.
    """

    data = data.copy()

    data["name"] = data["name"].map(
        normalize_text_value
    )

    data["match_name"] = data["name"].map(
        normalize_match_key
    )

    matched_symbol_info = symbol_info[
        symbol_info["category"].eq(category)
    ].copy()

    if sub_category is not None:
        matched_symbol_info = matched_symbol_info[
            matched_symbol_info["sub_category"].eq(sub_category)
        ].copy()

    if matched_symbol_info.empty:
        raise ValueError(
            "No metadata rows found for matching scope | "
            f"file={file_name} | sheet={sheet_name} | "
            f"category={category} | sub_category={sub_category}"
        )

    duplicated_names = matched_symbol_info[
        matched_symbol_info["match_name"].duplicated(keep=False)
    ]

    if not duplicated_names.empty:
        raise ValueError(
            "Duplicate metadata names detected within matching scope. "
            "Matching would be ambiguous.\n"
            f"file={file_name} | sheet={sheet_name} | "
            f"category={category} | sub_category={sub_category}\n"
            f"{duplicated_names.sort_values(by=['match_name', 'symbol'])}"
        )

    data = data.merge(
        matched_symbol_info[
            [
                "match_name",
                "symbol",
                "exchange",
                "country",
            ]
        ],
        how="left",
        on="match_name",
        validate="many_to_one",
    )

    unmapped_names = (
        data.loc[
            data["symbol"].isna(),
            "name",
        ]
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    if unmapped_names:
        raise ValueError(
            "Excel product names are not mapped in metadata.name | "
            f"file={file_name} | sheet={sheet_name} | names={unmapped_names}"
        )

    if "symbol_suffix" not in data.columns:
        data["symbol_suffix"] = ""

    data["symbol_suffix"] = (
        data["symbol_suffix"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    data["symbol"] = (
        data["symbol"]
        .astype("string")
        .str.strip()
        + data["symbol_suffix"]
    )

    for column in VALUE_COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    data = data[OUTPUT_COLUMNS]

    data = data.dropna(
        how="all",
        subset=VALUE_COLUMNS,
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
            "Duplicate TrendForce rows detected.\n"
            f"File: {file_name}\n"
            f"Sheet: {sheet_name}\n"
            f"{duplicated_rows}"
        )

    return data.reset_index(drop=True)


# ============================================================
# Transform: multi-field sheets
# ============================================================

def transform_multi_field_sheet(
    df: pd.DataFrame,
    file_name: str,
    sheet_name: str,
    category: str,
    sub_category: str | None,
    symbol_info: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transforms sheets with two-row columns.

    Input:
        level 0 = product name
        level 1 = high / low / average / worldwide / worldwide area

    Output:
        base_date, release_date, time, time_zone,
        symbol, exchange, country,
        high, low, average

    Notes:
        Last Avg is ignored.
        Worldwide becomes symbol + W.
        Worldwide Area becomes symbol + WA.
    """

    if not isinstance(df.columns, pd.MultiIndex):
        raise TypeError(
            f"Sheet must have MultiIndex columns | file={file_name} | sheet={sheet_name}"
        )

    data = df.copy()

    fixed_columns = []
    value_columns = []

    normalized_value_columns = []

    for column in data.columns:
        level_0 = normalize_text_value(
            column[0]
        )

        level_1 = normalize_text_value(
            column[1]
        )

        normalized_fixed = normalize_fixed_column_name(
            level_0
        )

        raw_field_key = normalize_field_key(
            level_1
        )

        normalized_field = normalize_field_name(
            level_1
        )

        if normalized_fixed in DATE_COLUMNS:
            fixed_columns.append(
                column
            )

        elif normalized_field is not None:
            value_columns.append(
                column
            )

            symbol_suffix = SYMBOL_SUFFIX_BY_FIELD.get(
                raw_field_key,
                "",
            )

            normalized_value_columns.append(
                (
                    normalize_text_value(level_0),
                    normalized_field,
                    symbol_suffix,
                )
            )

    if not fixed_columns:
        raise ValueError(
            f"No fixed date/time columns detected | file={file_name} | sheet={sheet_name}"
        )

    if not value_columns:
        raise ValueError(
            f"No value columns detected | file={file_name} | sheet={sheet_name}"
        )

    date_part = data[fixed_columns].copy()

    date_part.columns = [
        normalize_fixed_column_name(
            column[0]
        )
        for column in fixed_columns
    ]

    missing_date_columns = (
        set(DATE_COLUMNS)
        - set(date_part.columns)
    )

    if missing_date_columns:
        raise ValueError(
            "Required date/time columns are missing | "
            f"file={file_name} | sheet={sheet_name} | "
            f"missing={sorted(missing_date_columns)}"
        )

    date_part["base_date"] = pd.to_datetime(
        date_part["base_date"],
        errors="raise",
    ).dt.normalize()

    date_part["release_date"] = pd.to_datetime(
        date_part["release_date"],
        errors="raise",
    ).dt.normalize()

    date_part["time"] = parse_time_series(
        date_part["time"]
    )

    date_part["time_zone"] = (
        date_part["time_zone"]
        .astype("string")
        .str.strip()
    )

    value_part = data[value_columns].copy()

    value_part.columns = pd.MultiIndex.from_tuples(
        normalized_value_columns,
        names=[
            "name",
            "field",
            "symbol_suffix",
        ],
    )

    semi_long = (
        value_part
        .stack(
            level=[
                "name",
                "symbol_suffix",
            ],
            future_stack=True,
        )
        .reset_index()
    )

    if "level_0" in semi_long.columns:
        semi_long = semi_long.rename(
            columns={
                "level_0": "_row_id",
            }
        )

    else:
        semi_long = semi_long.rename(
            columns={
                semi_long.columns[0]: "_row_id",
            }
        )

    date_part = date_part.reset_index(
        drop=True
    )

    date_part["_row_id"] = date_part.index

    semi_long = semi_long.merge(
        date_part[
            [
                "_row_id",
                "base_date",
                "release_date",
                "time",
                "time_zone",
            ]
        ],
        how="left",
        on="_row_id",
        validate="many_to_one",
    )

    transformed = finalize_trendforce_rows(
        data=semi_long,
        file_name=file_name,
        sheet_name=sheet_name,
        category=category,
        sub_category=sub_category,
        symbol_info=symbol_info,
    )

    return transformed


# ============================================================
# Transform: single-value sheets
# ============================================================

def transform_single_value_sheet(
    df: pd.DataFrame,
    file_name: str,
    sheet_name: str,
    category: str,
    sub_category: str | None,
    symbol_info: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transforms sheets with one-row columns.

    Input:
        Base Date, Release Date, Time, Time Zone, product_1, product_2, ...

    Output:
        product values are stored in average.
    """

    data = df.copy()

    data.columns = [
        normalize_text_value(column)
        for column in data.columns
    ]

    rename_map = {
        column: normalize_fixed_column_name(column)
        for column in data.columns
    }

    data = data.rename(
        columns=rename_map
    )

    missing_date_columns = (
        set(DATE_COLUMNS)
        - set(data.columns)
    )

    if missing_date_columns:
        raise ValueError(
            "Required date/time columns are missing | "
            f"file={file_name} | sheet={sheet_name} | "
            f"missing={sorted(missing_date_columns)}"
        )

    value_columns = [
        column
        for column in data.columns
        if column not in DATE_COLUMNS
    ]

    if not value_columns:
        raise ValueError(
            f"No value columns detected | file={file_name} | sheet={sheet_name}"
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

    long_df = data.melt(
        id_vars=DATE_COLUMNS,
        value_vars=value_columns,
        var_name="name",
        value_name="average",
    )

    transformed = finalize_trendforce_rows(
        data=long_df,
        file_name=file_name,
        sheet_name=sheet_name,
        category=category,
        sub_category=sub_category,
        symbol_info=symbol_info,
    )

    return transformed


# ============================================================
# Workbook transform
# ============================================================

def transform_workbook(
    config: dict,
    symbol_info: pd.DataFrame,
) -> pd.DataFrame:
    """
    Transforms one TrendForce workbook.
    """

    file_name = config["file_name"]
    mode = config["mode"]
    category = config["category"]
    input_path = INPUT_DIR / file_name

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input workbook not found: {input_path}"
        )

    transformed_sheets = []

    for sheet_name, sub_category in config["sheets"].items():
        raw_sheet = read_excel_sheet(
            input_path=input_path,
            sheet_name=sheet_name,
            mode=mode,
        )

        if mode == "multi_field":
            transformed_sheet = transform_multi_field_sheet(
                df=raw_sheet,
                file_name=file_name,
                sheet_name=sheet_name,
                category=category,
                sub_category=sub_category,
                symbol_info=symbol_info,
            )

        elif mode == "single_value":
            transformed_sheet = transform_single_value_sheet(
                df=raw_sheet,
                file_name=file_name,
                sheet_name=sheet_name,
                category=category,
                sub_category=sub_category,
                symbol_info=symbol_info,
            )

        else:
            raise ValueError(
                f"Unsupported mode: {mode}"
            )

        LOGGER.info(
            "TrendForce sheet transformed | file=%s | sheet=%s | category=%s | sub_category=%s | rows=%d",
            file_name,
            sheet_name,
            category,
            sub_category,
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
            ],
            keep=False,
        )
    ]

    if not duplicated_rows.empty:
        raise ValueError(
            "Duplicate TrendForce rows detected after combining workbook sheets.\n"
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
            ]
        )
        .reset_index(drop=True)
    )

    return result

# ============================================================
# Main job
# ============================================================

def collect_trendforce_industry_data() -> None:
    """
    Reads all TrendForce industry workbooks,
    maps product names to metadata symbols,
    and saves one normalized Parquet file.
    """

    LOGGER.info(
        "TrendForce industry data job started | input_dir=%s | metadata_path=%s",
        INPUT_DIR,
        METADATA_PATH,
    )

    symbol_info = get_trendforce_symbol_info()

    transformed_workbooks = []

    for config in WORKBOOK_CONFIGS:
        transformed_workbook = transform_workbook(
            config=config,
            symbol_info=symbol_info,
        )

        LOGGER.info(
            "TrendForce workbook transformed | file=%s | rows=%d",
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
            ],
            keep=False,
        )
    ]

    if not duplicated_rows.empty:
        raise ValueError(
            "Duplicate TrendForce rows detected after combining all workbooks.\n"
            f"{duplicated_rows}"
        )

    result = (
        result.sort_values(
            by=[
                "base_date",
                "release_date",
                "time",
                "symbol",
            ]
        )
        .reset_index(drop=True)
    )

    if result.empty:
        raise ValueError(
            "No rows remained after TrendForce industry transformation."
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
        "TrendForce industry Parquet saved | output_path=%s | rows=%d",
        OUTPUT_PATH,
        len(result),
    )


if __name__ == "__main__":
    collect_trendforce_industry_data()