
LLM Twin (Yaşar Kemal Twin) - Güncel Durum Özeti ve Yol Haritası
====================================================================

1. PROJENİN HEDEFİ
------------------
Amaç: Yaşar Kemal'in üslubuna, düşünce dünyasına ve anlatı tavrına mümkün olduğunca yakın şekilde cevap verebilen bir "LLM Twin" (dijital ikiz) üretmek.

Bu sistem tek bir şey yapmıyor, 3 şey yapıyor:
1) Yaşar Kemal'e ait veya Yaşar Kemal'in sesi kabul edilebilecek metinleri (roman, öykü, röportaj, deneme vb.) topluyor.
2) Bu metinleri küçük anlamlı parçalara (chunk) bölüp vektör olarak bir bilgi bankasına yüklüyor.
3) Kullanıcı soru sorduğunda, Yaşar Kemal'in dünyasından en alakalı pasajları bulup dönüyor ve bu pasajlarla Yaşar Kemal tarzında cevap üretiyor.

Yani bu sadece "soru-cevap botu" değil. Bu, tam fonksiyonel bir "persona + RAG + LLM" sistemi.

Not: Proje üniversite için akademik amaçlıdır. Ticari bir kullanım hedeflenmediği açıkça belirtilmiştir. Bu telif ve etik kısmı için önemli.

----------------------------------------------------------

2. GENEL MİMARİ
---------------
Sistemin şu an kurulu olan mimarisi 5 katmandan oluşuyor:

(1) Veri Toplama Katmanı (Ingestion)
    - Kaynak: Yaşar Kemal ile ilgili URL'ler (röportajlar, PDF'ler, kitap parçaları, denemeler vb.).
    - Ana Script: src/ingest/batch_crawl.py
    - Yardımcı Scriptler: 
        * src/ingest/crawler.py (temel crawling fonksiyonları)
        * src/ingest/discover.py (otomatik URL keşfi - deneysel)
        * src/ingest/filter_candidates.py (URL filtreleme - deneysel)
    
    - Çalışma şekli:
        * data_raw/seed_urls.txt dosyasında güvenilir URL listesi tutuluyor (14 manuel doğrulanmış link).
        * batch_crawl.py bu URL'lerin her birini geziyor.
        * Eğer link PDF ise:
              - PDF'i indiriyor (requests ile).
              - pdfminer.six ile PDF'ten düz metin çıkarıyor.
          Eğer link normal HTML sayfa ise:
              - Selenium ile sayfayı açıyor (JS yüklenmiş hâliyle, headless mode).
              - BeautifulSoup ile <p> etiketlerinden paragrafları çekiyor.
        * Metni temizliyor (null byte, fazla boşluk vb.).
        * data_raw/ klasörüne timestamp'li .txt dosyası olarak kaydediyor (örn: 20251028_205943_000.txt).
        * Dosyanın ilk satırına "SOURCE: <url>" yazıyor (izlenebilirlik için).

    Bu aşama sayesinde biz gerçekten "Yaşar Kemal'in sesi" olan uzun text bloklarını local olarak düz metin halinde elde ettik.

(2) Ham Veri Deposu (data_raw/)
    - data_raw/ klasörü bizim ham arşivimiz.
    - İçeriği:
        * seed_urls.txt (14 URL)
        * 13 adet timestamp'li .txt dosyası (20251028_*.txt formatında)
    - Her dosya şöyle yapılandırıldı:
        SOURCE: <kaynak URL>

        <gerçek metin gövdesi buraya kaydedildi>

    - Bu dosyalar artık yalnızca viewer sayfası değil, gerçek PDF gövdesinin text'i. 
    - Örnek: İnce Memed 1-4, Sarı Sıcak, Üç Anadolu Efsanesi, Binboğalar Efsanesi, Ağrı Dağı Efsanesi, Teneke, Bir Ada Hikayesi 1, vb.
    - Bu klasör şu an DOLU ve çalışan. Yani sistemin beyni var, boş değil.

