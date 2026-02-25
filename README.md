# pip install playwright pandas openpyxl
# playwright install

import re
import os
import pandas as pd
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

COUNTIES_TOP30 = [
  "Fulton","Gwinnett","Cobb","DeKalb","Chatham","Clayton","Cherokee","Forsyth","Henry","Richmond",
  "Muscogee","Hall","Paulding","Coweta","Lowndes","Bibb","Douglas","Fayette","Columbia","Newton",
  "Carroll","Walton","Barrow","Spalding","Rockdale","Glynn","Effingham","Jackson","Bartow","Bulloch"
]

LIST_EXTS = (".pdf", ".xls", ".xlsx", ".csv")
KEYWORDS = ["tax sale", "taxsales", "taxsalelist", "delinquent", "fi fa", "fifa", "in rem", "judicial"]

def looks_like_list_link(url: str) -> bool:
    u = url.lower().split("?")[0]
    return u.endswith(LIST_EXTS) or any(k.replace(" ","") in u.replace("-","") for k in ["taxsale","taxsalelist","delinquent","fifa","inrem"])

def extract_links(page_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(page_url, wait_until="networkidle", timeout=45000)

        anchors = page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
        browser.close()

    out = []
    for href in anchors:
        if not href:
            continue
        abs_url = urljoin(page_url, href)
        if looks_like_list_link(abs_url):
            out.append(abs_url)
    # de-dupe
    out = list(dict.fromkeys(out))
    return out

def safe_filename(url: str):
    path = urlparse(url).path
    name = os.path.basename(path) or "download"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)

def download_file(url: str, folder: str):
    import requests
    os.makedirs(folder, exist_ok=True)
    fp = os.path.join(folder, safe_filename(url))
    r = requests.get(url, timeout=45, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    with open(fp, "wb") as f:
        f.write(r.content)
    return fp

def scrape_county_sources(county_to_seed_pages: dict):
    rows_sources = []
    downloaded = []

    for county, seed_pages in county_to_seed_pages.items():
        for page_url in seed_pages:
            try:
                links = extract_links(page_url)
                if not links:
                    rows_sources.append([county, page_url, "", "NO FILE LINKS FOUND"])
                    continue
                for link in links:
                    rows_sources.append([county, page_url, link, "OK"])
                    # Optionally download immediately
                    if link.lower().split("?")[0].endswith(LIST_EXTS):
                        downloaded.append([county, link, download_file(link, "downloads")])
            except Exception as e:
                rows_sources.append([county, page_url, "", f"ERROR: {e}"])

    df_sources = pd.DataFrame(rows_sources, columns=["County","List_Page_URL","List_File_URL","Status"])
    df_downloads = pd.DataFrame(downloaded, columns=["County","File_URL","Local_Path"])
    return df_sources, df_downloads

# You provide county_to_seed_pages after running search queries (SerpAPI/Bing/etc.)
# Example structure:
county_to_seed_pages = {
  "Chatham": ["https://tax.chathamcountyga.gov/TaxSaleList"],
  "Camden": ["https://www.co.camden.ga.us/87/Tax-Sale"],
}

if __name__ == "__main__":
    sources, downloads = scrape_county_sources(county_to_seed_pages)
    with pd.ExcelWriter("GA_TaxSale_Sources_and_Downloads.xlsx", engine="openpyxl") as writer:
        sources.to_excel(writer, sheet_name="Sources", index=False)
        downloads.to_excel(writer, sheet_name="Downloads", index=False)
    print("Wrote GA_TaxSale_Sources_and_Downloads.xlsx")
