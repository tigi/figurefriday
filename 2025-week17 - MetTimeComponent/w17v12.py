import pandas as pd
import dash
from dash import dcc, html
import dash_leaflet as dl
import plotly.io as pio
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import math

# stylesheet with the .dbc class to style  dcc, DataTable and AG Grid components with a Bootstrap theme
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
# if using the vizro theme
vizro_bootstrap = "https://cdn.jsdelivr.net/gh/mckinsey/vizro@main/vizro-core/src/vizro/static/css/vizro-bootstrap.min.css?v=2"

# default dark mode
#pio.templates.default = "vizro_dark"
load_figure_template(["vizro", "vizro_dark"])


#PROCESS MIGRATION DATA
df_allyears = pd.read_excel('undesa_pd_2024_ims_stock_by_sex_destination_and_origin.xlsx',
                        sheet_name='Table 1',
                        header=10,
                        usecols=[1,4,5,6,7,8,9,10,11,12,13,14])
# remove special character 


allyears = df_allyears.columns[4:]
selected_year = 'jul2024'



#PROCESS POPULATIONDATA

df_allpop = pd.read_csv('wpp2024_totalpopulationbysex-cleaned.csv')
#filter on time (=year), 
useyears = [ 1990,1995,2000,2005,2010,2015,2020,2024]
dff_allpop = df_allpop[df_allpop['Time'].isin(useyears)]


#DATA CLEANING

# Load data
#df = pd.read_csv("un-migration-streams-2024.txt")
df = df_allyears.copy(deep=True)

#remove trailing * from origin and destination
df['Origin']=df['Origin'].apply( lambda x: x.strip().replace("*",""))
df['Destination']=df['Destination'].apply( lambda x: x.strip().replace("*",""))



#PROCESS COUNTRIES LAT/LONG
countries_df = pd.read_csv("countries.csv")  # 'name', 'country', 'latitude', 'longitude'

# Prepare known countries list
known_countries = countries_df['name'].tolist()

# Separate known and unknown countries, unknow countries are continents, regions and descriptions of 
# the economic status of a country

#PROCESS INCOME ACCORDING TO WORLD BANK
# Load the income classification Excel
income_df = pd.read_excel('class-country.xlsx')  # .head(218) Adjust the path if needed

# Prepare a lookup dictionary: Economy -> Income group
income_lookup = income_df.set_index('Economy')['Income group'].to_dict()






#HELPERFUNCTIONS
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
           value=True,
           persistence = 'session' # False = Origin, True = Destination,
       ),
   ], style={  'verticalAlign': 'top', 'marginTop': '30px'})


# select_year = html.Div([
       
#       html.Label("Select year:"), 
#       dbc.Select(
#             id="year-dropdown",
#             options=[{'label': c, 'value': c} for c in allyears],
#             placeholder="Select a country",
#             value='jul2024',
#            #persistence = 'session' # False = Origin, True = Destination,
#        ),
#    ], style={  'verticalAlign': 'top', 'marginTop': '30px'})


modal = html.Div(
    [
        dbc.Button("Open modal", id="open", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Header")),
                dbc.ModalBody([
                    html.Div([html.H3('Trend over the years'),
                              html.Div(id = 'trend-chart')
                              ])
                    
                    ]),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ms-auto", n_clicks=0)
                ),
            ],
            id="modal",
            is_open=False,
        ),
    ]
)




 #create kpi card

