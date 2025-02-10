import pandas as pd
from feeds.webfeeds import WebFeed
from feeds.jswebfeeds import RCMPWebFeed
import os
import time
from settings import MAX_THREADS
from concurrent.futures import ThreadPoolExecutor
import logging


### NON-JS WEBFEED CODE

# makes output if it doesnt exist as a folder
os.makedirs("output", exist_ok=True)

start_time = time.time()

# Making all webfeeds into a varialbe
news_data = []
webfeeds = [
    WebFeed(base_url="https://www.canada.ca", path="/en/news/web-feeds.html"),
    WebFeed(base_url="https://www.cbc.ca", path="/rss/"),
    WebFeed(base_url="https://globalnews.ca", path="/pages/feeds/"),
    WebFeed(base_url="https://www.thestar.com", path="/site/static-pages/rss-feeds.html"),
]

# Getting all webfeeds according to word(s)
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    results = executor.map(lambda feed: feed.get_webfeed(["drugs", "drug"], ["fentanyl"]), webfeeds)

news_data = [article for result in results for article in result] # flatten into one array

try:
    df = pd.DataFrame(news_data)
except Exception as e:
    logging.debug(f'Error converting to data: {e}')
    df = None


logging.debug(df)
end_time = time.time()
elapsed_time = end_time - start_time
print(f'Elapsed time: {elapsed_time:.3f}s')

# Print to a .csv file
df.to_csv('output/news_articles.csv')


### JS WEBFEED CODE 

start_time = time.time()
js = RCMPWebFeed()

news_data_js = js.get_webfeed(["drugs", "drug"], ["fentanyl"])

print(news_data_js)
end_time = time.time()
elapsed_time = end_time - start_time
print(f'Elapsed time: {elapsed_time:.3f}s')

