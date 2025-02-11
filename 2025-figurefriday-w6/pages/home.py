# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 15:01:21 2025

@author: win11
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, callback_context, callback, register_page
import dash_ag_grid as dag
from data.data_functions import prepare_df_base #data etl

register_page(__name__, path="/")

#import data and do some basic drop and typeconversions

df = prepare_df_base()



def create_listgroup(frame, subject):
    #key is the subject and decidec how to style the row output

   
    listChildren = []
    
    for i, r in frame.iterrows():
        
        match subject:
            case 'author-titles':
                listChildren.append(dbc.ListGroupItem(f"{r['author']} ({r['title']} titles)"))
            case 'author-weeks':
                listChildren.append(dbc.ListGroupItem(f"{r['author']} ({r['year-week']} mentions)"))
            case 'publisher-titles':
                    listChildren.append(dbc.ListGroupItem(f"{r['publisher']} ({r['title']} titles)"))
            case 'publisher-weeks':
                    listChildren.append(dbc.ListGroupItem(f"{r['publisher']} ({r['year-week']} mentions)"))

            # If an exact match is not confirmed, this last case will be used if provided
            case _:
                listChildren.append(dbc.ListGroupItem(r))
        
        
        
       
        
        
    listgroup = dbc.ListGroup( children = listChildren, flush=True, numbered=True)
     
    
    return listgroup


def create_card(frame,subject,df_filtered):
    #this card is used to display the top3 's on cards.
    #convert frame to ordered list, frame is for example top 3 authors
    #if you omit images, you omit df_filtered from the input vars.
    
    
    subject_dict_cardtitles  = {'author-titles': 'Most bestsellers listed', 'author-weeks':'Most mentions', \
                                'publisher-titles': 'Most bestsellers listed', 'publisher-weeks':'Most mentions'}
    subject_dict_explanations = {'author-titles': 'The author on top had most different books in the bestseller list.', \
                                 'author-weeks':'The author on had most listings with a title (or more) on the bestseller lists.', \
                                  'publisher-titles': 'The publisher on top had most different books in the bestseller list.', \
                                 'publisher-weeks':'The publisher on top had most titles mentioned in the bestseller lists.',   
                                     }

    
    
    list_group = create_listgroup(frame, subject)
    
    #function, get first image for the top 1 author in this case
    #frame author.iloc[0] is the first author in top, thus author on no. 1
    #frames do not have an image, so filtering the df_filtered, gets the first image url for this author
    #this is maybe not the bookcover for the most succesful book, just the img cover which comes first
    #in the df.
    
    if (subject in ['author-titles','author-weeks']):       
    
        first_image = df_filtered['image_url'].loc[df_filtered['author']== frame['author'].iloc[0]].iloc[0]
    else:
        first_image = df_filtered['image_url'].loc[df_filtered['publisher']== frame['publisher'].iloc[0]].iloc[0]
    
    
    
    
    #get_random_image_number1()
    card = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    dbc.CardImg(
                        src=first_image,
                        className="img-fluid rounded-start",
                    ),
                    className="col-md-4",
                ),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H2(subject_dict_cardtitles.get(subject), className="card-title"),
                            list_group,
                            html.Small(subject_dict_explanations.get(subject),className='card-text text-muted')
                            
                        ]
                    ),
                    className="col-md-8",
                ),
            ],
            className=" g-0 d-flex align-items-top",
        )
    ]
   
   
    )

    return card


def create_basic_card(subject, df_filtered):
    
    #this card is for the left part of the row, it maybe has an explanation
    #it has a button which serves as the menu and links to a details page
    #with more overall statistics, subject is the fieldname in the df_filtered
    text_dict = {'author': 'authors', 'publisher': 'publishers'}
    
    number_of_weeks_selected = df_filtered['published_date'].nunique()
    #distinct something
    distinct_something = df_filtered[subject].nunique()

    #distinct_titles = df_filtered['title'].nunique()
    
    
    
    
    basic_card = dbc.Card(
    dbc.CardBody(
        [
            
            html.P(
                f"During the {number_of_weeks_selected} weeks you selected:",
                className="card-text",
            ),
            html.H2( f"{distinct_something} different {text_dict.get(subject)}"),
            html.P('had a book on the NYT bestsellerlist',className="card-text"),
            dbc.Button(f"Dive into {text_dict.get(subject)}", href = f"/{text_dict.get(subject)}",  color="info", size="lg", className="me-1")
        ]
    ), className='col-md-12'
)


    return basic_card








layout = html.Div([
         html.Div(id='authorlayout'),
         html.Div(id='publisherlayout')

         ])





@callback(
    Output('publisherlayout', 'children'),
    Input("store_df", "data"))

def content_layout_publisher (ourstore):
    
   df_filtered = pd.DataFrame(ourstore) 
   #print(df_filtered.head(20))
   
   #PUBLISHERS
   
   publisher_diff_books = df_filtered.groupby(['publisher'])['title'].nunique().reset_index()
   #top 3 authors with most different titles in list
   publisher_different_titles_top3 = publisher_diff_books.nlargest(3, ['title']) 
   publisher_maxweeks = df_filtered.groupby(['publisher'])['year-week'].count().reset_index()
   #top3 publisher weeks in listpub
   publisher_weeks_top3 = publisher_maxweeks.nlargest(3, ['year-week']) 
   
   
   
   
   publisherlayout = dbc.Row([
               #kpi publishers general, basic card data are calculated in basic card setup
               dbc.Col(create_basic_card('publisher',df_filtered), className='col-md-3'),
               dbc.Col(html.Img(src='assets/images/curltje.png',style={'maxWidth':'80%'}),className = 'col-md-1',style={'alignSelf':'center'}),
     
               #top 3 authors with most distinct titles
               dbc.Col(create_card(publisher_different_titles_top3,'publisher-titles', df_filtered), className=' col-md-4'),
               #top 3 authors most weeks in beststellers list in selected period
               dbc.Col(create_card(publisher_weeks_top3,'publisher-weeks',df_filtered), className='col-md-4')     
              
               ])

      
       

   return publisherlayout


@callback(
    Output('authorlayout', 'children'),
    Input("store_df", "data"),)

def content_layout_author(ourstore):
    
     
   df_filtered = pd.DataFrame(ourstore)
    
    #AUTHORS
    
   author_diff_books = df_filtered.groupby(['author'])['title'].nunique().reset_index()
   #top 3 authors with most different titles in list
   author_different_titles_top3 = author_diff_books.nlargest(3, ['title']) 


   #how many times was an author mentioned on the list 
   author_maxweeks = df_filtered.groupby(['author'])['year-week'].count().reset_index()
   #top3 author weeks in list

   author_weeks_top3 = author_maxweeks.nlargest(3, ['year-week']) 
   
   
   authorlayout = dbc.Row([
           #kpi authors general, basic card data are calculated in basic card setup
           dbc.Col(create_basic_card('author', df_filtered), className='col-md-3'),
           dbc.Col(html.Img(src='assets/images/curltje.png',style={'maxWidth':'80%'}),className = 'col-md-1',style={'alignSelf':'center'}),
           #top 3 authors with most distinct titles
           dbc.Col(create_card(author_different_titles_top3,'author-titles', df_filtered), className='col-md-4'),
           #top 3 authors most weeks in beststellers list in selected period
           dbc.Col(create_card(author_weeks_top3,'author-weeks',df_filtered), className='col-md-4')     
          
        

      ], style={'marginBottom':'2rem'})
       

   return authorlayout







