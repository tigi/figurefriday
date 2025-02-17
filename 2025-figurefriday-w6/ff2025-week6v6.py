# -*- coding: utf-8 -*-
"""
Created on Sat Feb  8 07:47:20 2025

@author: win11
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, callback_context, callback, dash_table,Patch, clientside_callback
import vizro

from data.data_functions import prepare_df_base #data etl

df = prepare_df_base()


# vizro_bootstrap = "https://cdn.jsdelivr.net/gh/mckinsey/vizro@main/vizro-core/src/vizro/static/css/vizro-bootstrap.min.css?v=2"

from dash_bootstrap_templates import load_figure_template
load_figure_template(["vizro", "vizro_dark"])



pio.templates["vizro_dark"].layout.paper_bgcolor = "black"
pio.templates["vizro_dark"].layout.plot_bgcolor = "#333333"
pio.templates["vizro_dark"].layout.font.color = "white"

color_mode_switch =  html.Span(
    [
        dbc.Label(className="fa fa-moon", html_for="color-mode-switch"),
        dbc.Switch( id="color-mode-switch", value=False, className="d-inline-block ms-1", persistence=True),
        dbc.Label(className="fa fa-sun", html_for="color-mode-switch"),
    ]
)



def header(df):
    
    
    rangeslider_years = df['year'].unique()
    #to prevent the marks from being 2k, 2k, 2k etc a dict is created for the marks    
    rangeslider_marks = {int(key): str(key) for key in rangeslider_years}
    #get min and max years for rangeslider
    min = rangeslider_years.min().item()
    max=rangeslider_years.max().item()
    
    header = dbc.Row([
        
        #TITLE
        dbc.Col([html.H1('New York Times,'),
                 html.H3(' bestseller lists (2011-2025)'),
                 html.H4('print & e-books fiction'),
                 ], className = 'col-sm-12 col-md-4', style={'textAlign':'center', 'color':'white'}),
               

        #RANGESLIDER
        dbc.Col([
                    
        dcc.RangeSlider(
            id='selected_range_years',
            #min=rangeslider_years.min(),
            #max=rangeslider_years.max(),
            step=1,
            marks= rangeslider_marks,
            value=[min, max],
            pushable=1,
            
            )
            
            
            ], className = 'col-sm-11 col-md-6', style={'paddingTop':'1rem', 'borderTopRightRadius': '4px','borderBottomRightRadius': '4px'}),
       
        #REFRESH RANGESLIDER BUTTON
        dbc.Col([dbc.Button(
            html.Img(src='assets/images/noun-reset-5884629-FFFFFF.png',style={'maxWidth':'30px'}), id="refresh-button", n_clicks=0
        )], className = 'col-sm-11 col-md-1'),
        #INFO BUTTON
        #LIGHT/DARKMODE BUTTON
        dbc.Col([
            # Create components for the dashboard
        color_mode_switch
        ])
        
        
    ], className = '', style={'margin':'0rem','marginBottom':'2rem','justifyContent':'space-between','alignItems':'center' })#endrow    
    return header


  

    
app = dash.Dash(__name__,use_pages=True, external_stylesheets=[vizro.bootstrap, dbc.icons.FONT_AWESOME]) 




app.layout = dbc.Container([
    #the complete df is stored in store_df nd is not changed, only used
    dcc.Store( id="store_df", data={}),
    header(df),
    html.Div(id='rangeslidervalues', style={'display': 'none'}), #if I remove this one, the whole callback is not triggered, why?
    dash.page_container,

    
    ], fluid=True, className = '')




#on start add processed data to store_df (browser memory)
@callback(Output('store_df', 'data'), 
          Output('rangeslidervalues', 'children'),          
          Input('selected_range_years', 'value'),
          )
def update_stores(value):
   # print(value)
    if not value:        
        return df.to_dict('records'),f" range: {str(value[0])} - {str(value[1])}"
    dff = df[df['year'].between(value[0], value[1]-1)]
    return dff.to_dict('records'), f" range: {str(value[0])} - {str(value[1])}"






#if the refresh button is clicked the rangeslider should be updated 
#the stored df is updated automatically by the previous callback

@app.callback(
    Output("selected_range_years", "value"), 
    [Input("refresh-button", "n_clicks")]
)
def on_button_click(n):
    if n is None:
        return "Not clicked."
    else:
        #this should be flexible but he
        value = [2011,2025]
        return value






clientside_callback(
    """
    (switchOn) => {
       document.documentElement.setAttribute('data-bs-theme', switchOn ? 'light' : 'dark');  
       return window.dash_clientside.no_update
    }
    """,
    Output("color-mode-switch", "id"),
    Input("color-mode-switch", "value"),
)




app.run_server(debug=True) 