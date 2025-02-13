from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from typing import Literal
import asyncio
from playwright.async_api import Page, async_playwright
import logging
import re
from urllib.parse import urlparse, urljoin
from contextlib import asynccontextmanager

'''
    For news feeds that require JavaScript.
'''

@dataclass
class JSWebFeed:
    base_url: str = field(default_factory=str)
    path: str = field(default_factory=str)
    parser_type: Literal['html', 'xml'] = 'html'
    
    
    @asynccontextmanager
    async def get_page(self) -> Page:
        '''
            Setup a PlayWright browser and return it (automatically closes afterwards)
        '''
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                yield page
        except Exception as e:
            logging.error(f'Error in PlayWright setup {e}')
        finally:
            if browser:
                await browser.close()
    
    
    async def get_request(self, url: str) -> str:
        '''
            Gets an HTTP request from Selenium. Returns content
        '''
        async with self.get_page() as p:
            # check for correct URL
            parsed = urlparse(url)
        
            if not parsed.netloc: # path, not url
                url = urljoin(self.base_url, url)
            elif not parsed.scheme: # missing scheme
                url = f"https://{url}"
            
            try:
                await p.goto(url)

                return await p.content()
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
    
    
    async def check_feed_for_word(self, title_words: list[str], url: str) -> list[str]:
        '''
            Recursively goes through each page on the JS news feed.
        
            Grabs all links that have keywords in them, then returns the list of links.
        '''
        async with self.get_page() as p:
            try:
                await p.goto(url)
                await p.wait_for_selector(".paginate_button", state="attached", timeout=10000)
            
                # finding max amt of pages
                pages = await p.query_selector_all('.paginate_button')
                total_pages = max([int(num) for s in pages for num in re.findall(r'\d+', await s.text_content())])
                    
                # recursively going through each page and grab news reports
                urls = []
                for i in range(1, total_pages + 1):
                    # checks for keywords
                    soup = BeautifulSoup(await p.content(), "html.parser")
                    descs = soup.find_all("td", class_ ="nws-tbl-desc mrgn-bbtm-md")
                    links = soup.find_all("a", class_="h4")
                    urls.extend([
                        link.get("href") for desc, link in zip(descs, links) 
                        if any(word.lower() in desc.get_text().lower() for word in title_words)
                    ])
                    
                    # wait until page is loaded, then reload DOM and click next button
                    try:
                        if i < total_pages:
                            await p.wait_for_selector(".paginate_button", state="attached", timeout=10000)
                            pages = await p.query_selector_all('.paginate_button')
                            await pages[-1].click()
                            await p.wait_for_load_state("domcontentloaded")
                    except Exception as e:
                        print(f'Error navigating to the next page: {e}')
                        break

                return urls
            except Exception as e:
                logging.error(f'Error checking feed: {e}')

    
    async def get_webfeed(self, title_words: list[str], feed_words: list[str]) -> list[dict]:
        '''
            Get all data from the webfeed links in base_url
        
            Returns a list of dictionaries of the title and links corresponding to the keywords
        '''
        print(f'Processing {self.base_url}{self.path}...')
        if not title_words or not await self.get_request(f'{self.base_url}{self.path}'):
            return []
        
        urls = await self.check_feed_for_word(title_words, f"{self.base_url}{self.path}")
        
        tasks = [self.get_request(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        news_results = []
        for i, content in enumerate(results):
            if isinstance(content, Exception) or not content:
                print(f'Could not fetch url {urls[i]}. Skipping...')
                continue
            
            soup = BeautifulSoup(content, f'{self.parser_type}.parser')
            page_text = soup.body.get_text().lower() if soup.body else ""
            if any(word in page_text for word in feed_words):
                title = soup.find("h1", class_="mrgn-tp-md").get_text()
                link = urls[i] if urls[i] else "Unknown Link"
                news_results.append({
                    'Title': title,
                    'Link': f'{self.base_url}{link}'
                })
       
        return news_results 