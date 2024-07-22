# create page function
from flask import Flask,flash
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from .views import views
def create_page():
    file_path = '10s_intervals.csv'
    data = pd.read_csv(file_path)




    # Convert Time column to datetime
    data['Time'] = pd.to_datetime(data['Time'], errors='coerce')
    date = '2020-12-13'
    data = data[data['Time'].dt.date == pd.to_datetime(date).date()]
    print(data.shape)
    print(data['Total Depth'].min())
    print(data['Total Depth'].max())

    data.replace(-999.25, np.nan, inplace = True)
    app = Flask(__name__)
    dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')
    # Layout of the app

    NUMERICAL_FEATURES_UNITS = {
    'Block Position': 'Feet',
    'Weight on Bit': 'Tons',
    'Hookload': 'Tons',
    'ROP Depth/Hour': 'Feet per hour',
    'MWD Gamma (API)': 'API units',
    'Top Drive RPM': 'RPM',
    'Top Drive Torque (ft-lbs)': 'Foot-pounds',
    'Flow In': 'Gallons per minute',
    'Pump Pressure': 'PSI',
    'SPM Total': 'Strokes per minute',
    'Pit Volume Active': 'Barrels',
    'Pit G/L Active': 'Gas/Liquid ratio',
    'Gas Total - units': 'Units of gas detection',
    'Trip Volume Active': 'Barrels',
    'Trip G/L': 'Gas/Liquid ratio',
    'Return Flow': 'Gallons per minute',
    'RES PS 2MHZ 18IN': 'Ohm-meters',
    'RES PS 400KHZ 18IN': 'Ohm-meters',
    'MWD Inclination': 'Degrees',
    'MWD Azimuth': 'Degrees',
    'H2S 01': 'Parts per million (ppm)',
    'RSS Azimuth': 'Degrees',
    'Total Depth': 'Feet',
    'Bit Diameter': 'Inches',
    'Bit RPM': 'RPM',
    'Depth Hole TVD': 'Feet',
    'Differential Pressure': 'PSI',
    'Downhole Torque': 'Foot-pounds',
    'MUD TEMP': 'Degrees Fahrenheit'
}

    dash_app.layout = html.Div([
    html.H1("Time-Series Dashboard"),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='timeseries-feature-dropdown',
                options=[{'label': col, 'value': col} for col in data.columns if col != 'Time'],
                value='Block Position',
                clearable=False
            ),
            dcc.Graph(id='timeseries-graph')
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            dcc.Graph(id='correlation-heatmap')
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'})
    ]),
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='pairplot-feature1-dropdown',
                options=[{'label': col, 'value': col} for col in data.columns if col != 'Time'],
                value='Block Position',
                clearable=False
            ),
            dcc.Dropdown(
                id='pairplot-feature2-dropdown',
                options=[{'label': col, 'value': col} for col in data.columns if col != 'Time'],
                value='Weight on Bit',
                clearable=False
            ),
            dcc.Graph(id='pairplot-graph')
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            dcc.Graph(id='trajectory-graph')
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'})
    ])
])

    # Callbacks
    @dash_app.callback(
        Output('timeseries-graph', 'figure'),
        Input('timeseries-feature-dropdown', 'value')
    )
    def update_timeseries(feature):
        unit = NUMERICAL_FEATURES_UNITS.get(feature, '')
        yaxis_title = f'{feature} ({unit})'
        fig = px.line(data, x='Time', y=feature, title=f'Time Series of {feature}')
        fig.update_layout(yaxis_title=yaxis_title)
        return fig

    @dash_app.callback(
        Output('correlation-heatmap', 'figure'),
        Input('timeseries-feature-dropdown', 'value')  # Just a dummy input to trigger the update
    )
    def update_heatmap(_):
        corr_matrix = data.corr()
        fig = px.imshow(corr_matrix, text_auto=True, title='Correlation Heatmap')
        return fig

    @dash_app.callback(
        Output('pairplot-graph', 'figure'),
        Input('pairplot-feature1-dropdown', 'value'),
        Input('pairplot-feature2-dropdown', 'value')
    )
    def update_pairplot(feature1, feature2):
        unit1 = NUMERICAL_FEATURES_UNITS.get(feature1, '')
        unit2 = NUMERICAL_FEATURES_UNITS.get(feature2, '')
        xaxis_title = f'{feature1} ({unit1})'
        yaxis_title = f'{feature2} ({unit2})'
        fig = px.scatter(data, x=feature1, y=feature2, title=f'Pair Plot of {feature1} and {feature2}')
        fig.update_layout(xaxis_title=xaxis_title, yaxis_title=yaxis_title)
        return fig

    @dash_app.callback(
        Output('trajectory-graph', 'figure'),
        Input('timeseries-feature-dropdown', 'value')  # Just a dummy input to trigger the update
    )
    def update_trajectory(_):
        if 'MWD Azimuth' in data.columns and 'MWD Inclination' in data.columns and 'Total Depth' in data.columns:
            depth = data['Total Depth'].fillna(method='ffill')
            inclination = np.radians(data['MWD Inclination'].fillna(0))
            azimuth = np.radians(data['MWD Azimuth'].fillna(0))

            x = np.array([0 for _ in range(1000)])
            y = np.array([0 for _ in range(1000)])
            z = np.linspace(9031, 9438, 1000)

            fig = go.Figure(data=[go.Scatter3d(
                x=x, y=y, z=z,
                mode='lines',
                line=dict(color='blue', width=2)
            )])
            fig.update_layout(title='Bit Trajectory', scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Depth',
                zaxis=dict(autorange='reversed')
            ))
            return fig
        return go.Figure()


    app.app_context().push()
    app.secret_key = "1212"
  

    app.register_blueprint(views,url_prefix='/')


    return app