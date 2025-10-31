"""
ZenML Pipeline Görüntüleyici (scripts/ sürümü)

Bu script, çalıştırılmış pipeline'ları ve detaylarını gösterir.
"""

from zenml.client import Client


def main():
    print("=" * 80)
    print("ZenML Pipeline Görüntüleyici")
    print("=" * 80)
    print()
    
    try:
        # Client'ı al
        client = Client()
        
        # Pipeline'ları listele
        print("📊 Pipeline'lar:")
        print("-" * 80)
        pipelines = client.list_pipelines()
        
        if not pipelines:
            print("❌ Henüz pipeline çalıştırılmamış.")
            return
        
        for pipeline in pipelines.items:
            print(f"\n✅ Pipeline: {pipeline.name}")
            print(f"   ID: {pipeline.id}")
            print(f"   Oluşturulma: {pipeline.created}")
            
        # Pipeline run'larını listele
        print("\n" + "=" * 80)
        print("📈 Pipeline Run'ları (Son 10):")
        print("-" * 80)
        
        runs = client.list_pipeline_runs(size=10)
        
        if not runs:
            print("❌ Henüz run kaydı yok.")
            return
        
        for i, run in enumerate(runs.items, 1):
            print(f"\n{i}. Run ID: {run.id}")
            print(f"   Pipeline: {run.name}")
            print(f"   Durum: {run.status}")
            print(f"   Başlangıç: {run.created}")
            
            # Step'leri göster
            if run.steps:
                print(f"   Step'ler ({len(run.steps)}):")
                for step_name, step_info in run.steps.items():
                    status_emoji = "✅" if step_info.status == "completed" else "❌"
                    print(f"     {status_emoji} {step_name}: {step_info.status}")
        
        print("\n" + "=" * 80)
        print("💡 ZenML Dashboard için:")
        print("   1. Terminal'de: zenml up")
        print("   2. Tarayıcıda: http://localhost:8237")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        print("\nDaha fazla bilgi için:")
        print("  - ZenML veritabanı konumu: ~/.zenml")
        print("  - Proje konfigürasyonu: .zenml/")


if __name__ == "__main__":
    main()
