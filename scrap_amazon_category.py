from collections import namedtuple
from bs4 import BeautifulSoup
import logging
import sys
import csv
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import argparse



AMAZON_BASE = 'https://www.amazon.fr'
"""The base url of amazon, this is used when found eelative paths during parsing"""

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
REVIEW_FIELED_NAMES = ['asin', 'username', 'rate', 'date', 'short_title', 'full_title']
PRODUCT_FIELED_NAMES = ['name', 'asin', 'price', 'average_rate', 'total_reviews']


Review = namedtuple('Review', REVIEW_FIELED_NAMES)
"""A review structure as requested in the test"""

Product = namedtuple('Product', PRODUCT_FIELED_NAMES)
"""A product structure as requested in the test"""


def parse_args():
    """The command line arguments parser
    The parser expects the following arguments, run `python scrap_amazon_category.py --help`
    ```
      --category-url   : The home page of the category to be scrapted
      --output-products: OUTPUT_PRODUCTS: Where to export the products. Default to None
      --output-reviews : Where to export the reviews. Default to None
      --quite          : Scrap only one product and one review for each parsed web-page
      --debug          : Activate debug log messages
    ```
    """
    parser = argparse.ArgumentParser(description='Parse Amazon category page, get all products and reviews and write them to csv files')
    parser.add_argument('--category-url', type=str,
                        default='https://www.amazon.fr/s?srs=14868146031&bbn=13910691&rh=n%3A13921051%2Cn%3A%2113910671%2Cn%3A13910691%2Cn%3A598657031&dc&fst=as%3Aoff&qid=1551293624&rnid=13910691&ref=sr_nr_n_0',
                        help='The home page of the category to be scrapted')
    parser.add_argument('--output-products', type=str, default='products.csv',
                        help='Where to export the products. Default to None')
    parser.add_argument('--output-reviews', type=str, default='reviews.csv',
                        help='Where to export the reviews. Default to None')
    parser.add_argument('--quite', action='store_true',
                        help='Scrap only one product and one review for each parsed web-page')
    parser.add_argument('--debug', action='store_true',
                        help='Activate debug log messages')
    return parser.parse_args()



def parse_review(soup):
    """Parse an amazon user review

    Arguments:
    ----------
    soup: the HTML content of the review, it should at least contain one element having as class attributes:
        - one `a-profile-name`: the username of the reviewer. Example: "AndAb"
        - one `a-icon-alt`: the rate given by the reviewer formatted as "x sur 5 étoiles". Example: "1,0 sur 5 étoiles"
        - one `review-date`: the date of the review formatted as "DD M YYYY". Example: "3 septembre 2018"
        - one `review-title`: the short title of the review. Example: "Produit non adéquat\n"
        - one `a-row a-spacing-small review-data`: the full content of the review.
            Example: "Impossibilité de mettre en service le système Arlo Pro 2 car le signal que diffuse......"
    type: BeatifulSoup

    return: an object containing the extracted review attributes
    type: Review
    """
    username = soup.find(class_='a-profile-name')
    rate = soup.find(class_='a-icon-alt')
    short_title = soup.find(class_='review-title')
    date = soup.find(class_='review-date')
    full_title = soup.find(class_='a-row a-spacing-small review-data')
    rate = re.findall(r'(\d\,\d).*', rate.text)[0]
    return username.text, rate, date.text, short_title.text.strip(), full_title.text.strip()



def get_next_page_url(soup):
    "Returns the next page url or None if next button doesn't exits or disabled(the last page)"
    # TODO: use find instead
    # TODO: use urllib.parse module to join and manipulate urls
    last = soup.select_one('.a-last')
    n = None
    if last:
        if 'a-disabled' not in last.attrs['class']:
            a = last.find('a', href=True)
            if a:
                n = AMAZON_BASE + a['href']
    return n


