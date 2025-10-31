# LLM Twin — Kullanım Kılavuzu (Windows / PowerShell)

Bu kılavuz, Yaşar Kemal LLM Twin projesini sıfırdan kurup çalıştırmanız için adım adım talimatlar içerir. Komutlar Windows PowerShell (v5.1+) için hazırlanmıştır.

## 1) Önkoşullar

- Windows 10/11
- Docker Desktop (Linux container modu)
- Python 3.10+ (öneri: 3.11/3.12) ve PowerShell
- En az 12 GB boş disk alanı (model ve veri indirimi için)

Notlar:
- LLM modeli Transformers üzerinden indirileceğinden ilk çalıştırmada internet gerekir.
- GPU varsa otomatik kullanılır; yoksa CPU’da da çalışır (daha yavaş).

## 2) Sanal Ortam ve Bağımlılıklar

PowerShell’i proje kökünde açın (`c:\Users\pc\llm-twin`).

```powershell
# (Önerilen) Python 3.12 ile sanal ortam oluştur ve aktif et
py -3.12 -m venv .venv
\.venv\Scripts\Activate.ps1

# Bağımlılıkları kur
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Not: Sisteminizde birden fazla Python sürümü varsa, özellikle 3.12 ile oluşturmak için `py -3.12 -m venv .venv` kullanın.

İpucu: PowerShell script çalıştırma kısıtına takılırsanız (ExecutionPolicy), yönetici PowerShell ile geçici izin verebilirsiniz:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3) Servisleri Başlat (Docker: MongoDB + Qdrant)

MongoDB ve Qdrant’ı Docker ile başlatın. Portlar: Mongo 27017, Qdrant 6333.

```powershell
# MongoDB
docker run -d --name llm-twin-mongo -p 27017:27017 mongo

# Qdrant
docker run -d --name llm-twin-qdrant -p 6333:6333 qdrant/qdrant
```

Kontrol:
- Qdrant Dashboard: http://localhost:6333/dashboard

Not: Portlar meşgulse, eski konteynerleri durdurup kaldırın:

```powershell
docker stop llm-twin-mongo llm-twin-qdrant 2>$null
docker rm   llm-twin-mongo llm-twin-qdrant 2>$null
```

Alternatif: docker-compose ile (repo kökünde `docker-compose.yml` var)

```powershell
docker compose up -d mongodb qdrant
# veya tüm servisleri (dosyada tanımlı) başlatmak için
docker compose up -d
```

## 4) (Opsiyonel) Veri Topla ve Vektörleri Yükle

Elinizde hazır `data_raw/` varsa bu adım opsiyoneldir. Sıfırdan akışı görmek için:

```powershell
# Tohum linklerden veriyi indir (PDF + HTML)
python src\ingest\batch_crawl.py

# Metinleri chunk’la, embedding üret ve DB’lere yaz
python src\embed\ingest_to_vectorstore.py
```

Beklenen çıktı (örnek): ~13 belge, ~1100+ chunk; MongoDB’ye kayıt, Qdrant’e vektör upsert.

## 5) API’yi Başlat ve Test Et

FastAPI uygulamasını çalıştırın. Derlenmiş kütüphanelerde (numpy/scipy/sklearn) reloader kaynaklı hataları engellemek için önce `--no-reload` ile başlatmanızı öneririz.

Seçenek A — `src/api` klasöründen başlatma:

```powershell
cd src\api
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --no-reload
```

Seçenek B — proje kökünden başlatma (PYTHONPATH ile):

```powershell
cd ..\..
$env:PYTHONPATH = "src"  # sadece bu oturum için
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --no-reload
```

Sağlık kontrolü ve örnek istekler:

```powershell
# Sağlık
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method GET | ConvertTo-Json -Depth 5

# Semantik arama
Invoke-RestMethod -Uri "http://127.0.0.1:8000/ask?question=Ya%C5%9Far%20Kemal%20do%C4%9Fa%20hakk%C4%B1nda%20ne%20d%C3%BC%C5%9F%C3%BCn%C3%BCyordu%3F" -Method GET | ConvertTo-Json -Depth 5

# Persona cevabı
Invoke-RestMethod -Uri "http://127.0.0.1:8000/ask_persona?question=..." -Method GET | ConvertTo-Json -Depth 5
```

Notlar:
- İlk isteklerde model indirimi zaman alabilir.
- Eğer `--no-reload` ile sorunsuz çalışıyorsa, geliştirme sırasında canlı yenileme için `--reload` deneyebilirsiniz.

### Hugging Face ile Llama 3.1 8B (gated) kullanımı

Llama 3.1 8B Instruct modeli lisanslı (gated) olduğu için Hugging Face hesabınızda erişim izni ve bir erişim token’ı gerekir.

1) Hugging Face’e giriş ve token:

```powershell
huggingface-cli login
# veya sadece bu oturum için token değişkeni
$env:HUGGINGFACE_HUB_TOKEN = "<HF_TOKEN>"
```

2) Model kimliğini ayarla (opsiyonel, varsayılan zaten Llama 3.1 8B):

```powershell
$env:LLM_MODEL_ID = "meta-llama/Meta-Llama-3.1-8B-Instruct"
```

3) API’yi başlat ve ilk istekte model indiriminin tamamlanmasını bekle:

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Notlar:
- İndirme boyutu büyüktür; disk alanı ve internet bağlantısını kontrol edin.
- GPU varsa otomatik kullanılır. GPU yoksa CPU’da çalışır (yavaş). İsterseniz `LLM_FALLBACK_MODEL_ID` ile küçük bir açık modele geçebilirsiniz (ör. `TinyLlama/TinyLlama-1.1B-Chat-v1.0`).

## 6) ZenML Pipeline Çalıştırma

Projedeki 5 adımlı pipeline’ı tek komutla çalıştırabilirsiniz.

```powershell
# Proje köküne dönün
cd ..\..\..

