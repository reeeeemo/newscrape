import pandas as pd
from dataclasses import dataclass
from webfeeds import CBCWebFeed, GovernmentWebFeed
import os

DEBUG = True

# makes output if it doesnt exist as a folder
os.makedirs("output", exist_ok=True)
pd.set_option("display.max_columns", None)  # Ensure all columns are visible
pd.set_option("display.max_colwidth", None) # Preventing truncuation
pd.set_option("display.width", 200) # Increase console width

# Making all webfeeds into a varialbe
govfeed = GovernmentWebFeed()
cbcfeed = CBCWebFeed()

# Getting all webfeeds according to word(s)
news_data = []
# news_data.update(govfeed.get_webfeed(["banana", "banana"], ["banana"]))
news_data.extend(cbcfeed.get_webfeed(["drugs", "drug"], ["fentanyl"]))
df = pd.DataFrame(news_data)

if DEBUG:
    print(df)

# Print to a .csv file
#df.to_csv('output/news_articles.csv')