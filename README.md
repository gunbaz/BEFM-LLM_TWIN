# LLM Twin

LLM Twin, RAG (Retrieval-Augmented Generation) tabanlı bilgi erişimi sağlayan bir sistemin temelini oluşturur. Bu repo, MongoDB üzerinde veri depolama, basit bir crawler, gerçek embedding üretimi, Qdrant vektör veritabanı entegrasyonu ve ZenML pipeline akışını içeren bir altyapı sunar.

## Mimari Bileşenler
- **MongoDB**: Ham belgelerin saklandığı kalıcı veri deposu.
- **Crawler**: Kaynak metinleri indirir ve MongoDB'ye yazar.
- **RAG Pipeline**: SentenceTransformers tabanlı embedding üretir ve Qdrant'a yazar.
- **ZenML Pipeline**: Crawl → embed → store adımlarından oluşur ve ZenML dekoratörleri ile çalışır.
- **Qdrant**: Embedding vektörlerini depolayan ve sorgulayan vektör veritabanı.

## Çalıştırma Talimatları
1. `docker-compose up -d` komutu ile MongoDB ve Qdrant servislerini başlatın.
2. `pip install -r requirements.txt` ile gerekli Python paketlerini yükleyin (ZenML ve SentenceTransformers dahil).
3. Proje kök dizininde `zenml init` komutunu çalıştırarak ZenML'i yapılandırın.
4. Örnek bir URL listesi ile crawler'ı çalıştırın: `python src/crawler/crawler.py https://example.com https://example.org`
5. ZenML pipeline'ını çalıştırın: `python src/zenml_pipeline/pipeline.py`
   - Pipeline, MongoDB'den ham dokümanları okuyacak, SentenceTransformers ile embedding üretecek ve Qdrant'a upsert edecektir.

## Yaklaşan Görevler / TODO
- ZenML artifact store ve orchestrator yapılandırmasını ekle.
- Qdrant koleksiyon şeması ve indeks ayarlarını üretim için sertleştir.
- Crawler'ı gerçek web içeriği indirmesi ve temizlemesi için genişlet.
