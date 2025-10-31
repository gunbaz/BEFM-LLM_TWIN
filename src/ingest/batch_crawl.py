import os
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse

RAW_DIR = "data_raw"
SEED_FILE = os.path.join(RAW_DIR, "seed_urls.txt")

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def load_seed_urls():
    if not os.path.exists(SEED_FILE):
        raise RuntimeError(f"{SEED_FILE} yok. seed_urls.txt oluşturmalısın.")
    urls = []
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if u and u.startswith("http"):
                urls.append(u)
    return urls

def fetch_pdf_text(url: str) -> str:
    """
    PDF indir → geçici dosyaya kaydet → metni pdfminer ile çıkar → geri döndür
    """
    # pdfminer tercihe bağlı; yoksa bu adımı atla
    try:
        from pdfminer.high_level import extract_text as pdf_extract_text
    except Exception:
        return ""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return ""
    except Exception:
        return ""

    # geçici pdf yolu
    tmp_pdf_path = os.path.join(RAW_DIR, "tmp_download.pdf")
    with open(tmp_pdf_path, "wb") as f:
        f.write(resp.content)

    try:
        text = pdf_extract_text(tmp_pdf_path)
    except Exception:
        text = ""

    # cleanup
    try:
        os.remove(tmp_pdf_path)
    except OSError:
        pass

    # düzelt
    text = text.replace("\x00", "")
    return text.strip()

def fetch_html_text(driver, url: str) -> str:
    """
    Selenium ile sayfayı yükle → <p> tagleri topla → fallback tüm text
    """
    driver.get(url)
    time.sleep(2)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    text = "\n\n".join([p for p in paragraphs if p])

    if not text.strip():
        text = soup.get_text(separator="\n", strip=True)

    # Temizlik
    text = " ".join(text.split())
    return text

def is_pdf_url(url: str) -> bool:
    # kaba kontrol: .pdf ile bitiyorsa ya da query'de .pdf geçiyorsa
    lower = url.lower()
    if ".pdf" in lower:
        return True
    # bazı URL'ler pdf viewer'a gider ama gerçek pdf'e redirect eder, bunu ilk aşamada yakalayamayabiliriz
    return False

def save_text(text: str, source_url: str, idx: int):
    os.makedirs(RAW_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{idx:03d}.txt"
    path = os.path.join(RAW_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"SOURCE: {source_url}\n\n")
        f.write(text)
    return path

def run_batch():
    urls = load_seed_urls()
    driver = get_driver()
    saved_files = []

    try:
        for i, url in enumerate(urls):
            try:
                if is_pdf_url(url):
                    text = fetch_pdf_text(url)
                else:
                    text = fetch_html_text(driver, url)

                if not text or len(text.strip()) < 50:
                    print(f"[WARN] {url} -> very short / empty, skipping")
                    continue

                out_path = save_text(text, url, i)
                print(f"[OK] {url} -> {out_path}")
                saved_files.append(out_path)
            except Exception as e:
                print(f"[ERR] {url}: {e}")
    finally:
        driver.quit()

    print(f"[DONE] Saved {len(saved_files)} files total.")

if __name__ == "__main__":
    run_batch()
