# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 11:51:17 2025

@author: win11
"""


import pandas as pd
import dash
from dash import dcc, html
import dash_leaflet as dl
import plotly.io as pio
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import dash_daq as daq
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import math

# stylesheet with the .dbc class to style  dcc, DataTable and AG Grid components with a Bootstrap theme
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
# if using the vizro theme
vizro_bootstrap = "https://cdn.jsdelivr.net/gh/mckinsey/vizro@main/vizro-core/src/vizro/static/css/vizro-bootstrap.min.css?v=2"

# default dark mode
#pio.templates.default = "vizro_dark"

#DATA CLEANING

# Load data
df = pd.read_csv("un-migration-streams-2024.txt")

#remove trailing * from origin and destination
df['Origin']=df['Origin'].apply( lambda x: x.strip().replace("*",""))
df['Destination']=df['Destination'].apply( lambda x: x.strip().replace("*",""))


countries_df = pd.read_csv("countries.csv")  # 'name', 'country', 'latitude', 'longitude'

# Prepare known countries list
known_countries = countries_df['name'].tolist()

# Separate known and unknown countries, unknow countries are continents, regions and descriptions of 
# the economic status of a country


# Load the income classification Excel
income_df = pd.read_excel('class-country.xlsx')  # .head(218) Adjust the path if needed

# Prepare a lookup dictionary: Economy -> Income group
income_lookup = income_df.set_index('Economy')['Income group'].to_dict()

# Function to get income group based on country name
def get_income_group(country):
    return income_lookup.get(country, "Unknown")

#split of countries and regions/continents/income descriptions
def split_known_unknown(df, known_countries):
    mask_known = df['Origin'].isin(known_countries) & df['Destination'].isin(known_countries)
    df_known = df[mask_known].copy()
    df_unknown = df[~mask_known].copy()
    return df_known, df_unknown

df_known, df_unknown = split_known_unknown(df, known_countries)
df_known = df_known.reset_index(drop=True)



# income group for origin and destination is added
df_known['origin_income_group'] = df_known['Origin'].apply(get_income_group)
df_known['destination_income_group'] = df_known['Destination'].apply(get_income_group)


#UI DEFINITIONS


    # Define color mapping
income_colors = {
        "High income": "#2ca02c",         # green
        "Upper middle income": "#1f77b4", # blue
        "Lower middle income": "#ff7f0e", # orange
        "Low income": "#d62728",          # red
        "Unknown": "#7f7f7f"              # grey
    }

# since getting the markercolors does not work very well, let's create two columns in advance
df_known['org_col'] = df_known['origin_income_group'].apply(lambda x: income_colors.get(x))
df_known['dest_col'] = df_known['destination_income_group'].apply(lambda x: income_colors.get(x))



#HELPER FUNCTIONS

#format numbers n = input float, offset length output string

def millify(n,offset):
    n = float(n)
    millnames = ['', 'K', 'M', 'B', 'T']
    
    if n == 0:
        return "0.00"
    
    millidx = min(len(millnames) - 1, int(math.floor(math.log10(abs(n)) / 3)))
    
    scaled = n / 10**(3 * millidx)
    
    return f"{scaled:.1f}{millnames[millidx]}"


#select country

select_country = html.Div([
        html.Label("Select Country:"),
        dbc.Select(
            id="country-dropdown",
            options=[{'label': c, 'value': c} for c in sorted(set(df_known['Origin']).union(set(df_known['Destination'])))],
            placeholder="Select a country",
            value='Netherlands'
        ),
    ], style={'display': 'inline-block'})

select_mode = html.Div([
       
       
      dbc.Switch(
           id="mode-switch",
           label="Toggle Emigration <=> Immigration",
           value=True # False = Origin, True = Destination,
       ),
   ], style={  'verticalAlign': 'top', 'marginTop': '30px'})

#create kpi card

def create_country_info_card(country,mode,netto, dff):
    
    #going to or coming from number of countries
    related_countries = len(dff)
    #people involved in immigration or emigration
    people_num = dff['2024'].sum()
    income_group_country =  get_income_group(country)
    graph_title = "Profile country of origin" if  mode  else "Profile destination country"
    # Define order for sorting barchart always the same way
    income_order = ["High income", "Upper middle income", "Lower middle income", "Low income", "Unknown"]
    
   
    
    #groupby column depends on immigration or emigration
    if not mode:
        #country is origin, count how many people go where in terms of income group destination
        groupby_col = 'destination_income_group'
    else:
        #country is destination, count how many people come where in terms of income group origin
        groupby_col = 'origin_income_group'
    

    dffl = dff.groupby(groupby_col).agg({
         # f"{groupby_col}": "max",
           "2024": "sum" 
        }
        ).reset_index()
        
    #calculate % of total people involved for separate bar income group and convert to string.
    dffl['perc_of_people_num'] = 100 * dffl['2024']/people_num 
    dffl['percent_label'] = dffl['perc_of_people_num'].apply(lambda x: str(round(x,1)) + "%")
    
    dffl[groupby_col] = pd.Categorical(dffl[groupby_col], categories=income_order, ordered=True)
    
    #  [::-1]  reverses the dataframe, which is necessary because it's horizontal, with first
    # row at bottom.
    dffl = dffl.sort_values(groupby_col)[::-1]

    # Add color column based on income group
    dffl['color'] = dffl[groupby_col].map(income_colors)

    # Set index and reindex to include all income groups
    dffl = dffl.set_index(groupby_col).reindex(income_order).reset_index()
    
    dffl = dffl[::-1]
    
    # Fill missing percentage and label values to make sure all bars are always shown
    dffl['perc_of_people_num'] = dffl['perc_of_people_num'].fillna(0)
    dffl['percent_label'] = dffl['percent_label'].fillna("0%")
    
    # Assign colors
    dffl['color'] = dffl[groupby_col].map(income_colors).fillna("#7f7f7f")
    
                 
                                              
     
    
    
    fig = go.Figure(go.Bar(
            x=dffl['perc_of_people_num'],
            y=dffl[f"{groupby_col}"],
            orientation='h',
            text=dffl['percent_label'],
            textposition='outside',
            insidetextanchor='start',
            cliponaxis=False ,
            textfont=dict(
                color='white',
                size=10),
            marker_color=dffl['color']   # <- fixed color per group
        ))
    
    
    # X-axis: show only short month names
    fig.update_xaxes(

        showgrid=False,
        fixedrange=True,
        gridcolor='rgba(255,255,255,0)',
     
        zeroline=False,
        visible=False,

    )
    

    
    
    fig.update_yaxes(visible=True, 

                   
                     showgrid = False,fixedrange=True, zeroline=False)
    
    
    fig.update_layout(

        showlegend=False,
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        #width=400,
        height=200,
        margin=dict(t=30, l=30, b=10, r=10),
        yaxis=dict(color="white" ),
        font=dict(size=10)
    )

    
    title = "Immigration" if mode else "Emigration"
     

    
    card = dbc.Card(
    [
        dbc.CardHeader([html.H2(f"{country}"),
                        html.H5(f"Netto migration {millify(netto,2)} *, {income_group_country} country **")
                        ], style={"textAlign":"center"}),
        dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H4(f"{title} ", className="card-title"),
                        html.H2(f"{millify(people_num,3)} people"),
                        html.P(f"{'to' if not mode else 'from'} {related_countries} countries",
                            className="card-text", style={'color':'white'}
                        ),
                        ],width=3, style={"textAlign":"center"}),
                    dbc.Col([
                        html.H4(f"{graph_title}", className="card-title", style={"textAlign":"center"}),
                        dcc.Graph(figure=fig)
                        
                        ],width=9)
                    
                    ])
                
               
            ]
        ),
        dbc.CardFooter([html.P('* immigration minus emigration'),
                        html.P('** World Bank Classification 2024')])
    ], style={"backgroundColor": "#66001f"}
    
)
    
    return card



# Merge lat/lon for lookup
lat_lon_dict = countries_df.set_index('name')[['latitude', 'longitude']].to_dict(orient='index')

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,  dbc_css, vizro_bootstrap])

# Layout
app.layout = dbc.Container([
    
    dbc.Row([
        dbc.Col([ html.H1("Migration Flows - period 1990 to 2024"),
                 html.P("Visuals and numbers are based on a summary of migrationnumbers from 1990 to 2024."),
                 html.P("Select a country, or switch the button to get started", style={"fontWeight":"bold"})]),
        dbc.Col(   )
        
        ], style={'margin':'1rem'}),
    dbc.Row([
        
        dbc.Col([ dbc.Row([
            dbc.Col(select_country),
            dbc.Col(select_mode)
            
            ], style={'marginBottom':'2rem','alignItems':'center'}),
            dbc.Row([
                
               #kpicard
               html.Div(id='country-kpi')
            
            
            
            
            
            ]),
        ]),
        
        dbc.Col([
     
         
         
         
         dl.Map(center=[20, 0], zoom=2, children=[
             dl.TileLayer(),
             dl.LayerGroup(id="arrows-layer")
         ], style={'height': '60vh', 'width': '100%'}),
         html.Div(id="switch-setting")
         
         
         ], style={'height':'60vh'})
 
 
 
    ],style={'margin':'1rem'})
        

           
        
        ])

# First, let's add a clientside callback to force a clean slate on country change
app.clientside_callback(
    """
    function(selected_country) {
        return [];  // Clear all markers when country changes
    }
    """,
    Output("arrows-layer", "children"),
    Input("country-dropdown", "value"),
    prevent_initial_call=True
)

# Then our regular server-side callback
@app.callback(
    Output("arrows-layer", "children", allow_duplicate=True),
    Output("country-kpi","children"),
   # Output("switch-setting", "children"),
    Input("country-dropdown", "value"),
    Input("mode-switch", "value"),
    prevent_initial_call=True
)
def update_map(selected_country, selected_mode):
    if not selected_country:
        return [], None, ""

    # Create entirely new markers from scratch
    arrows_and_markers = []
    
    # Get all countries we'll be showing (either origin or destination countries)
    mode_str = "Immigration" if selected_mode else "Emigration"
    
    # Get the filtered dataframe based on mode
    if selected_mode:  # Immigration
        # Selected country is destination, get origins
        countries_df = df_known[df_known['Destination'] == selected_country].copy()
    else:  # Emigration 
        # Selected country is origin, get destinations
        countries_df = df_known[df_known['Origin'] == selected_country].copy()
    
    # Calculate net migration    
    netto_migration = df_known[df_known['Destination'] == selected_country]['2024'].sum() - df_known[df_known['Origin'] == selected_country]['2024'].sum()

    # Create lines between countries
    for _, row in countries_df.iterrows():
        origin_coords = lat_lon_dict.get(row['Origin'])
        destination_coords = lat_lon_dict.get(row['Destination'])
        
        if origin_coords and destination_coords:
            arrows_and_markers.append(
                dl.Polyline(
                    positions=[
                        [origin_coords['latitude'], origin_coords['longitude']],
                        [destination_coords['latitude'], destination_coords['longitude']]
                    ],
                    color="#ffffff",
                    weight=1,
                    opacity=0.2
                )
            )
    
    # Create markers for countries
    marker_countries = []
    if selected_mode:  # Immigration
        # Show origin countries
        marker_countries = [(row['Origin'], row['2024']) for _, row in countries_df.iterrows()
                            if row['Origin'] != selected_country]
    else:  # Emigration
        # Show destination countries
        marker_countries = [(row['Destination'], row['2024']) for _, row in countries_df.iterrows() 
                            if row['Destination'] != selected_country]
    
    # Now create markers with fresh colors
    debug_info = []
    for country, people in marker_countries:
        # Get coordinates
        coords = lat_lon_dict.get(country)
        if not coords:
            continue
            
        # Get income group and color (calculate fresh every time)
        income_group = get_income_group(country)
        marker_color = income_colors.get(income_group, "#7f7f7f")
        
        # Add to debug info
        debug_info.append(f"{country}:{income_group}:{marker_color}")
            
        # Create marker
        arrows_and_markers.append(
            dl.CircleMarker(
                center=[coords['latitude'], coords['longitude']],
                radius=3 + math.sqrt(people) * 0.01,
                color=marker_color,
                fill=True,
                fillOpacity=0.7,
                children=[dl.Tooltip(f"{country}: {people:,} people ({income_group})")]
            )
        )
    
    # Add selected country as white marker
    selected_coords = lat_lon_dict.get(selected_country)
    if selected_coords:
        arrows_and_markers.append(
            dl.CircleMarker(
                center=[selected_coords['latitude'], selected_coords['longitude']],
                radius=8,
                color="white",
                fill=True, 
                fillOpacity=0.7,
                children=[dl.Tooltip(f"{selected_country}")]
            )
        )
    
    # Debug: first 3 countries and their colors
   # debug_text = f"Mode: {mode_str}, First 3 countries: " + ", ".join(debug_info[:3])
    
    return arrows_and_markers, create_country_info_card(selected_country, selected_mode, netto_migration, countries_df)


if __name__ == '__main__':
    app.run(debug=True)
