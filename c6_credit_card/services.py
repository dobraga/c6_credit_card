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


def plot_next_months(
    files: Files, file: File, past_months: int = 3, future_months: int = 6
):
    """
    Prepares data for plotting spending for past and future months.

    :param files: A Files object containing all processed credit card bills.
    :param file: The latest File object, used for calculating future installments.
    :param past_months: The number of past months to include in the plot.
    :param future_months: The number of future months to project.
    :return: A tuple containing lists of y-values (spending) and x-values (months).
    """
    # --- Past Months Data ---
    # Get historical spending data from all files
    all_months_data = files.summary_all().reset_index().sort_values("month")
    last_month = all_months_data["month"].max()

    # Filter for the desired number of past months
    past_data = all_months_data[
        all_months_data["month"]
        <= pd.to_datetime(last_month).to_period("M").to_timestamp()
    ].tail(past_months)

    # --- Future Months Data ---
    # Calculate recurring costs and installments from the latest bill
    recorrentes = file._df.query('type == "recorrente"').valor.sum()
    parcelas = (
        file._df.query("parcela > 0 and parcelas_faltantes > 0")
        .groupby("parcelas_faltantes")["valor"]
        .sum()
    )
    parcelas = parcelas.sort_index(ascending=False).cumsum().sort_index()

    # Backfill to get a dense series of future cumulative debt
    if not parcelas.empty:
        full_index = np.arange(1, parcelas.index.max() + 1)
        parcelas = parcelas.reindex(full_index).bfill()

    # Calculate future values for each month
    future_values = []
    for i in range(1, future_months + 1):
        installment_value = parcelas.get(i, 0)
        future_values.append(installment_value + recorrentes)

    # Create a date-indexed series for future data
    future_dates = pd.date_range(
        start=last_month + pd.DateOffset(months=1),
        periods=future_months,
        freq="MS",
    )
    future_data = pd.Series(future_values, index=future_dates)

    # --- Combine Data ---
    # Format past data for concatenation
    past_df = past_data.rename(columns={"month": "date", "tot_value": "value"})
    past_df = past_df.set_index("date")["value"]

    # Combine past and future data into a single series
    combined_data = pd.concat([past_df, future_data])

    ys = combined_data.values.tolist()
    xs = combined_data.index.tolist()

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
