from concurrent.futures import ThreadPoolExecutor
import feedparser
from dataclasses import dataclass, field
from typing import Literal
from bs4 import BeautifulSoup
import requests
from settings import MAX_THREADS
import logging
from urllib.parse import urlparse, urljoin

'''
    For most RSS/ATOM feeds that don't require JavaScript
'''



@dataclass
class WebFeed:
    '''
        Parent class for all WebFeeds
    '''
    base_url: str = field(default_factory=str)
    path: str = field(default_factory=str)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    parser_type: Literal["html", "xml"] = "html"
    

    def get_request(self, url) -> bytes:
        '''
            Get an HTTP request's content. Return none if any errors
        '''
        parsed = urlparse(url)

        if not parsed.netloc: # path, not url
            url = urljoin(self.base_url, url)
        elif not parsed.scheme: # missing scheme
            url = f"https://{url}"

        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.content
        except requests.Timeout:
            logging.debug(f"Timeout on {url}. Skipping...")
        except requests.RequestException as e:
            logging.debug(f"Request failed on {url}: {e}")
        return None
    

    def get_urls(self) -> set[str]:
        '''
            From the base_url given, get all of the RSS or ATOM web feeds
        
            Returns a set of RSS/ATOM links
        '''
        content = self.get_request(f"{self.base_url}{self.path}")

        if not content:
            return set()
        
        soup = BeautifulSoup(content, f'{self.parser_type}.parser')
        links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
        links = [link for link in links if 'rss' in link or 'atom' in link or 'feed' in link]
        return set(links)
    

    def check_feed_for_word(self, words: list[str], entries) -> list:
        '''
            In every feed, check if the title of the entry has any keywords given
        
            Returns a list of entries
        '''
        keyword_entries = []
        if not words or not entries:
            return []
            
        for entry in entries:
            desc = entry['description']
            if not desc:
                desc = entry.get('summary') if entry.get('summary') else ""
                
            if any(word in entry['title'].lower() or word in desc for word in words):
                keyword_entries.append(entry)
        return keyword_entries
    

    def check_entry_for_word(self, words: list[str], content) -> bool:
        '''
            In every entry, check if the body of the article has any keywords given
        
            Returns boolean
        '''
        # parse the news article itself
        soup = BeautifulSoup(content, 'html.parser')
        page_text = soup.body.get_text().lower() if soup.body else ""
        if any(word in page_text for word in words): # check to ensure there is talk of keywords within
            return True
        return False
    
    
    def get_webfeed(self, title_words: list[str], feed_words: list[str]) -> list[dict]:
        '''
            Get all data from the webfeed links in base_url
        
            Returns a list of dictionaries of the title and links corresponding to the keywords
        '''
        print(f'Processing {self.base_url}{self.path}...')
        urls = self.get_urls()
        if not urls or not title_words: 
            return []
        news_data = []
        seen_links = set()
        
        # get all feed entries 
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            all_entries = list(executor.map(self.get_request, urls))
            
        # parse through all webfeed links and look for keywords
        for entry in all_entries:
            if not entry:
                continue
            
            # get feed data (dict of items/entries)
            feed = feedparser.parse(entry)
            entries = getattr(feed, "entries", None) or \
                getattr(feed.feed, "items", None) or \
                getattr(feed.feed, "channel", {}).get("item", []) or \
                feed.get("items", [])
            
            if not isinstance(entries, list):
                logging.debug(f"Unexpected format for entries: {type(entries)}. Skipping...")
                continue
            if not entries:
                logging.debug(f"No entries found. Skipping...")
                continue
            
            keyword_entries = self.check_feed_for_word(title_words, entries)
            
            # get all links, titles, and content via multithreading for faster iteration
            links = []
            titles = []

            for entry in keyword_entries:
                link = entry.get("link")
                if not link:
                    link = entry.get("id") if entry.get("id") else entry.get("guid")
                logging.debug(f'link processed: {link}')
                links.append(link)
                titles.append(entry['title'])

            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                contents = set(executor.map(self.get_request, links))
                
            # for each entry inside of the webfeed that fits the initial keywords, look for secondary keywords
            for title, link, content in zip(titles, links, contents):
                if not content:
                    continue 

                if link in seen_links:
                    continue
                
                if self.check_entry_for_word(feed_words, content):
                    news_data.append({
                        'Title': title,
                        'Link': link
                    })
                    seen_links.add(link)
                
        return news_data
    
