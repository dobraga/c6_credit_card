from logging import DEBUG, INFO, basicConfig, getLogger
from warnings import filterwarnings

import click
# import numpy as np # Moved to services.py
# import pandas as pd # Moved to services.py
from dotenv import load_dotenv
from rich.console import Console # Keep CONSOLE here
# from rich.layout import Layout # Moved to output.py
# from rich.panel import Panel # Moved to output.py
# from rich.console import Group # Moved to output.py
from rich.logging import RichHandler # Keep for setup
# from uniplot.uniplot import plot # Moved to output.py

from c6_credit_card.data.file import File
from c6_credit_card.data.files import Files
from c6_credit_card.services import (
    plot_data_total,
    plot_data_type,
    plot_next_months,
    read_files,
    # plot_gastos_por_dia,
)
from c6_credit_card.output import ( # Import new output functions
    display_terminal_output,
    generate_html_output,
)

filterwarnings(action="ignore", category=UserWarning)


@click.command()
@click.option(
    "--pasta",
    "-p",
    help="Pasta com arquivos das faturas",
    prompt="Pasta com arquivos das faturas",
)
@click.option("--index", "-i", default=None, type=int)
@click.option("--verbose", "-v", is_flag=True, help="Print more output.")
@click.option("--force", "-f", is_flag=True, help="Force extract.")
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(["terminal", "html"], case_sensitive=False),
    default="terminal",
    help="Output format.",
)
def main(pasta, index, verbose, force, output_format):
    """Explore credit card bills from C6 in terminal."""
    if index:
        index = index - 1

    setup(verbose)
    LOG.info(f"Output format selected: {output_format}")
    files = read_files(pasta, force)
    file = files[index]

    LOG.info(f"using {file}")

    # Generate all plot data by calling service functions
    ys_next_months, xs_next_months = plot_next_months(file)
    ys_data_total, xs_data_total = plot_data_total(files)
    ys_data_type, xs_data_type, tps_data_type = plot_data_type(files)
    # plot_gastos_por_dia_data = plot_gastos_por_dia(file) # If needed for output functions

    # The plotting and Rich summary display are now handled by the output functions.
    # Removed direct plot() calls and Rich Panel rendering from here.

    if output_format == "terminal":
        display_terminal_output(
            CONSOLE=CONSOLE,
            file=file,
            files=files,
            ys_next_months=ys_next_months,
            xs_next_months=xs_next_months,
            ys_data_total=ys_data_total,
            xs_data_total=xs_data_total,
            ys_data_type=ys_data_type,
            xs_data_type=xs_data_type,
            tps_data_type=tps_data_type,
            # plot_gastos_por_dia_data=plot_gastos_por_dia_data, # Pass if used
        )
    elif output_format == "html":
        html_content = generate_html_output(
            file=file,
            files=files,
            ys_next_months=ys_next_months,
            xs_next_months=xs_next_months,
            ys_data_total=ys_data_total,
            xs_data_total=xs_data_total,
            ys_data_type=ys_data_type,
            xs_data_type=xs_data_type,
            tps_data_type=tps_data_type,
            # plot_gastos_por_dia_data=plot_gastos_por_dia_data, # Pass if used
        )
        print(html_content)
    else:
        LOG.error(f"Unknown output format: {output_format}")


def setup(verbose):
    load_dotenv()
    level = DEBUG if verbose else INFO
    basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(omit_repeated_times=False)],
    )


# def read_files(pasta, force): # Moved to services.py
#     files = Files(pasta)
#     LOG.info(files)
#     pswd = getenv("password") or input("Senha do arquivo: ")
#     files.process(pswd, force=force)
#     return files


# def plot_data_total(files: Files): # Moved to services.py
#     values: pd.DataFrame = files.summary_all().reset_index().sort_values("month")
#
#     ys = values.tot_value.tolist()
#     xs = values.month.tolist()
#     return ys, xs


# def plot_next_months(file: File): # Moved to services.py
#     recorrentes = file._df.query('type == "recorrente"').valor.sum()
#     parcelas = (
#         file._df.query("parcela > 0 and parcelas_faltantes > 0")
#         .groupby("parcelas_faltantes")["valor"]
#         .sum()
#     )
#
#     parcelas = parcelas.sort_index(ascending=False).cumsum().sort_index()
#
#     max_index = max(parcelas.keys())
#
#     arr = np.full(max_index + 1, np.nan)
#
#     for idx, value in parcelas.items():
#         arr[idx] = value
#
#     parcelas = pd.Series(arr[1:], name="parcelas_faltantes").ffill()
#
#     parcelas_rec = parcelas + recorrentes
#
#     print(f"total parcelas: R${parcelas.sum():,.2f} | recorrente: R${recorrentes:,.2f}")
#     print(
#         pd.DataFrame(
#             {"parcelas": parcelas, "recorrente": recorrentes, "total": parcelas_rec}
#         )
#     )
#
#     ys = parcelas_rec.values.tolist()
#     xs = parcelas_rec.index.tolist()
#     return ys, xs


# def plot_data_type(files: Files): # Moved to services.py
#     types: pd.DataFrame = files.summary_all("type").reset_index()
#     selected_types = (
#         types.sort_values("month")
#         .groupby("type")
#         .tot_value.sum()
#         .sort_values(ascending=False)
#         .head(6)
#         .index
#     )
#     tps = []
#     ys = []
#     xs = []
#     for t, df in types.sort_values("month").groupby("type"):
#         if t in selected_types:
#             tps.append(t)
#             xs.append(df.month)
#             ys.append(list(df["tot_value"].values))
#     return ys, xs, tps


# def plot_gastos_por_dia(file: File): # Moved to services.py
#     data = (
#         file._df.query('type != "recorrente" and parcelas_totais == 0')
#         .groupby("data")
#         .agg(qtd=("data", "count"), tot=("valor", "sum"))
#     )
#     return data.tot, data.index.strftime("%d").astype(int)


LOG = getLogger(__name__)
CONSOLE = Console()


if __name__ == "__main__":
    main()
