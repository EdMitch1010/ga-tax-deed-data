import re
import os
import json
import pandas as pd
from urllib.parse import urljoin, urlparse
from playwright.sync_api import (
    sync_playwright,
    LIST_EXTS,
    KEYWORDS,
    looks_like_list_link,
    extract_links,
    safe_filename,
    download_file,
    scrape_county_sources,
)

county_to_seed_pages = {
    "Fulton County": []  # Add appropriate pages to scrape from Fulton County
}

results = scrape_county_sources(county_to_seed_pages)

# Saving results to Fulton_Test_Results.xlsx
df = pd.DataFrame(results)
df.to_excel('Fulton_Test_Results.xlsx', index=False)