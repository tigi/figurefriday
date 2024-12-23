from dash import Dash, html,  Input, Output,  callback
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
#from data.dataprocessing2 import etl_data #data etl
#from components.theme import select_colormode #import light dark mode
from dash_bootstrap_templates import load_figure_template
# adds  templates to plotly.io
load_figure_template(["sandstone", "sandstone_dark"])
import plotly.express as px
import json
import pandas as pd


#this is not relevant for this assignment but I'm putting this all in one file
#without much thinking.

def select_colormode():


    
    
    color_mode_switch =  html.Span(
    [
        dbc.Label(className="fa fa-moon", html_for="color-mode-switch"),
        dbc.Switch( id="color-mode-switch", value=False, className="d-inline-block ms-1", persistence=True),
        dbc.Label(className="fa fa-sun", html_for="color-mode-switch"),
    ]
    )
    return color_mode_switch


# 1 DATAPROCESSING

def etl_data():

    df = df = pd.read_csv("https://raw.githubusercontent.com/plotly/Figure-Friday/refs/heads/main/2024/week-50/CMO-Historical-Data-Monthly.csv")
    
    df = df.drop([0, 1])  # drop sub headers
    
    #pick last 13 months = 12 times MoM
    df = df.tail(13)
    #it's so easy to copy from adam :-)
    df.rename(columns={'Unnamed: 0': 'Time'}, inplace=True)
    df['Time'] = pd.to_datetime(df['Time'], format='%YM%m')
    
    #remove a few columns with empty values, because replace three dots later, keeps giving errors
    removelist = ['Barley','Sorghum', 'Shrimps, Mexican', 'Phosphate rock']
    df = df.drop(removelist, errors = 'ignore', axis = 1)
    
    
    #create a list of all columnnames with values (except time)
    allcolumns = df.columns.values.tolist()[1:]
        
    dfp = pd.melt(df, id_vars=['Time'], value_vars=allcolumns)\
        .rename(columns={'variable':'Product','value':'Price'})\
            .sort_values(by=['Product','Time'], ascending=[ True, True])    
    
    #add price previous month
    dfp['Price'] = dfp['Price'].astype(float)
    dfp['Price pm'] =dfp['Price'].shift(1).astype(float)
    dfp['MoM price'] = round(100 * ((dfp['Price'] - dfp['Price pm'])/dfp['Price pm']),1).astype(float)

        
    dfp = dfp.loc[dfp['Time'] != '2023-11-01']
    
    return dfp




#read all data and pivot
df = etl_data()







app = Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE, dbc.icons.FONT_AWESOME])

#this should be filter last month numbers but for the sake of time
#filter 2024-11-01, lazy

dfgrid = df.loc[df['Time'] == '2024-11-01'].copy()  



##Try to create the mom sparkle line


dfgrid["graph"] = ''

for i, r in dfgrid.iterrows():
    filterDf = df[df["Product"] == r["Product"]]
    
    # #ymax and ymin and the x value,
    #no idea how to get this into the sparkle
    #with a correct marker syntax, giving up.
    ymax = filterDf['Price'].max()
    xmax = filterDf.loc[filterDf['Price'].idxmax(),'Time']
    ymin = filterDf['Price'].min()
    xmin = filterDf.loc[filterDf['Price'].idxmin(),'Time']
       
    
 
    fig = px.line(
       filterDf,
       x="Time",
       y="Price"
   )

    fig.update_layout(
       showlegend=False,
       yaxis_visible=False,
       yaxis_showticklabels=False,
       xaxis_visible=False,
       xaxis_showticklabels=False,
       margin=dict(l=0, r=0, t=0, b=0),
       template="plotly_white",
   )

    fig.add_scatter(x=[xmax, xmin],
                    y=[ymax, ymin], 
                    mode='markers', marker=dict(color=['green', 'red'], size=7))        
        
    
    dfgrid.at[i,'graph'] = fig
    
#columnheadernames should be dynamically
maxmonth_label = dfgrid['Time'].max()
prevmonth_label =  dfgrid['Time'].max()+ pd.DateOffset(months=-1)

columnDefs = [

  {
      "headerName": "Product",
      "field": "Product",
      
      "filter": True
  },
  {"headerName": "Avg Price (" + maxmonth_label.strftime('%b %Y') + ")", 
   "type": "rightAligned",
   "field": "Price",
   "valueFormatter": {"function": """d3.format("($,.2f")(params.value)"""},
   },
  {
      "headerName":"Avg Price (" + prevmonth_label.strftime('%b %Y') + ")",
      "type": "rightAligned",
      "field": "Price pm",
      "valueFormatter": {"function": """d3.format("($,.2f")(params.value)"""},
      "filter": True,
  },
   {
    "headerName": "Increase/decrease %",
  "type": "rightAligned",
  "field": "MoM price",

  "valueFormatter": {"function": """d3.format("(.1f")(params.value)"""},
  "filter": True,
  'cellStyle': {
            # Set of rules
            "styleConditions": [
                {
                    "condition": "params.value >= 3",
                    "style": {"backgroundColor": "mediumaquamarine"},
                },
                {
                    "condition": "params.value <= -3",
                    "style": {"backgroundColor": "lightcoral"},
                },
            ],
            # Default style if no rules apply
            "defaultStyle": {"backgroundColor": "white"},
        }
  
},
                                                
{
"field": "graph",
"cellRenderer": "DCC_GraphClickData",
"headerName": "MoM Avg.Price (last 12 months)",
"maxWidth": 300,
"minWidth": 300,

                                                }
  ]


defaultColDef = {
  "resizable": True,
  "sortable": True,
  "editable": True,
  }




# Main layout
app.layout = dbc.Container([

        dbc.Row([
            html.Div(html.H1('Commodity market prices until Dec. 2024'), className='col-md-12'),
            #html.Div(select_colormode(), className='col-md-6')                   
            ], style={"marginTop":"2rem"}),




            
        html.Div([
                dag.AgGrid(
                    id="custom-component-graph-grid",
                    columnDefs=columnDefs,
                    rowData=dfgrid.to_dict("records"),
                    columnSize="autoSize",
                    defaultColDef=defaultColDef,
                    dashGridOptions={"rowHeight": 48},
                    style={"height": "700px"}
                    ), 
                html.Div(id="custom-component-graph-output")
                
                ])              


        ])#end of container

    


@callback(
    Output("custom-component-graph-output", "children"),
    Input("custom-component-graph-grid", "cellRendererData"),
    
    
)
def graphClickData(d):
    return json.dumps(d)

if __name__ == "__main__":
    app.run_server(debug=True)
