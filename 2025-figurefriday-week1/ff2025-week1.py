# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 11:51:17 2025

@author: win11
"""

import plotly.express as px
import pandas as pd
from dash import Dash, html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import dash_daq as daq


###############################################################

# DATAPROCESSING #

###############################################################

#df_raw = pd.read_csv('NYC Marathon Results, 2024 - Marathon Runner Results.csv')


#df = df_raw[['runnerId', 'age', 'gender','countryCode','racesCount']].copy()
#drop age = 0, with all the nans
#df = df.dropna()
#add true/false column for usa citizen
#df['Usa citizen'] = df['countryCode'].apply(lambda x: 1 if x=='USA' else 0)



#df.to_csv("nycm_data.csv")

df = pd.read_csv("nycm_data.csv")

df_grouped_age =df.groupby(['age', 'gender','Usa citizen'])['age'].count().rename('Count').to_frame().reset_index()

#drop gender=x because I want to end with 4 groups, total of 119 runners dropped out of 55000+
df_grouped_age = df_grouped_age[(df_grouped_age['gender'] != 'X')].sort_values(by=['age'])



###############################################################

# BUCKET LIST THING FOR PEOPLE ABROAD?#

###############################################################



# Create plot
fig = px.area(df_grouped_age, x="age", y="Count", color= 'gender', color_discrete_map= {'M': '#1261a0',
                                      'W': '#0895d3'}, line_group='Usa citizen',
              pattern_shape_sequence=["|", ""],pattern_shape = 'Usa citizen', line_shape='spline')


#customize texts
fig.update_layout(
    title="You are never to old to run a marathon",
    xaxis_title="Runners age",
    yaxis_title="Total number of runners",
    legend_title="Profile",

)



#make legend for traces understandable
for tr in fig.select_traces():
    tr['name'] = tr['name'].replace('W,','Female')
    tr['name'] = tr['name'].replace('M,','Male')
    tr['name'] = tr['name'].replace('0','from abroad')
    tr['name'] = tr['name'].replace('1','from the USA')
    
    
    
def create_age_card(age):
    
    #imagesources
    
    age_image = age
    if age not in (40,50,60):
        age_image = "unknown"
    
    
    
    
    #calculate some values
    #%firsttimes
    
    total = len(df[(df['age'] == age)])
    total_first = len(df[(df['age'] == age) & (df['racesCount'] == 1)])
    first_count=str(round(100*(total_first/total),1))
    races_median = df[(df['age'] == age)]['racesCount'].median()
    races_max = df[(df['age'] == age)]['racesCount'].max()
    total_abroad = len(df[(df['age'] == age) & (df['Usa citizen'] == 0)])
    foreigners  =str(round(100*(total_abroad/total),1))
    
    
    card = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    dbc.CardImg(
                        src=f"/assets/{age_image}.jpg",
                        className="img-fluid rounded-start",
                    ),
                    className="col-md-4",
                ),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H4(f"Profile {age} years", className="card-title"),
                            html.Span(
                               "First marathon?",
                                className="card-text",style={"fontSize": "14px"}
                            ),
                            html.Span(
                               f" {first_count} %",
                                className="card-text", style={"fontWeight":"bold","fontSize": "14px"}
                            ),
                            html.Br(),
                            html.Span('Most experienced runner: ', style={"fontSize": "14px"}),
                            html.Span(
                               f" {races_max} marathons",
                                className="card-text", style={"fontWeight":"bold","fontSize": "14px"}
                            ),
                            html.Br(),
                            html.Span("Coming from abroad? ",style={"fontSize": "14px"}),
                            html.Span(
                               f"{foreigners}% of runners",
                                className="card-text", style={"fontWeight":"bold","fontSize": "14px"}
                            ),

                        ]
                    ),
                    className="col-md-8",
                ),
            ],
            className="g-0 d-flex align-items-center",
        )
    ],
    className="mb-4",
    style={"maxWidth": "540px"},
)
    
    
    
    
    return card

 


dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE, dbc_css])



app.layout = dbc.Container(
    [   dbc.Row([
        html.H1("Is the New York City Marathon on your bucketlist?"),
        dbc.Col([

            dcc.Graph(id="scatter-plot", figure = fig),

            
            ], className = 'col-md-12'),
        

          
        ]),
        
        dbc.Row([
            dbc.Col([create_age_card(40)],className='col-md-4'),
            dbc.Col([create_age_card(50)],className='col-md-4'),
            dbc.Col([create_age_card(60)],className='col-md-4')
            
            
            ]),
        
        
        dbc.Row([
            
            dbc.Col( 
                [html.H4('Enter your age and see your potential based on 2024 runner information of the NYCM'),
                    daq.NumericInput(
        id='my-numeric-input-1', min=18, max=100, value=30),
                    html.Br(),
    ], style={"backgroundColor": "#0895d3", "borderRadius": "4px", "color": "white", "padding": "1rem","textAlign":"center"}),
            dbc.Col([html.Div(id='numeric-input-output-1')]),
            dbc.Col([html.H2('Go for it!')], style={"textAlign": "Center"})
            
            ])
        
        
        
        
        
        
], style={"marginTop": "2rem"})


@callback(
    Output('numeric-input-output-1', 'children'),
    Input('my-numeric-input-1', 'value')
)
def update_output(value):
    return create_age_card(value)


app.run_server(debug=True)