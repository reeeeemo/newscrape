import pandas as pd
import feedparser
from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
from webfeeds import GovernmentWebFeed
import os

# makes output if it doesnt exist as a folder
os.makedirs("output", exist_ok=True)

pd.set_option("display.max_columns", None)  # Ensure all columns are visible
pd.set_option("display.max_colwidth", None) # Preventing truncuation
pd.set_option("display.width", 200) # Increase console width

webfeed = GovernmentWebFeed()

news_data = webfeed.get_webfeed(["drugs", "drug"], ["fentanyl"])

 
df = pd.DataFrame(news_data)

print(df)


df.to_csv('output/news_articles.csv')