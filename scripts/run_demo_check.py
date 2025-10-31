import os, sys, json
from urllib.parse import quote

# Ensure package imports work
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(ROOT, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from fastapi.testclient import TestClient
from llm_twin.api.main import app

client = TestClient(app)

print("[demo] /health çağrısı...")
hr = client.get('/health')
print(hr.status_code)
print(hr.text)

print("[demo] /ask çağrısı...")
q = "Yaşar Kemal doğa hakkında ne düşünüyordu?"
ar = client.get('/ask', params={ 'question': q })
print(ar.status_code)
try:
    data = ar.json()
    # sadece ilk eşleşmeyi kısaca göster
    if isinstance(data, dict) and 'matches' in data and data['matches']:
        m0 = data['matches'][0]
        print(json.dumps({
            'score': m0.get('score'),
            'preview': (m0.get('text') or '')[:120],
            'source_url': m0.get('source_url')
        }, ensure_ascii=False))
    else:
        print(ar.text)
except Exception:
    print(ar.text)

print("[demo] Bitti.")
