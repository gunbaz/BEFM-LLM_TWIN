# LLM Twin

LLM Twin, RAG (Retrieval-Augmented Generation) tabanlı bilgi erişimi sağlayan bir sistemin temelini oluşturur. Bu repo, MongoDB üzerinde veri depolama, basit bir crawler, göm embedding iskeleti ve ZenML tarzı pipeline akışını içeren bir altyapı sunar.

## Mimari Bileşenler
- **MongoDB**: Ham belgelerin saklandığı kalıcı veri deposu.
- **Crawler**: Kaynak metinleri indirir ve MongoDB'ye yazar.
- **RAG Pipeline**: Dummy embedding fonksiyonu ve vektör store arabirimini içerir.
- **ZenML Pipeline**: Crawl → embed → store adımlarından oluşan, ZenML dekoratörleri ile entegre edilecek iskelet.

## Çalıştırma Talimatları
1. `docker-compose up -d` komutu ile MongoDB servisini başlatın.
2. `pip install -r requirements.txt` ile gerekli Python paketlerini yükleyin.
3. Örnek bir URL listesi ile crawler'ı çalıştırın: `python src/crawler/crawler.py https://example.com https://example.org`
4. Pipeline akışını göstermek için: `python src/zenml_pipeline/pipeline.py https://example.com https://example.org`

## Yaklaşan Görevler / TODO
- Gerçek embedding modeli ve sentence-transformers entegrasyonu.
- Qdrant veya benzeri bir vektör veritabanı ile entegrasyon.
- ZenML'in gerçek `@step` ve `@pipeline` dekoratörleri ile orkestrasyon.
