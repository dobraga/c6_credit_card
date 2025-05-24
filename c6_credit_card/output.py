from rich.panel import Panel
from rich.layout import Layout
from rich.console import Group
from uniplot.uniplot import plot
import pandas as pd

# Assuming File and Files classes are defined elsewhere and will be imported if necessary
# from c6_credit_card.data.file import File # Will be needed by type hints and methods
# from c6_credit_card.data.files import Files # Will be needed by type hints and methods

def display_terminal_output(
    CONSOLE,  # Passed from __main__
    file, # Type: File
    files, # Type: Files
    ys_next_months,
    xs_next_months,
    ys_data_total,
    xs_data_total,
    ys_data_type,
    xs_data_type,
    tps_data_type,
):
    """Displays the C6 credit card analysis output in the terminal."""

    CONSOLE.print(f"Displaying output for file: {file.path.name}") # Example usage of CONSOLE

    plot(ys=ys_next_months, xs=xs_next_months, lines=True, title="Gastos próximos meses")
    plot(ys=ys_data_total, xs=xs_data_total, lines=True, title="Gastos por mês")
    plot(
        ys=ys_data_type,
        xs=xs_data_type,
        legend_labels=tps_data_type,
        lines=True,
        title="Gastos das categorias por mês",
    )

    # ys, xs = plot_gastos_por_dia(file) # This was originally in __main__ but plot_gastos_por_dia is in services
    # plot(ys=ys, xs=xs, lines=False, title="Gastos por dia")


    top_panel_layout = Layout() # Renamed from top_panel to avoid conflict with rich.panel.Panel
    summary = file.summary("type")
    top_panel_layout.split_row(
        summary.print("Total por tipo :warning:"),
        file.summary("local").top(8).print("Top locais"),
        file.summary("local", add_total=False)
        .sort(by=["qtd", "tot_value"], ascending=False)
        .top(8)
        .print("Top # locais"),
        file.summary("parcelas_faltantes").print("Total por parcelas"),
    )
    CONSOLE.print(Panel(Group(top_panel_layout), title="Summary"), height=20)

    tot_avista = file.select(parcelas_faltantes=0, parcela=0, type=" != 'recorrente'")
    tot_avista_val = tot_avista.data.valor.sum()

    tot_parcelados = file.select(parcelas_faltantes=" > 0", type=" != 'recorrente'")
    tot_parcelados_val = tot_parcelados.data.valor.sum()

    tot_fin = file.select(parcela=" > 0", parcelas_faltantes=0, type=" != 'recorrente'")
    tot_fin_val = tot_fin.data.valor.sum()

    summaries_prints = []
    # Ensure file.summary("type").data exists and is a DataFrame
    if hasattr(file.summary("type"), 'data') and isinstance(file.summary("type").data, pd.DataFrame):
        for tp in file.summary("type").data.query('type != "total"').type:
            tp_data = file.select(type=tp)
            qtd_compras = tp_data.data.shape[0]
            tp_value = tp_data.data.valor.sum()
            if tp != "others":
                tp_data = tp_data.top(10)
            summaries_prints.append(
                tp_data.print(f"Top gastos {tp}: {qtd_compras} compras R${tp_value:,.2f}")
            )
    else:
        CONSOLE.print("[bold red]Warning: Could not generate type summaries because file.summary('type').data is not as expected.[/bold red]")


    bottom_panel_group = [
        tot_parcelados.top(10).print(
            f"Compras parceladas: R${tot_parcelados_val:,.2f}"
        ),
        tot_avista.top(10).print(f"Compras à vista: R${tot_avista_val:,.2f}"),
        tot_fin.top(10).print(f"Compras finalizadas: R${tot_fin_val:,.2f}"),
        *summaries_prints,
    ]
    CONSOLE.print(Panel(Group(*bottom_panel_group), title="Top gastos"))


