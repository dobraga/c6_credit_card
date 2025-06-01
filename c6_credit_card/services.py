from logging import getLogger
from os import getenv

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

    parcelas = pd.Series(arr[1:], name="parcelas_faltantes").ffill().fillna(0)

    parcelas_rec = parcelas + recorrentes

    # print(f"total parcelas: R${parcelas.sum():,.2f} | recorrente: R${recorrentes:,.2f}")
    # print(
    #     pd.DataFrame(
    #         {"parcelas": parcelas, "recorrente": recorrentes, "total": parcelas_rec}
    #     )
    # )

    ys = parcelas_rec.values.tolist()
    xs = parcelas_rec.index.tolist()
    return ys, xs


def plot_data_type(files):  # files: Files
    """
    Prepares data for plotting spending by category over time.
    It identifies the top 5 spending categories and groups the rest into an 'outros' category.
    """
    types: pd.DataFrame = files.summary_all("type").reset_index()

    # Calculate total spending per type to identify top categories
    type_sums = types.groupby("type").tot_value.sum().sort_values(ascending=False)

    # Determine the number of top categories to display individually
    # We'll keep 5 top categories and group the rest into 'outros'
    top_n = 5
    selected_types_list = type_sums.head(top_n).index.tolist()

    tps = []
    ys = []
    xs = []

    # Process each of the selected top categories
    for t in selected_types_list:
        df_t = types[types["type"] == t].sort_values(by="month")
        tps.append(t)
        xs.append(df_t.month)
        ys.append(list(df_t["tot_value"].values))

    # Process the 'outros' (remainder) category
    df_others = types[~types["type"].isin(selected_types_list)]
    if not df_others.empty:
        # Group remaining types by month and sum their values
        df_others_monthly_sum = (
            df_others.groupby("month")["tot_value"].sum().reset_index()
        )

        # Ensure all months are present for 'outros' to align with other categories
        # Get all unique months from the original 'types' DataFrame to ensure consistent x-axis
        all_months = types["month"].unique()
        df_others_monthly_sum = (
            df_others_monthly_sum.set_index("month")
            .reindex(all_months, fill_value=0)
            .reset_index()
        )
        df_others_monthly_sum = df_others_monthly_sum.sort_values(by="month")

        tps.append("outros")
        xs.append(df_others_monthly_sum.month)
        ys.append(list(df_others_monthly_sum["tot_value"].values))

    return ys, xs, tps


def plot_gastos_por_dia(file: File):
    data = (
        file._df.query('type != "recorrente" and parcelas_totais == 0')
        .groupby("data")
        .agg(qtd=("data", "count"), tot=("valor", "sum"))
    )
    return data.tot, data.index.strftime("%d").astype(int)
