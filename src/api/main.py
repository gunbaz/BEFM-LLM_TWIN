from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List

import pymongo
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from sentence_transformers import SentenceTransformer

from .llm_infer import generate_answer



# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
app = FastAPI(title="LLM Twin API")


# -------------------------------------------------
# Health response modeli
# -------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    mongo_ok: bool
    qdrant_ok: bool


# -------------------------------------------------
# DB bağlantıları
# -------------------------------------------------
def get_mongo_client():
    # MongoDB Docker container 27017'de expose
    return pymongo.MongoClient("mongodb://localhost:27017")


def get_qdrant_client():
    # Qdrant Docker container 6333'te expose
    return QdrantClient(host="localhost", port=6333)


# -------------------------------------------------
# Sağlık kontrolü
# -------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health_check():
    # Mongo test
    try:
        mongo_client = get_mongo_client()
        mongo_client.admin.command("ping")
        mongo_ok = True
    except Exception:
        mongo_ok = False

    # Qdrant test
    try:
        qdrant_client = get_qdrant_client()
        _ = qdrant_client.get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False

    return HealthResponse(
        status="ok",
        mongo_ok=mongo_ok,
        qdrant_ok=qdrant_ok,
    )


# -------------------------------------------------
# Global objeler (embedding modeli, qdrant client, mongo db handle)
# bunları fonksiyon içinde her seferinde yeniden kurmamak için burada cacheliyoruz.
# -------------------------------------------------
_embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
_qdrant = QdrantClient(host="localhost", port=6333)
_mongo_db = pymongo.MongoClient("mongodb://localhost:27017")["llm_twin"]


# -------------------------------------------------
# Yardımcı: bir soruya en benzer top_k chunk'ı getir
# (Qdrant -> chunk_id -> Mongo text)
# -------------------------------------------------
def retrieve_top_chunks(user_question: str, top_k: int = 3):
    """
    user_question için embedding çıkar,
    Qdrant'ten en yakın top_k vektörü al,
    MongoDB'den bu chunkların metnini çek,
    liste döndür.
    """
    # 1. Embedding
    query_vec = _embed_model.encode([user_question])[0]

    # 2. Qdrant search
    search_results = _qdrant.search(
        collection_name="yasar_kemal_twin",
        query_vector=query_vec,
        limit=top_k
    )

    # 3. Mongo'dan text + source_url çek
    chunks = []
    for r in search_results:
        cid = r.id
        doc = _mongo_db["chunks"].find_one({"_id": cid})
        if doc:
            chunks.append({
                "score": r.score,
                "text": doc["text"],
                "source_url": doc["source_url"]
            })

    return chunks


# -------------------------------------------------
# /ask  -> ham pasajları döndür (debug / inceleme amaçlı)
# -------------------------------------------------
@app.get("/ask")
def ask(
    question: str = Query(..., description="Kullanıcının sorduğu soru")
):
    """
    Soruya semantik olarak en yakın pasajları getirir.
    Bu daha çok debug / inceleme endpoint'i.
    """
    try:
        top_chunks = retrieve_top_chunks(question, top_k=3)

        # biraz kırpıp dönelim ki telif açısından rahat olsun
        responses = []
        for ch in top_chunks:
            text_preview = (
                ch["text"][:400] + "..."
                if len(ch["text"]) > 400
                else ch["text"]
            )
            responses.append({
                "score": ch["score"],
                "text": text_preview,
                "source_url": ch["source_url"]
            })

        return {
            "question": question,
            "matches": responses
        }

    except Exception as e:
        return {"error": str(e)}


# -------------------------------------------------
# /ask_persona -> Yaşar Kemal tarzında yanıt üret
# -------------------------------------------------

class AskPersonaResponse(BaseModel):
    question: str
    answer: str
    used_chunks: List[dict]


@app.get("/ask_persona", response_model=AskPersonaResponse)
def ask_persona(
    question: str = Query(..., description="Soru"),
    top_k: int = 3
):
    """
    Yaşar Kemal'in temasına yakın anlatım üretir:
    - Qdrant+Mongo'dan bağlam toplanır
    - Persona prompt oluşturulur
    - Lokal Llama 3.1 8B modelinden cevap alınır
    """
    # 1. en alakalı chunk'ları getir
    chunks = retrieve_top_chunks(question, top_k=top_k)

    # 2. persona prompt inşa et
    persona_prompt_parts = [
        "Aşağıda Yaşar Kemal'in üslubuna benzeyen temalar var.",
        "Kurallar:",
        "- Kendini 'Ben Yaşar Kemal'im' diye tanıtma.",
        "- Metni bire bir kopyalama.",
        "- Doğayı yaşayan bir varlık gibi anlat.",
        "- Yoksulluğu utanç değil onurlu bir mücadele olarak anlat.",
        "- Ezilen insanı gururlu, dirençli, umut taşıyan biri olarak göster.",
        "- Türkçe yaz. Kısa ama yoğun ol.",
        "",
        f"SORU: {question}",
        "",
        "İLGİLİ PARÇALAR (bunları sadece ruh olarak kullan, direkt kopyalama):"
    ]

    for i, ch in enumerate(chunks):
        persona_prompt_parts.append(
            f"[PARÇA {i+1} / Kaynak: {ch['source_url']}]\n{ch['text']}\n"
        )

    persona_prompt_parts.append(
        "Yukarıdaki ruhu al, kendi sözlerinle cevap ver.\nCevap:"
    )

    final_prompt = "\n\n".join(persona_prompt_parts)

    # 3. Llama 3.1 8B LOCAL inference (güvenli çalıştırma)
    try:
        model_answer = generate_answer(final_prompt)
    except Exception as e:
        # Model indirilemedi / çalıştırılamadıysa zarifçe düş ve bağlamdan kısa bir yanıt döndür
        print(f"[ask_persona] Model inference hatası: {e}")
        # Basit, telif güvenli bir özetleme tarzı fallback
        lines = [
            "Model çevrimdışı olduğu için kısa bir bağlam özeti sunuyorum:",
            f"Soru: {question}",
            "Cevap (öz):"
        ]
        for i, ch in enumerate(chunks[:max(1, top_k)]):
            preview = ch.get("text", "")[:220].replace("\n", " ")
            lines.append(f"- ({i+1}) {preview}...")
        lines.append("Bu özet, ilgili pasajların ruhunu yansıtır; doğrudan alıntı değildir.")
        model_answer = "\n".join(lines)

    # 4. kaynak şeffaflığı
    used_chunks_preview = []
    for ch in chunks:
        used_chunks_preview.append({
            "source_url": ch["source_url"],
            "preview": ch["text"][:200]  # telif açısından kırp
        })

    return AskPersonaResponse(
        question=question,
        answer=model_answer,
        used_chunks=used_chunks_preview
    )
