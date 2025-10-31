import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

RAW_DIR = "data_raw"

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # tarayıcıyı ekranda açma
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_page_html(url: str) -> str:
    driver = get_driver()
    try:
        driver.get(url)
        # sayfa tam yüklensin diye ufak bekleme
        time.sleep(2)
        html = driver.page_source
    finally:
        driver.quit()
    return html

def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # çok kaba yaklaşım: <p> tag'lerini birleştir
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    text = "\n\n".join([p for p in paragraphs if p])

    # fallback: hiç <p> yoksa tüm body text
    if not text.strip():
        body = soup.get_text(separator="\n", strip=True)
        text = body

    return text

def save_raw_text(text: str, source_url: str) -> str:
    os.makedirs(RAW_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}.txt"
    fpath = os.path.join(RAW_DIR, fname)

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(f"SOURCE: {source_url}\n\n")
        f.write(text)

    return fpath

def crawl_and_save(url: str) -> str:
    html = fetch_page_html(url)
    text = extract_main_text(html)
    path = save_raw_text(text, url)
    return path

if __name__ == "__main__":
    test_url = "https://www.evrimagaci.org/"  # örnek bir sayfa
    out_path = crawl_and_save(test_url)
    print(f"[OK] Saved -> {out_path}")
