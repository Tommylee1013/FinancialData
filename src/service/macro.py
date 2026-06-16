from pathlib import Path

import duckdb
import pandas as pd

from src.utils.timezone import (
    normalize_time_column,
    build_timezone_aware_index,
)

# ============================================================
# Macro Service
# ============================================================

class MacroService(object):
    def __init__(
        self,
        db_path: str | Path,
    ) -> None:
        self.db_path = Path(db_path)
        self.collect_data()

    def collect_data(self) -> None:
        conn = duckdb.connect(
            str(self.db_path),
            read_only=True,
        )

        try:
            data = conn.execute(
                """
                select *
                from macro.macro_data
                order by release_date, time, symbol
                """
            ).df()

        finally:
            conn.close()

        self.data = data.copy()

    @staticmethod
    def _normalize_symbols(
        symbols: str | list[str],
    ) -> tuple[list[str], bool]:
        if isinstance(symbols, str):
            return [symbols.strip().upper()], True

        if isinstance(symbols, list):
            symbol_list = [
                str(symbol).strip().upper()
                for symbol in symbols
            ]

            symbol_list = [
                symbol
                for symbol in symbol_list
                if symbol
            ]

            if not symbol_list:
                raise ValueError(
                    "symbols list is empty."
                )

            return symbol_list, False

        raise TypeError(
            "symbols must be str or list[str]."
        )

    @staticmethod
    def _normalize_value_fields(
        value_fields: str | list[str],
    ) -> tuple[list[str], bool]:
        if isinstance(value_fields, str):
            return [value_fields.strip().lower()], True

        if isinstance(value_fields, list):
            field_list = [
                str(field).strip().lower()
                for field in value_fields
            ]

            field_list = [
                field
                for field in field_list
                if field
            ]

            if not field_list:
                raise ValueError(
                    "value_fields list is empty."
                )

            return field_list, False

        raise TypeError(
            "value_fields must be str or list[str]."
        )

    @staticmethod
    def _prepare_data(
        data: pd.DataFrame,
        index_set: str,
    ) -> pd.DataFrame:
        result = data.copy()

        required_columns = {
            index_set,
            "release_date",
            "time",
            "time_zone",
            "symbol",
            "actual",
            "forecast",
            "previous",
            "preliminary_release",
        }

        missing_columns = required_columns - set(result.columns)

        if missing_columns:
            raise ValueError(
                "required columns are missing: "
                f"{sorted(missing_columns)}"
            )

        for column in [
            "base_date",
            "release_date",
        ]:
            if column in result.columns:
                result[column] = pd.to_datetime(
                    result[column],
                    errors="raise",
                ).dt.normalize()

        result["time"] = normalize_time_column(
            result["time"]
        )

        result["time_zone"] = (
            result["time_zone"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        result["symbol"] = (
            result["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        if "exchange" in result.columns:
            result["exchange"] = (
                result["exchange"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

        if "country" in result.columns:
            result["country"] = (
                result["country"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

        for column in [
            "actual",
            "forecast",
            "previous",
        ]:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

        result["preliminary_release"] = (
            result["preliminary_release"]
            .astype("boolean")
        )

        return result

    @staticmethod
    def _build_index_column(
        data: pd.DataFrame,
        index_set: str,
        full_data: bool,
        tz: str | int | float | None = "utc+9",
    ) -> tuple[pd.DataFrame, str]:
        """
        full_data=False:
            use index_set as index.

        full_data=True:
            create timezone-aware datetime index from:
                index_set + time + time_zone

        The final index timezone is controlled by tz.
        """

        result = data.copy()

        if index_set not in result.columns:
            raise ValueError(
                f"index_set column not found: {index_set}"
            )

        result[index_set] = pd.to_datetime(
            result[index_set],
            errors="raise",
        ).dt.normalize()

        if not full_data:
            return result, index_set

        result, index_column = build_timezone_aware_index(
            data=result,
            index_set=index_set,
            tz=tz,
            index_column="__datetime_index__",
        )

        return result, index_column

    @staticmethod
    def _keep_last_observation(
        data: pd.DataFrame,
        index_set: str,
    ) -> pd.DataFrame:
        """
        Used when full_data=False.

        Keeps the last observation by:

            index_set + symbol

        If there are multiple releases on the same date,
        the latest value is selected by release_date, time, and time_zone.
        """

        sort_columns = [
            index_set,
            "symbol",
            "release_date",
            "time",
            "time_zone",
        ]

        sort_columns = [
            column
            for column in sort_columns
            if column in data.columns
        ]

        result = (
            data
            .sort_values(
                by=sort_columns
            )
            .drop_duplicates(
                subset=[
                    index_set,
                    "symbol",
                ],
                keep="last",
            )
            .reset_index(drop=True)
        )

        return result

    def get_series(
        self,
        symbols: str | list[str],
        index_set: str = "base_date",
        value_fields: str | list[str] = "actual",
        full_data: bool = False,
        tz: str | int | float | None = "utc+9",
        ffill: bool = False,
    ) -> pd.Series | pd.DataFrame:
        """
        Return macro series from long-form macro data.

        Parameters
        ----------
        symbols:
            Single symbol or list of symbols.

        index_set:
            Date column used as index.
            Recommended values:
                - "base_date"
                - "release_date"

        value_fields:
            Field or fields to return.

            Available values:
                - "actual"
                - "forecast"
                - "previous"
                - "preliminary_release"

            If one field is selected:
                symbols=str       -> pd.Series
                symbols=list[str] -> pd.DataFrame with single-level columns

            If multiple fields are selected:
                always returns pd.DataFrame with multiindex columns:
                    symbol, field

        full_data:
            False:
                Keeps the last value by index_set + symbol.
                Index is index_set.

            True:
                Builds timezone-aware datetime index from:
                    index_set + time + time_zone

                The output timezone is controlled by tz.

        tz:
            Target timezone when full_data=True.

            Accepted examples:
                - "utc"
                - "utc+0"
                - "utc+1"
                - "UTC+9"
                - 0
                - 1
                - 9
                - -5

            Default:
                "utc+9"

        ffill:
            If True, forward-fill missing values after wide conversion.

        Returns
        -------
        pd.Series:
            Returned only when symbols is str and value_fields is str.

        pd.DataFrame:
            Returned otherwise.
        """

        if not hasattr(self, "data"):
            raise AttributeError(
                "self.data가 존재하지 않습니다. 먼저 collect_data()를 실행하세요."
            )

        symbol_list, is_single_symbol = self._normalize_symbols(
            symbols
        )

        field_list, is_single_field = self._normalize_value_fields(
            value_fields
        )

        allowed_fields = {
            "actual",
            "forecast",
            "previous",
            "preliminary_release",
        }

        invalid_fields = set(field_list) - allowed_fields

        if invalid_fields:
            raise ValueError(
                "invalid value_fields detected: "
                f"{sorted(invalid_fields)}. "
                f"allowed fields are: {sorted(allowed_fields)}"
            )

        data = self._prepare_data(
            data=self.data,
            index_set=index_set,
        )

        selected_columns = [
            "base_date",
            "release_date",
            "time",
            "time_zone",
            "symbol",
            *field_list,
        ]

        data = data.loc[
            data["symbol"].isin(symbol_list),
            selected_columns,
        ].copy()

        if data.empty:
            raise ValueError(
                f"symbols not found: {symbol_list}"
            )

        if not full_data:
            data = self._keep_last_observation(
                data=data,
                index_set=index_set,
            )

        data, index_column = self._build_index_column(
            data=data,
            index_set=index_set,
            full_data=full_data,
            tz=tz,
        )

        duplicated_rows = data[
            data.duplicated(
                subset=[
                    index_column,
                    "symbol",
                ],
                keep=False,
            )
        ]

        if not duplicated_rows.empty:
            raise ValueError(
                "duplicated index-symbol pairs detected. "
                "use full_data=True or check duplicated rows.\n"
                f"{duplicated_rows}"
            )

        # ========================================================
        # Case 1: single value field
        #   columns = symbol
        # ========================================================

        if is_single_field:
            field = field_list[0]

            wide = (
                data
                .pivot(
                    index=index_column,
                    columns="symbol",
                    values=field,
                )
                .sort_index()
            )

            wide = wide.reindex(
                columns=symbol_list
            )

            wide.index.name = (
                f"{index_set}_full"
                if full_data
                else index_set
            )

            if ffill:
                wide = wide.ffill()

            if is_single_symbol:
                series = wide[symbol_list[0]].copy()
                series.name = symbol_list[0]
                return series

            return wide

        # ========================================================
        # Case 2: multiple value fields
        #   columns = multiindex(symbol, field)
        # ========================================================

        melted = data.melt(
            id_vars=[
                index_column,
                "symbol",
            ],
            value_vars=field_list,
            var_name="field",
            value_name="value",
        )

        duplicated_melted_rows = melted[
            melted.duplicated(
                subset=[
                    index_column,
                    "symbol",
                    "field",
                ],
                keep=False,
            )
        ]

        if not duplicated_melted_rows.empty:
            raise ValueError(
                "duplicated index-symbol-field pairs detected.\n"
                f"{duplicated_melted_rows}"
            )

        wide = (
            melted
            .pivot(
                index=index_column,
                columns=[
                    "symbol",
                    "field",
                ],
                values="value",
            )
            .sort_index()
        )

        wide.columns = pd.MultiIndex.from_tuples(
            [
                (
                    str(symbol).strip().upper(),
                    str(field).strip().lower(),
                )
                for symbol, field in wide.columns
            ],
            names=[
                "symbol",
                "field",
            ],
        )

        ordered_columns = [
            (
                symbol,
                field,
            )
            for symbol in symbol_list
            for field in field_list
            if (
                symbol,
                field,
            ) in wide.columns
        ]

        wide = wide.reindex(
            columns=pd.MultiIndex.from_tuples(
                ordered_columns,
                names=[
                    "symbol",
                    "field",
                ],
            )
        )

        wide.index.name = (
            f"{index_set}_full"
            if full_data
            else index_set
        )

        if ffill:
            wide = wide.ffill()

        return wide

    def get_actual_series(
        self,
        symbols: str | list[str],
        index_set: str = "base_date",
        full_data: bool = False,
        tz: str | int | float | None = "utc+9",
        ffill: bool = False,
    ) -> pd.Series | pd.DataFrame:
        return self.get_series(
            symbols=symbols,
            index_set=index_set,
            value_fields="actual",
            full_data=full_data,
            tz=tz,
            ffill=ffill,
        )

    def get_forecast_series(
        self,
        symbols: str | list[str],
        index_set: str = "base_date",
        full_data: bool = False,
        tz: str | int | float | None = "utc+9",
        ffill: bool = False,
    ) -> pd.Series | pd.DataFrame:
        return self.get_series(
            symbols=symbols,
            index_set=index_set,
            value_fields="forecast",
            full_data=full_data,
            tz=tz,
            ffill=ffill,
        )

    def get_previous_series(
        self,
        symbols: str | list[str],
        index_set: str = "base_date",
        full_data: bool = False,
        tz: str | int | float | None = "utc+9",
        ffill: bool = False,
    ) -> pd.Series | pd.DataFrame:
        return self.get_series(
            symbols=symbols,
            index_set=index_set,
            value_fields="previous",
            full_data=full_data,
            tz=tz,
            ffill=ffill,
        )

    def get_release_flag_series(
        self,
        symbols: str | list[str],
        index_set: str = "base_date",
        full_data: bool = False,
        tz: str | int | float | None = "utc+9",
        ffill: bool = False,
    ) -> pd.Series | pd.DataFrame:
        return self.get_series(
            symbols=symbols,
            index_set=index_set,
            value_fields="preliminary_release",
            full_data=full_data,
            tz=tz,
            ffill=ffill,
        )

    def available_symbols(self) -> list[str]:
        """
        Return available symbols in macro.macro_data.
        """

        if not hasattr(self, "data"):
            raise AttributeError(
                "self.data가 존재하지 않습니다. 먼저 collect_data()를 실행하세요."
            )

        return sorted(
            self.data["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
            .dropna()
            .unique()
            .tolist()
        )

    def available_symbol_info(self) -> pd.DataFrame:
        """
        Return symbol-level metadata such as exchange and country.
        """

        if not hasattr(self, "data"):
            raise AttributeError(
                "self.data가 존재하지 않습니다. 먼저 collect_data()를 실행하세요."
            )

        data = self.data.copy()

        data["symbol"] = (
            data["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        columns = [
            column
            for column in [
                "symbol",
                "exchange",
                "country",
            ]
            if column in data.columns
        ]

        return (
            data[columns]
            .drop_duplicates()
            .sort_values(
                by="symbol"
            )
            .reset_index(drop=True)
        )

    def available_fields(self) -> list[str]:
        """
        Return available value fields in macro.macro_data.
        """

        return [
            "actual",
            "forecast",
            "previous",
            "preliminary_release",
        ]