import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from flask import Flask

# Sample DataFrame, replace this with your data loading logic
df = pd.read_csv('cross_hotel_bookings.csv')

# Filter and clean data
df = df.dropna(subset=['Destination Hotel'])

df_a = df[df['Source Hotel'] != df['Destination Hotel']]
    
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Hotel Direct - Cross-Utilization Sankey Chart"),
            dcc.Dropdown(
                id='hotel-dropdown',
                options=[{'label': hotel, 'value': hotel} for hotel in sorted(df['Source Hotel'].dropna().astype(str).unique())],
                value=df['Source Hotel'].iloc[0],
                clearable=False
            ),
            dcc.Graph(id='sankey-graph'),
            # Adding style properties to the DataTable component
            dash_table.DataTable(
                id='data-table', 
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                style_table={'maxHeight': '50ex', 'overflowY': 'scroll', 'width': '100%', 'minWidth': '100%'},
            )
        ])
    ])
], fluid=True)


@app.callback(
    [Output('sankey-graph', 'figure'), Output('data-table', 'data')],
    [Input('hotel-dropdown', 'value')]
)
def update_graph(selected_hotel):
    # Filter for selected hotel as source and destination
    
    source_to_dest = df_a[df_a['Source Hotel'] == selected_hotel]
    dest_to_source = df_a[df_a['Destination Hotel'] == selected_hotel]
    
    # Create unique labels, with selected hotel at the beginning
    labels = [selected_hotel] + list(set(source_to_dest['Destination Hotel']) | set(dest_to_source['Source Hotel']))

   # Group by and sum for source_to_dest
    source_to_dest_grouped = source_to_dest.groupby(['Source Hotel', 'Destination Hotel']).agg({'Distinct count of confirmationnumber': 'sum'}).reset_index()

    # Group by and sum for dest_to_source
    dest_to_source_grouped = dest_to_source.groupby(['Source Hotel', 'Destination Hotel']).agg({'Distinct count of confirmationnumber': 'sum'}).reset_index()

    # Now, create sources, targets, and values using the grouped data
    source_indices = [0] * len(source_to_dest_grouped) + [labels.index(src) for src in dest_to_source_grouped['Source Hotel']]
    target_indices = [labels.index(tgt) for tgt in source_to_dest_grouped['Destination Hotel']] + [0] * len(dest_to_source_grouped)
    values = list(source_to_dest_grouped['Distinct count of confirmationnumber']) + list(dest_to_source_grouped['Distinct count of confirmationnumber'])

    # Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=10,
            thickness=20,
            line=dict(color="black", width=0.8),
            label=labels
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values
        )
    )])

    fig.update_layout(title_text=f"Combined Flow for {selected_hotel}", font_size=10)
    return fig, df[df['Source Hotel'] == selected_hotel].to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)
