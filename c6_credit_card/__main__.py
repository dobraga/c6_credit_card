from logging import DEBUG, INFO, basicConfig, getLogger
from os import getenv
from warnings import filterwarnings

import click
import pandas as pd
from dotenv import load_dotenv
from rich.console import Console, Group
from rich.layout import Layout
from rich.logging import RichHandler
from rich.panel import Panel
from uniplot.uniplot import plot

from data.files import Files

filterwarnings(action="ignore", category=UserWarning)


def setup(verbose):
    load_dotenv()
    level = DEBUG if verbose else INFO
    basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(omit_repeated_times=False)],
    )


def read_files(pasta, force):
    files = Files(pasta)
    LOG.info(files)
    pswd = getenv("password") or input("Senha do arquivo: ")
    files.process(pswd, force=force)
    return files


def plot_data(files):
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
    for t, df in types.sort_values("month").groupby("type"):
        if t in selected_types:
            tps.append(t)
            ys.append(list(df["tot_value"].values))
    return ys, tps


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
def main(pasta, index, verbose, force):
    """Explore credit card bills from C6 in terminal."""
    if index:
        index = index - 1

    setup(verbose)
    files = read_files(pasta, force)
    file = files[index]

    LOG.info(f"using {file}")

    ys, tps = plot_data(files)
    plot(ys=ys, legend_labels=tps, lines=True, title="Gastos das categorias por mês")

    top_panel = Layout()
    summary = file.summary("type")
    top_panel.split_row(
        summary.print("Total por tipo :warning:"),
        file.summary("local").top(8).print("Top locais"),
        file.summary("local", add_total=False)
        .sort(by=["qtd", "tot_value"], ascending=False)
        .top(8)
        .print("Top # locais"),
        file.summary("parcelas_faltantes").print("Total por parcelas"),
    )
    CONSOLE.print(Panel(Group(top_panel), title="Summary"), height=20)

    tot_avista = file.select(parcelas_faltantes=0, parcela=0)
    tot_avista_val = tot_avista.data.valor.sum()

    tot_parcelados = file.select(parcelas_faltantes=" > 0")
    tot_parcelados_val = tot_parcelados.data.valor.sum()

    tot_fin = file.select(parcela=" > 0", parcelas_faltantes=0, type=" != 'recorrente'")
    tot_fin_val = tot_fin.data.valor.sum()

    summaries = []
    for tp in summary.data.query('type != "total"').type:
        tp_data = file.select(type=tp)
        tp_value = tp_data.data.valor.sum()
        summaries.append(tp_data.top(10).print(f"Top gastos {tp}: R${tp_value:,.2f}"))

    bottom_panel = Panel(
        Group(
            tot_parcelados.top(10).print(
                f"Compras parceladas: R${tot_parcelados_val:,.2f}"
            ),
            tot_avista.top(10).print(f"Compras à vista: R${tot_avista_val:,.2f}"),
            tot_fin.top(10).print(f"Compras finalizadas: R${tot_fin_val:,.2f}"),
            *summaries,
        ),
        title="Top gastos",
    )
    CONSOLE.print(bottom_panel)


LOG = getLogger(__name__)
CONSOLE = Console()


if __name__ == "__main__":
    main()
