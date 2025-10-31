# ZenML Dashboard'u Docker ile başlat (scripts/ sürümü)
# Bu script, ZenML'in local Docker modunda çalışmasını sağlar.

# ZenML'i local modda başlat
zenml login --local --docker

# Dashboard'u başlat (blocking olmayan mod)
zenml up

Write-Host "ZenML dashboard açıldı: http://localhost:8237"