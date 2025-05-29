import pandas as pd
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from uniplot.uniplot import plot

from c6_credit_card.data.file import File


def display_terminal_output(
    CONSOLE,
    file: File,
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
    file: File,
    ys_next_months,
    xs_next_months,
    ys_data_total,
    xs_data_total,
    ys_data_type,
    xs_data_type,
    tps_data_type,
):
    """Generates a beautiful HTML representation of the C6 credit card analysis with Plotly charts."""

    # Calculate summary statistics
    total_spending = sum(ys_data_total) if ys_data_total else 0
    current_month_spending = ys_data_total[-1] if ys_data_total else 0
    previous_month_spending = (
        ys_data_total[-2] if len(ys_data_total) > 1 else current_month_spending
    )
    month_change = (
        (
            (current_month_spending - previous_month_spending)
            / previous_month_spending
            * 100
        )
        if previous_month_spending != 0
        else 0
    )

    # Get spending breakdown
    tot_parcelados = file.select(parcelas_faltantes=" > 0", type=" != 'recorrente'")
    tot_parcelados_val = (
        tot_parcelados.data.valor.sum() if not tot_parcelados.data.empty else 0
    )

    tot_avista = file.select(parcelas_faltantes=0, parcela=0, type=" != 'recorrente'")
    tot_avista_val = tot_avista.data.valor.sum() if not tot_avista.data.empty else 0

    tot_fin = file.select(parcela=" > 0", parcelas_faltantes=0, type=" != 'recorrente'")
    tot_fin_val = tot_fin.data.valor.sum() if not tot_fin.data.empty else 0

    total_transactions = len(file._df)

    # Prepare chart data
    next_months_data = {
        "x": xs_next_months if xs_next_months else [],
        "y": ys_next_months if ys_next_months else [],
    }

    monthly_data = {
        "x": [x.strftime("%Y-%m-%d") for x in xs_data_total] if xs_data_total else [],
        "y": ys_data_total if ys_data_total else [],
    }
    if len(xs_data_total) >= 12:
        monthly_data["x"] = monthly_data["x"][-12:]
        monthly_data["y"] = monthly_data["y"][-12:]

    # Prepare categories data
    categories_data = []
    if (
        tps_data_type is not None
        and ys_data_type is not None
        and xs_data_type is not None
    ):
        for i, category_name in enumerate(tps_data_type):
            cat_data = {
                "name": category_name,
                "x": xs_data_type[i].astype(str).tolist(),
                "y": ys_data_type[i],
            }
            if len(xs_data_type[i]) >= 12:
                cat_data["x"] = cat_data["x"][-12:]
                cat_data["y"] = cat_data["y"][-12:]
            categories_data.append(cat_data)

    # Get summary data
    summary_type_df = (
        file.summary("type").data
        if hasattr(file.summary("type"), "data")
        else pd.DataFrame()
    )
    summary_local_df = (
        file.summary("local").top(8).data
        if hasattr(file.summary("local"), "data")
        else pd.DataFrame()
    )
    summary_parcelas_df = (
        file.summary("parcelas_faltantes").data
        if hasattr(file.summary("parcelas_faltantes"), "data")
        else pd.DataFrame()
    )

    # Create category tags mapping
    category_tags = {
        "alimentacao": "tag-alimentacao",
        "transporte": "tag-transporte",
        "lazer": "tag-lazer",
        "saude": "tag-saude",
        "outros": "tag-outros",
        "compras": "tag-outros",
        "recorrente": "tag-outros",
    }

    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>C6 Credit Card Analysis</title>
    <script src="https://cdn.plot.ly/plotly-3.0.1.min.js" charset="utf-8"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .header h1 {{
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }}

        .header h2 {{
            font-size: 1.2rem;
            color: #666;
            font-weight: 400;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
        }}

        .stat-card h3 {{
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #333;
            margin-bottom: 10px;
        }}

        .stat-change {{
            font-size: 0.9rem;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 500;
        }}

        .positive {{ background: #e8f5e8; color: #2d6e2d; }}
        .negative {{ background: #fdeaea; color: #c53030; }}

        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}

        .chart-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .chart-title {{
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #333;
        }}

        .table-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            overflow-x: auto;
        }}

        .section-title {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 30px;
            color: #333;
            text-align: center;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        th {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.8rem;
        }}

        th:first-child {{ border-top-left-radius: 10px; }}
        th:last-child {{ border-top-right-radius: 10px; }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:hover {{
            background: rgba(102, 126, 234, 0.05);
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        .currency {{
            font-weight: 600;
            color: #2d6e2d;
        }}

        .category-tag {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            margin-right: 5px;
        }}

        .tag-alimentacao {{ background: #fef7e0; color: #b45309; }}
        .tag-transporte {{ background: #e0f2fe; color: #0369a1; }}
        .tag-lazer {{ background: #f3e8ff; color: #7c3aed; }}
        .tag-saude {{ background: #ecfdf5; color: #059669; }}
        .tag-outros {{ background: #f3f4f6; color: #374151; }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .animate-in {{
            animation: fadeInUp 0.6s ease-out;
        }}

        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2rem; }}
            .container {{ padding: 15px; }}
            .chart-grid {{ grid-template-columns: 1fr; }}
            .stat-card {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header animate-in">
            <h1>C6 Credit Card Analysis</h1>
            <h2>Relatório para arquivo: {file.file.name if hasattr(file, "file") and hasattr(file.file, "name") else "N/A"}</h2>
        </div>

        <div class="stats-grid animate-in">
            <div class="stat-card">
                <h3>Gasto Total do Mês</h3>
                <div class="stat-value">R$ {current_month_spending:,.2f}</div>
                <span class="stat-change {"positive" if month_change < 0 else "negative"}">{"+" if month_change > 0 else ""}{month_change:.1f}% vs mês anterior</span>
            </div>
            <div class="stat-card">
                <h3>Compras à Vista</h3>
                <div class="stat-value">R$ {tot_avista_val:,.2f}</div>
                <span class="stat-change positive">{len(tot_avista.data) if not tot_avista.data.empty else 0} transações</span>
            </div>
            <div class="stat-card">
                <h3>Compras Parceladas</h3>
                <div class="stat-value">R$ {tot_parcelados_val:,.2f}</div>
                <span class="stat-change negative">{len(tot_parcelados.data) if not tot_parcelados.data.empty else 0} transações</span>
            </div>
            <div class="stat-card">
                <h3>Número de Transações</h3>
                <div class="stat-value">{total_transactions}</div>
                <span class="stat-change positive">Total de compras</span>
            </div>
        </div>

        <div class="chart-grid animate-in">
            {'<div class="chart-container"><div class="chart-title">Gastos Próximos Meses</div><div id="nextMonthsChart"></div></div>' if xs_next_months and ys_next_months else ""}
            {'<div class="chart-container"><div class="chart-title">Gastos por Mês</div><div id="monthlyChart"></div></div>' if xs_data_total and ys_data_total else ""}
        </div>

        {'<div class="chart-container animate-in" style="margin-bottom: 30px;"><div class="chart-title">Gastos das Categorias por Mês</div><div id="categoriesChart"></div></div>' if categories_data else ""}

        <h2 class="section-title animate-in">Resumo por Categoria</h2>
        <div class="table-container animate-in">
            {generate_summary_table(summary_type_df, category_tags)}
        </div>

        <h2 class="section-title animate-in">Top Locais de Compra</h2>
        <div class="table-container animate-in">
            {generate_locations_table(summary_local_df)}
        </div>

        <h2 class="section-title animate-in">Análise de Parcelas</h2>
        <div class="table-container animate-in">
            {generate_installments_table(tot_avista_val, tot_parcelados_val, tot_fin_val, len(tot_avista.data) if not tot_avista.data.empty else 0, len(tot_parcelados.data) if not tot_parcelados.data.empty else 0, len(tot_fin.data) if not tot_fin.data.empty else 0)}
        </div>

        <h2 class="section-title animate-in">Top Gastos por Categoria</h2>
        {generate_top_expenses_by_category(file, summary_type_df)}
    </div>

    <script>
        // Chart data from Python
        const nextMonthsData = {next_months_data};
        const monthlyData = {monthly_data};
        const categoriesData = {categories_data};

        const layout = {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{ family: 'Inter, sans-serif', color: '#333' }},
            margin: {{ t: 20, r: 20, b: 40, l: 60 }},
            xaxis: {{ 
                showgrid: true, 
                gridcolor: 'rgba(0,0,0,0.1)',
                showline: false,
                zeroline: false
            }},
            yaxis: {{ 
                showgrid: true, 
                gridcolor: 'rgba(0,0,0,0.1)',
                showline: false,
                zeroline: false
            }}
        }};

        const layout_date = {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{ family: 'Inter, sans-serif', color: '#333' }},
            margin: {{ t: 20, r: 20, b: 40, l: 60 }},
            xaxis: {{ 
                type: 'date',
                showgrid: true, 
                gridcolor: 'rgba(0,0,0,0.1)',
                showline: false,
                zeroline: false
            }},
            yaxis: {{ 
                showgrid: true, 
                gridcolor: 'rgba(0,0,0,0.1)',
                showline: false,
                zeroline: false
            }}
        }};

        const config = {{
            responsive: true,
            displayModeBar: false
        }};

        // Create charts if data exists
        if (nextMonthsData.x && nextMonthsData.x.length > 0) {{
            const nextMonthsTrace = {{
                x: nextMonthsData.x,
                y: nextMonthsData.y,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Gastos Projetados',
                line: {{
                    color: '#667eea',
                    width: 3,
                    shape: 'spline'
                }},
                marker: {{
                    color: '#764ba2',
                    size: 8
                }}
            }};
            Plotly.newPlot('nextMonthsChart', [nextMonthsTrace], layout, config);
        }}

        if (monthlyData.x && monthlyData.x.length > 0) {{
            const monthlyTrace = {{
                x: monthlyData.x,
                y: monthlyData.y,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Gastos Mensais',
                line: {{
                    color: '#667eea',
                    width: 3,
                    shape: 'spline'
                }},
                marker: {{
                    color: '#764ba2',
                    size: 8
                }}
            }};
            Plotly.newPlot('monthlyChart', [monthlyTrace], layout_date, config);
        }}

        if (categoriesData && categoriesData.length > 0) {{
            const colors = ['#b45309', '#0369a1', '#7c3aed', '#059669', '#374151'];
            const traces = categoriesData.map((category, index) => ({{
                x: category.x,
                y: category.y,
                type: 'scatter',
                mode: 'lines+markers',
                name: category.name,
                line: {{ color: colors[index % colors.length], width: 2 }}
            }}));
            Plotly.newPlot('categoriesChart', traces, layout_date, config);
        }}

        // Add scroll animations
        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }};

        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }}
            }});
        }}, observerOptions);

        document.querySelectorAll('.animate-in').forEach(el => {{
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'all 0.6s ease-out';
            observer.observe(el);
        }});

        // Initial animation
        setTimeout(() => {{
            document.querySelectorAll('.animate-in').forEach((el, index) => {{
                setTimeout(() => {{
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }}, index * 100);
            }});
        }}, 100);
    </script>
