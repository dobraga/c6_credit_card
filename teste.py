import pandas as pd
from tabula.io import read_pdf


def _process_fatura(fatura: pd.DataFrame):
    if fatura.shape[1] != 4:
        return pd.DataFrame()

    columns = ["data", "local", "delete", "valor"]
    first_row = pd.DataFrame(fatura.columns).T
    fatura.columns = columns
    first_row.columns = columns

    return pd.concat([first_row, fatura], axis=0)


dfs = read_pdf(
    "faturas/Fatura_2024_04.pdf", password="107923", pages="all", silent=True
)
dfs = [_process_fatura(df) for df in dfs[1:-1]]
df = pd.concat(dfs, axis=0).drop(columns=["delete"])

print(df.query('local.str.contains("BUSER" )'))
