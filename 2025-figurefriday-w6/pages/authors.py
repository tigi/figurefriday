# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 07:41:17 2025

@author: win11
"""


import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, callback_context, callback,register_page
import dash_ag_grid as dag
from data.data_functions import prepare_df_base #data etl

register_page(__name__)

#import data and do some basic drop and typeconversions


    
    
layout= dbc.Row([
        dbc.Col([html.H1('Authors, to be continued')]),
       
        dbc.Col([html.P('Have a good day!', style={'fontSize': '4rem', 'color':'white'})])
        
        
        
        ])
                                         



