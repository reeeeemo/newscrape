import pandas as pd
from feeds.webfeeds import WebFeed
from feeds.jswebfeeds import RCMPWebFeed
import os
import time
from settings import MAX_THREADS
from concurrent.futures import ThreadPoolExecutor
import logging
import asyncio
from tkinter import *

# makes output if it doesnt exist as a folder
os.makedirs("output", exist_ok=True)

# Making all webfeeds into a variable
webfeeds = [
    WebFeed(base_url="https://www.canada.ca", path="/en/news/web-feeds.html"),
    WebFeed(base_url="https://www.cbc.ca", path="/rss/"),
    WebFeed(base_url="https://globalnews.ca", path="/pages/feeds/"),
    WebFeed(base_url="https://www.thestar.com", path="/site/static-pages/rss-feeds.html"),
]
js_webfeeds = [
    RCMPWebFeed(),    
]

async def fetch_nonjs_webfeeds(keywords: list[str], feedwords: list[str]):
    '''
        Schedules blocking function to run in a seperate thread (so code can run asynchrounsly)
        Returns a Coroutine that can be 'awaited' to get function output.
    '''
    def fetch_all_webfeeds():
        '''
            Getting all non-JS webfeed information that corresponds to the keywords and feedwords
            Returns a dictionary with info such as title of article, link
        '''
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            results = executor.map(lambda feed: feed.get_webfeed(keywords, feedwords), webfeeds)
        return [article for result in results for article in result] # flatten into one array
    return await asyncio.to_thread(fetch_all_webfeeds)


async def fetch_js_webfeeds(keywords: list[str], feedwords: list[str]):
    '''
        Getting all JS webfeed information that corresponds to the keywords and feedwords
        Returns a dictionary with info such as title of article, link
    '''
    tasks = [feed.get_webfeed(keywords, feedwords) for feed in js_webfeeds]
    results = await asyncio.gather(*tasks)
    return [article for result in results for article in result]

def get_user_keywords_input() -> (list[str], list[str]):
    '''
        Gets keywords and feedwords chosen from user. These will define which articles to collect
        Returns the pair of lists (keywords, feedwords)
    '''
    print('If multiple keyword entries, seperate with commas. These are optional. Case Insensitive.')
    entry = input('Please enter the keywords you wish to use to search in the article titles for: ')
    keyword_entries = [keyword.strip() for keyword in entry.split(',')]

    entry = input('Please enter the keywords you wish to use to search in the article body text: ') 
    feedword_entries = [keyword.strip() for keyword in entry.split(',')]
    
    return keyword_entries, feedword_entries

async def main():
    # start timer + get keywords and feedwords
    start_time = time.time()
    keywords, feedwords = get_user_keywords_input()
    print(f'Keywords: {keywords}\nFeedwords: {feedwords}')

    # get function tasks for our webfeeds, then asynchronously get them
    nonjs_task = fetch_nonjs_webfeeds(keywords, feedwords)
    js_task = fetch_js_webfeeds(keywords, feedwords)
    
    nonjs_results, js_results = await asyncio.gather(nonjs_task, js_task)
    news_data = nonjs_results + js_results


    # output to dataframe and get time taken
    if news_data:
        df = pd.DataFrame(news_data)    
        df.to_csv('output/news_articles.csv', index=False)
    else:
        logging.info('No articles found.')    
    
    logging.debug(df)
    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f'Elapsed time: {elapsed_time:.3f}s')

if __name__ == "__main__":
    asyncio.run(main())    