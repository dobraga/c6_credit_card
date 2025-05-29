from logging import DEBUG, INFO, basicConfig, getLogger
from pathlib import Path
from warnings import filterwarnings

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

from c6_credit_card.output import display_terminal_output, generate_html_output
from c6_credit_card.services import (
    plot_data_total,
    plot_data_type,
    plot_next_months,
    read_files,
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
            CONSOLE=Console(),
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
        Path("report.html").write_text(html_content)
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


LOG = getLogger(__name__)


if __name__ == "__main__":
    main()
