from pathlib import Path

import duckdb
import pandas as pd

from src.utils.timezone import (
    normalize_time_column,
    build_timezone_aware_index,
)

# ============================================================
# Industry Service
# ============================================================

class IndustryService(object):
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
            index_data = conn.execute(
                """
                select *
                from industry.index_data
                order by release_date, time, symbol
                """
            ).df()

            components_data = conn.execute(
                """
                select *
                from industry.components_data
                order by release_date, time, symbol, item
                """
            ).df()

        finally:
            conn.close()

        self.index_data = index_data.copy()
        self.components_data = components_data.copy()

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
    def _prepare_common_columns(
        data: pd.DataFrame,
        required_columns: set[str],
    ) -> pd.DataFrame:
        result = data.copy()

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

        if "time" in result.columns:
            result["time"] = normalize_time_column(
                result["time"]
            )

        if "time_zone" in result.columns:
            result["time_zone"] = (
                result["time_zone"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

        if "symbol" in result.columns:
            result["symbol"] = (
                result["symbol"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

        if "item" in result.columns:
            result["item"] = (
                result["item"]
                .astype("string")
                .str.strip()
            )

        if "value" in result.columns:
            result["value"] = pd.to_numeric(
                result["value"],
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
        key_columns: list[str],
    ) -> pd.DataFrame:
        """
        Used when full_data=False.

        Keeps the last observation by:

            index_set + key_columns

        Examples
        --------
        index_data:
            index_set + symbol

        components_data:
            index_set + symbol + item
        """

        sort_columns = [
            index_set,
            *key_columns,
            "release_date",
            "time",
            "time_zone",
        ]

        sort_columns = [
            column
            for column in sort_columns
            if column in data.columns
        ]

        subset_columns = [
            index_set,
            *key_columns,
        ]

        result = (
            data
            .sort_values(
                by=sort_columns
            )
            .drop_duplicates(
                subset=subset_columns,
                keep="last",
            )
            .reset_index(drop=True)
        )

        return result

    def get_index_series(
        self,
        symbols: str | list[str],
        index_set: str = "base_date",
        full_data: bool = False,
        tz: str | int | float | None = "utc+9",
    ) -> pd.Series | pd.DataFrame:
        """
        Return series from industry.index_data.

        symbol 1개:
            pd.Series

        symbol 여러 개:
            pd.DataFrame
            columns = symbol

        full_data=False:
            index = index_set
            keeps the last value by index_set + symbol.

        full_data=True:
            index = timezone-aware datetime index built from:
                index_set + time + time_zone

            target timezone is controlled by tz.
        """

        if not hasattr(self, "index_data"):
            raise AttributeError(
                "self.index_data가 존재하지 않습니다. collect_data()를 먼저 실행하세요."
            )

        symbol_list, is_single_symbol = self._normalize_symbols(
            symbols
        )

        data = self._prepare_common_columns(
            data=self.index_data,
            required_columns={
                "base_date",
                "release_date",
                "time",
                "time_zone",
                "symbol",
                "value",
            },
        )

        data = data.loc[
            data["symbol"].isin(symbol_list),
            [
                "base_date",
                "release_date",
                "time",
                "time_zone",
                "symbol",
                "value",
            ],
        ].copy()

        if data.empty:
            raise ValueError(
                f"symbols not found in index_data: {symbol_list}"
            )

        if not full_data:
            data = self._keep_last_observation(
                data=data,
                index_set=index_set,
                key_columns=[
                    "symbol",
                ],
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
                "duplicated index-symbol pairs detected in index_data.\n"
                f"{duplicated_rows}"
            )

        wide = (
            data
            .pivot(
                index=index_column,
                columns="symbol",
                values="value",
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

        if is_single_symbol:
            series = wide[symbol_list[0]].copy()
            series.name = symbol_list[0]
            return series

        return wide

    def get_components_series(
        self,
        symbols: str | list[str],
        index_set: str = "base_date",
        full_data: bool = False,
        tz: str | int | float | None = "utc+9",
    ) -> pd.DataFrame:
        """
        Return component series from industry.components_data.

        symbol 1개:
            pd.DataFrame
            columns = item

        symbol 여러 개:
            pd.DataFrame
            columns = multiindex(symbol, item)

        item can differ by symbol.

        full_data=False:
            index = index_set
            keeps the last value by index_set + symbol + item.

        full_data=True:
            index = timezone-aware datetime index built from:
                index_set + time + time_zone

            target timezone is controlled by tz.
        """

        if not hasattr(self, "components_data"):
            raise AttributeError(
                "self.components_data가 존재하지 않습니다. collect_data()를 먼저 실행하세요."
            )

        symbol_list, is_single_symbol = self._normalize_symbols(
            symbols
        )

        data = self._prepare_common_columns(
            data=self.components_data,
            required_columns={
                "base_date",
                "release_date",
                "time",
                "time_zone",
                "symbol",
                "item",
                "value",
            },
        )

        data = data.loc[
            data["symbol"].isin(symbol_list),
            [
                "base_date",
                "release_date",
                "time",
                "time_zone",
                "symbol",
                "item",
                "value",
            ],
        ].copy()

        if data.empty:
            raise ValueError(
                f"symbols not found in components_data: {symbol_list}"
            )

        if not full_data:
            data = self._keep_last_observation(
                data=data,
                index_set=index_set,
                key_columns=[
                    "symbol",
                    "item",
                ],
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
                    "item",
                ],
                keep=False,
            )
        ]

        if not duplicated_rows.empty:
            raise ValueError(
                "duplicated index-symbol-item pairs detected in components_data.\n"
                f"{duplicated_rows}"
            )

        wide = (
            data
            .pivot(
                index=index_column,
                columns=[
                    "symbol",
                    "item",
                ],
                values="value",
            )
            .sort_index()
        )

        wide.columns = pd.MultiIndex.from_tuples(
            [
                (
                    str(symbol).strip().upper(),
                    str(item).strip(),
                )
                for symbol, item in wide.columns
            ],
            names=[
                "symbol",
                "field",
            ],
        )

        wide = wide.sort_index(
            axis=1,
            level=[
                0,
                1,
            ],
        )

        wide.index.name = (
            f"{index_set}_full"
            if full_data
            else index_set
        )

        if is_single_symbol:
            symbol = symbol_list[0]

            if symbol not in wide.columns.get_level_values(0):
                raise ValueError(
                    f"symbol not found in components_data: {symbol}"
                )

            single = wide[symbol].copy()
            single = single.sort_index(axis=1)
            single.index.name = wide.index.name

            return single

        return wide

    def get_series(
            self,
            symbols: str | list[str],
            index_set: str = "base_date",
            full_data: bool = False,
            tz: str | int | float | None = "utc+9",
    ) -> pd.DataFrame:
        """
        Return index_data and components_data together.

        핵심 정책:
            - index_data에만 있는 symbol도 허용
            - components_data에만 있는 symbol도 허용
            - 양쪽에 모두 있는 symbol도 허용

        반환 규칙:
            1. index_data만 존재하는 경우
                columns = single-level symbol columns
                예: DXI, CFMDRAM

            2. components_data가 포함되는 경우
                columns = multiindex(symbol, field)

            3. index_data + components_data가 같이 있는 경우
                index_data는 field = "value"로 승격
                components_data는 field = item

        full_data=False:
            index = index_set
            keeps the last observation by index_set.

        full_data=True:
            index = timezone-aware datetime index built from:
                index_set + time + time_zone

            target timezone is controlled by tz.
        """

        symbol_list, _ = self._normalize_symbols(
            symbols
        )

        index_wide: pd.DataFrame | None = None
        components_wide: pd.DataFrame | None = None

        # ========================================================
        # index_data side
        # ========================================================

        if hasattr(self, "index_data"):
            index_data = self._prepare_common_columns(
                data=self.index_data,
                required_columns={
                    "base_date",
                    "release_date",
                    "time",
                    "time_zone",
                    "symbol",
                    "value",
                },
            )

            index_data = index_data.loc[
                index_data["symbol"].isin(symbol_list),
                [
                    "base_date",
                    "release_date",
                    "time",
                    "time_zone",
                    "symbol",
                    "value",
                ],
            ].copy()

            if not index_data.empty:
                if not full_data:
                    index_data = self._keep_last_observation(
                        data=index_data,
                        index_set=index_set,
                        key_columns=[
                            "symbol",
                        ],
                    )

                index_data, index_column = self._build_index_column(
                    data=index_data,
                    index_set=index_set,
                    full_data=full_data,
                    tz=tz,
                )

                duplicated_index_rows = index_data[
                    index_data.duplicated(
                        subset=[
                            index_column,
                            "symbol",
                        ],
                        keep=False,
                    )
                ]

                if not duplicated_index_rows.empty:
                    raise ValueError(
                        "duplicated index-symbol pairs detected in index_data.\n"
                        f"{duplicated_index_rows}"
                    )

                index_wide = (
                    index_data
                    .pivot(
                        index=index_column,
                        columns="symbol",
                        values="value",
                    )
                    .sort_index()
                )

                index_wide = index_wide.reindex(
                    columns=[
                        symbol
                        for symbol in symbol_list
                        if symbol in index_wide.columns
                    ]
                )

                index_wide.index.name = (
                    f"{index_set}_full"
                    if full_data
                    else index_set
                )

        # ========================================================
        # components_data side
        # ========================================================

        if hasattr(self, "components_data"):
            components_data = self._prepare_common_columns(
                data=self.components_data,
                required_columns={
                    "base_date",
                    "release_date",
                    "time",
                    "time_zone",
                    "symbol",
                    "item",
                    "value",
                },
            )

            components_data = components_data.loc[
                components_data["symbol"].isin(symbol_list),
                [
                    "base_date",
                    "release_date",
                    "time",
                    "time_zone",
                    "symbol",
                    "item",
                    "value",
                ],
            ].copy()

            if not components_data.empty:
                if not full_data:
                    components_data = self._keep_last_observation(
                        data=components_data,
                        index_set=index_set,
                        key_columns=[
                            "symbol",
                            "item",
                        ],
                    )

                components_data, index_column = self._build_index_column(
                    data=components_data,
                    index_set=index_set,
                    full_data=full_data,
                    tz=tz,
                )

                duplicated_component_rows = components_data[
                    components_data.duplicated(
                        subset=[
                            index_column,
                            "symbol",
                            "item",
                        ],
                        keep=False,
                    )
                ]

                if not duplicated_component_rows.empty:
                    raise ValueError(
                        "duplicated index-symbol-item pairs detected in components_data.\n"
                        f"{duplicated_component_rows}"
                    )

                components_wide = (
                    components_data
                    .pivot(
                        index=index_column,
                        columns=[
                            "symbol",
                            "item",
                        ],
                        values="value",
                    )
                    .sort_index()
                )

                components_wide.columns = pd.MultiIndex.from_tuples(
                    [
                        (
                            str(symbol).strip().upper(),
                            str(item).strip(),
                        )
                        for symbol, item in components_wide.columns
                    ],
                    names=[
                        "symbol",
                        "field",
                    ],
                )

                components_wide = components_wide.sort_index(
                    axis=1,
                    level=[
                        0,
                        1,
                    ],
                )

                components_wide.index.name = (
                    f"{index_set}_full"
                    if full_data
                    else index_set
                )

        # ========================================================
        # no data found
        # ========================================================

        if index_wide is None and components_wide is None:
            raise ValueError(
                "symbols not found in index_data or components_data: "
                f"{symbol_list}"
            )

        # ========================================================
        # case 1: index_data only
        # 단일 레이어 컬럼 유지
        # ========================================================

        if index_wide is not None and components_wide is None:
            return index_wide

        # ========================================================
        # case 2: components_data only
        # multiindex 유지
        # ========================================================

        if index_wide is None and components_wide is not None:
            return components_wide

        # ========================================================
        # case 3: index_data + components_data
        # 이때만 index_data를 (symbol, "value")로 승격
        # ========================================================

        index_wide_multi = index_wide.copy()

        index_wide_multi.columns = pd.MultiIndex.from_tuples(
            [
                (
                    str(column).strip().upper(),
                    "value",
                )
                for column in index_wide_multi.columns
            ],
            names=[
                "symbol",
                "field",
            ],
        )

        combined = pd.concat(
            [
                index_wide_multi,
                components_wide,
            ],
            axis=1,
            join="outer",
        )

        combined = combined.sort_index()

        combined = combined.sort_index(
            axis=1,
            level=[
                0,
                1,
            ],
        )

        combined.index.name = (
            f"{index_set}_full"
            if full_data
            else index_set
        )

        return combined

    def available_index_symbols(self) -> list[str]:
        if not hasattr(self, "index_data"):
            raise AttributeError(
                "self.index_data가 존재하지 않습니다. collect_data()를 먼저 실행하세요."
            )

        return sorted(
            self.index_data["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
            .dropna()
            .unique()
            .tolist()
        )

    def available_component_symbols(self) -> list[str]:
        if not hasattr(self, "components_data"):
            raise AttributeError(
                "self.components_data가 존재하지 않습니다. collect_data()를 먼저 실행하세요."
            )

        return sorted(
            self.components_data["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
            .dropna()
            .unique()
            .tolist()
        )

    def available_items(
        self,
        symbol: str | None = None,
    ) -> pd.DataFrame | list[str]:
        if not hasattr(self, "components_data"):
            raise AttributeError(
                "self.components_data가 존재하지 않습니다. collect_data()를 먼저 실행하세요."
            )

        data = self.components_data.copy()

        data["symbol"] = (
            data["symbol"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        data["item"] = (
            data["item"]
            .astype("string")
            .str.strip()
        )

        if symbol is not None:
            symbol = symbol.strip().upper()

            return (
                data.loc[
                    data["symbol"].eq(symbol),
                    "item",
                ]
                .dropna()
                .drop_duplicates()
                .sort_values()
                .tolist()
            )

        return (
            data[
                [
                    "symbol",
                    "item",
                ]
            ]
            .dropna()
            .drop_duplicates()
            .sort_values(
                by=[
                    "symbol",
                    "item",
                ]
            )
            .reset_index(drop=True)
        )