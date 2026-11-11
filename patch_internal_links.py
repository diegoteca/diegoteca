import os
import re
import urllib.parse
import polars as pl

# En este script recorro todos los archivos .qmd y reemplazo los links absolutos de WordPress
# por enlaces relativos internos en Quarto/Netlify

df_paginas = pl.read_csv("catalogo_paginas.csv")

# Mapeos que voy a construir:
# 1. URL canónica -> ruta relativa desde content
# 2. subsite + id -> ruta relativa
# 3. subsite + slug -> ruta relativa

map_url = {}
map_id = {}
map_slug = {}

for row in df_paginas.iter_rows(named=True):
    subsite = row["subsite"]
    pid = str(row["id"])
    slug = row["slug"]
    link = row["link"].rstrip("/") if row["link"] else ""
    qmd_path = row["qmd_path"].replace("\\", "/") # e.g. content/metodocuanti/unidad-1.qmd
    # En Quarto el enlace HTML resultante dentro del sitio es /content/metodocuanti/unidad-1.html
    # O como enlace relativo entre páginas:
    html_target = "/" + qmd_path.replace(".qmd", ".html")
    
    if link:
        map_url[link] = html_target
        map_url[link + "/"] = html_target
    
    map_id[(subsite, pid)] = html_target
    map_slug[(subsite, slug)] = html_target

# Agrego casos especiales de las páginas principales de subsites
subsites = [
    "metodocuanti", "sociologiadeltrabajo", "preferenciasycapitalsocial",
    "muestra-unaj", "encuestasocioeducativa2016", "usomedicamentos"
]

for s in subsites:
    map_url[f"https://diegoteca.com.ar/{s}"] = f"/content/{s}/inicio.html"
    map_url[f"https://diegoteca.com.ar/{s}/"] = f"/content/{s}/inicio.html"
    map_url[f"http://diegoteca.com.ar/{s}"] = f"/content/{s}/inicio.html"
    map_url[f"http://diegoteca.com.ar/{s}/"] = f"/content/{s}/inicio.html"

map_url["https://diegoteca.com.ar"] = "/"
map_url["https://diegoteca.com.ar/"] = "/"
map_url["http://diegoteca.com.ar"] = "/"
map_url["http://diegoteca.com.ar/"] = "/"

print(f"Total reglas de URLs preparadas: {len(map_url)}")

# Función para resolver cualquier link de diegoteca
def resolver_link(match):
    full_url = match.group(0)
    # Quito caracteres de cierre que puedan haberse colado
    cleaned_url = full_url.rstrip(".,;)\"'>")
    suffix = full_url[len(cleaned_url):]

    parsed = urllib.parse.urlparse(cleaned_url)
    netloc = parsed.netloc.lower()
    path = parsed.path
    query = urllib.parse.parse_qs(parsed.query)

    # Si es un archivo de medios/uploads, dejamos que patch_media_links se encargue o lo enrutamos a media/
    if "/wp-content/uploads/" in path:
        return full_url

    # Si es de diegoteca.com.ar
    if "diegoteca.com.ar" in netloc:
        # Verifico si tiene parámetro ?page_id=X o ?p=X
        page_id = None
        if "page_id" in query:
            page_id = query["page_id"][0]
        elif "p" in query:
            page_id = query["p"][0]

        # Determino el subsite según el primer segmento del path
        parts = [p for p in path.split("/") if p]
        subsite = "root"
        if parts and parts[0] in subsites:
            subsite = parts[0]

        if page_id and (subsite, page_id) in map_id:
            return map_id[(subsite, page_id)] + suffix

        # Si coincide exactamente con map_url
        url_sin_slash = cleaned_url.rstrip("/")
        if cleaned_url in map_url:
            return map_url[cleaned_url] + suffix
        if url_sin_slash in map_url:
            return map_url[url_sin_slash] + suffix

        # Si tiene un slug en el path
        if parts:
            slug = parts[-1]
            if (subsite, slug) in map_slug:
                return map_slug[(subsite, slug)] + suffix

    return full_url

# Aplico los reemplazos en todos los .qmd
modificados = 0
reemplazos_totales = 0

url_regex = re.compile(r'https?://(?:[a-zA-Z0-9_\-]+\.)?diegoteca\.com\.ar[^\s\)\]\"\'><]*')

for root, dirs, files in os.walk("content"):
    for file in files:
        if file.endswith(".qmd"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                texto_original = f.read()

            nuevo_texto = url_regex.sub(resolver_link, texto_original)

            if nuevo_texto != texto_original:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(nuevo_texto)
                modificados += 1

print(f"Proceso terminado. Archivos modificados: {modificados}")
