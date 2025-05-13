import dash
import dash_leaflet as dl
from dash import html, Input, Output, dcc, State
import pycountry
from dash_extensions.javascript import assign
import json
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import pandas as pd
import math
import plotly.graph_objects as go


##I SHOULD CLEANUP THIS CODE BUT I'M NOT IN THE MOOD ##

# stylesheet with the .dbc class to style  dcc, DataTable and AG Grid components with a Bootstrap theme
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
# if using the vizro theme
vizro_bootstrap = "https://cdn.jsdelivr.net/gh/mckinsey/vizro@main/vizro-core/src/vizro/static/css/vizro-bootstrap.min.css?v=2"

# default dark mode
#pio.templates.default = "vizro_dark"
load_figure_template(["vizro", "vizro_dark"])



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



# Convert country name to ISO3 code (Keep this function as is - it's working well)
def country_name_to_iso3(name):
    original_name = name
    try:
        if name == "Kosovo": return "XKX"
        if name == "Micronesia (Federated States of)": return "FSM"
        if name == "Iran (Islamic Republic of)": return "IRN"
        if name == "Bolivia (Plurinational State of)": return "BOL"
        if name == "Venezuela (Bolivarian Republic of)": return "VEN"
        if name == "Brunei Darussalam": return "BRN"
        if name == "Cabo Verde": return "CPV"
        if name == "Congo": return "COG"
        if name == "Côte d'Ivoire" or name == "Cote d'Ivoire": return "CIV"
        if name == "Czechia" or name == "Czech Republic": return "CZE"
        if name == "Holy See": return "VAT"
        if name == "Lao People's Democratic Republic": return "LAO"
        if name == "North Macedonia" or name == "The former Yugoslav Republic of Macedonia": return "MKD"
        if name == "Palestine, State of" or name == "State of Palestine": return "PSE"
        if name == "Republic of Moldova" or name == "Moldova, Republic of": return "MDA"
        if name == "Russian Federation": return "RUS"
        if name == "Swaziland": return "SWZ"
        if name == "Eswatini": return "SWZ"
        if name == "Syrian Arab Republic": return "SYR"
        if name == "Timor-Leste": return "TLS"
        if name == "United Republic of Tanzania" or name == "Tanzania, United Republic of": return "TZA"
        if name == "United States Virgin Islands": return "VIR"
        if name == "United States of America": return "USA"
        if name == "Viet Nam": return "VNM"
        if name == "Türkiye" or name == "Turkey": return "TUR"
        if name == "Taiwan, Province of China": return "TWN"
        if name == "China, Hong Kong Special Administrative Region": return "HKG"
        if name == "China, Macao Special Administrative Region": return "MAC"
        if name == "Democratic People's Republic of Korea": return "PRK"
        if name == "Republic of Korea": return "KOR"
        if name == "United Kingdom of Great Britain and Northern Ireland": return "GBR"
        if name == "Svalbard and Jan Mayen Islands": return "SJM"
        if name == "Faeroe Islands": return "FRO"
        if name == "Åland Islands": return "ALA"
        if name == "Saint-Barthélemy": return "BLM"
        if name == "Saint Martin (French part)": return "MAF"
        if name == "Sint Maarten (Dutch part)": return "SXM"
        if name == "Bonaire, Sint Eustatius and Saba": return "BES"
        if name == "Falkland Islands (Malvinas)": return "FLK"
        if name == "Democratic Republic of the Congo": return "COD"
        if name == "Sark": return "GGY"
        if name == "Wallis and Futuna Islands": return "WLF"
        if name == "Somaliland": return "SML"
        country_lookup = pycountry.countries.lookup(name)
        return country_lookup.alpha_3.upper()
    except LookupError:
        try:
            country_lookup = pycountry.countries.search_fuzzy(name)
            if country_lookup: return country_lookup[0].alpha_3.upper()
        except LookupError: pass
        return None
    except Exception: return None

# --- UN Data Processing ---
local_un_data_filename = "assets/un-geoscheme-subregions-countries.json"
with open(local_un_data_filename, 'r', encoding='utf-8') as f:
        un_data_direct_load = json.load(f)

# ***** CHANGE 1: Build iso_to_un_subregion_name map *****
iso_to_un_subregion_name = {} # Renamed and will store subregion name directly
unmapped_un_countries_log = []
mapped_un_country_count = 0

