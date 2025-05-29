import pandas as pd
import plotly.express as px
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from uniplot.uniplot import plot

from c6_credit_card.data.file import File
from c6_credit_card.data.files import Files


def display_terminal_output(
    CONSOLE,
    file: File,
    files: Files,
    ys_next_months,
    xs_next_months,
    ys_data_total,
    xs_data_total,
    ys_data_type,
    xs_data_type,
    tps_data_type,
):
    """Displays the C6 credit card analysis output in the terminal."""

    CONSOLE.print(f"Displaying output for file: {file.file.name}")

    plot(
        ys=ys_next_months, xs=xs_next_months, lines=True, title="Gastos próximos meses"
    )
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

    top_panel_layout = (
        Layout()
    )  # Renamed from top_panel to avoid conflict with rich.panel.Panel
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
    if hasattr(file.summary("type"), "data") and isinstance(
        file.summary("type").data, pd.DataFrame
    ):
        for tp in file.summary("type").data.query('type != "total"').type:
            tp_data = file.select(type=tp)
            qtd_compras = tp_data.data.shape[0]
            tp_value = tp_data.data.valor.sum()
            if tp != "others":
                tp_data = tp_data.top(10)
            summaries_prints.append(
                tp_data.print(
                    f"Top gastos {tp}: {qtd_compras} compras R${tp_value:,.2f}"
                )
            )
    else:
        CONSOLE.print(
            "[bold red]Warning: Could not generate type summaries because file.summary('type').data is not as expected.[/bold red]"
        )

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
    file,  # Type: File
    files,  # Type: Files
    ys_next_months,
    xs_next_months,
    ys_data_total,
    xs_data_total,
    ys_data_type,
    xs_data_type,
    tps_data_type,
):
    """Generates an HTML representation of the C6 credit card analysis with Plotly charts."""
    html_parts = []

    html_parts.append("<h1>C6 Credit Card Analysis</h1>")
    html_parts.append(f"<h2>Report for file: {file.file.name}</h2>")
    html_parts.append("<h3>Plots</h3>")

    # Plot 1: Gastos próximos meses
    if xs_next_months and ys_next_months:
        df_next_months = pd.DataFrame(
            {"Mês": xs_next_months, "Valor (R$)": ys_next_months}
        )
        fig_next_months = px.line(
            df_next_months, x="Mês", y="Valor (R$)", title="Gastos Próximos Meses"
        )
        html_parts.append(
            fig_next_months.to_html(full_html=False, include_plotlyjs="cdn")
        )
    else:
        html_parts.append("<p><b>Gastos próximos meses:</b> No data available.</p>")

    # Plot 2: Gastos por mês
    if xs_data_total and ys_data_total:
        df_data_total = pd.DataFrame(
            {"Mês": xs_data_total, "Valor (R$)": ys_data_total}
        )
        fig_data_total = px.line(
            df_data_total, x="Mês", y="Valor (R$)", title="Gastos por Mês"
        )
        html_parts.append(
            fig_data_total.to_html(full_html=False, include_plotlyjs="cdn")
        )
    else:
        html_parts.append("<p><b>Gastos por mês:</b> No data available.</p>")

    # Plot 3: Gastos das categorias por mês
    if tps_data_type and ys_data_type and xs_data_type:
        try:
            # Create a common index of all unique months, sorted
            all_months_set = set()
            for month_list in xs_data_type:
                if month_list:  # Ensure month_list is not empty
                    all_months_set.update(month_list)

            if all_months_set:  # Proceed if there are any months
                all_months_sorted = sorted(list(all_months_set))
                plot_data_type_df = pd.DataFrame(index=all_months_sorted)
                plot_data_type_df.index.name = "Mês"

                for i, category_name in enumerate(tps_data_type):
                    if (
                        i < len(ys_data_type)
                        and i < len(xs_data_type)
                        and xs_data_type[i]
                        and ys_data_type[i]
                    ):
                        # Create a temporary series for the current category
                        s = pd.Series(
                            ys_data_type[i], index=xs_data_type[i], name=category_name
                        )
                        # Map to the common index; this aligns data and introduces NaNs where a category doesn't have data for a month
                        plot_data_type_df[category_name] = plot_data_type_df.index.map(
                            s
                        )

                # Fill NaNs - if a category doesn't exist for a month, it will be 0 after ffill/bfill then fillna(0)
                # Or, decide on a different strategy like interpolate or leave as NaN for Plotly to handle
                plot_data_type_df = (
                    plot_data_type_df.ffill().bfill().fillna(0)
                )  # Fill remaining NaNs with 0

                if not plot_data_type_df.empty:
                    plot_data_type_df_melted = plot_data_type_df.reset_index().melt(
                        id_vars="Mês", var_name="Category", value_name="Valor (R$)"
                    )
                    fig_types = px.line(
                        plot_data_type_df_melted,
                        x="Mês",
                        y="Valor (R$)",
                        color="Category",
                        title="Gastos das Categorias por Mês",
                    )
                    html_parts.append(
                        fig_types.to_html(full_html=False, include_plotlyjs="cdn")
                    )
                else:
                    html_parts.append(
                        "<p><b>Gastos das categorias por mês:</b> Processed data frame is empty.</p>"
                    )
            else:
                html_parts.append(
                    "<p><b>Gastos das categorias por mês:</b> No month data available for categories.</p>"
                )
        except Exception as e:
            html_parts.append(
                f"<p><b>Gastos das categorias por mês:</b> Error generating plot: {e}</p>"
            )
            # Log the error for debugging if a logger is available
    else:
        html_parts.append(
            "<p><b>Gastos das categorias por mês:</b> No data available.</p>"
        )

    # Summaries (remain as HTML tables)
    html_parts.append("<h3>Summary</h3>")
    summary_type_df = file.summary("type").data
    html_parts.append("<h4>Total por tipo</h4>")
    html_parts.append(summary_type_df.to_html(index=False, border=1))

    summary_local_df = file.summary("local").top(8).data
    html_parts.append("<h4>Top locais</h4>")
    html_parts.append(summary_local_df.to_html(index=False, border=1))

    summary_local_qtd_df = (
        file.summary("local", add_total=False)
        .sort(by=["qtd", "tot_value"], ascending=False)
        .top(8)
        .data
    )
    html_parts.append("<h4>Top # locais (by quantity and value)</h4>")
    html_parts.append(summary_local_qtd_df.to_html(index=False, border=1))

    summary_parcelas_df = file.summary("parcelas_faltantes").data
    html_parts.append("<h4>Total por parcelas</h4>")
    html_parts.append(summary_parcelas_df.to_html(index=False, border=1))

    # Bottom Panel content (remain as HTML tables)
    html_parts.append("<h3>Top Gastos</h3>")

    tot_parcelados = file.select(parcelas_faltantes=" > 0", type=" != 'recorrente'")
    tot_parcelados_val = tot_parcelados.data.valor.sum()
    html_parts.append(f"<h4>Compras parceladas: R${tot_parcelados_val:,.2f}</h4>")

    tot_avista = file.select(parcelas_faltantes=0, parcela=0, type=" != 'recorrente'")
    tot_avista_val = tot_avista.data.valor.sum()
    html_parts.append(tot_avista.top(10).data.to_html(index=False, border=1))
    html_parts.append(f"<h4>Compras à vista: R${tot_avista_val:,.2f}</h4>")
    html_parts.append(tot_parcelados.top(10).data.to_html(index=False, border=1))

    tot_fin = file.select(parcela=" > 0", parcelas_faltantes=0, type=" != 'recorrente'")
    html_parts.append(
        f"<h4>Compras finalizadas: R${tot_fin.data.valor.sum():,.2f}</h4>"
    )
    html_parts.append(tot_fin.top(10).data.to_html(index=False, border=1))

    if hasattr(file.summary("type"), "data") and isinstance(
        file.summary("type").data, pd.DataFrame
    ):
        for tp in file.summary("type").data.query('type != "total"').type:
            tp_data_selected = file.select(type=tp)
            qtd_compras = tp_data_selected.data.shape[0]
            tp_value = tp_data_selected.data.valor.sum()
            html_parts.append(
                f"<h4>Top gastos {tp}: {qtd_compras} compras R${tp_value:,.2f}</h4>"
            )
            if tp != "others":
                tp_data_selected = tp_data_selected.top(10)
            html_parts.append(tp_data_selected.data.to_html(index=False, border=1))

    return "\n".join(html_parts)
