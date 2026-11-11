import urllib.request
import json

# En este script verifico la disponibilidad de cada post individualmente en metodocuanti
pids = [
    998, 981, 936, 422, 381, 355, 342, 308, 237, 188, 12
]

for pid in pids:
    url = f"https://diegoteca.com.ar/metodocuanti/wp-json/wp/v2/posts/{pid}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        print(f"Post {pid}: OK -> {data.get('slug')} | {data.get('title', {}).get('rendered')}")
    except Exception as e:
        print(f"Post {pid}: ERROR -> {e}")