def get_page_using_selenuim(url, timeout=15, wait_for='body'):
    """Get an HTML page using `selenuim`, when using `selenuim` we are using a
       real browser and thus even JavaScript is executed
    :param url the URL of the page to get.
    :type str
    :param timeout How much seconds to wait for the :param:`~wait_for` element to appear before raising a TimeoutException
    :type int
    :param wait_for: a CSS selector to wait for
    :type str, deafults to "body"
    :return the source of the web page
    :type str
    :raise TimeoutException if timeout is elapsed and `wait_for` element is not present in the page
    """
    # create chrome driver to access the web-page
    # note: accessing the web page using requests is not sufficient, I think this is because the returned page from amazon
    #       contains JavaScript scripts that when executed render the products HTML information!
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    # get the page
    driver.get(url)
    #make sure the element that contains data consumption is loaded
    #this will raise an exception on timeout
    element_present = EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
    WebDriverWait(driver, timeout).until(element_present)
    return driver.page_source



def get_see_all_reviews_url(soup):
    """Get the "see all reviews" button url
    :param soup the page to search inside the next button
    :type BeautifulSoup
    :return the url of the "see all reviews" button, None if such button don't exists
    :type str
    """
    # TODO: use urllib.parse module to join and manipulate urls
    see_all_reviews_url = soup.find(attrs={'data-hook': 'see-all-reviews-link-foot'}, href=True)['href']
    base, params = see_all_reviews_url.split('?')
    amazon_added_suffix = '/ref=cm_cr_dp_d_show_all_btm'
    see_all_reviews_url = AMAZON_BASE + base + amazon_added_suffix + '?' + params
    return see_all_reviews_url



def parse_product(url, quite=False):
    """Parse the product information and reviews

    :param url the URL of the product page, the page should contain the following elements:
        - The product name at the id: `productTitle`
        - The product price at the selector: `#olp_feature_div >  #olp-sl-new .a-color-price`
        - The average rate stars at: `.averageCustomerReviews > .a-icon-alt`
        - The total number of reviews at: `.averageCustomerReviews > .acrCustomerReviewText`
        - the Amazon Product Code (ASIN) at a table row with text: `ASIN`.
              This field is optional, we can get it from the url if it's not found
    :type str
    :param quite Whether to extract all the reviews or just be quite and extract only one review for each parsed web-page
    :type quite, defaluts to False
    :return a tuple (product, reviews) a product and a list of it's reviews
    :type tuple (product, reviews), product: Product, reviews: a list of Review
    """
    logging.info('Parsing product from {}'.format(url))

    html = get_page_using_selenuim(url)
    soup = BeautifulSoup(html, 'lxml')
    name = soup.find(id='productTitle').text.strip()
    price = soup.select_one('#olp_feature_div >  #olp-sl-new .a-color-price')
    if price:
        price = price.text
    else:
        price = None
    average_costumer_reviews = soup.find(id='averageCustomerReviews')
    average_rate = average_costumer_reviews.find(class_='a-icon-alt').text
    average_rate = re.findall(r'(\d\.\d).*', average_rate)[0]
    total_reviews = average_costumer_reviews.find(id='acrCustomerReviewText').text
    total_reviews = re.findall(r'(\d+).*', total_reviews)[0]
    asin = soup.find(text='ASIN')
    # some products don't have the technical spec table, is so we get ASIN from url
    if asin:
        asin = asin.next_element.text
    else:
        asin = url.split('/')[5]
    see_all_reviews_url = get_see_all_reviews_url(soup)
    reviews = []
    page_number = 1
    # initialise next with the first page of the reviews
    next = see_all_reviews_url
    while next:
        html = get_page_using_selenuim(next)
        soup = BeautifulSoup(html, 'lxml')
        reviews_urls = soup.find_all(class_= 'a-section review aok-relative')
        if quite:
            reviews_urls = reviews_urls[:1]
        logging.info('Getting {} review from page {}: {}'.format(len(reviews_urls), page_number, next))
        r = [Review(asin, *parse_review(url)) for url in reviews_urls]
        reviews = reviews + r
        next = get_next_page_url(soup)
        page_number = page_number + 1

    product = Product(name, asin, price, average_rate, total_reviews)
    logging.info('Parsed successfully name={}, asin={}, rate={}, total_reviews={}'.format(product.name, product.asin, product.average_rate, product.total_reviews))
    return product, reviews


