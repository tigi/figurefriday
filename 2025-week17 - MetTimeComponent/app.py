# -*- coding: utf-8 -*-
"""
Created on Fri Apr 25 18:16:05 2025

@author: win11
"""

import dash
from dash import html

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H3("Radial Sankey Chart"),
    html.Iframe(src="/assets/radial_sankey.html", width="100%", height="800px", style={"border": "none"})
])

if __name__ == '__main__':
    app.run(debug=True)
