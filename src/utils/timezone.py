import pandas as pd

from datetime import timezone, timedelta

# ============================================================
# Timezone Helpers
# ============================================================

def parse_utc_offset(
    tz: str | int | float | None = "utc+9",
) -> timezone:
    """
    Convert user-provided UTC offset into datetime.timezone.

    Accepted examples
    -----------------
    None      -> UTC+0
    "utc"     -> UTC+0
    "utc+0"   -> UTC+0
    "UTC+1"   -> UTC+1
    "utc+09"  -> UTC+9
    "utc-5"   -> UTC-5
    1         -> UTC+1
    9         -> UTC+9
    -5        -> UTC-5
    """

    if tz is None:
        return timezone.utc

    if isinstance(tz, (int, float)):
        hours = int(tz)

        return timezone(
            timedelta(hours=hours)
        )

    if isinstance(tz, str):
        value = (
            tz
            .strip()
            .upper()
            .replace(" ", "")
        )

        if value in {
            "UTC",
            "UTC+0",
            "UTC-0",
            "UTC+00",
            "UTC-00",
            "+0",
            "-0",
            "0",
        }:
            return timezone.utc

        value = value.replace("UTC", "")

        try:
            hours = int(value)

        except ValueError as exc:
            raise ValueError(
                "tz must be like 'utc', 'utc+1', 'UTC+9', 'utc-5', 1, 9, or -5."
            ) from exc

        return timezone(
            timedelta(hours=hours)
        )

    raise TypeError(
        "tz must be str, int, float, or None."
    )


def normalize_time_column(
    series: pd.Series,
) -> pd.Series:
    """
    DuckDB time column may come as datetime.time, string, or object.
    This method normalizes it into HH:MM:SS string format.
    """

    result = (
        series
        .astype("string")
        .str.strip()
    )

    result = (
        result
        .str.replace(
            r"^(\d{2}:\d{2}:\d{2}).*$",
            r"\1",
            regex=True,
        )
    )

    return result


def normalize_utc_offset_for_parsing(
    series: pd.Series,
) -> pd.Series:
    """
    Convert UTC offset strings into pandas-parseable offset strings.

    Examples
    --------
    UTC+0 -> +00:00
    UTC+1 -> +01:00
    UTC+9 -> +09:00
    UTC-5 -> -05:00
    """

    result = (
        series
        .astype("string")
        .str.strip()
        .str.upper()
        .str.replace("UTC", "", regex=False)
    )

    def convert(value: str) -> str:
        if pd.isna(value):
            return pd.NA

        value = str(value).strip()

        if value in {
            "",
            "+0",
            "-0",
            "0",
            "+00",
            "-00",
        }:
            return "+00:00"

        sign = "+"

        if value.startswith("-"):
            sign = "-"
            value = value[1:]

        elif value.startswith("+"):
            value = value[1:]

        hours = int(value)

        return f"{sign}{hours:02d}:00"

    return result.map(convert)


def build_timezone_aware_index(
    data: pd.DataFrame,
    index_set: str,
    tz: str | int | float | None = "utc+9",
    index_column: str = "__datetime_index__",
) -> tuple[pd.DataFrame, str]:
    """
    Build a timezone-aware datetime index column from:

        index_set + time + time_zone

    Process
    -------
    1. Parse original local timestamp using row-level UTC offset.
    2. Convert all timestamps to UTC.
    3. Convert UTC timestamps to target timezone offset.
    4. Return dataframe and generated index column name.

    Example
    -------
    input:
        release_date = 2026-06-08
        time         = 14:00:00
        time_zone    = UTC+9

    tz="utc":
        2026-06-08 05:00:00+00:00

    tz="utc+1":
        2026-06-08 06:00:00+01:00

    tz=9:
        2026-06-08 14:00:00+09:00
    """

    result = data.copy()

    required_columns = {
        index_set,
        "time",
        "time_zone",
    }

    missing_columns = required_columns - set(result.columns)

    if missing_columns:
        raise ValueError(
            "required columns for timezone-aware index are missing: "
            f"{sorted(missing_columns)}"
        )

    target_tz = parse_utc_offset(
        tz
    )

    result[index_set] = pd.to_datetime(
        result[index_set],
        errors="raise",
    ).dt.normalize()

    result["time"] = normalize_time_column(
        result["time"]
    )

    offset = normalize_utc_offset_for_parsing(
        result["time_zone"]
    )

    datetime_text = (
        result[index_set].dt.strftime("%Y-%m-%d")
        + " "
        + result["time"].astype(str)
        + " "
        + offset.astype(str)
    )

    result[index_column] = (
        pd.to_datetime(
            datetime_text,
            errors="raise",
            utc=True,
        )
        .dt.tz_convert(target_tz)
    )

    return result, index_column