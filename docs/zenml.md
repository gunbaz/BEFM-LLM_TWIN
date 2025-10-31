# ZenML Kullanım Rehberi

## İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Pipeline'ları Görüntüleme](#pipelineları-görüntüleme)
3. [Dashboard Kurulumu](#dashboard-kurulumu)
4. [Docker ile Dashboard](#docker-ile-dashboard)
5. [Veritabanı Konumları](#veritabanı-konumları)
6. [Troubleshooting](#troubleshooting)

---

## Genel Bakış

### 🎯 ZenML Nedir?

ZenML pipeline'ları **Docker container'larında değil**, ZenML'in **SQLite veritabanında** saklanır.

**Konum:** 
- Global: `C:\Users\pc\AppData\Roaming\zenml\`
- Proje: `C:\Users\pc\llm-twin\.zenml/`

### 💡 Docker vs ZenML

**Önemli Fark:**
- Docker container'ları: MongoDB ve Qdrant (veriler burada)
- ZenML metadata: SQLite database (pipeline bilgileri burada)

```
┌─────────────────────────────────────────────┐
│  Docker Containers                          │
│  ├── mongo (27017)   <- VERİ               │
│  └── qdrant (6333)   <- VEKTÖRLER          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ZenML (SQLite)                             │
│  ├── Pipeline tanımları                     │
│  ├── Run geçmişi                            │
│  ├── Step durumları                         │
│  └── Artifact metadata                      │
└─────────────────────────────────────────────┘
```

---

## Pipeline'ları Görüntüleme

### 1️⃣ Python Script ile (En Kolay - Önerilen)

```bash
python scripts\view_pipelines_detailed.py
```

**Bu script gösterir:**
- 📊 Tüm pipeline'lar
- 🎯 En son run'ın tüm detayları
- 📋 Step'lerin durumları ve süreleri
- 📜 Son 5 run
- 📊 Genel istatistikler (başarı oranı)

### 2️⃣ Basit Liste

```bash
python scripts\view_pipelines.py
```

**Bu script gösterir:**
- ✅ Tüm pipeline'lar
- ✅ Pipeline run'ları (son 10)
- ✅ Her run'ın durumu (completed/failed)
- ✅ Step'lerin durumu

### 3️⃣ ZenML Dashboard (Görsel Arayüz)

**⚠️ Windows'ta özel kurulum gerekiyor:**

#### Seçenek A: Blocking Mode (Basit ama terminal'i bloklar)
```bash
# Yeni bir terminal aç ve çalıştır (terminal açık kalacak)
zenml login --local --blocking

# Tarayıcıda aç
http://localhost:8237
```

#### Seçenek B: Docker ile (Önerilen - Detaylar aşağıda)
```bash
# Docker container içinde çalıştır
zenml login --local --docker

# Tarayıcıda aç
http://localhost:8237
```

**Dashboard'da görebilirsiniz:**
- 📊 Pipeline grafiği (DAG view)
- 📈 Step'lerin süresi
- 📁 Artifact'lar (çıktılar)
- 📜 Loglar
- 🔄 Run geçmişi

### 4️⃣ ZenML CLI (Terminal - İleri Seviye)

```bash
# Pipeline'ları listele
zenml pipeline list

# Run'ları listele
zenml pipeline runs list

# Belirli bir run'ı incele
zenml pipeline runs describe <RUN_ID>
```

**⚠️ Not:** Windows'ta global zenml CLI bazı sorunlar verebilir. 
Proje içindeki Python ile çalıştırın:
```bash
python scripts\view_pipelines_detailed.py  # Önerilen yöntem
```

---

## Dashboard Kurulumu

### Yerel Dashboard (Basit Kullanım)

#### Adım 1: ZenML'i Başlat
```bash
zenml init
```

#### Adım 2: Blocking Mode ile Dashboard Aç
```bash
# Yeni bir terminal aç
zenml login --local --blocking

# Tarayıcıda aç
http://localhost:8237
```

**⚠️ Not:** Bu mod terminal'i meşgul eder. Dashboard kullanırken başka terminal açmalısınız.

---

## Docker ile Dashboard

### Neden Docker Dashboard?

- ✅ Terminal'i bloklamaz
- ✅ Arka planda sürekli çalışır
- ✅ Profesyonel production-ready setup
- ✅ Diğer servislerle (MongoDB, Qdrant) entegre

### Kurulum Adımları

#### Adım 1: Docker Servisleri Başlat

```powershell
# Tüm servisleri başlat (MongoDB, Qdrant, ZenML)
docker-compose up -d

# Servislerin durumunu kontrol et
docker ps
```

**Beklenen çıktı:**
```
CONTAINER ID   IMAGE              PORTS                    STATUS
xxxxx          mongo              0.0.0.0:27017->27017     Up
xxxxx          qdrant/qdrant      0.0.0.0:6333->6333       Up
xxxxx          zenml/zenml        0.0.0.0:8080->8080       Up
```

#### Adım 2: ZenML Server'ın Hazır Olmasını Bekleyin

```powershell
# ZenML loglarını takip et
docker logs -f llm-twin-zenml

# Server başladığında şunu göreceksiniz:
# "INFO:     Application startup complete."
# "INFO:     Uvicorn running on http://0.0.0.0:8080"
```

⏳ **NOT:** İlk başlatmada database oluşturma 1-2 dakika sürebilir.

#### Adım 3: ZenML Dashboard'a Erişin

Tarayıcınızda açın: **http://localhost:8080**

**İlk Giriş Bilgileri:**
- Username: `default`
- Password: (boş bırakın, Enter'a basın)

#### Adım 4: Projenizi ZenML Docker Server'a Bağlayın

```powershell
# Virtual environment'ı aktifleştir
.\.venv\Scripts\Activate.ps1

# ZenML'i Docker server'a bağla
zenml connect --url http://localhost:8080 --username default --password ""

# Bağlantıyı doğrula
zenml status
```

**Çıktı şöyle olmalı:**
```
Connected to ZenML server: 'http://localhost:8080'
Global active project: default
...
```

#### Adım 5: Pipeline'ı Çalıştırın

```powershell
# Pipeline'ı Docker server'a bağlı olarak çalıştır
python scripts\run_pipeline.py
```

Pipeline çalışması bittiğinde, Docker dashboard'unda göreceksiniz!

#### Adım 6: Dashboard'da Pipeline'ları Görüntüleyin

1. **Tarayıcıda** http://localhost:8080 adresine gidin
2. Sol menüden **"Pipelines"** seçin
3. **"llm_twin_ingestion_pipeline"** adlı pipeline'ınızı göreceksiniz
4. Pipeline'a tıklayarak:
   - ✅ Tüm step'leri görün
   - 📊 DAG (Directed Acyclic Graph) görselleştirmesini inceleyin
   - ⏱️ Çalışma sürelerini görün
   - 📝 Her step'in input/output'larını kontrol edin
   - 🔍 Artifact'ları inceleyin

---

## Veritabanı Konumları

### Global ZenML Store
```
C:\Users\pc\AppData\Roaming\zenml\
├── config.yaml          # Global konfigürasyon
├── database_backup/     # Yedekler
└── zenml.db             # SQLite veritabanı
```

### Proje Bazlı Store
```
C:\Users\pc\llm-twin\
└── .zenml/
    ├── config.yaml     # Proje konfigürasyonu
    └── local_stores/   # Local metadata store
```

---

## Dashboard Özellikleri

### 📊 Pipelines Sayfası
- Tüm pipeline'ların listesi
- Son çalışma durumları
- Çalışma sayıları ve istatistikler

### 🔄 Pipeline Runs
- Her pipeline çalışmasının detayları
- Step-by-step izleme
- Başarı/hata durumları
- Execution timeline

### 📦 Artifacts
- Pipeline'ların ürettiği artifacts
- Metadata bilgileri
- Artifact versiyonları

### ⚙️ Stacks
- Aktif stack konfigürasyonu
- Component'ler (orchestrator, artifact store, vb.)

---

## Troubleshooting

### Windows'ta Dashboard Sorunları

**Sorun:** "Running the ZenML server locally as a background process is not supported on Windows"

**Çözüm 1 - Terminal Görüntüleme (Önerilen):**
```bash
python scripts\view_pipelines_detailed.py
```

**Çözüm 2 - Blocking Mode:**
```bash
# Yeni terminal aç
zenml login --local --blocking
# Terminal açık kalacak, dashboard çalışacak
```

**Çözüm 3 - Docker:**
```bash
zenml login --local --docker
```

### Docker Dashboard Açılmıyor

```powershell
# Container çalışıyor mu kontrol et
docker ps --filter name=zenml

# Logları kontrol et
docker logs llm-twin-zenml

# Container'ı yeniden başlat
docker-compose restart zenml
```

### "Can't connect to server" Hatası

```powershell
# ZenML server'ın sağlığını kontrol et
curl http://localhost:8080/health

# Response: {"status": "ok"} görmelisiniz

# Bağlantıyı yeniden kur
zenml disconnect
zenml connect --url http://localhost:8080
```

### Pipeline Dashboard'da Gözükmüyor

```powershell
# Doğru server'a bağlı olduğunuzu kontrol edin
zenml status

# URL şu olmalı: http://localhost:8080 (Docker) veya http://localhost:8237 (Local)

# Pipeline'ı doğru server'a bağlıyken çalıştırdığınızdan emin olun
# (zenml connect SONRASINDA run_pipeline.py çalıştırın)
```

### Dashboard Açılmıyorsa

```bash
# Server'ı durdur
zenml down

# Tekrar başlat (blocking mode)
zenml login --local --blocking
```

### Pipeline Görünmüyorsa

```bash
# ZenML'i yeniden başlat
zenml init

# Pipeline'ı tekrar çalıştır
python scripts\run_pipeline.py
```

### Versiyon Uyumsuzluğu

```bash
# Global ve local ZenML'i senkronize et
pip install --upgrade zenml[local]
```

---

## Servisleri Yönetme

### Servisleri Durdurma

```powershell
# Tüm servisleri durdur (veriler korunur)
docker-compose stop

# Servisleri tamamen kaldır (veriler silinir)
docker-compose down -v
```

### Faydalı Komutlar

```powershell
# Container'ları listele
docker-compose ps

# Tüm logları göster
docker-compose logs

# Sadece ZenML logları
docker logs -f llm-twin-zenml

# ZenML server'ı yeniden başlat
docker-compose restart zenml

# Pipeline çalışmalarını listele (terminal'den)
python scripts\view_pipelines_detailed.py
```

---

## 📈 Şu Anki Pipeline Durumu

Çalıştırdığınız pipeline: **llm_twin_ingestion_pipeline**

✅ **Başarılı Run:**
- Durum: **completed** ✅
- Step'ler:
  - step_collect_raw (cached)
  - step_read_and_parse (cached)
  - step_clean_text (cached)
  - step_chunk_text (cached)
  - step_embed_and_store (completed)
  
**Sonuç:** 1147 chunk başarıyla MongoDB ve Qdrant'e kaydedildi!

---

## 🚀 Özet İş Akışı

### Local Dashboard (Basit)
1. ✅ `zenml login --local --blocking` → Dashboard başlat
2. ✅ Tarayıcıda http://localhost:8237 → Dashboard aç
3. ✅ `python scripts\run_pipeline.py` → Pipeline'ı çalıştır
4. ✅ Dashboard'ı yenile → Pipeline'ı görüntüle!

### Docker Dashboard (Production)
1. ✅ `docker-compose up -d` → Servisleri başlat
2. ✅ Tarayıcıda http://localhost:8080 → Dashboard aç
3. ✅ `zenml connect --url http://localhost:8080` → Server'a bağlan
4. ✅ `python scripts\run_pipeline.py` → Pipeline'ı çalıştır
5. ✅ Dashboard'ı yenile → Pipeline'ı görüntüle!

---

**Sonuç:** Pipeline'larınız artık profesyonel bir dashboard ile izlenebilir durumda! 🚀

---

**Daha fazla bilgi için:**
- [Pipeline Kılavuzu](pipeline.md) - Pipeline detaylı kullanım
- [Proje Durumu](context.md) - Teknik geliştirme geçmişi
- [ZenML Documentation](https://docs.zenml.io/)
- Ana kılavuz: `../KULLANIM_KILAVUZU.md`
