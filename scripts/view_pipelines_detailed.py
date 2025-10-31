"""
ZenML Pipeline Detaylı Görüntüleyici (scripts/ sürümü)

Windows'ta ZenML dashboard'u arka planda çalışmadığı için,
bu script terminal tabanlı detaylı bir görüntüleme sağlar.
"""

from datetime import datetime
from zenml.client import Client


def format_duration(seconds):
    """Saniyeyi okunabilir formata çevir"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"


def print_header(title):
    """Başlık yazdır"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title):
    """Bölüm başlığı yazdır"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)


def main():
    print_header("🚀 ZenML Pipeline Detaylı Görüntüleyici")
    
    try:
        client = Client()
        
        # Pipeline'ları listele
        print_section("📊 Kayıtlı Pipeline'lar")
        pipelines = client.list_pipelines()
        
        if not pipelines.items:
            print("❌ Henüz pipeline kaydı yok.")
            return
        
        for pipeline in pipelines.items:
            print(f"\n✅ {pipeline.name}")
            print(f"   📝 ID: {pipeline.id}")
            print(f"   📅 Oluşturulma: {pipeline.created}")
            print(f"   🔄 Toplam Run: {len(list(client.list_pipeline_runs(pipeline_id=pipeline.id).items))}")
        
        # En son run'ı detaylı göster
        print_section("🎯 En Son Pipeline Run")
        
        latest_run = client.list_pipeline_runs(size=1).items[0]
        
        print(f"\n📌 Pipeline: {latest_run.name}")
        print(f"🆔 Run ID: {latest_run.id}")
        print(f"📊 Durum: {latest_run.status.upper()}")
        
        if latest_run.status == "completed":
            print(f"✅ Başarıyla tamamlandı!")
        elif latest_run.status == "failed":
            print(f"❌ Başarısız oldu!")
        
        print(f"🕒 Başlangıç: {latest_run.created}")
        print(f"🕐 Bitiş: {latest_run.updated}")
        
        # Step'leri detaylı göster
        print_section("📋 Step Detayları")
        
        if latest_run.steps:
            total_duration = 0
            step_count = len(latest_run.steps)
            completed_steps = 0
            
            for i, (step_name, step_info) in enumerate(latest_run.steps.items(), 1):
                status_emoji = {
                    'completed': '✅',
                    'failed': '❌',
                    'running': '🔄',
                    'cached': '💾'
                }.get(step_info.status, '❓')
                
                print(f"\n{i}. {status_emoji} {step_name}")
                print(f"   Durum: {step_info.status}")
                print(f"   ID: {step_info.id}")
                
                if step_info.status == 'completed':
                    completed_steps += 1
                
                # Step'in süresini hesapla
                if hasattr(step_info, 'started_at') and hasattr(step_info, 'completed_at'):
                    if step_info.started_at and step_info.completed_at:
                        duration = (step_info.completed_at - step_info.started_at).total_seconds()
                        total_duration += duration
                        print(f"   ⏱️  Süre: {format_duration(duration)}")
            
            print(f"\n📈 Özet:")
            print(f"   Toplam Step: {step_count}")
            print(f"   Tamamlanan: {completed_steps}")
            print(f"   Toplam Süre: {format_duration(total_duration)}")
        
        # Tüm run'ları listele
        print_section("📜 Son 5 Pipeline Run")
        
        runs = client.list_pipeline_runs(size=5)
        
        for i, run in enumerate(runs.items, 1):
            status_emoji = {
                'completed': '✅',
                'failed': '❌',
                'running': '🔄'
            }.get(run.status, '❓')
            
            print(f"\n{i}. {status_emoji} {run.name}")
            print(f"   Durum: {run.status}")
            print(f"   Tarih: {run.created}")
            print(f"   Run ID: {run.id}")
        
        # İstatistikler
        print_section("📊 Genel İstatistikler")
        
        all_runs = client.list_pipeline_runs()
        total_runs = len(all_runs.items)
        successful_runs = sum(1 for run in all_runs.items if run.status == 'completed')
        failed_runs = sum(1 for run in all_runs.items if run.status == 'failed')
        
        print(f"\n✨ Toplam Run: {total_runs}")
        print(f"✅ Başarılı: {successful_runs}")
        print(f"❌ Başarısız: {failed_runs}")
        
        if total_runs > 0:
            success_rate = (successful_runs / total_runs) * 100
            print(f"📈 Başarı Oranı: {success_rate:.1f}%")
        
        # Pipeline çalıştırma bilgisi
        print_section("🚀 Yeni Pipeline Çalıştırma")
        print("\nPipeline'ı tekrar çalıştırmak için:")
        print("   python scripts/run_pipeline.py")
        
        print_header("✨ Görüntüleme Tamamlandı")
        print()
        
        # Windows için dashboard bilgisi
        print("💡 NOT: Windows'ta ZenML Dashboard için alternatif yöntemler:")
        print("   1. Docker ile: zenml login --local --docker")
        print("   2. Bu script: python scripts/view_pipelines_detailed.py")
        print("   3. Web server: zenml login --local --blocking (ayrı terminal)")
        print()
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