</body>
</html>"""

    return html_template


def generate_summary_table(summary_df, category_tags):
    """Generate summary table HTML"""
    if summary_df.empty:
        return "<p>Dados não disponíveis</p>"

    html = """
    <table>
        <thead>
            <tr>
                <th>Categoria</th>
                <th>Quantidade</th>
                <th>Valor Total</th>
                <th>Valor Médio</th>
                <th>% do Total</th>
            </tr>
        </thead>
        <tbody>
    """

    total_value = (
        summary_df["tot_value"].sum() if "tot_value" in summary_df.columns else 1
    )

    for _, row in summary_df.iterrows():
        if row.get("type", "") != "total":
            category = row.get("type", "outros")
            tag_class = category_tags.get(category.lower(), "tag-outros")
            quantity = row.get("qtd", 0)
            tot_value = row.get("tot_value", 0)
            avg_value = tot_value / quantity if quantity > 0 else 0
            percentage = (tot_value / total_value * 100) if total_value > 0 else 0

            html += f"""
            <tr>
                <td><span class="category-tag {tag_class}">{category.title()}</span></td>
                <td>{quantity}</td>
                <td class="currency">R$ {tot_value:,.2f}</td>
                <td class="currency">R$ {avg_value:,.2f}</td>
                <td>{percentage:.1f}%</td>
            </tr>
            """

    html += "</tbody></table>"
    return html


def generate_locations_table(locations_df):
    """Generate locations table HTML"""
    if locations_df.empty:
        return "<p>Dados não disponíveis</p>"

    html = """
    <table>
        <thead>
            <tr>
                <th>Local</th>
                <th>Quantidade</th>
                <th>Valor Total</th>
                <th>Valor Médio</th>
            </tr>
        </thead>
        <tbody>
    """

    for _, row in locations_df.iterrows():
        local = row.get("local", "N/A")
        quantity = row.get("qtd", 0)
        tot_value = row.get("tot_value", 0)
        avg_value = tot_value / quantity if quantity > 0 else 0

        html += f"""
        <tr>
            <td>{local}</td>
            <td>{quantity}</td>
            <td class="currency">R$ {tot_value:,.2f}</td>
            <td class="currency">R$ {avg_value:,.2f}</td>
        </tr>
        """

    html += "</tbody></table>"
    return html


def generate_installments_table(
    avista_val, parcelado_val, finalizado_val, avista_qty, parcelado_qty, finalizado_qty
):
    """Generate installments analysis table"""
    html = """
    <table>
        <thead>
            <tr>
                <th>Tipo</th>
                <th>Quantidade</th>
                <th>Valor Total</th>
                <th>Valor Médio</th>
            </tr>
        </thead>
        <tbody>
    """

    installment_data = [
        ("À Vista", avista_qty, avista_val),
        ("Parcelado (Em andamento)", parcelado_qty, parcelado_val),
        ("Parcelado (Finalizado)", finalizado_qty, finalizado_val),
    ]

    for tipo, quantity, total_value in installment_data:
        avg_value = total_value / quantity if quantity > 0 else 0
        html += f"""
        <tr>
            <td>{tipo}</td>
            <td>{quantity}</td>
            <td class="currency">R$ {total_value:,.2f}</td>
            <td class="currency">R$ {avg_value:,.2f}</td>
        </tr>
        """

    html += "</tbody></table>"
    return html


def generate_top_expenses_by_category(file, summary_df):
    """Generate top expenses by category section"""
    html = ""

    if not summary_df.empty:
        for _, row in summary_df.iterrows():
            tp = row.get("type", "")
            if tp and tp != "total":
                try:
                    tp_data_selected = file.select(type=tp)
                    if not tp_data_selected.data.empty:
                        qtd_compras = tp_data_selected.data.shape[0]
                        tp_value = tp_data_selected.data.valor.sum()

                        html += f"""
                        <div class="table-container animate-in">
                            <h4>Top Gastos {tp.title()}: {qtd_compras} compras - R$ {tp_value:,.2f}</h4>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Descrição</th>
                                        <th>Local</th>
                                        <th>Valor</th>
                                        <th>Data</th>
                                        <th>Parcelas</th>
                                    </tr>
                                </thead>
                                <tbody>
                        """

                        # Get top 10 expenses for this category
                        top_expenses = (
                            tp_data_selected.top(10).data
                            if tp != "others"
                            else tp_data_selected.data
                        )

                        for _, expense_row in top_expenses.head(10).iterrows():
                            desc = expense_row.get("type", "N/A")
                            local = expense_row.get("local", "N/A")
                            valor = expense_row.get("valor", 0)
                            data = expense_row.get("data", "N/A")
                            if data != "N/A":
                                data = data.strftime("%d/%m/%Y")

                            parcela = expense_row.get("parcela", 0)
                            parcelas_faltantes = expense_row.get(
                                "parcelas_faltantes", 0
                            )

                            parcelas_info = (
                                f"{parcela}/{parcela + parcelas_faltantes}"
                                if parcela > 0 or parcelas_faltantes > 0
                                else "À vista"
                            )

                            html += f"""
                            <tr>
                                <td>{desc}</td>
                                <td>{local}</td>
                                <td class="currency">R$ {valor:,.2f}</td>
                                <td>{data}</td>
                                <td>{parcelas_info}</td>
                            </tr>
                            """

                        html += """
                                </tbody>
                            </table>
                        </div>
                        """
                except Exception as e:
                    html += f"<p>Erro ao processar categoria {tp}: {e}</p>"

    return html
