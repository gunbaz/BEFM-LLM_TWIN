import os
import time
from datetime import datetime
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

OUT_DIR = "data_raw"

SEARCH_QUERIES = [
    "Yaşar Kemal röportaj",
    "Yaşar Kemal ile söyleşi",
    "Yaşar Kemal söyleşi",
    "Yaşar Kemal konuşuyor",
    "Yaşar Kemal ile söyleşi metni",
    "Yaşar Kemal gazete yazısı",
    "Yaşar Kemal deneme yazısı",
    "Yaşar Kemal politika üzerine",
    "Yaşar Kemal edebiyat üzerine konuşuyor",
    "Yaşar Kemal ile uzun röportaj"
]

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def search_query_and_collect_links(driver, query, max_links=10):
    # Basit çözüm: Bing kullanıyoruz çünkü genelde Google daha agresif bot tespit ediyor.
    url = "https://www.bing.com/search?q=" + quote_plus(query)

    driver.get(url)
    time.sleep(2)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    links = []
    for li in soup.select("li.b_algo h2 a"):
        href = li.get("href")
        text = li.get_text(strip=True)
        if href and href.startswith("http"):
            links.append((text, href))
        if len(links) >= max_links:
            break

    return links

def save_links(all_links):
    os.makedirs(OUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUT_DIR, f"url_candidates_{ts}.txt")

    with open(path, "w", encoding="utf-8") as f:
        for (title, href) in all_links:
            f.write(f"{title}\n{href}\n\n")

    return path

def run_discovery():
    driver = get_driver()
    all_links = []

    try:
        for q in SEARCH_QUERIES:
            links = search_query_and_collect_links(driver, q, max_links=10)
            all_links.extend(links)
            # ufak uyku, bot gibi görünmemek için
            time.sleep(1)
    finally:
        driver.quit()

    out_path = save_links(all_links)
    print(f"[OK] Collected {len(all_links)} links -> {out_path}")

if __name__ == "__main__":
    run_discovery()
