import os
import time
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

RAW_DIR = "data_raw"

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def read_discovery_file():
    files = [f for f in os.listdir(RAW_DIR) if f.startswith("url_candidates_")]
    if not files:
        raise RuntimeError("url_candidates_*.txt bulunamadı. Önce discover.py çalıştırmalısın.")

    files.sort(reverse=True)
    latest = files[0]

    path = os.path.join(RAW_DIR, latest)
    links = []

    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines()]

    current_title = None
    for line in lines:
        if line == "":
            continue
        if line.startswith("http"):
            links.append((current_title or "", line))
            current_title = None
        else:
            current_title = line

    return links

def get_rendered_text(driver, url: str) -> str:
    try:
        driver.get(url)
        # sitenin JS yüklemesi için ufak bekleme
        time.sleep(2)
        html = driver.page_source
    except Exception:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    # ana gövde metni kaba şekilde al
    text = soup.get_text(separator="\n", strip=True)
    # normalize
    text = " ".join(text.split())
    return text

def score_link(title: str, text: str) -> int:
    t = title.lower()
    x = text.lower()

    score = 0

    # Başlıkta Yaşar Kemal geçiyorsa +3
    if "yaşar kemal" in t:
        score += 3

    # Gövdede Yaşar Kemal geçiyorsa +2
    if "yaşar kemal" in x:
        score += 2

    # Eğer "konser", "bilet" gibi bariz alakasız sinyal varsa puan 0'ın altına düşür
    # (ama tamamen yok etmiyoruz)
    noise_words = ["konser", "bilet", "şarkıcı", "sahne aldı", "albüm", "turne"]
    for n in noise_words:
        if n in x:
            score -= 3

    return score

def filter_links(links, min_score=1):
    driver = get_driver()
    filtered = []

    try:
        for (title, url) in links:
            text = get_rendered_text(driver, url)
            s = score_link(title, text)
            if s >= min_score:
                filtered.append((title, url, s))
    finally:
        driver.quit()

    return filtered

def save_filtered(filtered):
    os.makedirs(RAW_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(RAW_DIR, f"filtered_urls_{ts}.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        for (title, url, s) in filtered:
            f.write(f"[score={s}] {title}\n{url}\n\n")

    return out_path

def run_filter():
    links = read_discovery_file()
    filtered = filter_links(links, min_score=1)
    out_path = save_filtered(filtered)
    print(f"[OK] Filtered {len(filtered)} links -> {out_path}")

if __name__ == "__main__":
    run_filter()