def parse_amazon_category(url, quite=False):
    """Parse an Amazon category's products and reviews

    :param url the URL of the home page of the cateory, the page should contain a list of products and a pagination
        - the list of products should have `.s-result-list`, each product should have a link leading to it's page at:
        `.s-result-list > .s-result-item .sg-row span[data-component-type="s-product-image"] a`
        - the pagination should have a next button with class: `.a-last`
    :type str
    :param quite Whether to extract all products and all reviews or just be quite and extract only one product and one review for each parsed web-page
    :type quite, defaluts to False
    :return a tuple (products, reviews) a list of extracted products and reviews
    :type tuple (products, reviews), products: a list of Product, reviews: a list of Review
    """
    logging.info('Parsing amazon category from {}'.format(url))
    products = []
    reviews = []

    try:
        # initialise next with the first page
        next = url
        page_number = 1
        while next:
            html = get_page_using_selenuim(next)#, wait_for='.a-last')
            soup = BeautifulSoup(html, 'lxml')
            products_urls = soup.select('.s-result-list > .s-result-item .sg-row span[data-component-type="s-product-image"] a')
            products_urls = [AMAZON_BASE + a['href'] for a in products_urls]
            # if quite process only the first product
            if quite:
                products_urls = products_urls[:1]
            logging.info('Getting {} product from page {}: {}'.format(len(products_urls), page_number, next))
            for url in products_urls:
                p, r = parse_product(url, quite)
                products.append(p)
                reviews = reviews + r
            next = get_next_page_url(soup)
            page_number = page_number + 1
    except KeyboardInterrupt:
        logging.warning('Scrapping interpreted, we have only {} products and {} reviews'.format(len(products), len(reviews)))
        return products, reviews

    return products, reviews



def export_products(products, products_file):
    """Export a list of products to a csv file
    The fields written are :const:`~PRODUCT_FIELED_NAMES`
    :param products a list of products to be exported
    :type list of Reveiw objects
    :param products_file path where to write the csv
    :type str
    """
    logging.info('Exporting {} products to {}'.format(len(products), products_file))
    with open(products_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=PRODUCT_FIELED_NAMES)
        writer.writeheader()
        writer.writerows([p._asdict() for p in products])
    logging.info('Successfully exported {} products to {}'.format(len(products), products_file))


def export_reviews(reviews, reviews_file):
    """Export a list of reviews to a csv file
    The fields written are :const:`~REVIEW_FIELED_NAMES`
    :param reviews a list of reviews to be exported
    :type list of Reveiw objects
    :param reviews_file path where to write the csv
    :type str
    """
    logging.info('Exporting {} reviews to {}'.format(len(reviews), reviews_file))
    with open(reviews_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELED_NAMES)
        writer.writeheader()
        writer.writerows([r._asdict() for r in reviews])
    logging.info('Successfully exported {} reviews to {}'.format(len(reviews), reviews_file))


if __name__ == '__main__':
    args = parse_args()
    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(stream=sys.stdout, level=level, format='%(levelname)s %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    if args.quite:
        logging.warning('Scrapping launched with quite mode, this is intended for testing purpose only as it will get one element (review/product) from each parsed page')
    products, reviews = parse_amazon_category(args.category_url, args.quite)
    # export products only if it's not empty
    if products:
        export_products(products, args.output_products)
    # export reviews only if it's not empty
    if reviews:
        export_reviews(reviews, args.output_reviews)
