import os
import glob
import uuid
from typing import List, Tuple, Dict
from zenml import step
import pymongo
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer

# Batch crawl fonksiyonlarını import et (paket yolu)
# Mevcut dizin yapısına göre import (src/ingest)
from ingest.batch_crawl import run_batch, load_seed_urls

RAW_DIR = "data_raw"
CHUNK_SIZE = 800
COLLECTION_NAME = "yasar_kemal_twin"


@step
def step_collect_raw() -> List[str]:
    """
    Selenium crawler ile içerik topla.
    seed_urls.txt'deki URL'leri okuyup batch_crawl ile metinleri toplar.
    
    Returns:
        List[str]: Toplanan dosyaların path'leri
    """
    print("[STEP 1] Veri toplama başlıyor...")
    
    # Seed URL'leri kontrol et
    seed_urls = load_seed_urls()
    print(f"[STEP 1] {len(seed_urls)} URL işlenecek")
    
    # Mevcut dosyaları say
    existing_files = glob.glob(os.path.join(RAW_DIR, "*.txt"))
    existing_count = len([f for f in existing_files if not any(x in f for x in ["seed_urls", "url_candidates", "filtered_urls"])])
    
    print(f"[STEP 1] Mevcut dosya sayısı: {existing_count}")
    
    if existing_count > 0:
        print(f"[STEP 1] Zaten {existing_count} dosya var. Yeniden toplama yapılmayacak.")
        return existing_files
    
    # Veri topla
    run_batch()
    
    # Toplanan dosyaları listele
    collected_files = glob.glob(os.path.join(RAW_DIR, "*.txt"))
    collected_files = [f for f in collected_files if not any(x in f for x in ["seed_urls", "url_candidates", "filtered_urls"])]
    
    print(f"[STEP 1] Toplam {len(collected_files)} dosya toplandı")
    return collected_files


@step
def step_read_and_parse(file_paths: List[str]) -> List[Tuple[str, str]]:
    """
    Ham dosyaları okur ve parse eder.
    
    Args:
        file_paths: Okunacak dosya path'leri
        
    Returns:
        List[Tuple[str, str]]: (source_url, text_body) tuple'ları
    """
    print("[STEP 2] Dosyalar okunuyor ve parse ediliyor...")
    
    results = []
    for path in file_paths:
        # Kontrol dosyalarını atla
        base = os.path.basename(path)
        if "seed_urls" in base or "url_candidates" in base or "filtered_urls" in base:
            continue
        
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                raw = f.read().strip()
            
            # SOURCE: ... satırını ayır
            source_url = "unknown"
            lines = raw.splitlines()
            if lines and lines[0].startswith("SOURCE:"):
                source_url = lines[0].replace("SOURCE:", "").strip()
                text_body = "\n".join(lines[1:]).strip()
            else:
                text_body = raw
            
            # Çok kısa metinleri atla
            if len(text_body) < 50:
                print(f"[STEP 2] Çok kısa, atlanıyor: {base}")
                continue
            
            results.append((source_url, text_body))
            print(f"[STEP 2] Okundu: {base} ({len(text_body)} karakter)")
            
        except Exception as e:
            print(f"[STEP 2] Hata: {path} - {e}")
    
    print(f"[STEP 2] Toplam {len(results)} doküman parse edildi")
    return results


