import os
import logging
import pandas as pd

# Constants
DEBUG = True
MAX_THREADS = os.cpu_count()

# Debug config
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO, format="%(levelname)s: %(message)s")

# Pandas config
pd.set_option("display.max_columns", None)  # Ensure all columns are visible
pd.set_option("display.max_colwidth", None) # Preventing truncuation
pd.set_option("display.width", 200) # Increase console width
