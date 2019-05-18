## Amazon Scrapper
Amazon Scrapper: A script to scrap products and reviews data from amazon.fr and export it to csv files 

## Requirements

| Software  |
| ----------------- | 
|    bs4,  selenuim | 

```
virtualenv --python=python3 env
source env/bin/activate
pip install -r requirements.txt
```

For selenuim to execute properly, you should have a web browser and it's driver available in the `PATH` environment variable.

Here's the instruction for installing Google Chrome driver on Ubuntu

```
wget https://chromedriver.storage.googleapis.com/74.0.3729.6/chromedriver_linux64.zip
unzip chromedriver_linux46.zip
sudo cp chromedriver /usr/local/bin/
```

If you don't have Google Chrome run the following:

```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
```

## How to use ?
The script has a small command line interface here's the help (`python scrapeProduct.py --help`):
```
usage: scrapeProduct.py [-h] [--category-url CATEGORY_URL]
                             [--output-products OUTPUT_PRODUCTS]
                             [--output-reviews OUTPUT_REVIEWS] [--quite]
                             [--debug]

Parse Amazon category page, get all products and reviews and write them to csv
files

optional arguments:
  -h, --help            show this help message and exit
  --category-url CATEGORY_URL
                        The home page of the category to be scrapted
  --output-products OUTPUT_PRODUCTS
                        Where to export the products. Default to products.csv
  --output-reviews OUTPUT_REVIEWS
                        Where to export the reviews. Default to reviews.csv
  --quite               Scrap only one product and one review for each parsed
                        web-page. Defaults to false
  --debug               Activate debug log messages. Defaults to false
```

Note that all the arguments are optional, The most useful argument is `quite` it enables you to test the script **quietly**

```bash
python scrapeProduct.py --quite
```
Data will be exported in two files:

* `products.csv`: contains information about products: name, asin, average_rate and total number of reviews
* `reviews.csv`: contains information about user reviews for a given product: asin, username, rate, date, short title, full title