def create_country_info_card(country,mode, netto, dff):
    
     
     #going to or coming from number of countries
     related_countries = len(dff)
     #people involved in immigration or emigration
     people_num = dff[selected_year].sum()
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
            f"{selected_year}": "sum" 
         }
         ).reset_index()
         
     #calculate % of total people involved for separate bar income group and convert to string.
     dffl['perc_of_people_num'] = 100 * dffl[selected_year]/people_num 
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
     
     # Reverse the income_order list for a horizontal bar chart
     income_order_reversed = income_order[::-1]
     
     # Use a lambda function to add two spaces to each reversed label
     income_order_with_spaces = list(map(lambda label: label + "  ", income_order_reversed))
       
                                               
     fig = go.Figure(go.Bar(
         x=dffl['perc_of_people_num'],
         y=dffl[f"{groupby_col}"],
         orientation='h',
         text=dffl['percent_label'],
         textposition='outside',
         insidetextanchor='start',
         cliponaxis=False,
         textfont=dict(
             color='white',
             size=10),
         marker_color=dffl['color']   # fixed color per group
     ))
     
     # X-axis: show only short month names
     fig.update_xaxes(
         showgrid=False,
         fixedrange=True,
         gridcolor='rgba(255,255,255,0)',
         zeroline=False,
         visible=False,
     )
     
     # Y-axis: set tickvals and ticktext to match income_order
     fig.update_yaxes(
         visible=True,
         showgrid=False,
         fixedrange=True,
         zeroline=False,
         tickvals=list(range(len(income_order_with_spaces))),  # Assuming the y-values are integers corresponding to the order in income_order
         ticktext=income_order_with_spaces,  # Use the modified labels with two spaces
         

  
     )
     
     fig.update_layout(
         showlegend=False,
         plot_bgcolor="rgba(255,255,255,0)",
         paper_bgcolor="rgba(255,255,255,0)",
         height=200,
         margin=dict(t=30, l=30, b=10, r=10),
         yaxis=dict(color="white"),
         font=dict(size=10),
         xaxis_range=[0,110]
     )

     
     title = "Immigration" if mode else "Emigration"
      

     
     card = dbc.Card(
     [
         dbc.CardHeader([html.H2(f"{country} {selected_year}"),
                         html.H5(f"Netto migration {millify(netto,2)} *, {income_group_country} country **")
                         ], style={"textAlign":"center"}),
         dbc.CardBody([
                 dbc.Row([
                     dbc.Col([
                         html.H3(f"{title} ", className="card-title"),
                         html.H2(f"{millify(people_num,3)} people"),
                         html.P(f"{'to' if not mode else 'from'} {related_countries} countries",
                             className="card-text", style={'color':'white'}
                         ),
                         ],width=3, style={"textAlign":"center"}),
                     dbc.Col([
                         html.H3(f"{graph_title}", className="card-title", style={"textAlign":"center"}),
                         html.Div(dcc.Graph(figure=fig))
                         
                         ],width=9)
                     
                     ])
                 
                
             ]
         ),
         dbc.CardFooter([html.P('* immigration minus emigration'),
                         html.P('** World Bank Classification 2024')])
     ], style={"backgroundColor": "#66001f"}
     
 )
     
     return card
 
    
 
def create_trend_country(country, mode, dff):
    
     #groupby column depends on immigration or emigration
     
     if not mode:
         #country is origin, count how many people go where in terms of income group destination
         groupby_col = 'Origin'
         chart_title = f'{country}: trend citizens living abroad 1990-2024'
     else:
         #country is destination, count how many people come where in terms of income group origin
         groupby_col = 'Destination'
         chart_title = f'{country}: trend citizens from abroad 1990 - 2024'
     

     dffg = dff.groupby(groupby_col).sum().reset_index()
     print(dffg.info())
    
     #print(dffg.head())
     data_columns = [col for col in dffg.columns if 'jul' in col]
     data_columns.append(f"{groupby_col}")
     data = dffg[data_columns]
     print(data)
     linedata = pd.melt(data, id_vars=[f"{groupby_col}"], value_vars=data_columns[:-1 or None])
     print(linedata.head(10))
    
     linefig = go.Figure(data=go.Scatter(x=linedata['variable'], y=linedata['value']))
     linefig.update_layout(
         height =300,
         title=chart_title,
         template='vizro_dark'
         )
    
    
     return dcc.Graph(figure = linefig)



# Merge lat/lon for lookup
lat_lon_dict = countries_df.set_index('name')[['latitude', 'longitude']].to_dict(orient='index')

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,  dbc_css, vizro_bootstrap])

# Layout
app.layout = dbc.Container([
    
    dbc.Row([
        dbc.Col([ html.H1("Migration Stock"),
                 html.P("Visuals and numbers are based on the number of people born in a country other than that in which they live, including refugees."),
                 html.P("Select a country, or switch the button to get started", style={"fontWeight":"bold"})]),
        dbc.Col(   )
        
        ], style={'margin':'1rem'}),
    dbc.Row([
        
        dbc.Col([ dbc.Row([
            dbc.Col(select_country),
            dbc.Col(select_mode),
            dbc.Col(modal)
            
            ], style={'marginBottom':'2rem'}),
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

         
         
         ], style={'height':'60vh'})
 
 
 
    ],style={'margin':'1rem'})
        

           
        
        ])


    


