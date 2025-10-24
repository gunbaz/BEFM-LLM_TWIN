"""Basit crawler:
- Sabit URL listesini alır
- Her URL için placeholder doküman oluşturur
- MongoDB'deki raw_documents koleksiyonuna yazar
"""

from __future__ import annotations

from typing import Iterable, List
from pymongo.collection import Collection

from src.config import MONGO_DB, get_mongo_client


# Bu projede ingest edeceğimiz başlangıç kaynakları (Yaşar Kemal metinleri vb.)
URLS: List[str] = [
    "https://ia600709.us.archive.org/22/items/YaarKemalnceMemed1/Ya%C5%9Far%20Kemal%20%C4%B0nce%20Memed%201.pdf",
    "https://ia800709.us.archive.org/22/items/YaarKemalnceMemed1/Yasar%20Kemal%20%C4%B0nce%20Memed%202.pdf",
    "https://ia600709.us.archive.org/22/items/YaarKemalnceMemed1/Yasar%20Kemal%20%C4%B0nce%20Memed%203.pdf",
    "https://ia800709.us.archive.org/22/items/YaarKemalnceMemed1/Yasar%20Kemal%20%C4%B0nce%20Memed%204.pdf",

    "https://docviewer.yandex.com.tr/view/0/?page=11&*=hwh1O0z3If8nO7q20XH5sdK1qWJ7InVybCI6InlhLWRpc2stcHVibGljOi8vS3BHeEtnSTlLSi9RWTMybmtlbGl3VTFZZUwydDc0SUdOdVIyQUM4b0J4dz0iLCJ0aXRsZSI6IllhxZ9hciBLZW1hbCAtIFNhcsSxIFPEsWNhay5wZGYiLCJub2lmcmFtZSI6ZmFsc2UsInVpZCI6IjAiLCJ0cyI6MTc1OTk1NDgwODc2OCwieXUiOiI3NjMxNDQwMzIxNjk3OTc0MzIzIn0%3D",

    "https://el-kitap.org/wp-content/uploads/2023/10/Yasar-Kemal-Uc-Anadolu-Efsanesi.pdf",
    "https://el-kitap.org/wp-content/uploads/2023/10/Yasar-Kemal-Binbogalar-Efsanesi.pdf",
    "https://kitab-evi.com/wp-content/uploads/2024/11/Yasar-Kemal-Agridagi-Efsanesi.pdf",
    "https://kitab-evi.com/wp-content/uploads/2025/01/Yasar-Kemal-Teneke.pdf",

    "https://el-kitap.org/wp-content/uploads/2024/08/Yasar-Kemal-Bir-Ada-Hikayesi-1-Firat-Suyu-Kan-Akiyor-Baksana.pdf",
    "https://kitab-evi.com/wp-content/uploads/2025/01/2303-Filler_Sultani_Ile_Qirmizi_Sakalli_Topal_Qarinca-Yashar_Kemal-1994-217s.pdf",
    "https://www.yapikrediyayinlari.com.tr/dosyalar/2017/03/4ac60615-6ffb-45b7-b514-36f7485d53aa.pdf",
    "https://kitab-evi.com/wp-content/uploads/2025/01/yasar-kemal-yilani-oldurseler_Mir.az_.pdf",
    "https://www.yapikrediyayinlari.com.tr/dosyalar/2017/03/zulmun-artsin-PDF-tadimlik.pdf",
    "https://d4470015f2.cbaul-cdnwnd.com/a6458390cd3e2b54d2a2683f725d0238/200000258-4fc1b50bb3/Ya%C5%9Far%20Kemal%20_%20Allah%E2%80%99%C4%B1n%20Askerleri.pdf",
]


class PlaceholderCrawler:
    """URL listesindeki her kaynak için placeholder bir doküman MongoDB'ye yazar."""

    def __init__(self) -> None:
        client = get_mongo_client()
        database = client[MONGO_DB]
        self.collection: Collection = database["raw_documents"]

    def crawl(self, urls: Iterable[str]) -> List[dict]:
        """Verilen URL'ler için placeholder dokümanları üret ve MongoDB'ye kaydet."""
        documents = []
        for url in urls:
            documents.append(
                {
                    "url": url,
                    "text": "placeholder",  # ileride buraya gerçek content (pdf text) gelecek
                    "status": "fetched",    # ileride 'parsed', 'embedded' gibi aşamalar ekleyeceğiz
                }
            )

        if not documents:
            return []

        result = self.collection.insert_many(documents)

        inserted_documents: List[dict] = []
        for doc, inserted_id in zip(documents, result.inserted_ids):
            enriched = {**doc, "_id": inserted_id}
            inserted_documents.append(enriched)

        return inserted_documents


def main() -> None:
    crawler = PlaceholderCrawler()
    inserted_documents = crawler.crawl(URLS)
    print(
        f"Inserted {len(inserted_documents)} documents into raw_documents "
        f"collection in database '{MONGO_DB}'."
    )
    for d in inserted_documents:
        print(f"- {d['url']} -> {d['_id']}")


if __name__ == "__main__":
    main()
