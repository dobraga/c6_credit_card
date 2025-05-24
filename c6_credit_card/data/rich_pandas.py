from typing import Optional

import pandas as pd
from rich.table import Table


def df_to_table(
        df: pd.DataFrame, title=None,
        show_index: bool = False, index_name: Optional[str] = None) -> Table:
    """Convert a pandas.DataFrame obj into a rich.Table obj.
    Args:
        df (DataFrame): A Pandas DataFrame to be converted to a rich Table.
        show_index (bool): Add a column with a row count to the table. Defaults to True.
        index_name (str, optional): The column name to give to the index column. Defaults to None, showing no value.
    Returns:
        Table: The rich Table instance passed, populated with the DataFrame values."""
    rich_table = Table(title=title)

    dt_cols = []
    if 'data' in df.columns:
        df.data = df.data.dt.strftime('%d/%m')
        dt_cols.append('data')
    if 'month' in df.columns:
        df.month = df.month.dt.strftime('%m/%Y')
        dt_cols.append('month')

    df = df.drop(columns=['parcelas_totais'], errors='ignore')
    df = df[dt_cols + [c for c in df.columns if c not in dt_cols]]

    if show_index:
        index_name = str(index_name) if index_name else ""
        rich_table.add_column(index_name)

    for column in df.columns:
        rich_table.add_column(str(column))

    for index, value_list in enumerate(df.values.tolist()):
        row = [str(index)] if show_index else []
        row += [str(x) for x in value_list]
        rich_table.add_row(*row)

    return rich_table
