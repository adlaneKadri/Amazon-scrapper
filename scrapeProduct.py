#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Written as part of https://www.scrapehero.com/how-to-scrape-amazon-product-reviews-using-python/
from lxml import html
from json import dump,loads
from requests import get
import json
from re import sub
from dateutil import parser as dateparser
from time import sleep
from bs4 import BeautifulSoup

def scrape(amazon_url):
    soup = BeautifulSoup(amazon_url, "lxml")
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
    #1- get short title of the review
    Short_title_of_the_Review= url_product.split("/")[3]

    response = get(amazon_url, headers = headers, verify=False, timeout=30)
    #get the HTML page 
    htmlPage = response.text.replace('\x00','')
    parser = html.fromstring(htmlPage)
    ps = html.fromstring(response.content)
    #2-get product name
    PRODUCT_NAME = '//h1//span[@id="productTitle"]//text()'
    productName = parser.xpath(PRODUCT_NAME)
    
    #3-get stars : 
    rating = {}
    Rate = '//table[@id="histogramTable"]//tr'
    starts  = parser.xpath(Rate)
    for start in starts:
            extracted_start = start.xpath('./td//a//text()')
            if extracted_start:
                rating_key = extracted_start[0] 
                raw_raing_value = extracted_start[1]
                rating_value = raw_raing_value
                if rating_key:
                    rating.update({rating_key: rating_value})

    #4-get price 
    PRICE_ID = '//table//tr//td//span[@id="priceblock_ourprice"]//text()'
    product_price = parser.xpath(PRICE_ID)
    #print(product_price)
    
    #5- get Total Number of User Reviews for the Product
    numberReviews = '//a//span[@id="acrCustomerReviewText"]//text()'
    totalReviews  = parser.xpath(numberReviews)[0].split(" ")[0]
    #print(totalReviews)


    #6 Name of the User posting the Review
    nameUserReview = '//div//a[@id="bylineInfo"]//text()'
    nameUSER  = parser.xpath(nameUserReview)[0]
    #print(nameUSER)


    #7 Date of the Review 
    dateOfReview = '//tr[@class,'date-first-available']//td[contains(@class, 'value')]//text()'
    dateReview  = parser.xpath(dateOfReview)[0]
    print(dateReview)

    #8- get Amazon Product Code (ASIN)



    #return (set OF all this informations)




    





url_product  = "https://www.amazon.fr/Arlo-Pro-VMS4330P-100EUS-rechargeable-bi-directionnel/dp/B0777TMW1Y/"
url_product1 = "https://www.amazon.com/Imploding-Kittens-First-Expansion-Exploding/dp/B01HSIIFQ2/"
scrape(url_product)