# Sanal ortam aktif değilse yeniden aktif edin
.\.venv\Scripts\Activate.ps1

# Pipeline’ı başlatın (yeni konum)
python scripts\run_pipeline.py
```

Terminalde adım adım ilerleme ve özet çıktılar göreceksiniz. Bu çalışma, MongoDB/Qdrant içeriğini doldurur/günceller.

## 7) ZenML Dashboard (Docker) ile Koşuları Görüntüleme

ZenML Server’ı Docker’da çalıştırabilir ve koşuları web arayüzünden takip edebilirsiniz.

1) ZenML Server’ı başlatın (8080):

```powershell
docker run -d --name llm-twin-zenml -p 8080:8080 zenmldocker/zenml-server:0.90.0
```

2) İlk açılış (onboarding):
- Tarayıcıdan http://localhost:8080 adresine gidin ve sunucunun açıldığını doğrulayın.

3) CLI’yi sunucuya bağlayın ve pipeline’ı ZenML’e kaydedin:

```powershell
.\.venv\Scripts\Activate.ps1

# Sunucuya bağlan
zenml connect --url http://localhost:8080
zenml status

# Pipeline’ı çalıştır (koşular dashboard’a düşecek)
python scripts\run_pipeline.py
```

4) Dashboard’da görüntüleyin:
- http://localhost:8080 → Pipelines → llm_twin_ingestion_pipeline → Runs

Notlar:
- Sadece Docker’daki ZenML sunucusuna bağlıyken yapılan koşular dashboard’da görünür. Önceki yerel koşular görünmeyebilir.
- Eğer `zenml` CLI sürümü ile sunucu sürümü uyumsuzsa, `requirements.txt` içindeki ZenML sürümünü sunucuya göre hizalayın veya farklı bir sunucu etiketi kullanın (örn. `:0.91.x`).

## 8) Temizlik ve Sıfırlama

Konteynerleri durdurmak/kaldırmak:

```powershell
# API’yi manuel durdurun (Ctrl+C)

# Docker servisleri
docker stop llm-twin-mongo llm-twin-qdrant llm-twin-zenml 2>$null
docker rm   llm-twin-mongo llm-twin-qdrant llm-twin-zenml 2>$null
```

Veri klasörlerini (kalıcı hacimler yerine) temizlemeniz gerekirse MongoDB/Qdrant verilerini manuel siliyor olacaksınız (bu kılavuz varsayılan container içi depolamayı kullanır).

## 9) Sık Karşılaşılan Sorunlar (FAQ)

- PowerShell aktivasyon hatası (ExecutionPolicy):
  - `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` komutunu aynı oturumda çalıştırın.

- Port çakışması (27017/6333/8080 meşgul):
  - `docker ps` ile çalışan konteynerleri tespit edip durdurun/kaldırın.

- ZenML sunucu “Creating database tables” takılması:
  - 1-2 dakika bekleyin, sonra logları kontrol edin: `docker logs llm-twin-zenml --tail 200`.
  - Gerekirse konteyneri kaldırıp yeniden başlatın.

- Model indirilemiyor/çok yavaş:
  - İlk indirme uzun sürebilir. Bağlantınızı kontrol edin.
  - Yetersiz disk alanı model indirmesini engelleyebilir.

- GPU belleği yetersiz:
  - Sistem 8-bit quantization kullanır; yine de bellek yetmezse CPU’da çalışır (daha yavaş).

### Derlenmiş Modül Hataları (NumPy / SciPy / scikit-learn)

Belirtiler:
- `ImportError: No module named 'sklearn.__check_build._check_build'`
- NumPy/SciPy C-extension uyumsuzluk hataları veya reloader içinde farklı sürüm uyarıları

Çözüm Adımları (sanal ortam aktifken):

```powershell
# Temiz ikili kurulumlar (Windows + Python 3.12 için test edilmiş kombinasyon)
python -m pip install --no-cache-dir --only-binary=:all: numpy==2.3.4 scipy==1.16.3 scikit-learn==1.7.2

# Gerekirse sadece scikit-learn'i yeniden kurun
python -m pip uninstall -y scikit-learn
python -m pip install --no-cache-dir --only-binary=:all: scikit-learn==1.7.2

# Uvicorn'u reloader kapalı başlatın
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --no-reload
```

Not: Reloader (–-reload) bazı durumlarda farklı işlemde farklı Python ikilileri yükleyip bu hataları tetikleyebilir.

## 10) Yararlı Komutlar (Özet)

```powershell
# Sanal ortam
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Servisler
docker run -d --name llm-twin-mongo  -p 27017:27017 mongo
docker run -d --name llm-twin-qdrant -p 6333:6333   qdrant/qdrant

# Veri ve embedding
python src\ingest\batch_crawl.py
python src\embed\ingest_to_vectorstore.py

# API
cd src\api
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --no-reload

# Pipeline
cd ..\..\..
python scripts\run_pipeline.py

# ZenML Server (Docker) ve bağlanma
docker run -d --name llm-twin-zenml -p 8080:8080 zenmldocker/zenml-server:0.90.0
zenml connect --url http://localhost:8080
zenml status
python run_pipeline.py
```

---

Bu kılavuz projeyi uçtan uca çalıştırmanız için hazırlandı. Takıldığınız noktada repository’deki `context.txt`, `PIPELINE_GUIDE.md` ve kaynak kod içi yorumları da referans alabilirsiniz.