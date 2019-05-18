# web Scraping

## Requirements

In the following software and hardware list, you can run the code file in this repository.

| Software  | OS  |
| ------------------------------------ | ----------------------------------- |
| Python 2.x/3.x, bs4, selenium | Ubuntu 16.04 or greater |

* Use `pip3` to install this packages:

E.g.

```
pip3 install bs4
```
you’ll need to download `ChromeDriver` and add it to the bin path 

after downloading `chromeDriver`, enter in the download folder using `cd  path_of_the_folder`, and after execute the following command :  
```
sudo cp chromedriver /usr/bin
```

## scraping test 

To test the script you run **scrapeProduct.py**.

E.g.

```
python3 scrapeProduct.py
```

You will get as an output 2 files (reviews.csv: contains information about reviews of a product, products.csv: contain information about products)

#### PS 

this execution took me a long time, so I propose to launch the script by adding an attribute --quite just to retrieve the information of a single product of each page (it's just to see the final result)

run the script as the following : 
```
python3 scrapeProduct.py --quite
```