# print("--- Building iso_to_un_subregion_name map ---")
for top_level_key, value_list in un_data_direct_load.items():
    current_subregions_to_process = []
    # The UN JSON structure:
    # Keys can be "Intermediate Regions" (like "Sub-Saharan Africa") which contain lists of subregion dicts,
    # OR keys can be actual "Subregions" (like "Northern Europe") which contain lists of country strings.
    if isinstance(value_list, list) and value_list:
        if isinstance(value_list[0], str): # top_level_key IS the subregion name
            # Here, top_level_key is the subregion name we want (e.g., "Northern Europe")
            # and value_list is the list of its countries.
            current_subregions_to_process.append((top_level_key, value_list))
        elif isinstance(value_list[0], dict): # top_level_key is an intermediate region
            # value_list is a list of actual subregion dicts like [{"Eastern Africa": [...]}, {"Middle Africa": [...]}]
            for subregion_dict_item in value_list:
                for actual_subregion_name_key, countries_list_for_subregion in subregion_dict_item.items():
                    # actual_subregion_name_key is the subregion name we want (e.g., "Eastern Africa")
                    current_subregions_to_process.append((actual_subregion_name_key, countries_list_for_subregion))
    
    for un_subregion_name_from_data, country_name_list in current_subregions_to_process:
        # un_subregion_name_from_data is now the specific UN subregion name string
        for country_name_str in country_name_list:
            if not isinstance(country_name_str, str): continue
            iso3 = country_name_to_iso3(country_name_str)
            if iso3:
                 # Store the direct UN subregion name
                iso_to_un_subregion_name[iso3.upper()] = un_subregion_name_from_data
                mapped_un_country_count += 1
            else:
                unmapped_un_countries_log.append(f"{country_name_str} (UN Subregion in data: {un_subregion_name_from_data}) - ISO3 FAILED")

# print(f"Processed {mapped_un_country_count} UN country names and mapped them to a UN Subregion Name.")
# print(f"Total unique ISO_A3 codes in map: {len(iso_to_un_subregion_name)}")
if unmapped_un_countries_log:
    print(f"\n{len(unmapped_un_countries_log)} UN country names still UNMAPPED (showing up to 5):")
    for c_entry in sorted(list(set(unmapped_un_countries_log)))[:5]: print(f"  - {c_entry}")

# print("\nSample of iso_to_un_subregion_name:", dict(list(iso_to_un_subregion_name.items())[:5]))


# ***** CHANGE 2: Assign colors to unique UN subregion names *****
unique_un_subregion_names = sorted(list(set(iso_to_un_subregion_name.values())))
# print(f"\n--- Assigning colors to UN Subregions ---")
# print(f"Found {len(unique_un_subregion_names)} unique UN Subregion names for coloring: {unique_un_subregion_names[:10]}... (first 10 shown)")

un_subregion_name_to_color = {}
if unique_un_subregion_names:
    num_subregions = len(unique_un_subregion_names)
    for i, sub_name in enumerate(unique_un_subregion_names):
        # Generate distinct colors using HSL color space
        # Hue: 0-360, Saturation: 50-100%, Lightness: 40-60%
        hue = int(i * (360 / num_subregions))
        saturation = 70  # Can adjust this (e.g., 60 + (i % 5) * 8 for slight variation)
        lightness = 50   # Can adjust this (e.g., 45 + (i % 3) * 5 for slight variation)
        un_subregion_name_to_color[sub_name] = f"hsl({hue}, {saturation}%, {lightness}%)"
else:
    print("Warning: No unique UN subregion names found after mapping. Default colors will be used.")


country_transparancy = .6

