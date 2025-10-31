from zenml import pipeline
from .steps import (
    step_collect_raw,
    step_read_and_parse,
    step_clean_text,
    step_chunk_text,
    step_embed_and_store
)

@pipeline
def llm_twin_ingestion_pipeline():
    """
    Yaşar Kemal LLM Twin - Tam Veri İşleme Pipeline'ı
    
    Bu pipeline şu adımları gerçekleştirir:
    1. Web'den ham veri toplar (seed_urls.txt'den)
    2. Dosyaları okur ve parse eder
    3. Metinleri temizler ve normalize eder
    4. Metinleri chunk'lara böler
    5. Embedding'ler üretir ve Qdrant + MongoDB'ye kaydeder
    
    Returns:
        Dict: Pipeline istatistikleri (mongo_count, qdrant_count)
    """
    # Step 1: Veri toplama
    file_paths = step_collect_raw()
    
    # Step 2: Dosyaları oku ve parse et
    documents = step_read_and_parse(file_paths)
    
    # Step 3: Metinleri temizle
    cleaned_documents = step_clean_text(documents)
    
    # Step 4: Chunk'lara böl
    chunks = step_chunk_text(cleaned_documents)
    
    # Step 5: Embedding üret ve kaydet
    stats = step_embed_and_store(chunks)
    
    return stats
