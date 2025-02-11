# -*- coding: utf-8 -*-
"""
Created on Sun Feb  9 17:46:09 2025

@author: win11


"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, callback_context, callback
import dash_ag_grid as dag

def add_header(df_filtered = df):
    
    
    rangeslider_years = df_filtered['year'].unique()
    #to prevent the marks from being 2k, 2k, 2k etc a dict is created for the marks    
    rangeslider_marks = {int(key): str(key) for key in rangeslider_years}

    
    header = dbc.Row([
        
        dbc.Col([html.H1('New York Times bestseller lists, some insights')], className = 'col-sm-12 col-md-4', style={ 'backgroundColor':'white', 'borderRadius':'4px'}),
        dbc.Col([
                    
        dcc.RangeSlider(
            id='selected_range_years',
    min=rangeslider_years.min(),
    max=rangeslider_years.max(),
    step=1,
    marks= rangeslider_marks,
    value=[2011, 2025],
    #minimum = 52 weeks
    pushable=1
),
            
            
            ], className = 'col-sm-12 col-md-8', style={'backgroundColor':'white','paddingTop':'1rem', 'borderTopRightRadius': '4px','borderBottomRightRadius': '4px'})

        
        
    ], id='header', className = 'bg-info', style={'margin':'0rem','marginBottom':'2rem','justifyContent':'space-between','alignItems':'center' })#endrow    
    return header


@callback(
    Output("header", "children"),
    Input("store", "data"),
)
def update(store):
    if store == {}:
        return "Select year on the graph page"
    df_filtered = pd.DataFrame(store)

    return add_header(df_filtered)