def generate_html_output(
    file, # Type: File
    files, # Type: Files
    ys_next_months,
    xs_next_months,
    ys_data_total,
    xs_data_total,
    ys_data_type,
    xs_data_type,
    tps_data_type,
):
    """Generates a basic HTML representation of the C6 credit card analysis."""
    html_parts = []

    html_parts.append("<h1>C6 Credit Card Analysis</h1>")
    html_parts.append(f"<h2>Report for file: {file.path.name}</h2>")

    # Plots - placeholder text
    html_parts.append("<h3>Plots</h3>")
    html_parts.append("<p><b>Gastos próximos meses:</b> (Plot data not rendered in HTML)</p>")
    # Simple table for next months
    df_next_months = pd.DataFrame({'Month': xs_next_months, 'Value': ys_next_months})
    html_parts.append("<h4>Gastos próximos meses (Data)</h4>")
    html_parts.append(df_next_months.to_html(index=False, border=1))


    html_parts.append("<p><b>Gastos por mês:</b> (Plot data not rendered in HTML)</p>")
    df_data_total = pd.DataFrame({'Month': xs_data_total, 'Value': ys_data_total})
    html_parts.append("<h4>Gastos por mês (Data)</h4>")
    html_parts.append(df_data_total.to_html(index=False, border=1))

    html_parts.append("<p><b>Gastos das categorias por mês:</b> (Plot data not rendered in HTML)</p>")
    # For multi-series plot, a more complex table or multiple tables
    html_parts.append("<h4>Gastos das categorias por mês (Data)</h4>")
    # This is a bit tricky as ys_data_type is a list of lists.
    # We'll create a table for each category for simplicity.
    if tps_data_type and ys_data_type and xs_data_type and len(tps_data_type) == len(ys_data_type) and len(xs_data_type) > 0:
        for i, cat_name in enumerate(tps_data_type):
            if i < len(ys_data_type) and i < len(xs_data_type): # ensure indices are valid
                df_cat = pd.DataFrame({'Month': xs_data_type[i], cat_name: ys_data_type[i]})
                html_parts.append(f"<h5>{cat_name}</h5>")
                html_parts.append(df_cat.to_html(index=False, border=1))
            else:
                html_parts.append(f"<p>Error: Data mismatch for category {cat_name}</p>")
    else:
        html_parts.append("<p>No category data or data mismatch for plotting.</p>")


    # Summaries
    html_parts.append("<h3>Summary</h3>")

    # Top Panel content
    # Replicating rich panel structure is complex. We'll use underlying data.
    # file.summary returns a Summary object which has a .data (pandas DF) and a .print method
    # We will try to access .data for HTML conversion.

    summary_type_df = file.summary("type").data
    html_parts.append("<h4>Total por tipo</h4>")
    html_parts.append(summary_type_df.to_html(index=False, border=1))

    summary_local_df = file.summary("local").top(8).data
    html_parts.append("<h4>Top locais</h4>")
    html_parts.append(summary_local_df.to_html(index=False, border=1))

    summary_local_qtd_df = file.summary("local", add_total=False).sort(by=["qtd", "tot_value"], ascending=False).top(8).data
    html_parts.append("<h4>Top # locais (by quantity and value)</h4>")
    html_parts.append(summary_local_qtd_df.to_html(index=False, border=1))
    
    summary_parcelas_df = file.summary("parcelas_faltantes").data
    html_parts.append("<h4>Total por parcelas</h4>")
    html_parts.append(summary_parcelas_df.to_html(index=False, border=1))

    # Bottom Panel content
    html_parts.append("<h3>Top Gastos</h3>")

    tot_avista = file.select(parcelas_faltantes=0, parcela=0, type=" != 'recorrente'")
    html_parts.append(f"<h4>Compras parceladas: R${file.select(parcelas_faltantes=' > 0', type=' != recorrente').data.valor.sum():,.2f}</h4>")
    html_parts.append(tot_avista.top(10).data.to_html(index=False, border=1))

    tot_parcelados = file.select(parcelas_faltantes=" > 0", type=" != 'recorrente'")
    html_parts.append(f"<h4>Compras à vista: R${file.select(parcelas_faltantes=0, parcela=0, type=' != recorrente').data.valor.sum():,.2f}</h4>")
    html_parts.append(tot_parcelados.top(10).data.to_html(index=False, border=1))
    
    tot_fin = file.select(parcela=" > 0", parcelas_faltantes=0, type=" != 'recorrente'")
    html_parts.append(f"<h4>Compras finalizadas: R${tot_fin.data.valor.sum():,.2f}</h4>")
    html_parts.append(tot_fin.top(10).data.to_html(index=False, border=1))

    if hasattr(file.summary("type"), 'data') and isinstance(file.summary("type").data, pd.DataFrame):
        for tp in file.summary("type").data.query('type != "total"').type:
            tp_data_selected = file.select(type=tp)
            qtd_compras = tp_data_selected.data.shape[0]
            tp_value = tp_data_selected.data.valor.sum()
            html_parts.append(f"<h4>Top gastos {tp}: {qtd_compras} compras R${tp_value:,.2f}</h4>")
            if tp != "others":
                tp_data_selected = tp_data_selected.top(10)
            html_parts.append(tp_data_selected.data.to_html(index=False, border=1))
    
    return "\n".join(html_parts)
