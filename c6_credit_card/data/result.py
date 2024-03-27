from dataclasses import dataclass
from typing import Optional

from pandas import DataFrame

from .rich_pandas import df_to_table


@dataclass
class Result:
    data: DataFrame

    def top(self, top: int):
        return Result(self.data.head(top).copy())

    def sort(self, **kwargs):
        return Result(self.data.sort_values(**kwargs))

    def print(
        self, title=None, show_index: bool = False, index_name: Optional[str] = None
    ):
        return df_to_table(self.data, title, show_index, index_name)
