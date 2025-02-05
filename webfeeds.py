import pandas as pd
import feedparser
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import requests


@dataclass
class GovernmentWebFeed:
    base_url: str = "https://api.io.canada.ca/io-server/gc/news/en/v2?sort=publishedDate&orderBy=desc&publishedDate%3E=2024-01-25&pick=100&format=atom&atomtitle="
    provinces: list[str] = field(default_factory=lambda: ["National%20News", "Alberta", "Ontario", "British%20Columbia", "Manitoba", "New%20Brunswick", 
             "Newfoundland%20and%20Labrador", "Northwest%20Territories", "Nova%20Scotia",
             "Nunavut", "Prince%20Edward%20Island", "Quebec", "Saskatchewan", "Yukon"])
    
    def get_url(self, title: str = "National%20News") -> str:
        return f'{self.base_url}{title}'
    
    def get_webfeed(self, title_words: list[str], feed_words: list[str]) -> list[dict]:
        news_data = []
        seen_links = set()
        for prov in self.provinces:
            rss_url = self.get_url(prov) 
            feed = feedparser.parse(rss_url) # get and parse webfeed
            # for each news article
            keyword_entries = self.check_feed_for_word(title_words, feed.entries)
            
            for entry in keyword_entries:
                if entry.id in seen_links:
                    continue
                response = requests.get(entry.link)
                if response.status_code != 200:
                    print(f'Error getting url {entry.link}: {response.status_code}. Skipping...')
                    continue
                soup = BeautifulSoup(response.content, 'html.parser')
                page_text = soup.body.get_text().lower() if soup.body else ""
                if any(word in page_text for word in feed_words): # check to ensure there is talk of fentanyl within
                    news_data.append({
                        'Province': prov.replace("%20", " "),
                        'Title': entry.title,
                        'Link': entry.id
                    })
                    seen_links.add(entry.id)
        return news_data

    def check_feed_for_word(self, words: list[str], entries) -> list:
        keyword_entries = []
        if not words or not entries:
            return []
            
        for entry in entries:
            if any(word in entry.title.lower() for word in words):
                keyword_entries.append(entry)
        return keyword_entries
               