(3) Vektörleştirme ve Kalıcı Depolama Katmanı
    - Script: src/embed/ingest_to_vectorstore.py
    - Adımlar:
        * data_raw/*.txt dosyalarını okuyor (seed_urls.txt hariç).
        * İlk satırdaki SOURCE bilgisini parse ediyor.
        * Geri kalan tüm gövde metni parçalara bölüyor ("chunk").
          - Chunk boyutu: CHUNK_SIZE = 800 kelime (basit word-split chunking).
          - Amaç: uzun bir PDF'i yüzlerce küçük parça halinde arayabilmek.
        * Her chunk için bir benzersiz chunk_id (uuid) oluşturuyor.
        * Her chunk için embedding üretmek için sentence-transformers/all-MiniLM-L6-v2 modeli kullanılıyor.
        * Bu embedding (ve chunk metni) iki yere yazılıyor:
            - MongoDB: metnin kendisini ve metadata'yı saklıyoruz.
                - DB: llm_twin
                - Koleksiyon: chunks
                - Kayıt formatı:
                    {
                      "_id": chunk_id,
                      "source_url": "<kaynak>",
                      "text": "<chunk metni>"
                    }
            - Qdrant: aynı chunk_id ile embedding vektörü saklanıyor.
                - Koleksiyon adı: yasar_kemal_twin
                - Vector config: COSINE distance
                - Her point şu şekilde kaydediliyor:
                    id = chunk_id
                    vector = embedding
                    payload = {
                        "text": <chunk metni>,
                        "source_url": <kaynak>
                    }

    Bu sayede:
    - MongoDB = metnin kendisi (insana okunabilir içerik)
    - Qdrant = o metnin sayısal temsili (aramaya uygun vektör)
    - chunk_id = ikisini birbirine bağlıyor.

    ingest_to_vectorstore.py BAŞARIYLA ÇALIŞTIRILDI:
        - "13 source documents" (data_raw içindeki belgeler).
        - "Inserted 1147 chunks into MongoDB."
        - "Upserted 1147 vectors into Qdrant."
      Yani şu anda ~1147 anlamlı metin parçamız var ve sistem gerçekten dolu.

(4) Retrieval Katmanı (Sorgulama)
    - API: /ask endpoint'i (FastAPI içinde - src/api/main.py)
    - Çalışma şekli:
        * Kullanıcı "Yaşar Kemal doğa hakkında ne düşünüyordu?" gibi bir soru soruyor.
        * retrieve_top_chunks() fonksiyonu:
            1. Soruyu sentence-transformers ile embedding'e çevirir.
            2. Qdrant'te "bu soruya en yakın hangi chunk'lar var?" diye semantic search yapar.
            3. En iyi eşleşen ilk top_k (default=3) sonuç alır.
            4. Her sonuçtaki chunk_id ile MongoDB'ye gidip gerçek metin bulur.
        * JSON olarak geri döner:
            {
              "question": "...",
              "matches": [
                {
                  "score": ...,
                  "text": "...chunk'ın ilk 400 karakteri...",
                  "source_url": "..."
                },
                ...
              ]
            }

    Bu endpoint TEST EDİLDİ ve ÇALIŞIYOR.
    Soru: "Yaşar Kemal doğa hakkında ne düşünüyordu?"
    Dönen pasajlar: doğanın canlılığı, insanın doğayla bağı, ezilen halkın toprakla ilişkisi, direniş, onur, dağ, ova, rüzgâr…
    Yani semantik retrieval doğru çalışıyor. Rastgele saçmalık dönmüyor, konuyla tematik olarak ilgili Yaşar Kemal pasajları dönüyor.

(5) Persona + LLM Katmanı ✅ TAM FONKSİYONEL
    - API endpoint: /ask_persona (FastAPI içinde - src/api/main.py)
    - LLM Modülleri:
        * src/api/llm_infer.py: Ana inference fonksiyonu (generate_answer)
        * src/api/llm_local.py: Lokal Llama 3.1 8B Instruct modeli yükleme ve inference
    
    - Çalışma şekli:
        * Kullanıcının sorusunu al.
        * retrieve_top_chunks() ile Qdrant→Mongo üzerinden en alakalı chunk'ları topla.
        * Bu chunk'ları kullanarak bir "persona prompt" hazırla.
        * Prompt içeriği:
            - "Sen Yaşar Kemal değilsin ama onun anlatı ruhuna yakın konuş."
            - "Doğayı canlı bir varlık gibi anlat."
            - "Ezilen insanı onurlu ve dirençli göster."
            - "Metni olduğu gibi kopyalama, kendi sözlerinle özetle."
            - "Kısa ama yoğun ol."
            - İlgili parçalar (chunk'lar) ekleniyor.
        * Bu prompt llm_infer.generate_answer() ile Llama 3.1 8B modeline gönderiliyor.
        * Model cevabı üretiyor (max_new_tokens=300, temperature=0.7).
        * Response olarak döner:
            {
              "question": "...",
              "answer": "...Yaşar Kemal tarzında üretilen cevap...",
              "used_chunks": [
                {
                  "source_url": "...",
                  "preview": "...ilk 200 karakter..."
                },
                ...
              ]
            }

    ✅ BU KATMAN ARTIK TAM FONKSİYONEL!
    - Llama 3.1 8B Instruct modeli torch + transformers + bitsandbytes ile yükleniyor.
    - LOW_MEM_MODE=True: 8-bit quantization ile düşük bellekte çalışıyor.
    - device_map="auto": GPU varsa GPU, yoksa CPU kullanıyor.
    - Model uygulama başlarken yükleniyor (startup sırasında).

----------------------------------------------------------

3. KULLANDIĞIMIZ ANA ARAÇLAR VE DURUMLARI
-----------------------------------------

✅ Python sanal ortamı (.venv):
    Proje için gerekli tüm paketler yüklendi. pip ile yönetiliyor.
    requirements.txt güncel (torch, transformers, accelerate, bitsandbytes, sentence-transformers, fastapi, uvicorn, selenium, beautifulsoup4, pymongo, qdrant-client, zenml, vb.)

✅ Docker:
    MongoDB ve Qdrant docker container olarak ayağa kaldırıldı.
    docker ps çıktısında:
        - mongo (27017 portu)
        - qdrant (6333 portu)
    Qdrant dashboard: http://localhost:6333/dashboard (erişilebilir)

✅ MongoDB:
    Yerel olarak auth'suz container'da koşuyor. 
    - Database: llm_twin
    - Collection: chunks (1147 kayıt)
    - Her kayıt: _id (chunk_id), source_url, text

✅ Qdrant:
    - Collection: yasar_kemal_twin (1147 vektör)
    - Vector size: 384 (all-MiniLM-L6-v2 output dimension)
    - Distance: COSINE
    - Bu koleksiyon semantic search için kullanılıyor.

✅ sentence-transformers:
    Model: all-MiniLM-L6-v2
    Bu model hem chunk embedding'i hem soru embedding'i için kullanılıyor.
    Bu sayede soru ile pasajlar aynı vektör uzayında karşılaştırılabiliyor.

✅ Llama 3.1 8B Instruct:
    Model: meta-llama/Meta-Llama-3.1-8B-Instruct
    Yükleme: torch + transformers + bitsandbytes (8-bit quantization)
    Kullanım: /ask_persona endpoint'inden persona prompt'u alıp Yaşar Kemal tarzında cevap üretiyor.
    Max tokens: 300
    Temperature: 0.7
    Top-p: 0.9
    Repetition penalty: 1.1

✅ FastAPI + Uvicorn:
    src/api/main.py içinde uygulama var.
    Endpoint'ler:
        - GET /health -> sistem ayakta mı? (mongo_ok, qdrant_ok kontrolü)
        - GET /ask -> semantik arama yap ve en benzer pasajları göster (debug amaçlı)
        - GET /ask_persona -> Yaşar Kemal tarzında tam cevap üret (TAM FONKSİYONEL ✅)

✅ Selenium + BeautifulSoup:
    HTML sayfalarından içerik toplamak için kullanıldı.
    Tarayıcıyı headless modda açıyor (--headless=new, --no-sandbox, --disable-dev-shm-usage).
    Sayfayı tamamen yüklettikten sonra paragraf metinlerini topluyoruz.

✅ pdfminer.six:
    PDF linklerini indirmek ve düz metin çıkarmak için kullanılıyor.
    Bu sayede elimizde gerçek Yaşar Kemal yazılarına ait uzun düz text var.
    Null byte temizleme yapılıyor.

✅ ZenML (TAM FONKSİYONEL):
    - src/pipeline/pipeline.py: llm_twin_ingestion_pipeline() tanımlı ve çalışıyor
    - src/pipeline/steps.py: 5 tam fonksiyonel step:
        * step_collect_raw(): Veri toplama (batch_crawl entegrasyonu)
        * step_read_and_parse(): Dosya okuma ve SOURCE parse
        * step_clean_text(): Metin temizleme ve normalize
        * step_chunk_text(): 800 kelimelik chunk'lara bölme + UUID
        * step_embed_and_store(): Embedding + MongoDB/Qdrant kaydetme
    - run_pipeline.py: Pipeline runner script
    - PIPELINE_GUIDE.md: Detaylı kullanım kılavuzu
    Amaç: MLOps / LLMOps disiplinine uygun otomasyon tarafını göstermek.
    ✅ Pipeline tam fonksiyonel ve çalıştırılabilir!

⏳ Docker Compose:
    docker/ klasöründe api.Dockerfile ve tgi.Dockerfile var ama boş.
    Henüz docker-compose.yml yok.
    Şu an mongo ve qdrant manuel olarak docker run ile çalıştırılıyor.

----------------------------------------------------------

4. BUGÜNE KADAR YAŞANAN ÖNEMLİ DÖNÜM NOKTALARI
----------------------------------------------

(1) İlk başta URL keşfini otomatik yapmak istedik (discover.py, filter_candidates.py).
    - discover.py: Bing aramalarını Selenium ile çalıştırıp "Yaşar Kemal röportaj", "Yaşar Kemal söyleşi" gibi anahtar kelimelerle toplu link listeledi.
    - filter_candidates.py: linklerin içeriğini kontrol edip alakasız olanları (örneğin "Yaşar konseri") elemek istedi.
    - Problem:
        * Bazı sayfalar JS ile içerik yüklediği için requests ile çektiğimiz gövde boştı.
        * "Yaşar" geçen ama "Yaşar Kemal" olmayan şeyler çok geldi (şarkıcı vb.).
        * Skorlamamız fazla katıydı, kalan link sayısı 0 oluyordu.
    - Sonuç:
        * Tamamen otomatik "link keşfi" bu aşamada güvenilir olmadı.

(2) Çözüm: İnsan destekli tohum (seed) yaklaşımına geçtik.
    - data_raw/seed_urls.txt diye bir dosya oluşturuldu.
    - Bu dosyada gerçekten Yaşar Kemal'e ait veya onunla doğrudan ilgili 14 link listelendi:
        * Archive.org'dan İnce Memed 1-4 PDF'leri
        * Yandex docviewer'dan Sarı Sıcak PDF
        * el-kitap.org ve kitab-evi.com'dan çeşitli Yaşar Kemal eserleri
        * Yapı Kredi Yayınları'ndan tadımlık PDF'ler
    - Bundan sonra pipeline şöyle oldu:
        * seed_urls.txt -> batch_crawl.py -> data_raw/*.txt (13 dosya)
    - Bu, sektörde profesyonelce kabul edilen bir yöntemdir (curated seed set + otomatik toplama).

(3) PDF sorunu çözüldü.
    - İlk sürümlerde sadece Selenium'dan page_source alıyorduk. Bu, PDF viewer sayfasının kendisini kaydediyordu; gerçek metni değil.
    - Sonra batch_crawl.py geliştirilerek:
        * `is_pdf_url()` ile link PDF mi diye bakılıyor (.pdf uzantısı kontrolü).
        * PDF ise doğrudan requests ile indiriliyor (tmp_download.pdf).
        * pdfminer.six ile text'e çevriliyor.
        * Null byte (\x00) temizleniyor.
    - Bu sayede artık data_raw/*.txt dosyalarının gövdesi gerçekten Yaşar Kemal metni oldu.

(4) ingest_to_vectorstore.py başarıyla çalıştı ve sistem doldu.
    - 13 belge işlendi.
    - ~1147 chunk ortaya çıktı.
    - Bu chunk'lar MongoDB ve Qdrant'e kaydedildi.
    - Bu sistemin "beyni" artık gerçek olarak var.

(5) /ask endpoint'i ile gerçekte semantik arama yapabildik.
    - Sisteme "Yaşar Kemal doğa hakkında ne düşünüyordu?" diye sorduk.
    - Geri dönen pasajlar doğa, toprak, ezilen halk vs. üzerineydi.
    - Bu, retrieval tarafının gerçekten çalıştığını kanıtlıyor.

(6) /ask_persona endpoint'i tasarlandı ve TAM FONKSİYONEL HALE GETİRİLDİ.
    - Bu endpoint, kullanıcı sorusu + en yakın chunk'ları bir araya getirip LLM'e gönderilecek prompt'u kuruyor.
    - Prompt şu yönergeleri içeriyor:
        * "Sen Yaşar Kemal değilsin ama onun sesi gibi konuş."
        * "Doğayı canlı, insanı onurlu anlat."
        * "Metni kopyalama, kendi sözlerinle söyle."
    - Bu kısım telif / etik güvenliğini de içinde taşıyor.
    - llm_local.py ile Llama 3.1 8B Instruct modeli entegre edildi.
    - Model başlangıçta yükleniyor (8-bit quantization ile).
    - generate_local_response() fonksiyonu prompt'u alıp cevap üretiyor.

----------------------------------------------------------

5. ŞU ANKİ DURUM (ÖNEMLİ SNAPSHOT - 30 Ekim 2025)
-----------------------------------------------

✅ Sistem TAM FONKSİYONEL ve ÜRETİM HAZIR:

- data_raw klasöründe:
    ✅ 13 adet timestamp'li .txt dosyası (Yaşar Kemal eserleri)
    ✅ seed_urls.txt (14 kaynak URL)
    ✅ Toplam içerik: İnce Memed serisi, Sarı Sıcak, Üç Anadolu Efsanesi, Binboğalar, Ağrı Dağı, Teneke, vb.

- batch_crawl.py:
    ✅ seed_urls.txt içindeki linklere gidip metinleri otomatik topluyor
    ✅ PDF + HTML destekliyor
    ✅ pdfminer.six ile PDF parsing
    ✅ Selenium ile JS-loaded sayfa parsing
    ✅ Sonuç: 13 dosya başarıyla toplandı

- ingest_to_vectorstore.py:
    ✅ Bu kaydedilmiş metinleri alıyor, chunk'luyor (800 kelime), embedding çıkıyor
    ✅ MongoDB ve Qdrant içine yüklüyor
    ✅ Sonuç: 1147 chunk başarıyla oluşturuldu ve kaydedildi

- Docker:
    ✅ MongoDB konteyner çalışıyor (27017 portu)
    ✅ Qdrant konteyner çalışıyor (6333 portu)
    ✅ Qdrant dashboard erişilebilir
    ✅ Sağlık kontrolü: mongo_ok=True, qdrant_ok=True

- FastAPI:
    ✅ /health -> sistem sağlığı kontrolü (çalışıyor)
    ✅ /ask -> semantik arama (test edildi, çalışıyor)
    ✅ /ask_persona -> TAM FONKSİYONEL Yaşar Kemal tarzında cevap üretiyor
    ✅ Llama 3.1 8B Instruct modeli yüklü ve çalışıyor

Yani:
    ✅ Veri toplama (Ingestion)
    ✅ Vektör veritabanı (Qdrant + MongoDB)
    ✅ Semantic Retrieval (RAG)
    ✅ API (FastAPI)
    ✅ Persona prompt üretimi
    ✅ LLM inference (Llama 3.1 8B)
    ✅ Tam fonksiyonel end-to-end sistem

Pratik olarak:
✅ Sistemimiz TAM OLARAK ÇALIŞIYOR ve kullanıma hazır!
✅ Kullanıcı soru soruyor → sistem alakalı Yaşar Kemal pasajlarını buluyor → Llama modeli Yaşar Kemal tarzında cevap üretiyor.

----------------------------------------------------------

6. SONRAKİ ADIMLAR (İYİLEŞTİRME VE GENIŞLETME)
-------------------------------------------

A) ✅ TAMAMLANDI: /ask_persona endpoint'ini bitirmek
    ✅ Llama 3.1 8B Instruct modeli entegre edildi
    ✅ llm_local.py ve llm_infer.py modülleri eklendi
    ✅ Persona prompt otomatik olarak LLM'e gönderiliyor
    ✅ Kullanıcı tek endpoint ile doğrudan "Yaşar Kemal tarzında" yanıt alıyor

B) ✅ TAMAMLANDI: ZenML pipeline'ını tamamlamak
    ✅ 5 tam fonksiyonel step oluşturuldu
    ✅ Pipeline tam entegre ve çalışıyor
    ✅ run_pipeline.py runner script eklendi
    ✅ PIPELINE_GUIDE.md kullanım kılavuzu eklendi
    ✅ "MLOps / LLMOps standartlarına uygun veri hattı" başarıyla gösterildi
    ✅ Pipeline: Veri toplama → Parse → Temizlik → Chunking → Embedding → DB kaydetme

C) ⏳ Docker Compose (opsiyonel iyileştirme)
    - docker-compose.yml dosyası oluşturularak tüm servisler tek komutla ayağa kaldırılabilir:
        * mongodb
        * qdrant
        * api (FastAPI uygulaması)
    - docker/api.Dockerfile doldurulmalı (şu an boş)
    - docker/tgi.Dockerfile doldurulmalı (şu an boş)
    - Bu, "projeyi baştan ayağa kaldırmak tek tuş" demek olur.
    - Öncelik: ORTA (deployment kolaylığı için faydalı)

D) ⏳ Model optimizasyonu (opsiyonel iyileştirme)
    - Şu an Llama 3.1 8B 8-bit quantization ile yükleniyor.
    - Alternatifler:
        * 4-bit quantization (daha düşük bellek)
        * GGUF format + llama.cpp (daha hızlı inference)
        * vLLM (batch inference için)
        * Text Generation Inference (TGI) server (production-grade)
    - Öncelik: ORTA (performans iyileştirmesi için)

E) ⏳ Web UI / Streamlit arayüzü (opsiyonel)
    - Kullanıcıların tarayıcıdan soru sorabilmesi için basit bir web UI.
    - Streamlit veya Gradio kullanılabilir.
    - Öncelik: ORTA (demo amaçlı faydalı)

F) ⏳ Daha fazla veri toplama (opsiyonel)
    - seed_urls.txt'ye daha fazla kaynak eklenebilir (özellikle röportajlar, makaleler, denemeler).
    - Discover.py ve filter_candidates.py iyileştirilebilir.
    - Öncelik: DÜŞÜK (mevcut 1147 chunk yeterli)

G) ⏳ Chunk stratejisi iyileştirmesi (opsiyonel)
    - Şu an basit word-split chunking kullanılıyor (800 kelime).
    - Alternatifler:
        * Sentence-based chunking (daha anlamlı parçalar)
        * Overlap eklemek (chunk'lar arası bilgi kaybını azaltmak)
        * Semantic chunking (LangChain)
    - Öncelik: DÜŞÜK (mevcut chunking çalışıyor)

----------------------------------------------------------

7. AKADEMİK / ETİK NOT
----------------------
Bu proje açıkça akademik bir çalışmadır.
Toplanan içeriklerin bazıları telif kapsamındadır (örneğin roman pasajları).
Bu içerikler:
    - lokal ortamda tutulmaktadır (data_raw/ klasörü)
    - direkt olarak paylaşılmamakta, yalnızca anlam ve üslup analizi için kullanılmaktadır
    - son kullanıcıya otomatik şekilde uzun kopyalar halinde geri verilmemesi için
      /ask_persona prompt'unda kural konmuştur:
        "Metni doğrudan kopyalama; kendi sözlerinle anlat."
    - /ask endpoint'i chunk'ları 400 karakter ile kırparak döndürüyor (telif koruması)
    - /ask_persona endpoint'i chunk preview'ları 200 karakter ile kırpıyor

Ayrıca sistem, Yaşar Kemal'i "ben Yaşar Kemal'im" diye konuşturmaya zorlanmıyor;
"onun diline yakın ol ama onun olduğunu iddia etme" gibi yönergeler kullanılıyor.
Bu, etik sunum açısından önemlidir.

Prompt içinde açıkça belirtilen kurallar:
    - "Sen Yaşar Kemal değilsin"
    - "Metni bire bir kopyalama"
    - "Kendi sözlerinle yeniden anlat"
    - "İlgili parçaları sadece ruh olarak kullan"

----------------------------------------------------------

8. PROJE YAPISI (Güncel)
------------------------
```
llm-twin/
├── context.txt                          # Bu dosya (güncel proje durumu)
├── README.md                            # Boş (doldurulabilir)
├── requirements.txt                     # Python bağımlılıkları (güncel)
├── data_raw/                            # Ham veri deposu ✅
│   ├── seed_urls.txt                    # 14 kaynak URL
│   └── 20251028_*.txt                   # 13 metin dosyası (Yaşar Kemal eserleri)
├── data_clean/                          # Boş (şimdilik kullanılmıyor)
├── embeddings/                          # Boş (embedding'ler Qdrant'te)
├── docker/                              # Docker dosyaları (kısmen hazır)
│   ├── api.Dockerfile                   # Boş (doldurulacak)
│   └── tgi.Dockerfile                   # Boş (doldurulacak)
├── src/
│   ├── ingest/                          # Veri toplama modülleri ✅
│   │   ├── batch_crawl.py               # Ana veri toplama scripti
│   │   ├── crawler.py                   # Temel crawler fonksiyonları
│   │   ├── discover.py                  # Otomatik URL keşfi (deneysel)
│   │   └── filter_candidates.py         # URL filtreleme (deneysel)
│   ├── embed/                           # Embedding modülleri ✅
│   │   └── ingest_to_vectorstore.py     # Chunk + embedding + Qdrant/Mongo yükleme
│   ├── api/                             # FastAPI uygulaması ✅
│   │   ├── main.py                      # Ana API (health, ask, ask_persona)
│   │   ├── llm_infer.py                 # LLM inference wrapper
│   │   └── llm_local.py                 # Llama 3.1 8B yükleme + inference
│   ├── pipeline/                        # ZenML pipeline ✅
│   │   ├── pipeline.py                  # Pipeline tanımı (tam fonksiyonel)
│   │   └── steps.py                     # 5 tam fonksiyonel step
│   ├── schemas/                         # Boş
│   └── store/                           # Boş
├── run_pipeline.py                      # ZenML pipeline runner ✅
├── view_pipelines.py                    # Pipeline görüntüleyici ✅
├── PIPELINE_GUIDE.md                    # Pipeline kullanım kılavuzu ✅
├── ZENML_GUIDE.md                       # ZenML görüntüleme rehberi ✅
├── zenml_config/                        # Boş
└── .venv/                               # Python sanal ortamı
```

----------------------------------------------------------

9. NASIL ÇALIŞTIRILIR? (Hızlı Başlangıç)
---------------------------------------

1. Gereksinimleri kur:
   ```bash
   pip install -r requirements.txt
   ```

2. Docker servislerini başlat:
   ```bash
   docker run -d --name mongo -p 27017:27017 mongo
   docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
   ```

3. (İsteğe bağlı) Veri topla:
   ```bash
   python src/ingest/batch_crawl.py
   ```

4. (İsteğe bağlı) Vektörleri yükle:
   ```bash
   python src/embed/ingest_to_vectorstore.py
   ```

5. API'yi başlat:
   ```bash
   cd src/api
   uvicorn main:app --reload
   ```

6. Tarayıcıdan test et:
   - Health check: http://localhost:8000/health
   - Semantic search: http://localhost:8000/ask?question=Yaşar%20Kemal%20doğa%20hakkında%20ne%20düşünüyordu?
   - Persona cevap: http://localhost:8000/ask_persona?question=Yaşar%20Kemal%20doğa%20hakkında%20ne%20düşünüyordu?

----------------------------------------------------------

10. ÖZET CÜMLESİ (SON DURUM - 30 Ekim 2025)
-----------------------------------------
✅ Sistemimiz TAM FONKSİYONEL ve KULLANIMA HAZIR!

- ✅ Yaşar Kemal metinlerinden oluşan zengin bir bilgi tabanı var (1147 chunk).
- ✅ Bu bilgi tabanı otomatik olarak parçalanmış, embedding'lenmiş ve hem MongoDB'ye hem Qdrant'e yazılmış durumda.
- ✅ Qdrant üzerinden semantik arama yapıyoruz ve bu çalışıyor (canlı test edildi).
- ✅ FastAPI ile REST API katmanımız var: /health, /ask, /ask_persona.
- ✅ /ask_persona endpoint'i Yaşar Kemal benzeri cevap üretmek için Llama 3.1 8B Instruct modelini kullanıyor.
- ✅ Persona prompt otomatik olarak LLM'e gönderiliyor ve cevap üretiliyor.
- ✅ ZenML pipeline TAM FONKSİYONEL: 5 step'li otomatik veri işleme pipeline'ı çalışıyor.
- ✅ Pipeline test edildi: 13 dosya → parse → temizlik → 1147 chunk → embedding → DB kaydetme
- ✅ Tüm sistem end-to-end çalışıyor: Soru → Retrieval → Persona Prompt → LLM → Cevap

Sistem artık ÜRETİM HAZIR ve akademik sunum için TAM!

MLOps/LLMOps özellikleri:
    ✅ ZenML ile izlenebilir pipeline
    ✅ Otomatik veri toplama ve işleme
    ✅ Reproducible runs (aynı pipeline tekrar çalıştırılabilir)
    ✅ Step-level tracking ve logging
    ✅ Pipeline versioning

Bir sonraki odak noktaları (opsiyonel iyileştirmeler):
    - Docker Compose ile deployment kolaylığı
    - Web UI eklenmesi (Streamlit/Gradio)
    - Model optimizasyonu (4-bit quant, vLLM, TGI)
    - ZenML dashboard ile görselleştirme

(End of report - Son güncelleme: 30 Ekim 2025)

----------------------------------------------------------

2. GENEL MİMARİ
---------------
Sistemin şu an kurulu olan mimarisi 5 katmandan oluşuyor:

(1) Veri Toplama Katmanı (Ingestion)
    - Kaynak: Yaşar Kemal ile ilgili URL’ler (röportajlar, PDF’ler, kitap parçaları, denemeler vb.).
    - Script: batch_crawl.py
    - Çalışma şekli:
        * seed_urls.txt dosyasında güvenilir URL listesi tutuluyor (manuel doğrulanmış linkler).
        * batch_crawl.py bu URL’lerin her birini geziyor.
        * Eğer link PDF ise:
              - PDF’i indiriyor.
              - pdfminer.six ile PDF’ten düz metin çıkarıyor.
          Eğer link normal HTML sayfa ise:
              - Selenium ile sayfayı açıyor (JS yüklenmiş hâliyle).
              - BeautifulSoup ile <p> etiketlerinden paragrafları çekiyor.
        * Metni temizliyor.
        * data_raw/ klasörüne timestamp’li .txt dosyası olarak kaydediyor.
        * Dosyanın ilk satırına “SOURCE: <url>” yazıyor (izlenebilirlik için).

    Bu aşama sayesinde biz gerçekten “Yaşar Kemal’in sesi” olan uzun text bloklarını local olarak düz metin halinde elde ettik.

(2) Ham Veri Deposu (data_raw/)
    - data_raw/ klasörü bizim ham arşivimiz.
    - İçindeki her dosya şöyle yapılandırıldı:
        SOURCE: <kaynak URL>

        <gerçek metin gövdesi buraya kaydedildi>

    - Bu dosyalar artık yalnızca viewer sayfası değil, gerçek PDF gövdesinin text’i. Yani kaynaktan gelen ham Yaşar Kemal anlatısı elimizde.
    - Bu klasör şu an DOLU. Yani sistemin beyni var, boş değil.

(3) Vektörleştirme ve Kalıcı Depolama Katmanı
    - Script: ingest_to_vectorstore.py
    - Adımlar:
        * data_raw/*.txt dosyalarını okuyor.
        * İlk satırdaki SOURCE bilgisini alıyor.
        * Geri kalan tüm gövde metni parçalara bölüyor (“chunk”).
          - Chunk boyutu CHUNK_SIZE = 800 kelime civarı.
          - Amaç: uzun bir PDF’i yüzlerce küçük parça halinde arayabilmek.
        * Her chunk için bir benzersiz chunk_id (uuid) oluşturuyor.
        * Her chunk için embedding üretmek için sentence-transformers/all-MiniLM-L6-v2 modeli kullanılıyor.
        * Bu embedding (ve chunk metni) iki yere yazılıyor:
            - MongoDB: metnin kendisini ve metadata’yı saklıyoruz.
                - DB: llm_twin
                - Koleksiyon: chunks
                - Kayıt formatı:
                    {
                      "_id": chunk_id,
                      "source_url": "<kaynak>",
                      "text": "<chunk metni>"
                    }
            - Qdrant: aynı chunk_id ile embedding vektörü saklanıyor.
                - Koleksiyon adı: yasar_kemal_twin
                - Her point şu şekilde kaydediliyor:
                    id = chunk_id
                    vector = embedding
                    payload = {
                        "text": <chunk metni>,
                        "source_url": <kaynak>
                    }

    Bu sayede:
    - MongoDB = metnin kendisi (insana okunabilir içerik)
    - Qdrant = o metnin sayısal temsili (aramaya uygun vektör)
    - chunk_id = ikisini birbirine bağlıyor.

    ingest_to_vectorstore.py çalıştırıldı ve sonuç:
        - “13 source documents” (data_raw içindeki belgeler).
        - “Inserted 1147 chunks into MongoDB.”
        - “Upserted 1147 vectors into Qdrant.”
      Yani şu anda ~1147 anlamlı metin parçamız var ve sistem gerçekten dolu.

(4) Retrieval Katmanı (Sorgulama)
    - API: /ask endpoint’i (FastAPI içinde)
    - Çalışma şekli:
        * Kullanıcı “Yaşar Kemal doğa hakkında ne düşünüyordu?” gibi bir soru soruyor.
        * Kod bu soruyu embedding’e çeviriyor (aynı sentence-transformers modeliyle).
        * Qdrant’te “bu soruya en yakın hangi chunk’lar var?” diye semantic search yapılıyor.
        * En iyi eşleşen ilk N (mesela 3) sonuç alınıyor.
        * Her sonuçtaki chunk_id ile MongoDB’ye gidilip gerçek metin bulunuyor.
        * JSON olarak geri dönüyor:
            {
              "question": "...",
              "matches": [
                {
                  "score": ...,
                  "text": "...chunk'ın içinden bir pasaj...",
                  "source_url": "..."
                },
                ...
              ]
            }

    Bu endpoint TEST EDİLDİ.
    Soru: “Yaşar Kemal doğa hakkında ne düşünüyordu?”
    Dönen pasajlar: doğanın canlılığı, insanın doğayla bağı, ezilen halkın toprakla ilişkisi, direniş, onur, dağ, ova, rüzgâr…
    Yani semantik retrieval doğru çalışıyor. Rastgele saçmalık dönmüyor, konuyla tematik olarak ilgili Yaşar Kemal pasajları dönüyor.

(5) Persona Katmanı
    - API taslağı: /ask_persona endpoint’i
    - Görevi:
        * Kullanıcının sorusunu al.
        * Yine Qdrant→Mongo üzerinden en alakalı chunk’ları topla.
        * Bu chunk’ları kullanarak bir “persona prompt” hazırla.
        * Bu prompt şu yönergeleri içeriyor:
            - “Sen Yaşar Kemal değilsin ama onun anlatı ruhuna yakın konuş.”
            - “Doğayı canlı bir varlık gibi anlat.”
            - “Ezilen insanı onurlu ve dirençli göster.”
            - “Metni olduğu gibi kopyalama, kendi sözlerinle özetle.”
            - “Kısa ama yoğun ol.”
        * Prompt’un sonunda “CEVAP:” bırakılıyor.
        * Bu prompt JSON halinde geri dönüyor.

    Henüz bu prompt otomatik olarak bir LLM’e gönderilip cevap üretmiyor, ama bu endpoint tasarlandı. Yani stil sentezi için arayüz hazır.

----------------------------------------------------------

3. KULLANDIĞIMIZ ANA ARAÇLAR VE DURUMLARI
-----------------------------------------

- Python sanal ortamı (venv):
    Proje için gerekli tüm paketler yüklendi. pip ile yönetiliyor.

- Docker:
    MongoDB ve Qdrant docker container olarak ayağa kaldırıldı.
    docker ps çıktısında:
        - mongo (27017)
        - qdrant (6333)
    Qdrant dashboard’u tarayıcıdan açılabildi.

- MongoDB:
    Yerel olarak auth’suz container’da koşturuluyor. llm_twin isimli veritabanı var, chunks koleksiyonu var ve 1000+ kayıt içeriyor.

- Qdrant:
    yasar_kemal_twin isimli bir koleksiyon oluşturuldu.
    Bu koleksiyona 1147 vektör yüklendi.
    Bu koleksiyon semantic search için kullanılıyor.

- sentence-transformers:
    all-MiniLM-L6-v2 modeli kullanılıyor.
    Bu model hem chunk embedding’i hem soru embedding’i için kullanılıyor.
    Bu sayede soru ile pasajlar aynı uzayda karşılaştırılabiliyor.

- FastAPI + Uvicorn:
    src/api/main.py içinde uygulama var.
    /health endpoint’i mongo_ok ve qdrant_ok döndürerek servislerin ayakta olduğunu gösteriyor.
    /ask endpoint’i çalışıyor ve test edildi.
    /ask_persona endpoint’i prompt üretmek üzere tasarlandı.

- Selenium + BeautifulSoup:
    HTML sayfalarından içerik toplamak için kullanıldı.
    Tarayıcıyı headless (görünmez) modda açıyoruz. Sayfayı tamamen yüklettikten sonra paragraf metinlerini topluyoruz.

- pdfminer.six:
    PDF linklerini indirmek ve düz metin çıkarmak için kullanılıyor.
    Bu sayede elimizde gerçek Yaşar Kemal yazılarına ait uzun düz text var.

- ZenML:
    ZenML pipeline iskeleti hazırlandı, step’ler tanımlandı ama henüz pipeline aktif olarak bağlanmadı.
    Amaç:
        * step_collect_raw  -> veri toplama (batch crawl)
        * step_clean_text   -> metni temizleme, gereksiz header/footer silme
        * step_embed_and_store -> embedding + Mongo/Qdrant’e yükleme
    Bu kısım “MLOps / LLMOps disiplinine uygun otomasyon” tarafını göstermek için var.

----------------------------------------------------------

4. BUGÜNE KADAR YAŞANAN ÖNEMLİ DÖNÜM NOKTALARI
----------------------------------------------

(1) İlk başta URL keşfini otomatik yapmak istedik (discover.py, filter_candidates.py).
    - discover.py: Bing aramalarını Selenium ile çalıştırıp “Yaşar Kemal röportaj”, “Yaşar Kemal söyleşi” gibi anahtar kelimelerle toplu link listeledi.
    - filter_candidates.py: linklerin içeriğini kontrol edip alakasız olanları (örneğin “Yaşar konseri”) elemek istedi.
    - Problem:
        * Bazı sayfalar JS ile içerik yüklediği için requests ile çektiğimiz gövde boştı.
        * “Yaşar” geçen ama “Yaşar Kemal” olmayan şeyler çok geldi (şarkıcı vb.).
        * Skorlamamız fazla katıydı, kalan link sayısı 0 oluyordu.
    - Sonuç:
        * Tamamen otomatik “link keşfi” bu aşamada güvenilir olmadı.

(2) Çözüm: İnsan destekli tohum (seed) yaklaşımına geçtik.
    - seed_urls.txt diye bir dosya oluşturuldu.
    - Bu dosyada gerçekten Yaşar Kemal’e ait veya onunla doğrudan ilgili (röportaj, deneme, roman PDF’i vb.) linkler listelendi.
    - Bundan sonra pipeline şöyle oldu:
        * seed_urls.txt -> batch_crawl.py -> data_raw/*.txt
    - Bu, sektörde profesyonelce kabul edilen bir yöntemdir (curated seed set + otomatik toplama).

(3) PDF sorunu çözüldü.
    - İlk sürümlerde sadece Selenium’dan page_source alıyorduk. Bu, PDF viewer sayfasının kendisini kaydediyordu; gerçek metni değil.
    - Sonra batch_crawl.py geliştirilerek:
        * `is_pdf_url()` ile link PDF mi diye bakılıyor.
        * PDF ise doğrudan indiriliyor, pdfminer.six ile text’e çevriliyor.
    - Bu sayede artık data_raw/*.txt dosyalarının gövdesi gerçekten Yaşar Kemal metni oldu.

(4) ingest_to_vectorstore.py başarıyla çalıştı ve sistem doldu.
    - 13 belge işlendi.
    - ~1147 chunk ortaya çıktı.
    - Bu chunk’lar MongoDB ve Qdrant’e kaydedildi.
    - Bu sistemin “beyni” artık gerçek olarak var.

(5) /ask endpoint’i ile gerçekte semantik arama yapabildik.
    - Sisteme “Yaşar Kemal doğa hakkında ne düşünüyordu?” diye sorduk.
    - Geri dönen pasajlar doğa, toprak, ezilen halk vs. üzerineydi.
    - Bu, retrieval tarafının gerçekten çalıştığını kanıtlıyor.

(6) /ask_persona endpoint’i tasarlandı.
    - Bu endpoint, kullanıcı sorusu + en yakın chunk’ları bir araya getirip LLM’e gönderilecek prompt’u kuruyor.
    - Prompt şu yönergeleri içeriyor:
        * “Sen Yaşar Kemal değilsin ama onun sesi gibi konuş.”
        * “Doğayı canlı, insanı onurlu anlat.”
        * “Metni kopyalama, kendi sözlerinle söyle.”
    - Bu kısım telif / etik güvenliğini de içinde taşıyor.

----------------------------------------------------------

5. ŞU ANKİ DURUM (ÖNEMLİ SNAPSHOT)
----------------------------------

Şu anda sistemimiz şunu yapabiliyor:

- data_raw klasöründe:
    Gerçek Yaşar Kemal metinleri düz text halinde saklı.

- batch_crawl.py:
    seed_urls.txt içindeki linklere gidip bu metinleri otomatik topluyor, parse ediyor ve kaydediyor.
    PDF + HTML destekliyor.

- ingest_to_vectorstore.py:
    Bu kaydedilmiş metinleri alıyor, chunk’luyor, embedding çıkıyor, MongoDB ve Qdrant içine yüklüyor.
    Bu script başarıyla çalıştı ve 1000+ chunk oluşturuldu.

- Docker:
    MongoDB ve Qdrant konteyner olarak çalışıyor.
    Qdrant dashboard’a girildi, çalıştığı onaylandı.
    Sağlık kontrolünde mongo_ok ve qdrant_ok True döndü.

- FastAPI:
    /health -> sistem ayakta mı?
    /ask    -> semantik arama yap ve en benzer pasajları göster.
    /ask_persona -> (taslak) aynı aramayı yap, sonra Yaşar Kemal tarzında cevap yazması için bir LLM’e verilebilecek prompt hazırla.

Yani:
    Retrieval ✅
    Vektör veritabanı ✅
    API ✅
    Persona prompt üretimi (yarı hazır) ✅
    LLM cevabı (otomatize) ⏳

Pratik olarak:
Artık elimizde Yaşar Kemal’in sesi var ve biz o sesi sorulara bağlayabiliyoruz.

----------------------------------------------------------

6. SONRAKİ ADIMLAR
------------------

A) /ask_persona endpoint’ini bitirmek
    - Şu an endpoint prompt’u dönecek şekilde tasarlandı.
    - Bu endpoint’e son adım olarak bir LLM çağrısı eklenebilir.
      Örneğin:
        1. persona_prompt değişkenini oluştur.
        2. Bir LLM (örneğin yerel bir Llama modelini, vLLM ile çalışan bir endpointi ya da HuggingFace pipeline’ını) çağır.
        3. Modelden dönen yanıtı kullanıcıya “answer” olarak ver.
    - Böylece kullanıcı tek endpoint ile doğrudan “Yaşar Kemal tarzında” yanıt alır.

B) ZenML pipeline’ını tamamlamak
    - steps.py içindeki step_collect_raw(), step_clean_text(), step_embed_and_store() fonksiyonlarına gerçek kodu koyarak bu süreci otomatik/izlenebilir hale getirebiliriz.
    - Bu ileride “MLOps / LLMOps standartlarına uygun veri hattı” diye sunulabilir. Hoca için etkileyici.

C) Docker Compose
    - api (FastAPI)
    - mongo
    - qdrant
    şeklinde bir docker-compose.yml yazılıp tek komutla tüm stack ayağa kalkabilir.
    - Bu, “projeyi baştan ayağa kaldırmak tek tuş” demek olur.

D) LLM entegrasyonu (inference servisi)
    - Özellikle Text Generation Inference (TGI), vLLM, llama.cpp, ya da Hugging Face pipeline ile küçük bir model.
    - Bu model, /ask_persona’nın persona_prompt’unu alıp final cevabı üretir.
    - Prompt içinde etik yönergelerimiz var: “kopyalama, yeniden yaz.”

----------------------------------------------------------

7. AKADEMİK / ETİK NOT
----------------------
Bu proje açıkça akademik bir çalışmadır.
Toplanan içeriklerin bazıları telif kapsamındadır (örneğin roman pasajları).
Bu içerikler:
    - lokal ortamda tutulmaktadır.
    - direkt olarak paylaşılmamakta, yalnızca anlam ve üslup analizi için kullanılmaktadır.
    - son kullanıcıya otomatik şekilde uzun kopyalar halinde geri verilmemesi için
      /ask_persona prompt’unda kural konmuştur:
        “Metni doğrudan kopyalama; kendi sözlerinle anlat.”

Ayrıca sistem, Yaşar Kemal’i "ben Yaşar Kemal’im" diye konuşturmaya zorlanmıyor;
“onun diline yakın ol ama onun olduğunu iddia etme” gibi yönergeler kullanılıyor.
Bu, etik sunum açısından önemlidir.

----------------------------------------------------------

8. ÖZET CÜMLESİ (SON DURUM)
---------------------------
- Elimizde Yaşar Kemal metinlerinden oluşan bir bilgi tabanı var.
- Bu bilgi tabanı otomatik olarak parçalara bölünmüş, embedding’lenmiş ve hem MongoDB’ye hem Qdrant’e yazılmış durumda.
- Qdrant üzerinden semantik arama yapıyoruz ve bu çalışıyor (canlı test ettik).
- FastAPI ile bir REST API katmanımız var: /health, /ask, /ask_persona.
- /ask_persona prompt’u, Yaşar Kemal benzeri cevap üretmek için bir dil modeline verilmek üzere otomatik hazırlanıyor.
- Tek eksik: Henüz bu prompt otomatik olarak bir dil modeline (LLM) gönderilmiyor. Bir sonraki adım bu olacak.

Bu noktadan sonra yeni sohbette doğrudan şunu söylemem yeterli:
“Her şey çalışıyor, /ask_persona prompt’u hazır. Bir LLM’e bu prompt’u verip cevabı API’den döndürmek istiyorum.”

(End of report.)
