import urllib.request
import re
from bs4 import BeautifulSoup

url = "https://diegoteca.com.ar/metodocuanti/ejercicios-practicos/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
articles = soup.find_all('article')
print(f"Total articulos encontrados: {len(articles)}")

for idx, art in enumerate(articles):
    art_id = art.get('id', '')
    title_el = art.find(['h1', 'h2', 'h3', 'h4', 'a', 'span'])
    links = [a.get('href') for a in art.find_all('a') if a.get('href')]
    img = art.find('img')
    img_src = img.get('src') if img else None
    print(f"\n--- Articulo #{idx+1} ({art_id}) ---")
    print("Links:", links)
    print("Img:", img_src)
