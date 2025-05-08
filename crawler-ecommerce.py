# pip3 install requests beautifulsoup4
import requests
from bs4 import BeautifulSoup
import re
import csv

target_url = "https://www.scrapingcourse.com/ecommerce/"

# initialize the list of discovered URLs
urls_to_visit = [target_url]

# set a maximum crawl limit
max_crawl = 20

# create a regex pattern for product page URLs
url_pattern = re.compile(r"/page/\d+/")

# define a list to collect scraped data
product_data = []

def crawler():
    # set a crawl counter to track the crawl depth
    crawl_count = 0
 
    while urls_to_visit and crawl_count < max_crawl:

        # get the page to visit from the list
        current_url = urls_to_visit.pop(0)

        # request the target URL
        response = requests.get(current_url)
        response.raise_for_status()

        # parse the HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # collect all the links
        for link_element in soup.find_all("a", href=True):
            url = link_element["href"]

            # convert links to absolute URLs
            if not url.startswith("http"):
                absolute_url = requests.compat.urljoin(target_url, url)
            else:
                absolute_url = url

            # ensure the crawled link belongs to the target domain and hasn't been visited
            if (
                absolute_url.startswith(target_url)
                and absolute_url not in urls_to_visit
            ):
                urls_to_visit.append(absolute_url)

        # extract content only if the current URL matches the regex page pattern
        if url_pattern.search(current_url):
            # get the parent element
            product_containers = soup.find_all("li", class_="product")

            # scrape product data
            for product in product_containers:
                data = {
                    "Url": product.find("a", class_="woocommerce-LoopProduct-link")[
                        "href"
                    ],
                    "Image": product.find("img", class_="product-image")["src"],
                    "Name": product.find("h2", class_="product-name").get_text(),
                    "Price": product.find("span", class_="price").get_text(),
                }

                # append extracted data
                product_data.append(data)

        # update the crawl count
        crawl_count += 1

# execute the crawl
crawler()

# save data to CSV
csv_filename = "products.csv"
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["Url", "Image", "Name", "Price"])
    writer.writeheader()
    writer.writerows(product_data)
