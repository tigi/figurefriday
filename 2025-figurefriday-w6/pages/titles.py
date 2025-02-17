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


register_page(__name__, name="Titles", path="/titles")

#import data and do some basic drop and typeconversions


    
    
layout= dbc.Row([
        dbc.Col([html.H1('Publishers and Titles, to be continued'), 
                 dcc.Link("On publishing industry", href='https://authornews.penguinrandomhouse.com/2009-to-2019-a-decade-of-changes-in-book-publishing/'),
                 html.P(' '),
                dcc.Link('Rise of audiobooks, see 2016', href="https://www.pbs.org/newshour/arts/a-short-history-of-the-audiobook-20-years-after-the-first-portable-digital-audio-device"),
        html.P(' '),
       dcc.Link('NYT bestseller audiobooks', href=" https://www.nytimes.com/books/best-sellers/2024/12/01/audio-fiction/"),
        html.P('is 2016 the year when the top-20 changed into a top-15?', style={'color':'white'}),
        html.Img(src="assets/images/audiobooks.jpg")]),
       
        dbc.Col([html.Div(id='bar_publishers'),
                 html.P('dots = distinct publishers, lines&markers distinct titles, green=mentions', style={'color':'white'})])
        
        
        
        ])
# =============================================================================
#                                          
# 
# @callback(
#     Output('title_publishers', 'children'),
#     Input("store_df", "data"))
# 
# 
#     
# def create_titles_over_years(store_df):
#     
#     df_filtered = pd.DataFrame(store_df)
#     
#     #groupby distinct publisher per week
#     df_in = df_filtered.groupby(by = ['year'])['publisher'].nunique().reset_index()
#     #print(df_in)
#     #unique titles
#     df_int = df_filtered.groupby(by = ['year'])['title'].nunique().reset_index()
#     df_inm = df_filtered.groupby(by = ['year'])['title'].count().reset_index()
#     fig = go.Figure()
#     
#     fig.add_trace(go.Scatter(x=df_in['year'], y=df_in['publisher'],
#                     mode='markers',
#                     name='markers'))
#     fig.add_trace(go.Scatter(x=df_int['year'], y=df_int['title'],
#                     mode='lines+markers',
#                     name='lines+markers'))
#     fig.add_trace(go.Scatter(x=df_inm['year'], y=df_inm['title'],
#                     mode='lines',
#                     name='lines'))
#     
#     return dcc.Graph(figure = fig)
# 
# 
# 
# =============================================================================
