import os
import uuid
import glob
import pymongo
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
from typing import List, Tuple

RAW_DIR = "data_raw"
CHUNK_SIZE = 800  # yaklaşık kelime/piece uzunluğu gibi davranacağız
COLLECTION_NAME = "yasar_kemal_twin"

def load_mongo():
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["llm_twin"]
    return db

def load_qdrant():
    return QdrantClient(host="localhost", port=6333)

def load_model():
    # yaygın ve iyi bir sentence transformer. internet yoksa lokalde hata verebilir;
    # ama şu an kod iskeleti olarak koyuyoruz.
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def read_raw_files() -> List[Tuple[str, str]]:
    """
    data_raw içindeki tüm timestampli txt dosyaları oku.
    her dosya: (source_url, full_text) dönecek
    """
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.txt")))
    results = []
    for path in files:
        # seed_urls.txt gibi kontrol dosyalarını atla
        base = os.path.basename(path)
        if "seed_urls" in base or "url_candidates" in base or "filtered_urls" in base:
            continue

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

        if len(text_body) < 50:
            # çok kısa, çöp gibi -> geç
            continue

        results.append((source_url, text_body))
    return results

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """
    Çok basit chunker: metni boşluklardan bölerek sabit uzunluklu parçalara ayır.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        piece = " ".join(words[i:i+chunk_size])
        if len(piece) > 0:
            chunks.append(piece)
    return chunks

def ensure_qdrant_collection(qdrant: QdrantClient, vector_size: int):
    collections = qdrant.get_collections()
    names = [c.name for c in collections.collections]
    if COLLECTION_NAME in names:
        return  # zaten var

    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qmodels.VectorParams(
            size=vector_size,
            distance=qmodels.Distance.COSINE
        ),
    )

def main():
    # 1. servisleri hazırla
    mongo = load_mongo()
    qdrant = load_qdrant()
    model = load_model()

    # 2. Qdrant koleksiyonunu hazırla
    test_vec = model.encode(["deneme vektörü"])[0]
    vector_size = len(test_vec)
    ensure_qdrant_collection(qdrant, vector_size)

    # 3. ham dosyaları oku
    docs = read_raw_files()
    print(f"[INFO] Found {len(docs)} source documents.")

    # 4. her dokümanı chunk'la ve içeriği Mongo+Qdrant'e yaz
    points_to_upsert = []  # Qdrant'e toplu push için
    mongo_records = []     # Mongo'ya toplu insert için

    for (source_url, body) in docs:
        chunks = chunk_text(body)

        for chunk_text_block in chunks:
            chunk_id = str(uuid.uuid4())

            # embedding üret
            embedding = model.encode([chunk_text_block])[0].tolist()

            # MongoDB kaydı
            mongo_records.append({
                "_id": chunk_id,
                "source_url": source_url,
                "text": chunk_text_block,
            })

            # Qdrant kaydı için point
            points_to_upsert.append(
                qmodels.PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "source_url": source_url,
                        "text": chunk_text_block,
                    }
                )
            )

    # 5. Mongo'ya yaz
    if mongo_records:
        mongo["chunks"].insert_many(mongo_records)
        print(f"[INFO] Inserted {len(mongo_records)} chunks into MongoDB.")

    # 6. Qdrant'e yaz
    if points_to_upsert:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points_to_upsert
        )
        print(f"[INFO] Upserted {len(points_to_upsert)} vectors into Qdrant.")

    print("[DONE] Ingestion complete.")

if __name__ == "__main__":
    main()
