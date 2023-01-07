from dataclasses import dataclass
from pandas import DataFrame
from typing import Optional

from .rich_pandas import df_to_table


@dataclass
class Result:
    data: DataFrame

    def top(self, top: int):
        return Result(self.data.head(top))

    def print(self, title=None, show_index: bool = False,
              index_name: Optional[str] = None):
        return df_to_table(self.data, title, show_index, index_name)