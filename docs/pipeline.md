# Pipeline Kullanım Kılavuzu

## İçindekiler
1. [Hızlı Başlangıç](#hızlı-başlangıç)
2. [Pipeline Mimarisi](#pipeline-mimarisi)
3. [Kurulum](#kurulum)
4. [Pipeline'ı Çalıştırma](#piplineı-çalıştırma)
5. [Pipeline Görüntüleme](#pipeline-görüntüleme)
6. [Hata Ayıklama](#hata-ayıklama)
7. [SSS](#sık-sorulan-sorular)

---

## 🚀 Hızlı Başlangıç

### En Kolay Yöntem (Önerilen)

```bash
python scripts\view_pipelines_detailed.py
```

Bu size gösterecek:
- ✅ Tüm pipeline'lar
- 📊 En son run'ın detayları
- 📈 Step durumları ve süreleri
- 📜 Run geçmişi
- 📊 İstatistikler

### 📊 Şu Anki Durumunuz

```
Pipeline: llm_twin_ingestion_pipeline
Durum: ✅ COMPLETED
Steps: 5/5 tamamlandı
- step_collect_raw (cached)
- step_read_and_parse (cached)
- step_clean_text (cached)
- step_chunk_text (cached)
- step_embed_and_store (completed)

Sonuç: 1147 chunk başarıyla MongoDB ve Qdrant'e kaydedildi!
```

---

## Pipeline Mimarisi

### Pipeline Adımları

1. **step_collect_raw**: 
   - seed_urls.txt'deki URL'leri okur
   - batch_crawl ile metinleri toplar
   - data_raw/ klasörüne kaydeder

2. **step_read_and_parse**:
   - Ham dosyaları okur
   - SOURCE satırını parse eder
   - (source_url, text_body) tuple'ları üretir

3. **step_clean_text**:
   - Null byte'ları temizler
   - Fazla boşlukları normalize eder
   - Kısa satırları filtreler

4. **step_chunk_text**:
   - Metinleri 800 kelimelik parçalara böler
   - Her chunk için UUID üretir

5. **step_embed_and_store**:
   - sentence-transformers/all-MiniLM-L6-v2 ile embedding üretir
   - MongoDB'ye chunk metinlerini kaydeder
   - Qdrant'e vektörleri kaydeder

### Veri Akışı

```
seed_urls.txt → batch_crawl → data_raw/*.txt
              ↓
    step_collect_raw (ZenML)
              ↓
    step_read_and_parse
              ↓
      step_clean_text
              ↓
      step_chunk_text
              ↓
   step_embed_and_store
              ↓
    MongoDB + Qdrant
```

---

## Kurulum

### 1. ZenML'i Başlat (İlk Kez)
```bash
zenml init
```

### 2. ZenML Server'ı Başlat (Opsiyonel, UI için)
```bash
zenml up
```

### 3. Docker Servislerini Kontrol Et
Pipeline çalıştırılmadan önce MongoDB ve Qdrant container'larının ayakta olması gerekir:
```bash
docker ps
```

Eğer container'lar çalışmıyorsa:
```bash
docker start mongo
docker start qdrant
```

---

## Pipeline'ı Çalıştırma

### Basit Çalıştırma
```bash
python scripts\run_pipeline.py
```

### ZenML Dashboard'dan İzleme
1. ZenML server'ı başlat:
```bash
zenml up
```

2. Tarayıcıda açılan dashboard'dan pipeline'ları izle:
```
http://localhost:8237
```

3. Pipeline'ı çalıştır:
```bash
python scripts\run_pipeline.py
```

---

## Pipeline Görüntüleme

### 🎯 Yöntem 1: Detaylı Terminal Görünümü (Önerilen)
```bash
python scripts\view_pipelines_detailed.py
```

### 🎯 Yöntem 2: Basit Liste
```bash
python scripts\view_pipelines.py
```

### 🎯 Yöntem 3: Dashboard (Görsel - Opsiyonel)

**Yeni bir terminal açın ve çalıştırın:**
```bash
zenml login --local --blocking
```

**Tarayıcıda:**
```
http://localhost:8237
```

**⚠️ Not:** Blocking mode terminal'i meşgul eder. Dashboard kullanırken başka bir terminal açmalısınız.

---

## Hata Ayıklama

### ZenML Logları Görmek İçin:
```bash
zenml pipeline runs list
zenml pipeline runs describe <RUN_ID>
```

### Belirli Bir Step'in Çıktısını Görmek İçin:
```python
from zenml.client import Client

client = Client()
run = client.get_pipeline_run("<RUN_ID>")
step_output = run.steps["step_name"].output.load()
print(step_output)
```

---

## Pipeline Metrikleri

Pipeline başarıyla tamamlandığında şu bilgileri görürsünüz:
- MongoDB'e kaydedilen chunk sayısı
- Qdrant'e kaydedilen vektör sayısı
- Her step'in süre bilgileri (ZenML dashboard'da)

---

## 📁 Veriler Nerede?

- **MongoDB**: localhost:27017 (1147 chunk)
  - Database: `llm_twin`
  - Collection: `chunks`
- **Qdrant**: localhost:6333 (1147 vektör)
  - Collection: `yasar_kemal_twin`
- **ZenML Metadata**: `C:\Users\pc\AppData\Roaming\zenml\`
- **Proje Config**: `.zenml/`

---

## Sık Sorulan Sorular

### Pipeline'lar Docker'da görünmüyor?
✅ Normal! ZenML pipeline'ları Docker'da değil, kendi veritabanında saklanır.

### Dashboard açılmıyor?
✅ Windows'ta arka plan servisi çalışmıyor. Blocking mode kullanın veya terminal görüntüleyiciyi tercih edin.

### Versiyon uyumsuzluğu hatası?
✅ Proje içindeki Python kullanın: `C:/Users/pc/llm-twin/.venv/Scripts/python.exe`

### Pipeline re-run edildiğinde ne olur?
⚠️ Mevcut chunk'lar silinir ve yeniden oluşturulur.

---

## Önemli Notlar

- Pipeline'ı tekrar çalıştırmadan önce Docker servislerinin ayakta olduğundan emin olun
- Pipeline başarıyla tamamlandığında tüm chunk'lar MongoDB ve Qdrant'e kaydedilir
- Her step caching kullanır, değişiklik yoksa tekrar çalışmaz

---

## 🎉 Başarı!

Sisteminiz çalışıyor! Pipeline'ınız başarıyla tamamlandı ve verileriniz hazır.

```
✅ Veri toplama
✅ Vektörleştirme
✅ MongoDB kayıt
✅ Qdrant kayıt
✅ Pipeline tracking
```

Artık API'nizi kullanabilir veya yeni pipeline'lar çalıştırabilirsiniz! 🚀

---

**Daha fazla bilgi için:**
- [ZenML Kılavuzu](zenml.md) - ZenML detaylı kullanım
- [Proje Durumu](context.md) - Teknik geliştirme geçmişi
- Ana kılavuz: `../KULLANIM_KILAVUZU.md`
