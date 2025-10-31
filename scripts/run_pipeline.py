"""
ZenML Pipeline Runner - Yaşar Kemal LLM Twin (scripts/ sürümü)

Bu script, tam veri işleme pipeline'ını çalıştırır:
1. Veri toplama (seed_urls.txt'den)
2. Parse etme
3. Temizleme
4. Chunk'lama
5. Embedding + MongoDB/Qdrant'e kaydetme

Kullanım:
    python scripts/run_pipeline.py
"""

import os
import sys

# Proje root'unu ve src'i PYTHONPATH'e ekle
scripts_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(scripts_dir)
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Yeni düzen: src altında doğrudan paketler mevcut (llm_twin prefix'i yok)
from pipeline.pipeline import llm_twin_ingestion_pipeline


def main():
    print("=" * 80)
    print("Yaşar Kemal LLM Twin - ZenML Pipeline")
    print("=" * 80)
    print()
    
    print("Pipeline başlatılıyor...")
    print()
    
    try:
        # Pipeline'ı çalıştır
        result = llm_twin_ingestion_pipeline()
        
        print()
        print("=" * 80)
        print("Pipeline başarıyla tamamlandı! ✅")
        print("=" * 80)
        print(f"Pipeline Run ID: {getattr(result, 'id', 'N/A')}")
        print(f"Pipeline Status: {getattr(result, 'status', 'N/A')}")
        print()
        print("Tüm adımlar başarıyla tamamlandı:")
        print("  ✅ Step 1: Veri toplama (seed_urls.txt)")
        print("  ✅ Step 2: Dosya okuma ve parse")
        print("  ✅ Step 3: Metin temizleme")
        print("  ✅ Step 4: Chunk'lara bölme")
        print("  ✅ Step 5: Embedding + MongoDB/Qdrant kaydetme")
        print()
        print("ZenML dashboard'dan detayları görüntüleyebilirsiniz:")
        print("  zenml up  # Server'ı başlat")
        print("  http://localhost:8237  # Dashboard URL")
        print()
        
    except Exception as e:
        print()
        print("=" * 80)
        print("Pipeline hatası! ❌")
        print("=" * 80)
        print(f"Hata: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
