# -*- coding: utf-8 -*-
"""
Created on Sat Feb  8 11:13:23 2025

@author: win11
"""


#for webscraping
import requests
from bs4 import BeautifulSoup

url = 'https://www.nytimes.com/books/best-sellers/2025/01/05/combined-print-and-e-book-fiction/'
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
        print(f"Title: {title}")
        print(f"Image URL: {image_url}\n")
        
        
