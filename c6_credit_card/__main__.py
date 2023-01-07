from logging import basicConfig, getLogger, INFO, DEBUG
from rich.console import Console, Group
from rich.logging import RichHandler
from uniplot.uniplot import plot
from rich.layout import Layout
from dotenv import load_dotenv
from rich.panel import Panel
from os import getenv
import pandas as pd
import click


from data.files import Files


@click.command()
@click.option('--pasta', '-p', help='Pasta com arquivos das faturas',
              prompt='Pasta com arquivos das faturas')
@click.option('--index', '-i', default=None, type=int)
@click.option('--verbose', '-v', is_flag=True, help="Print more output.")
@click.option('--force', '-f', is_flag=True, help="Force extract.")
def main(pasta, index, verbose, force):
    """Explore credit card bills from C6 in terminal."""
    load_dotenv()
    level = DEBUG if verbose else INFO
    basicConfig(
        level=level, format="%(message)s", datefmt="[%X]",
        handlers=[RichHandler(omit_repeated_times=False)]
    )

    if index:
        index = index - 1

    files = Files(pasta)
    LOG.info(files)
    pswd = getenv('password') or input('Senha do arquivo: ')
    files.process(pswd, force=force)

    types: pd.DataFrame = files.summary_all('type').reset_index()
    tps = []
    ys = []
    for t, df in types.sort_values('month').groupby('type'):
        tps.append(t)
        ys.append(list(df['tot_value'].values))

    plot(ys=ys, legend_labels=tps, lines=True,
         title='Gastos das categorias por mês')

    LOG.info(f'using {files[index]}')

    top_panel = Layout()
    summary = files[index].summary('type')
    top_panel.split_row(
        summary.print('Total por tipo :warning:'),
        files[index].summary('local').top(8).print('Top locais'),
        files[index].summary('parcelas_faltantes').print('Total por parcelas'),
    )
    CONSOLE.print(Panel(Group(top_panel), title='Summary'))

    bottom_panel = Panel(Group(
        files[index].select(parcelas_faltantes=' > 0').print(
            'Top compras parceladas'),
        files[index].select(
            parcelas_faltantes=0, type=" != 'recorrente'").print(
            'Top compras finalizadas'),

        *[files[index].select(type=tp).print(f'Top gastos {tp}') for tp in summary.data.query('type != "total"').type]

    ), title='Top gastos')
    CONSOLE.print(bottom_panel)


LOG = getLogger(__name__)
CONSOLE = Console()


if __name__ == '__main__':
    main()