un_subregion_name_to_color =  {
    'Australia and New Zealand': f'hsla(0, 100%, 65%, {country_transparancy})',
    'Caribbean': f'hsla(20, 100%, 65%, {country_transparancy})',
    'Central America': f'hsla(40, 100%, 65%, {country_transparancy})',
    'Central Asia': f'hsla(60, 100%, 65%, {country_transparancy})',
    'Eastern Africa':f'hsla(80, 100%, 65%, {country_transparancy})',
    'Eastern Asia': f'hsla(100, 100%, 65%, {country_transparancy})',
    'Eastern Europe': f'hsla(120, 100%, 65%, {country_transparancy})',
    'Melanesia': f'hsla(140, 100%, 65%, {country_transparancy})',
    'Micronesia': f'hsla(160, 100%, 65%, {country_transparancy})',
    'Middle Africa': f'hsla(180, 100%, 65%, {country_transparancy})',
    'Northern Africa': f'hsla(200, 100%, 65%, {country_transparancy})',
    'Northern America': f'hsla(220, 100%, 65%, {country_transparancy})',
    'Northern Europe': f'hsla(240, 100%, 65%, {country_transparancy})',
    'Polynesia': f'hsla(260, 100%, 65%, {country_transparancy})',
    'South America': f'hsla(280, 100%, 65%,{country_transparancy})',
    'South-Eastern Asia': f'hsla(300, 100%, 65%, {country_transparancy})',
    'Southern Africa': f'hsla(320, 100%, 65%, {country_transparancy})',
    'Southern Asia': f'hsla(340, 100%, 65%, {country_transparancy})',
    'Southern Europe': f'hsla(10, 100%, 65%, {country_transparancy})',
    'Western Africa': f'hsla(30, 100%, 65%, {country_transparancy})',
    'Western Asia': f'hsla(50, 100%, 65%, {country_transparancy})',
    'Western Europe': f'hsla(70, 100%, 65%,{country_transparancy})'
}


with open('assets/countries.geojson', 'r', encoding='utf-8') as f: # Added encoding
        geojson_data = json.load(f)


# ***** CHANGE 3: Styling GeoJSON features using UN subregion names *****
#print("\n--- Styling GeoJSON features by UN Subregion ---")
countries_styled_with_subregion_color = 0
countries_styled_with_default_color = 0
geojson_iso_codes_not_in_our_map = set()
un_subregions_actually_used_for_styling = set()

for i, feature in enumerate(geojson_data.get("features", [])):
    props = feature.get("properties", {})
    iso_a3_geojson_raw = props.get("ISO3166-1-Alpha-3") # Correct GeoJSON key

    style_to_apply = {"fillColor": "#CCCCCC", "color": "black", "weight": 1, "fillOpacity": 0.7} # Default
        
    

    if iso_a3_geojson_raw and isinstance(iso_a3_geojson_raw, str):
        iso_a3_geojson_processed = iso_a3_geojson_raw.upper().strip()
        if iso_a3_geojson_processed and iso_a3_geojson_processed != "NONE":
            # Get the direct UN subregion name for this country's ISO
            un_subregion_name_for_country = iso_to_un_subregion_name.get(iso_a3_geojson_processed)
            
            if un_subregion_name_for_country:
                # Get the color assigned to this specific UN subregion name
                color = un_subregion_name_to_color.get(un_subregion_name_for_country)
                if color:
                    style_to_apply["fillColor"] = color
                    countries_styled_with_subregion_color += 1
                    un_subregions_actually_used_for_styling.add(un_subregion_name_for_country)
                else: # Should not happen if un_subregion_name_to_color is well-formed
                    countries_styled_with_default_color += 1
            else:
                # This ISO code from GeoJSON was not found in our UN data map
                geojson_iso_codes_not_in_our_map.add(iso_a3_geojson_processed)
                countries_styled_with_default_color += 1
        else: # Processed ISO was empty or "NONE"
            countries_styled_with_default_color += 1
    else: # Raw ISO from GeoJSON was None, not a string, or empty
        countries_styled_with_default_color += 1
            
    props["style"] = style_to_apply
    feature["properties"] = props

# Final summary prints
# print(f"\n{countries_styled_with_subregion_color} GeoJSON features styled with a specific UN Subregion color.")
# print(f"{countries_styled_with_default_color} GeoJSON features styled with the default color.")
# print(f"Number of unique UN Subregions actually applied to map: {len(un_subregions_actually_used_for_styling)}")
# print(f"UN Subregions effectively styled on map: {sorted(list(un_subregions_actually_used_for_styling))}")

# if geojson_iso_codes_not_in_our_map:
#     print(f"\n{len(geojson_iso_codes_not_in_our_map)} PROCESSED ISO codes from GeoJSON were NOT found in your iso_to_un_subregion_name map (showing up to 20):")
#     for code in sorted(list(geojson_iso_codes_not_in_our_map))[:20]: print(f"  - '{code}'")


