from os import getenv
from logging import getLogger

import numpy as np
import pandas as pd

from c6_credit_card.data.file import File
from c6_credit_card.data.files import Files

LOG = getLogger(__name__)

def read_files(pasta, force):
    files = Files(pasta)
    LOG.info(files)
    pswd = getenv("password") or input("Senha do arquivo: ")
    files.process(pswd, force=force)
    return files


def plot_data_total(files: Files):
    values: pd.DataFrame = files.summary_all().reset_index().sort_values("month")

    ys = values.tot_value.tolist()
    xs = values.month.tolist()
    return ys, xs


def plot_next_months(file: File):
    recorrentes = file._df.query('type == "recorrente"').valor.sum()
    parcelas = (
        file._df.query("parcela > 0 and parcelas_faltantes > 0")
        .groupby("parcelas_faltantes")["valor"]
        .sum()
    )

    parcelas = parcelas.sort_index(ascending=False).cumsum().sort_index()

    if not parcelas.empty:
        max_index = parcelas.index.max()
    else:
        max_index = 0

    arr = np.full(max_index + 1, np.nan)

    for idx, value in parcelas.items():
        arr[idx] = value

    parcelas = pd.Series(arr[1:], name="parcelas_faltantes").ffill().fillna(0) # Added fillna(0)

    parcelas_rec = parcelas + recorrentes

    print(f"total parcelas: R${parcelas.sum():,.2f} | recorrente: R${recorrentes:,.2f}")
    print(
        pd.DataFrame(
            {"parcelas": parcelas, "recorrente": recorrentes, "total": parcelas_rec}
        )
    )

    ys = parcelas_rec.values.tolist()
    xs = parcelas_rec.index.tolist()
    return ys, xs


def plot_data_type(files: Files):
    types: pd.DataFrame = files.summary_all("type").reset_index()
    selected_types = (
        types.sort_values("month")
        .groupby("type")
        .tot_value.sum()
        .sort_values(ascending=False)
        .head(6)
        .index
    )
    tps = []
    ys = []
    xs = []
    for t, df in types.sort_values("month").groupby("type"):
        if t in selected_types:
            tps.append(t)
            xs.append(df.month)
            ys.append(list(df["tot_value"].values))
    return ys, xs, tps


def plot_gastos_por_dia(file: File):
    data = (
        file._df.query('type != "recorrente" and parcelas_totais == 0')
        .groupby("data")
        .agg(qtd=("data", "count"), tot=("valor", "sum"))
    )
    return data.tot, data.index.strftime("%d").astype(int)
