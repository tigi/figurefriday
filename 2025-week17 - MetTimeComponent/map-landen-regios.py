import dash
import dash_leaflet as dl
from dash import html
import requests
import pycountry
from dash_extensions.javascript import assign
import json
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import pandas as pd


# stylesheet with the .dbc class to style  dcc, DataTable and AG Grid components with a Bootstrap theme
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
# if using the vizro theme
vizro_bootstrap = "https://cdn.jsdelivr.net/gh/mckinsey/vizro@main/vizro-core/src/vizro/static/css/vizro-bootstrap.min.css?v=2"

# default dark mode
#pio.templates.default = "vizro_dark"
load_figure_template(["vizro", "vizro_dark"])


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


country_transparancy = .8

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



#READ THE REAL DATA
df_migration = pd.read_csv('migration_region.csv')

#start
origin='Western Africa'
period='jul2024'

print(df_migration[df_migration['Origin'] == origin][period])



# Dash app layout (Keep as is)
geojson_style_function = assign("function(feature) { return feature.properties.style; }")
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,  dbc_css, vizro_bootstrap])
app.layout = html.Div([
    html.H1("Country Boundaries Coloured by UN Subregion"), # Updated title
    dl.Map(center=(20, 0), zoom=2, children=[
        
#         dl.TileLayer(
#     url="https://api.maptiler.com/maps/basic/{z}/{x}/{y}.png?key=YNHV8a5LLoD02hxoJDnD",
#     attribution="&copy; MapTiler & OpenStreetMap contributors"
# ),
        dl.GeoJSON(data=geojson_data, id="geojson", options=dict(style=geojson_style_function)),
        *region_dots                  
    ], style={'height': '85vh', 'width': '100%'})
])









if __name__ == "__main__":
    app.run_server(debug=True)