region_centroids = {
    "Northern Africa": (28.0, 10.0),
    "Western Africa": (9.0, -5.0),
    "Middle Africa": (0.0, 20.0),
    "Eastern Africa": (0.0, 38.0),
    "Southern Africa": (-23.0, 24.0),
    "Northern Europe": (60.0, 15.0),
    "Western Europe": (48.0, 5.0),
    "Eastern Europe": (54.0, 30.0),
    "Southern Europe": (42.0, 15.0),
    "Central America": (15.0, -90.0),
    "Caribbean": (18.0, -70.0),
    "South America": (-10.0, -60.0),
    "Northern America": (45.0, -100.0),
    "Western Asia": (33.0, 45.0),
    "Central Asia": (45.0, 70.0),
    "Southern Asia": (22.0, 80.0),
    "South-Eastern Asia": (10.0, 105.0),
    "Eastern Asia": (35.0, 115.0),
    "Australia and New Zealand": (-25.0, 135.0),
    "Melanesia": (-7.0, 150.0),
    "Micronesia": (7.0, 158.0),
    "Polynesia": (-15.0, -150.0),
}

region_dots = [
    dl.CircleMarker(
        center=coords,
        radius=6,
        color="white",
        fillColor="yellow",
        fillOpacity=0.7,
        children=[dl.Tooltip(region)],
    )
    for region, coords in region_centroids.items()
]



#create kpi card