@app.callback(
    Output("arrows-layer", "children"),
    Output("country-kpi","children"),
    Output("trend-chart","children"),
    Input("country-dropdown", "value"),
    Input("mode-switch", "value"),
)
def update_map(selected_country, selected_mode):
    
    
    if not selected_country:
        selected_country = 'Netherlands'
        
    # if not selected_year:
    #         selected_year = 'jul2024'

    
    arrows_and_markers = []
    

    if selected_mode == False:  # Origin mode - immigration
        dff = df_known[df_known['Origin'] == selected_country].reset_index(drop=True)
    else:  # Destination mode - emigration
        dff = df_known[df_known['Destination'] == selected_country].reset_index(drop=True)
        
    netto_migration = df_known[df_known['Destination'] == selected_country][selected_year].sum() - df_known[df_known['Origin'] == selected_country][selected_year].sum()

    
    #add the polylines
    
    for _, row in dff.iterrows():
        
        
        origin_coords = lat_lon_dict.get(row['Origin'])
        destination_coords = lat_lon_dict.get(row['Destination'])

        if not origin_coords or not destination_coords:
            continue

        positions = [
            [origin_coords['latitude'], origin_coords['longitude']],
            [destination_coords['latitude'], destination_coords['longitude']]
        ]

        # Draw the grey line
        arrows_and_markers.append(
            dl.Polyline(positions=positions,
                        color="#ffffff",
                        weight=1,
                        opacity=0.2)
        )

        # Determine the other country (the one different from selected)
        if selected_mode == False:  # Origin mode - country as source immigratie
            target_country = row['Destination']
            people = row[selected_year]
            coords = destination_coords
            income_group = row['destination_income_group']
            varcolor = row['dest_col']
        else :  # Destination mode - country as destination - immigratie
            target_country = row['Origin']
            people = row[selected_year]
            coords = origin_coords
            income_group = row['origin_income_group']
            varcolor=row['org_col']
        
        
        
        #print(f"{target_country}  {varcolor}")

       
        
    
     # add the markers
     
    for _, row in dff.iterrows():
         
         
         origin_coords = lat_lon_dict.get(row['Origin'])
         destination_coords = lat_lon_dict.get(row['Destination'])

         if not origin_coords or not destination_coords:
             continue

         positions = [
             [origin_coords['latitude'], origin_coords['longitude']],
             [destination_coords['latitude'], destination_coords['longitude']]
         ]


         # Determine the other country (the one different from selected)
         if selected_mode == False:  # Origin mode - country as source immigratie
             target_country = row['Destination']
             people = row[selected_year]
             coords = destination_coords
             income_group = row['destination_income_group']
             varcolor = row['dest_col']
         else :  # Destination mode - country as destination - immigratie
             target_country = row['Origin']
             people = row[selected_year]
             coords = origin_coords
             income_group = row['origin_income_group']
             varcolor=row['org_col']
         
         
         
         #print(f"{target_country}  {varcolor}")

         # Skip placing a colored marker if it's the selected country
         if target_country == selected_country:
             continue



         people = row[selected_year]
         radius = 3 + math.sqrt(people) * 0.01


         arrows_and_markers.append(
             dl.CircleMarker(
                 center=[coords['latitude'], coords['longitude']],
                 radius=radius,
                 color=varcolor,
                 fill=True,
                 fillOpacity=0.7,
                 children=[dl.Tooltip(f"{target_country}: {people:,} people, {income_group}")]
             )
         )    
        
        
        
        
        
    #add the country itself as white marker
    
    selected_coords = lat_lon_dict.get(selected_country)
    
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
    

    return arrows_and_markers, \
        create_country_info_card(selected_country, selected_mode, netto_migration, dff), \
            create_trend_country(selected_country, selected_mode, dff)


##MODAL CALLBACK FOR OVERALL TRENDLINE#####

@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open





if __name__ == '__main__':
    app.run_server(debug=True)
