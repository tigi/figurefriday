# -*- coding: utf-8 -*-
"""
Created on Sat Feb  8 10:47:05 2025

@author: win11
"""

import pandas as pd
#for webscraping
import requests
from bs4 import BeautifulSoup




def prepare_df_base():

    df_raw = pd.read_csv('NYT Fiction Bestsellers - Bestsellers.csv')
    #drop not necessary columns, bestseller date is dropped because published_date
    #and other data reflect the lists published on ny times website, last week in data:
    #https://www.nytimes.com/books/best-sellers/2025/01/05/combined-print-and-e-book-fiction/
    #way url is setup makes it easy to create a link to the page and maybe scrape image url's?
    #try if time left
    df_base= df_raw.drop(columns=['list_name','isbns', 'bestsellers_date'])
    #convert dates, bestsellers date will be used for filtering, no
    #weeknumber necessary
    df_base['published_date'] = pd.to_datetime(df_base['published_date'])    
    #yearcolumn makes rangeslider filling and filtering easier
    df_base['year'] = df_base['published_date'].dt.isocalendar().year.astype(int)  
    
    #create string label voor year - week, to use in visuals reference for easy on the eye
    #maybe filtering
    df_base['year-week'] = df_base['published_date'].dt.isocalendar().year.astype(str)  + \
        '-' + df_base['published_date'].dt.isocalendar().week.astype(str) 
    #scrape bookimages from nyt websites
    #scrape_book_images_from_web(df_base)
    
    #READ SCRAPER RESULTS FROM .CSV, DO IT ONLY ONCE, no extra index col
    df_scraper_raw = pd.read_csv('scraper_results.csv', index_col=0)
    df_scraper = df_scraper_raw.drop(columns = ['img_url','published_date'])
    
    #add scraper images to df on title = title
    
    df_return = df_base.merge(df_scraper, left_on='title', right_on='title',  suffixes=('', '_right'))
    #df_final = df_return.drop(['img_url','published_date_right']).reset_index()
    
    
    
    return df_return


def scrape_book_images_from_web(df):
    
    #SCRAPING STRATEGY
    #create copy of df with only distinct title and a published date, published date
    #can be used for the correct url to find the imag until you bump into a 404 (url not found)
    #groupby title, max published date because were going back in time when scraping.
    #published date is ordered ascending because the chances on a 404 (based on webdev
    #experience are greater the further you go back in time.)
    
    
    df_scraper = df.groupby('title')['published_date'].max().reset_index()
    df_scraper_final = df_scraper.sort_values(by=['published_date'], ascending = False)
    #order of scrape_dates are all the dates were going to construct a url and scrape
    order_of_scrape_dates = df_scraper_final['published_date'].unique()
    
    #loop through dates, construct url and start scraping,
    #start with 3 url's
    
    for datum in order_of_scrape_dates:
        #datum is a timestamp 
        y = str(datum.year)
        if(datum.month<10):
            m = '0'+str(datum.month) 
        else: 
            m=str(datum.month)
        if(datum.day<10):
            d = '0'+str(datum.day) 
        else: 
            d=str(datum.day)
        url = f"https://www.nytimes.com/books/best-sellers/{y}/{m}/{d}/combined-print-and-e-book-fiction/"
        #print(url)
        #url = 'https://www.nytimes.com/books/best-sellers/2025/01/05/combined-print-and-e-book-fiction/'
        response = requests.get(url)
    
        if response.status_code == 200:
            page_content = response.text
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
        
        soup = BeautifulSoup(page_content, 'html.parser')
     
        bestsellers = soup.find_all('article', attrs={'itemtype': 'https://schema.org/Book'})
    
    
        for book in bestsellers:
        
            title_tag = book.find('h3')
            image_tag = book.find('img', attrs={'role': 'presentation'})
            if title_tag and image_tag:
                title = title_tag.get_text(strip=True)
                image_url = image_tag['src']
                #print(f"Title: {title}")
                #print(f"Image URL: {image_url}\n")
                
                #add image to df_scraper_final, match on title
                
                df_scraper_final.loc[df_scraper_final['title'] ==title, 'image_url'] = image_url
        
    #write results to a csv file, so you only have to scrape once hopefully, depends on structured data
    df_scraper_final.to_csv('scraper_results.csv')
    #print(df_scraper_final.head(50))


    return 'gelukt'