@step
def step_clean_text(documents: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """
    Metinleri temizler ve normalize eder.
    
    Args:
        documents: (source_url, raw_text) tuple'ları
        
    Returns:
        List[Tuple[str, str]]: (source_url, cleaned_text) tuple'ları
    """
    print("[STEP 3] Metinler temizleniyor...")
    
    cleaned_documents = []
    
    for source_url, text in documents:
        # Temizlik işlemleri
        # 1. Null byte'ları temizle
        text = text.replace("\x00", "")
        
        # 2. Fazla boşlukları temizle
        text = " ".join(text.split())
        
        # 3. Çok kısa satırları filtrele (opsiyonel)
        lines = text.split("\n")
        lines = [line.strip() for line in lines if len(line.strip()) > 10]
        text = "\n".join(lines)
        
        cleaned_documents.append((source_url, text))
        print(f"[STEP 3] Temizlendi: {source_url[:50]}... ({len(text)} karakter)")
    
    print(f"[STEP 3] Toplam {len(cleaned_documents)} doküman temizlendi")
    return cleaned_documents


@step
def step_chunk_text(documents: List[Tuple[str, str]]) -> List[Dict]:
    """
    Metinleri chunk'lara böler.
    
    Args:
        documents: (source_url, cleaned_text) tuple'ları
        
    Returns:
        List[Dict]: Her chunk için dict (chunk_id, source_url, text)
    """
    print("[STEP 4] Metinler chunk'lara bölünüyor...")
    
    all_chunks = []
    
    for source_url, text in documents:
        # Basit word-split chunking
        words = text.split()
        
        chunk_count = 0
        for i in range(0, len(words), CHUNK_SIZE):
            piece = " ".join(words[i:i+CHUNK_SIZE])
            if len(piece) > 0:
                chunk_id = str(uuid.uuid4())
                all_chunks.append({
                    "chunk_id": chunk_id,
                    "source_url": source_url,
                    "text": piece
                })
                chunk_count += 1
        
        print(f"[STEP 4] {source_url[:50]}... -> {chunk_count} chunk")
    
    print(f"[STEP 4] Toplam {len(all_chunks)} chunk oluşturuldu")
    return all_chunks


@step
def step_embed_and_store(chunks: List[Dict]) -> Dict[str, int]:
    """
    Chunk'lar için embedding üretir ve MongoDB + Qdrant'e kaydeder.
    
    Args:
        chunks: chunk dict'leri (chunk_id, source_url, text)
        
    Returns:
        Dict[str, int]: İstatistikler (mongo_count, qdrant_count)
    """
    print("[STEP 5] Embedding'ler üretiliyor ve kaydediliyor...")
    
    # Servisleri hazırla
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
    mongo_db = mongo_client["llm_twin"]
    qdrant = QdrantClient(host="localhost", port=6333)
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    # Qdrant koleksiyonunu hazırla
    test_vec = model.encode(["deneme vektörü"])[0]
    vector_size = len(test_vec)
    
    collections = qdrant.get_collections()
    names = [c.name for c in collections.collections]
    if COLLECTION_NAME not in names:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=vector_size,
                distance=qmodels.Distance.COSINE
            ),
        )
        print(f"[STEP 5] Qdrant koleksiyonu oluşturuldu: {COLLECTION_NAME}")
    else:
        print(f"[STEP 5] Qdrant koleksiyonu zaten var: {COLLECTION_NAME}")
    
    # Chunk'ları işle
    points_to_upsert = []
    mongo_records = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = chunk["chunk_id"]
        source_url = chunk["source_url"]
        text = chunk["text"]
        
        # Embedding üret
        embedding = model.encode([text])[0].tolist()
        
        # MongoDB kaydı
        mongo_records.append({
            "_id": chunk_id,
            "source_url": source_url,
            "text": text,
        })
        
        # Qdrant kaydı için point
        points_to_upsert.append(
            qmodels.PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "source_url": source_url,
                    "text": text,
                }
            )
        )
        
        if (i + 1) % 100 == 0:
            print(f"[STEP 5] {i + 1}/{len(chunks)} chunk işlendi...")
    
    # MongoDB'ye yaz
    if mongo_records:
        # Önce mevcut kayıtları temizle (re-run için)
        mongo_db["chunks"].delete_many({})
        mongo_db["chunks"].insert_many(mongo_records)
        print(f"[STEP 5] MongoDB'ye {len(mongo_records)} chunk kaydedildi")
    
    # Qdrant'e yaz
    if points_to_upsert:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points_to_upsert
        )
        print(f"[STEP 5] Qdrant'e {len(points_to_upsert)} vektör kaydedildi")
    
    return {
        "mongo_count": len(mongo_records),
        "qdrant_count": len(points_to_upsert)
    }
