# newscrape
Python-based news scraper that collects news from Canadian news outlets via user-inputted keywords to filter article titles and body text

## How to Use?
When you run the executable, you should see a GUI pop up with some info text.

**What are Keywords and Entrywords?**
Keywords are words that the scraper will use to filter article *titles*. Entrywords are words that the scraper will use to filter the text *inside of the article*.

**To add/remove a Keyword/Entryword:**
- Type in the entry box your keyword (caps insensitive)
- Click the "Keyword" or "Entryword" radio button
- Click "Add"
- If removing, select the item in the list and click "Remove"

Once given all keywords and entrywords, click "Submit" and it will start the scraping process.

**The output CSV will be in `output/news_articles.csv`**

## Current list of news sites parsed
- [Gov. Of Canada News Web Feeds](https://www.canada.ca/en/news/web-feeds.html)
- [CBC](https://www.cbc.ca/rss/)
- [Global News](https://globalnews.ca/pages/feeds/)
- [Toronto Star](https://www.thestar.com/site/static-pages/rss-feeds.html)
- [RCMP](https://rcmp.ca/en/news)

**More will be added if there is demand**