from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import Literal
from selenium.webdriver.ie.webdriver import WebDriver
from settings import MAX_THREADS
import logging
import re
from urllib.parse import urlparse, urljoin
from contextlib import contextmanager

'''
    For news feeds that require JavaScript.
'''

@dataclass
class JSWebFeed:
    base_url: str = field(default_factory=str)
    path: str = field(default_factory=str)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    parser_type: Literal['html', 'xml'] = 'html'
    
    '''
        Setup a Selenium WebDriver and return it
    '''
    @contextmanager
    def get_driver(self) -> WebDriver:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        try:
            yield driver
        finally:
            driver.quit()
    
    '''
        Gets an HTTP request from Selenium. Returns content
    '''
    def get_request(self, url: str) -> str:
        with self.get_driver() as driver:
            parsed = urlparse(url)
        
            if not parsed.netloc: # path, not url
                url = urljoin(self.base_url, url)
            elif not parsed.scheme: # missing scheme
                url = f"https://{url}"
            
            try:
                driver.get(url)
                
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"    
                )

                return driver.page_source
            except Exception as e:
                logging.debug(f'Error: {e}')
                return None
    
    def get_webfeed(self, title_words: list[str], feed_words: list[str]) -> list[dict]:
        print('Getting blank webfeed. Returning')
        return []

        
@dataclass
class RCMPWebFeed(JSWebFeed):
    base_url: str = "https://rcmp.ca"
    path: str = "/en/news"
    
    '''
        Recursively goes through each page on the JS news feed.
        
        Grabs all links that have keywords in them, then returns the list of links.
    '''
    def check_feed_for_word(self, title_words: list[str], url: str) -> list[str]:
        with self.get_driver() as driver:
            try:
                driver.get(url)
            except Exception as e:
                logging.debug(f'Error: {e}')
                return []

            # finding max amt of pages
            pages = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "paginate_button"))
            )
            total_pages = max([int(num) for s in pages for num in re.findall(r'\d+', s.text)])
            
                
            # recursively going through each page and grab news reports
            urls = []
            for _ in range(1, total_pages):
                # checks for keywords
                soup = BeautifulSoup(driver.page_source, "html.parser")
                descs = soup.find_all("td", class_ ="nws-tbl-desc mrgn-bbtm-md")
                links = soup.find_all("a", class_="h4")
                urls.extend([
                    link.get("href") for desc, link in zip(descs, links) 
                    if any(word.lower() in desc.get_text().lower() for word in title_words)
                ])
                
                # wait until page is loaded, then reload DOM and click next button
                try:
                    pages = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, "paginate_button"))    
                    )
                    pages[-1].click()
                except Exception as e:
                    print(f'Error navigating to the next page: {e}')
                    break

            return urls

    '''
        Get all data from the webfeed links in base_url
        
        Returns a list of dictionaries of the title and links corresponding to the keywords
    '''
    def get_webfeed(self, title_words: list[str], feed_words: list[str]) -> list[dict]:
        print(f'Processing {self.base_url}{self.path}...')
        if not title_words or not self.get_request(f'{self.base_url}{self.path}'):
            return []
        
        urls = self.check_feed_for_word(title_words, f"{self.base_url}{self.path}")
        
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            results = list(executor.map(self.get_request, urls))
        
        print(results)
        news_results = []
        for i, content in enumerate(results):
            if not content:
                continue
            
            soup = BeautifulSoup(content, f'{self.parser_type}.parser')
            page_text = soup.body.get_text().lower() if soup.body else ""
            if any(word in page_text for word in feed_words):
                title = soup.find("h1", class_="mrgn-tp-md").get_text()
                link = urls[i] if urls[i] else "Unknown Link"
                news_results.append({
                    'Title': title,
                    'Link': link
                })
            # beautiful soup to check for feed words inside content
            # beautiful soup to parse for title and url
       
        return news_results 