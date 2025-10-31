LLM Twin (Yaşar Kemal Twin)
============================

Bu repository, Yaşar Kemal’in üslubuna yakın yanıtlar üreten bir RAG + LLM sistemini içerir.

- Hızlı başlangıç ve uçtan uca kurulum için kullanım kılavuzu: KULLANIM_KILAVUZU.md
- API kaynak kodu (mevcut): `src/api`
- Veri toplama (mevcut): `src/ingest`
- Embedding yükleme (mevcut): `src/embed/ingest_to_vectorstore.py`
- ZenML pipeline (mevcut): `src/pipeline`

Yeni, profesyonel paket yapısı (eklenmiştir ve kademeli geçiştedir):
- Uygulama paketi: `src/llm_twin/`
	- API: `src/llm_twin/api`
	- Ingest: `src/llm_twin/ingest`
	- Embedding: `src/llm_twin/embed`
	- Pipeline: `src/llm_twin/pipeline`
- Komut dosyaları: `scripts/`
	- Pipeline çalıştırma: `scripts/run_pipeline.py`
	- Görüntüleyiciler: `scripts/view_pipelines.py`, `scripts/view_pipelines_detailed.py`
	- ZenML Docker başlatma: `scripts/start_zenml_docker.ps1`

> Detaylı adımlar, Docker komutları, ZenML Dashboard ve sorun giderme için lütfen `KULLANIM_KILAVUZU.md` dosyasını okuyun.
# LLM Twin - Yaşar Kemal Digital Twin

🎯 **Amaç:** Yaşar Kemal'in üslubuna yakın yanıtlar verebilen RAG+LLM sistemi.

## ✨ Özellikler
- ✅ 1147 chunk'lık Yaşar Kemal metinleri (data_raw/)
- ✅ Semantic search (Qdrant + MongoDB)
- ✅ Persona-based LLM responses (Llama 3.1 8B)
- ✅ FastAPI REST API
- ✅ ZenML pipeline entegrasyonu

## 🚀 Hızlı Başlangıç

### 1. Kurulum
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Docker Servislerini Başlat
```powershell
docker run -d --name mongo -p 27017:27017 mongo
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### 3. API'yi Çalıştır
```powershell
uvicorn llm_twin.api.main:app --reload
```

### 4. Test Et
- Health: http://localhost:8000/health
- Persona sorgu: http://localhost:8000/ask_persona?question=Yaşar%20Kemal%20doğa%20hakkında%20ne%20düşünüyordu?

## 📚 Dokümantasyon
- **[Kullanım Kılavuzu](KULLANIM_KILAVUZU.md)** - Detaylı kullanım talimatları
- **[Pipeline Rehberi](docs/pipeline.md)** - ZenML pipeline kullanımı
- **[ZenML Kılavuzu](docs/zenml.md)** - Dashboard ve Docker setup
- **[Proje Durumu](docs/context.md)** - Teknik geliştirme geçmişi

## 🏗️ Proje Yapısı
```
llm-twin/
├── src/llm_twin/       # Ana Python paketi
│   ├── api/            # FastAPI endpoints
│   ├── ingest/         # Veri toplama
│   ├── embed/          # Vektörleştirme
│   └── pipeline/       # ZenML pipeline
├── scripts/            # CLI araçları
├── docs/               # Detaylı dokümantasyon
├── data_raw/           # Yaşar Kemal metinleri
└── docker/             # Dockerfile'lar
```

## 🛠️ Teknolojiler
- Python 3.11+
- FastAPI
- ZenML
- Qdrant (vector DB)
- MongoDB
- Llama 3.1 8B Instruct
- sentence-transformers

## 📄 Lisans
Bu proje akademik amaçlıdır. Ticari kullanım hedeflenmemiştir.

## 🤝 Katkıda Bulunma
Detaylar için [KULLANIM_KILAVUZU.md](KULLANIM_KILAVUZU.md) dosyasına bakın.
