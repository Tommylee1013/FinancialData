from pathlib import Path

import duckdb
import pandas as pd

from src.utils.timezone import (
    normalize_time_column,
    build_timezone_aware_index,
)


# ============================================================
# Price Service
# ============================================================

class PriceService(object):
    def __init__(
        self,
        db_path: str | Path,
        multi_level_index: bool = True,
    ) -> None:
        self.db_path = Path(db_path)
        self.multi_level_index = multi_level_index
        self.collect_data()

    def collect_data(self) -> None:
        conn = duckdb.connect(
            str(self.db_path),
            read_only=True,
        )

        try:
            index_data = conn.execute(
                """
                select
                    'index' as asset_type,
                    *
                from market.index_data
                order by release_date, time, symbol
                """
            ).df()

            volatility_data = conn.execute(
                """
                select
                    'volatility' as asset_type,
                    *
                from market.volatility_data
                order by release_date, time, symbol
                """
            ).df()

            fx_data = conn.execute(
                """
                select 'fx' as asset_type,
                       *
                from market.fx_data
                order by release_date, time, symbol
                """
            ).df()

        finally:
            conn.close()

        self.index_data = index_data.copy()
        self.volatility_data = volatility_data.copy()
        self.fx_data = fx_data.copy()

        self.data = (
            pd.concat(
                [
                    self.index_data,
                    self.volatility_data,
                    self.fx_data
                ],
                axis=0,
                ignore_index=True,
            )
        )

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
    def _normalize_asset_types(
        asset_types: str | list[str] | None,
    ) -> list[str] | None:
        if asset_types is None:
            return None

        if isinstance(asset_types, str):
            asset_type_list = [
                asset_types.strip().lower()
            ]

        elif isinstance(asset_types, list):
            asset_type_list = [
                str(asset_type).strip().lower()
                for asset_type in asset_types
            ]

            asset_type_list = [
                asset_type
                for asset_type in asset_type_list
                if asset_type
            ]

        else:
            raise TypeError(
                "asset_types must be str, list[str], or None."
            )

        valid_asset_types = {
            "index",
            "volatility",
            'fx',
        }

        invalid_asset_types = sorted(
            set(asset_type_list) - valid_asset_types
        )

        if invalid_asset_types:
            raise ValueError(
                "invalid asset_types: "
                f"{invalid_asset_types}. "
                "valid asset_types are ['index', 'volatility', 'fx']."
            )

        if not asset_type_list:
            raise ValueError(
                "asset_types list is empty."
            )

        return asset_type_list

    @staticmethod
    def _normalize_value_columns(
        value_column: str | list[str] | None,
    ) -> tuple[list[str], bool]:
        """
        value_column:
            str:
                single field only.
                example: "close"

            list[str]:
                selected fields.
                example: ["open", "close"]

            None:
                full OHLCV.
                ["open", "high", "low", "close", "volume"]

        Returns
        -------
        tuple[list[str], bool]
            value_columns, is_single_value_column
        """

        valid_value_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

        if value_column is None:
            return valid_value_columns.copy(), False

        if isinstance(value_column, str):
            column = value_column.strip().lower()

            if column not in valid_value_columns:
                raise ValueError(
                    "invalid value_column: "
                    f"{column}. "
                    "valid value_columns are "
                    "['open', 'high', 'low', 'close', 'volume']."
                )

            return [column], True

        if isinstance(value_column, list):
            columns = [
                str(column).strip().lower()
                for column in value_column
            ]

            columns = [
                column
                for column in columns
                if column
            ]

            if not columns:
                raise ValueError(
                    "value_column list is empty."
                )

            invalid_columns = [
                column
                for column in columns
                if column not in valid_value_columns
            ]

            if invalid_columns:
                raise ValueError(
                    "invalid value_column: "
                    f"{invalid_columns}. "
                    "valid value_columns are "
                    "['open', 'high', 'low', 'close', 'volume']."
                )

            columns = [
                column
                for column in valid_value_columns
                if column in columns
            ]

            return columns, len(columns) == 1

        raise TypeError(
            "value_column must be str, list[str], or None."
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
            "exchange",
            "country",
            "asset_type",
            "open",
            "high",
            "low",
            "close",
            "volume",
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

        result["exchange"] = (
            result["exchange"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        result["country"] = (
            result["country"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        result["asset_type"] = (
            result["asset_type"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
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
            "asset_type",
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

    @staticmethod
    def _remove_duplicate_index(
        obj: pd.Series | pd.DataFrame,
        duplicate_index_method: str = "last",
    ) -> pd.Series | pd.DataFrame:
        """
        Remove duplicated index after pivot/unstack.

        duplicate_index_method:
            - "last"
            - "first"
            - "mean"
        """

        if not obj.index.has_duplicates:
            return obj

        if duplicate_index_method == "last":
            return obj.groupby(level=0).last()

        if duplicate_index_method == "first":
            return obj.groupby(level=0).first()

        if duplicate_index_method == "mean":
            return obj.groupby(level=0).mean(numeric_only=True)

        raise ValueError(
            "duplicate_index_method must be one of "
            "['last', 'first', 'mean']."
        )

    def _filter_data(
        self,
        symbols: str | list[str],
        index_set: str,
        asset_types: str | list[str] | None,
    ) -> tuple[pd.DataFrame, list[str], bool]:
        if not hasattr(self, "data"):
            raise AttributeError(
                "self.data가 존재하지 않습니다. 먼저 collect_data()를 실행하세요."
            )

        symbol_list, is_single_symbol = self._normalize_symbols(
            symbols
        )

        asset_type_list = self._normalize_asset_types(
            asset_types=asset_types,
        )

        data = self._prepare_data(
            data=self.data,
            index_set=index_set,
        )

        if asset_type_list is not None:
            data = data.loc[
                data["asset_type"].isin(asset_type_list)
            ].copy()

        data = data.loc[
            data["symbol"].isin(symbol_list)
        ].copy()

        if data.empty:
            raise ValueError(
                "symbols not found: "
                f"{symbol_list}"
            )

        symbol_asset_count = (
            data[
                [
                    "symbol",
                    "asset_type",
                ]
            ]
            .drop_duplicates()
            .groupby("symbol")
            .size()
        )

        duplicated_symbols = (
            symbol_asset_count[
                symbol_asset_count > 1
            ]
            .index
            .tolist()
        )

        if duplicated_symbols:
            raise ValueError(
                "same symbol exists in multiple asset_types. "
                "please specify asset_types='index' or "
                "asset_types='volatility'. "
                f"duplicated symbols: {duplicated_symbols}"
            )

        return data, symbol_list, is_single_symbol

    def get_series(
        self,
        symbols: str | list[str],
        index_set: str = "base_date",
        value_column: str | list[str] | None = None,
        asset_types: str | list[str] | None = None,
        full_data: bool = False,
        tz: str | int | float | None = "utc+9",
        ffill: bool = False,
        multi_level_index: bool | None = None,
        duplicate_index_method: str = "last",
    ) -> pd.Series | pd.DataFrame:
        """
        Return price series from market.index_data and market.volatility_data.

        Parameters
        ----------
        symbols:
            Single symbol or list of symbols.

        index_set:
            Date column used as index.
            Recommended values:
                - "base_date"
                - "release_date"

        value_column:
            str:
                Return one field only.
                Example:
                    value_column="close"

            list[str]:
                Return selected fields.
                Example:
                    value_column=["open", "close"]

            None:
                Return full OHLCV.
                Equivalent to:
                    ["open", "high", "low", "close", "volume"]

        asset_types:
            Optional table filter.
            Accepted values:
                - None
                    Use both index_data and volatility_data.
                - "index"
                    Use market.index_data only.
                - "volatility"
                    Use market.volatility_data only.
                - list[str]
                    Example: ["index", "volatility"]

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

        ffill:
            If True, forward-fill missing values after wide conversion.

        multi_level_index:
            Used only when multiple value columns are returned.

            True:
                columns=MultiIndex(symbol, field)
                Example:
                    ("SPX", "close")

            False:
                columns=MultiIndex(field, symbol)
                Example:
                    ("close", "SPX")

            None:
                Use self.multi_level_index.

        duplicate_index_method:
            How to aggregate duplicated index after pivot.
            Accepted values:
                - "last"
                - "first"
                - "mean"

        Returns
        -------
        pd.Series:
            Returned when:
                - symbols is str
                - value_column is str

        pd.DataFrame:
            Returned otherwise.
        """

        if multi_level_index is None:
            multi_level_index = self.multi_level_index

        value_columns, is_single_value_column = self._normalize_value_columns(
            value_column=value_column,
        )

        data, symbol_list, is_single_symbol = self._filter_data(
            symbols=symbols,
            index_set=index_set,
            asset_types=asset_types,
        )

        keep_columns = [
            "base_date",
            "release_date",
            "time",
            "time_zone",
            "symbol",
            "exchange",
            "country",
            "asset_type",
        ] + value_columns

        data = data[
            [
                column
                for column in keep_columns
                if column in data.columns
            ]
        ].copy()

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

        # ----------------------------------------------------
        # Case 1. Single value column
        # ----------------------------------------------------
        if is_single_value_column:
            field = value_columns[0]

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

            wide = self._remove_duplicate_index(
                obj=wide,
                duplicate_index_method=duplicate_index_method,
            )

            if ffill:
                wide = wide.ffill()

            if is_single_symbol:
                series = wide[symbol_list[0]].copy()
                series.name = symbol_list[0]
                return series

            return wide

        # ----------------------------------------------------
        # Case 2. Multiple value columns: OHLCV or selected fields
        # ----------------------------------------------------
        wide = (
            data
            .pivot(
                index=index_column,
                columns="symbol",
                values=value_columns,
            )
            .sort_index()
        )

        # pivot result is columns=(field, symbol)
        # First, force complete field-symbol order.
        wide = wide.reindex(
            columns=pd.MultiIndex.from_product(
                [
                    value_columns,
                    symbol_list,
                ],
                names=[
                    "field",
                    "symbol",
                ],
            )
        )

        wide.index.name = (
            f"{index_set}_full"
            if full_data
            else index_set
        )

        wide = self._remove_duplicate_index(
            obj=wide,
            duplicate_index_method=duplicate_index_method,
        )

        if ffill:
            wide = wide.ffill()

        # Single asset:
        # columns should be single index:
        # open, high, low, close, volume
        if is_single_symbol:
            single = wide.xs(
                symbol_list[0],
                axis=1,
                level="symbol",
            )

            single = single.reindex(
                columns=value_columns
            )

            single.columns.name = None

            return single

        # Multiple assets:
        # multi_level_index=True:
        #   columns=(symbol, field)
        # multi_level_index=False:
        #   columns=(field, symbol)
        if multi_level_index:
            wide = wide.swaplevel(
                "field",
                "symbol",
                axis=1,
            )

            wide = wide.reindex(
                columns=pd.MultiIndex.from_product(
                    [
                        symbol_list,
                        value_columns,
                    ],
                    names=[
                        "symbol",
                        "field",
                    ],
                )
            )

            return wide.sort_index(axis=1)

        wide = wide.reindex(
            columns=pd.MultiIndex.from_product(
                [
                    value_columns,
                    symbol_list,
                ],
                names=[
                    "field",
                    "symbol",
                ],
            )
        )

        return wide.sort_index(axis=1)

    def available_symbols(
        self,
        asset_types: str | list[str] | None = None,
    ) -> list[str]:
        """
        Return available symbols in market.index_data and market.volatility_data.
        """

        if not hasattr(self, "data"):
            raise AttributeError(
                "self.data가 존재하지 않습니다. 먼저 collect_data()를 실행하세요."
            )

        data = self.data.copy()

        asset_type_list = self._normalize_asset_types(
            asset_types=asset_types,
        )

        if asset_type_list is not None:
            data["asset_type"] = (
                data["asset_type"]
                .astype("string")
                .str.strip()
                .str.lower()
            )

            data = data.loc[
                data["asset_type"].isin(asset_type_list)
            ].copy()

        return sorted(
            data["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
            .dropna()
            .unique()
            .tolist()
        )

    def available_symbol_info(
        self,
        asset_types: str | list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Return symbol-level metadata such as asset_type, exchange, and country.
        """

        if not hasattr(self, "data"):
            raise AttributeError(
                "self.data가 존재하지 않습니다. 먼저 collect_data()를 실행하세요."
            )

        data = self.data.copy()

        asset_type_list = self._normalize_asset_types(
            asset_types=asset_types,
        )

        data["symbol"] = (
            data["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        data["asset_type"] = (
            data["asset_type"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        if asset_type_list is not None:
            data = data.loc[
                data["asset_type"].isin(asset_type_list)
            ].copy()

        columns = [
            column
            for column in [
                "symbol",
                "asset_type",
                "exchange",
                "country",
            ]
            if column in data.columns
        ]

        return (
            data[columns]
            .drop_duplicates()
            .sort_values(
                by=[
                    "asset_type",
                    "symbol",
                ]
            )
            .reset_index(drop=True)
        )