import pandas as pd
import feedparser
from dataclasses import dataclass, field
from typing import Literal
from bs4 import BeautifulSoup
import requests

'''
    Parent class for all WebFeeds
'''
@dataclass
class WebFeed:
    base_url: str = field(default_factory=str)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    parser_type: Literal["html", "xml"] = "html"
    
    '''
        From the base_url given, get all of the RSS or ATOM web feeds
        
        Returns a set of RSS/ATOM links
    '''
    def get_urls(self) -> set[str]:
        try:
            response = requests.get(self.base_url,headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.Timeout:
            print(f'Timeout error: {self.base_url}. Skipping...')
            return set()
        except requests.RequestException as e:
            print(f'Error getting url {self.base_url}: {e}')
            return set()

        soup = BeautifulSoup(response.content, f'{self.parser_type}.parser')
        links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
        links = [link for link in links if 'rss' in link or 'atom' in link]
        return set(links)
    
    '''
        In every feed, check if the title of the entry has any keywords given
        
        Returns a list of entries
    '''
    def check_feed_for_word(self, words: list[str], entries) -> list:
        keyword_entries = []
        if not words or not entries:
            return []
            
        for entry in entries:
            if any(word in entry['title'].lower() for word in words):
                keyword_entries.append(entry)
        return keyword_entries
    
    '''
        In every entry, check if the body of the article has any keywords given
        
        Returns boolean
    '''
    def check_entry_for_word(self, words: list[str], link) -> bool:
        try:
            response = requests.get(link, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.Timeout:
            print(f'Timeout error: {link}. Skipping...')
            return False
        except requests.RequestException as e:
            print(f'Error getting entry {link}: {e}')
            return False
        
        # parse the news article itself
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.body.get_text().lower() if soup.body else ""
        if any(word in page_text for word in words): # check to ensure there is talk of keywords within
            return True
        return False
    
    def get_webfeed(self, title_words: list[str], feed_words: list[str]) -> list[dict]:
        urls = self.get_urls()
        if not urls or not title_words: # if there are no title words to search for, too much data
            return []
        
        news_data = []
        seen_links = set()
        for url in urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=5)
                response.raise_for_status()
            except requests.Timeout:
                print(f"Timeout on {url}. Skipping...")
                continue
            except requests.RequestException as e:
                print(f"Request failed on {url}: {e}")
                continue
            
            # get feed data (dict of items/entries)
            feed = feedparser.parse(response.content)
            
            entries = getattr(feed, "entries", None) or \
                getattr(feed.feed, "items", None) or \
                getattr(feed.feed, "channel", {}).get("item", []) or \
                feed.get("items", [])
            
            if not isinstance(entries, list):
                print(f"Unexpected format for entries: {type(entries)}. Skipping...")
                continue

            if not entries:
                print(f"No entries found for {url}. Skipping...")
                continue
            
            keyword_entries = self.check_feed_for_word(title_words, entries)
            for entry in keyword_entries:
                # get the news article
                link = entry.get("link")
                if not link:
                    link = entry.get("id") if entry.get("id") else entry.get("guid")
                    
                print(link)

                if link in seen_links:
                    continue
                
                if self.check_entry_for_word(feed_words, link):
                    news_data.append({
                        'Title': entry['title'],
                        'Link': link
                    })
                    seen_links.add(link)
                
                    
        return news_data
    

@dataclass
class GovernmentWebFeed(WebFeed):
    base_url: str = "https://www.canada.ca/en/news/web-feeds.html"
    


@dataclass
class CBCWebFeed(WebFeed):
    base_url: str = "https://www.cbc.ca/rss/"
