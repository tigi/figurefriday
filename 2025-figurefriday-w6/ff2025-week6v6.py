# -*- coding: utf-8 -*-
"""
Created on Sat Feb  8 07:47:20 2025

@author: win11
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, callback_context, callback, dash_table
import dash_ag_grid as dag
from data.data_functions import prepare_df_base #data etl

df = prepare_df_base()



def header(df):
    
    
    rangeslider_years = df['year'].unique()
    #to prevent the marks from being 2k, 2k, 2k etc a dict is created for the marks    
    rangeslider_marks = {int(key): str(key) for key in rangeslider_years}

    
    header = dbc.Row([
        
        dbc.Col([html.H1('New York Times,'),
                 html.H3(' bestseller lists (2011-2025)')
                 ], className = 'col-sm-12 col-md-4', style={'textAlign':'center', 'color':'white'}),
        
        dbc.Col([
                    
        dcc.RangeSlider(
            id='selected_range_years',
            min=rangeslider_years.min(),
            max=rangeslider_years.max(),
            step=1,
            marks= rangeslider_marks,
            value=[2011, 2025],
            pushable=1
            ),
            
            
            ], className = 'col-sm-12 col-md-8', style={'backgroundColor':'white','paddingTop':'1rem', 'borderTopRightRadius': '4px','borderBottomRightRadius': '4px'})

        
        
    ], className = 'bg-info', style={'margin':'0rem','marginBottom':'2rem','justifyContent':'space-between','alignItems':'center' })#endrow    
    return header


  

    
app = dash.Dash(__name__,use_pages=True, external_stylesheets=[dbc.themes.SANDSTONE, dbc.icons.FONT_AWESOME]) 




app.layout = dbc.Container([
    #the complete df is stored in store_df nd is not changed, only used
    dcc.Store( id="store_df", data={}),
    header(df),
    html.Div(id='rangeslidervalues', style={'display': 'none'}), #if I remove this one, the whole callback is not triggered, why?
    dash.page_container,

    
    ], fluid=True, className = 'bg-primary')




#on start add processed data to store_df (browser memory)
@callback(Output('store_df', 'data'), 
          Output('rangeslidervalues', 'children'),          
          Input('selected_range_years', 'value'))
def update_stores(value):
   # print(value)
    if not value:
        return df.to_dict('records'),f" range: {str(value[0])} - {str(value[1])}"
    dff = df[df['year'].between(value[0], value[1]-1)]
    return dff.to_dict('records'), f" range: {str(value[0])} - {str(value[1])}"






app.run_server(debug=True) 