def create_region_info_card(region,dff):
    
    
     selected_year = 'jul2024'
     #going to or coming from number of countries
     related_regions = len(dff)
     #people involved in immigration or emigration
     graph_title = f"Region of origin for people migrated to {region}" 

     people_num=dff[selected_year].sum()
         
     #calculate % of total people involved for separate bar income group and convert to string.
     dff['perc_of_people_num'] = dff[selected_year].apply(lambda x: 100 * x/people_num)
     dff['percent_label'] = dff['perc_of_people_num'].apply(lambda x: str(round(x,1)) + "%")
     dff.sort_values('perc_of_people_num', inplace=True)
     
     # Assign colors
     dff['color'] = dff['Origin'].map(un_subregion_name_to_color).fillna("#7f7f7f")
     
     

     
     # Use a lambda function to add two spaces to each reversed label
     #income_order_with_spaces = list(map(lambda label: label + "  ", income_order_reversed))
       
                                               
     fig = go.Figure(go.Bar(
         x=dff['perc_of_people_num'],
         y=dff['Origin'],
         orientation='h',
         text=dff['percent_label'],
         textposition='outside',
         insidetextanchor='start',
         cliponaxis=False,
         textfont=dict(
             color='white',
             size=10),
         marker_color=dff['color']   # fixed color per group
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
  # Use the modified labels with two spaces
         tickfont=dict(color='white')

  
     )
     

     fig.update_layout(
         showlegend=False,
         plot_bgcolor="rgba(255,255,255,0)",
         paper_bgcolor="rgba(255,255,255,0)",
        # height=200,
         margin=dict(t=30, l=30, b=10, r=10),
         yaxis=dict(color="white"),
         font=dict(size=10),
         xaxis_range=[0,110]
     )

     
     title = "Total" 
      

     
     card = dbc.Card(
     [
         dbc.CardHeader([html.H2(f"{region} juli 2024"),
                         ], style={"textAlign":"center"}),
         dbc.CardBody([
                 dbc.Row([
                     dbc.Col([
                         html.H3(f"{title} ", className="card-title"),
                         html.H2(f"{millify(people_num,3)} people"),

                         ],width=3, style={"textAlign":"center"}),
                     dbc.Col([
                         html.H3(f"{graph_title}", className="card-title", style={"textAlign":"center"}),
                         html.Div(dcc.Graph(figure=fig)),
                         
                         ],width=9)
                     
                     ])
                 
                
             ]
         ),
         dbc.CardFooter([                         html.P('* Datasource: https://www.un.org/development/desa/pd/content/international-migrant-stock. '),
                                  html.P('If destination and origin regions are equal, this means people moved countries in the same region.')

                         ])
     ], style={"backgroundColor": "#66001f",'height': '85vh'}
     
 )
     
     return card




#READ THE REAL DATA
df_migration = pd.read_csv('migration_region.csv')

#start
origin='Western Europe'
period='jul2024'

#print(df_migration[df_migration['Origin'] == origin][period])




select_region = html.Div([
        html.Label("Select destination region:"),
        dbc.Select(
            id="region-dropdown",
            options=[{'label': c, 'value': c} for c in sorted(set(df_migration['Origin']).union(set(df_migration['Destination'])))],
            placeholder="Select destination region",
            value='Western Europe'
        ),
    ], style={'display': 'inline-block'})

modal = html.Div(
    [
        dbc.Button("Show trend", id="open", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Trend 1990 - 2024")),
                dbc.ModalBody([
                    html.Div([
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

def create_trend_region(region, dff):
 
    
     #filter out irrelevant columns
     data_columns = [col for col in dff.columns if 'jul' in col]
     data_columns.append('Destination')
     data = dff[data_columns]
     
     
     dffg = data.groupby('Destination').sum().reset_index()
     #print(dffg.tail(10))
     
     
     linedata = pd.melt(dffg, id_vars=['Destination'], value_vars=data_columns[:-1 or None])
     #print(linedata.head(10))
    
     linefig = go.Figure(data=go.Scatter(x=linedata['variable'], y=linedata['value']))
     linefig.update_layout(
         height =300,
         template='vizro_dark',
         showlegend=False,
         margin=dict(t=50, l=10, b=30, r=10),

         title = f"Migrants living in {region}",
         
         )
    
    
     return dcc.Graph(figure = linefig)



# Dash app layout (Keep as is)
geojson_style_function = assign("function(feature) { return feature.properties.style; }")
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,  dbc_css, vizro_bootstrap])
app.layout = dbc.Container([html.Div([
    html.H1("Migration by region july 2024"),
    dbc.Row([
        dbc.Col([
            select_region, # Updated title,
            
            
            ], width=6),
        dbc.Col([dbc.Col(modal)])
        
        ], style={'display':'flex'}),

    dbc.Row([
    dbc.Col([ html.Div(id='region-kpi')]),
    dbc.Col([
        html.Div(id='region-map')
    ])
    ])
    ])

])


#Region will only be used as origin, at least as first.

@app.callback(
    #[Output('sankey-diagram', 'figure'),
     Output('region-map', 'children'),
     Output('region-kpi', 'children'),
     Output("trend-chart","children"),
     Input('region-dropdown', 'value')
)

def update_map(selected_region):
    
    region_dots = [
        dl.CircleMarker(
            center=coords,
            radius=10 if selected_region == region else 6,
            color="white",
            fillColor="white" if selected_region == region else "yellow",
            fillOpacity=1 if selected_region == region else .7,
            children=[dl.Tooltip(region)],
        )
        for region, coords in region_centroids.items()
    ]
    

    
    
    #filter migration data on selected region and year. Selected region as origin
    
    dff_migration = df_migration[df_migration['Destination'] == selected_region]
    
    #draw lines from origin to destination
    
    destination_latlon = region_centroids.get(selected_region)
    #print(destination_latlon)
    
    polylines = []
    for index,row in dff_migration.iterrows():
        #print(row['Origin'])
        origin_latlon =  region_centroids.get(row['Origin'])
        #print(origin_latlon)
        
        region_poly = dl.Polyline(positions=[destination_latlon, origin_latlon], weight=1)
        #patterns = [dict(offset="100%", repeat="0", arrowHead=dict(pixelSize=15, polygon=False, pathOptions=dict(stroke=True)))]
        #arrow = dl.PolylineDecorator(children=polyline, patterns=patterns)
        
        polylines.append(region_poly)
        
    
    
    
    
    
    region_map = dl.Map(center=(20, 0), zoom=2, id = "region-map", children=[
        *region_dots,
        *polylines,
        
         dl.TileLayer(
     url="https://api.maptiler.com/maps/basic/{z}/{x}/{y}.png?key=YNHV8a5LLoD02hxoJDnD",
     attribution="&copy; MapTiler & OpenStreetMap contributors"
 ),
        dl.GeoJSON(data=geojson_data, id="geojson", options=dict(style=geojson_style_function)),
                
    ], style={'height': '85vh', 'width': '100%'})
    
    
    
    return  region_map, create_region_info_card(selected_region,dff_migration), create_trend_region(selected_region, dff_migration)

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






if __name__ == "__main__":
    app.run_server(debug=True)
