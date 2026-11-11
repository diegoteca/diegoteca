# /// script
# dependencies = [
#   "httpx",
#   "polars",
#   "beautifulsoup4",
#   "markdownify",
#   "pyyaml"
# ]
# ///
"""
Script de respaldo y extracción para la red WordPress diegoteca.com.ar.
Descargo todo el contenido estructurado vía REST API y los adjuntos.
Comento el código en primera persona.
"""

import os
import json
import re
from pathlib import Path
import httpx
import polars as pl
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import yaml

# Defino el directorio base de trabajo
BASE_DIR = Path(r"C:\Users\dquar\positron_projects\diegoteca")
BACKUP_DIR = BASE_DIR / "backup_raw"
MEDIA_DIR = BASE_DIR / "media"
QUARTO_CONTENT_DIR = BASE_DIR / "content"

# Configuro la lista de subsitios identificados en diegoteca.com.ar
SUBSITES = [
    {"slug": "root", "url": "https://diegoteca.com.ar", "title": "Diegoteca Principal"},
    {"slug": "metodocuanti", "url": "https://diegoteca.com.ar/metodocuanti", "title": "Metodología Cuantitativa"},
    {"slug": "sociologiadeltrabajo", "url": "https://diegoteca.com.ar/sociologiadeltrabajo", "title": "Sociología del Trabajo"},
    {"slug": "preferenciasycapitalsocial", "url": "https://diegoteca.com.ar/preferenciasycapitalsocial", "title": "Preferencias Sociales y Capital Social"},
    {"slug": "encuestasocioeducativa2016", "url": "https://diegoteca.com.ar/encuestasocioeducativa2016", "title": "Encuesta Socioeducativa 2016"},
    {"slug": "muestra-unaj", "url": "https://diegoteca.com.ar/muestra-unaj", "title": "Muestra UNAJ"},
    {"slug": "usomedicamentos", "url": "https://diegoteca.com.ar/usomedicamentos", "title": "Uso de Medicamentos"},
]

def obtener_json(cliente: httpx.Client, endpoint: str):
    """
    Realizo una petición GET paginada para obtener todos los elementos del endpoint.
    Manejo paginación hasta agotar resultados.
    """
    elementos = []
    pagina = 1
    while True:
        url_paginada = f"{endpoint}?per_page=50&page={pagina}"
        try:
            respuesta = cliente.get(url_paginada)
            if respuesta.status_code == 400: # Generalmente indica que la página solicitada excede el total
                break
            respuesta.raise_for_status()
            datos = respuesta.json()
            if not datos:
                break
            elementos.extend(datos)
            
            total_paginas = int(respuesta.headers.get("X-WP-TotalPages", 1))
            if pagina >= total_paginas:
                break
            pagina += 1
        except Exception as error:
            print(f"[!] Error al consultar {url_paginada}: {error}")
            break
    return elementos

def descargar_adjunto(cliente: httpx.Client, url_media: str, ruta_destino: Path):
    """
    Descargo un archivo multimedia preservando la ruta y evitando descargas redundantes.
    """
    if ruta_destino.exists():
        return
    try:
        ruta_destino.parent.mkdir(parents=True, exist_ok=True)
        with cliente.stream("GET", url_media) as respuesta:
            if respuesta.status_code == 200:
                with open(ruta_destino, "wb") as f:
                    for chunk in respuesta.iter_bytes():
                        f.write(chunk)
                print(f"[+] Archivo descargado: {ruta_destino.name}")
    except Exception as error:
        print(f"[!] Error descargando archivo {url_media}: {error}")

def limpiar_html_a_markdown(html_content: str) -> str:
    """
    Limpio código basura de plugins de WordPress (OWA tracker, spans innecesarios)
    y convierto el cuerpo a Markdown limpio.
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remuevo scripts y estilos incrustados
    for elem in soup(["script", "style"]):
        elem.decompose()
        
    # Remuevo bloques de tiempo de lectura de plugins
    for elem in soup.find_all("span", class_=lambda c: c and "reading-time" in c):
        elem.decompose()
        
    texto_limpio = str(soup)
    texto_md = md(texto_limpio, heading_style="ATX", strip=['span'])
    return texto_md.strip()

def main():
    """
    Función principal de extracción: recorro cada subsitio, descargo páginas,
    artículos y archivos multimedia, y guardo el catálogo con Polars.
    """
    print("[*] Iniciando proceso de respaldo de diegoteca.com.ar...")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    QUARTO_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    registro_paginas = []
    registro_medios = []

    with httpx.Client(headers=headers, timeout=30.0, follow_redirects=True) as cliente:
        for subsitio in SUBSITES:
            slug = subsitio["slug"]
            url_base = subsitio["url"]
            titulo_sitio = subsitio["title"]
            print(f"\n==========================================")
            print(f"[*] Procesando subsitio: {titulo_sitio} ({slug})")
            print(f"==========================================")
            
            sub_backup_dir = BACKUP_DIR / slug
            sub_backup_dir.mkdir(parents=True, exist_ok=True)
            
            sub_quarto_dir = QUARTO_CONTENT_DIR / slug
            sub_quarto_dir.mkdir(parents=True, exist_ok=True)

            api_base = f"{url_base}/wp-json/wp/v2"

            # 1. Obtengo las páginas
            print(f"[*] Consultando páginas...")
            paginas = obtener_json(cliente, f"{api_base}/pages")
            print(f"    Total páginas encontradas: {len(paginas)}")
            with open(sub_backup_dir / "pages.json", "w", encoding="utf-8") as f:
                json.dump(paginas, f, ensure_ascii=False, indent=2)

            for p in paginas:
                p_id = p.get("id")
                p_slug = p.get("slug")
                p_title = p.get("title", {}).get("rendered", "")
                p_link = p.get("link", "")
                p_date = p.get("date", "")
                p_content = p.get("content", {}).get("rendered", "")
                
                # Convierto a Markdown para Quarto
                md_content = limpiar_html_a_markdown(p_content)
                
                # Escribo el archivo .qmd correspondiente
                qmd_path = sub_quarto_dir / f"{p_slug}.qmd"
                frontmatter = {
                    "title": BeautifulSoup(p_title, "html.parser").get_text(),
                    "date": p_date,
                    "original_url": p_link,
                    "subsite": slug
                }
                
                with open(qmd_path, "w", encoding="utf-8") as f_qmd:
                    f_qmd.write("---\n")
                    yaml.dump(frontmatter, f_qmd, allow_unicode=True, sort_keys=False)
                    f_qmd.write("---\n\n")
                    f_qmd.write(md_content + "\n")

                registro_paginas.append({
                    "subsite": slug,
                    "type": "page",
                    "id": p_id,
                    "slug": p_slug,
                    "title": frontmatter["title"],
                    "link": p_link,
                    "date": p_date,
                    "qmd_path": str(qmd_path.relative_to(BASE_DIR))
                })

            # 2. Obtengo las entradas / posts
            print(f"[*] Consultando posts...")
            posts = obtener_json(cliente, f"{api_base}/posts")
            print(f"    Total posts encontrados: {len(posts)}")
            with open(sub_backup_dir / "posts.json", "w", encoding="utf-8") as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)

            for post in posts:
                post_id = post.get("id")
                post_slug = post.get("slug")
                post_title = post.get("title", {}).get("rendered", "")
                post_link = post.get("link", "")
                post_date = post.get("date", "")
                post_content = post.get("content", {}).get("rendered", "")

                md_content = limpiar_html_a_markdown(post_content)
                qmd_path = sub_quarto_dir / f"post_{post_slug}.qmd"
                frontmatter = {
                    "title": BeautifulSoup(post_title, "html.parser").get_text(),
                    "date": post_date,
                    "original_url": post_link,
                    "subsite": slug
                }

                with open(qmd_path, "w", encoding="utf-8") as f_qmd:
                    f_qmd.write("---\n")
                    yaml.dump(frontmatter, f_qmd, allow_unicode=True, sort_keys=False)
                    f_qmd.write("---\n\n")
                    f_qmd.write(md_content + "\n")

                registro_paginas.append({
                    "subsite": slug,
                    "type": "post",
                    "id": post_id,
                    "slug": post_slug,
                    "title": frontmatter["title"],
                    "link": post_link,
                    "date": post_date,
                    "qmd_path": str(qmd_path.relative_to(BASE_DIR))
                })

            # 3. Obtengo los archivos multimedia (Media)
            print(f"[*] Consultando y descargando multimedia...")
            medios = obtener_json(cliente, f"{api_base}/media")
            print(f"    Total medios encontrados: {len(medios)}")
            with open(sub_backup_dir / "media.json", "w", encoding="utf-8") as f:
                json.dump(medios, f, ensure_ascii=False, indent=2)

            sub_media_dir = MEDIA_DIR / slug
            sub_media_dir.mkdir(parents=True, exist_ok=True)

            for m in medios:
                source_url = m.get("source_url")
                if not source_url:
                    continue
                nombre_archivo = Path(source_url.split("?")[0]).name
                ruta_local = sub_media_dir / nombre_archivo
                descargar_adjunto(cliente, source_url, ruta_local)

                registro_medios.append({
                    "subsite": slug,
                    "id": m.get("id"),
                    "title": m.get("title", {}).get("rendered", ""),
                    "source_url": source_url,
                    "local_path": str(ruta_local.relative_to(BASE_DIR)),
                    "mime_type": m.get("mime_type", "")
                })

    # Creo los DataFrames con Polars y exporto catálogos
    df_paginas = pl.DataFrame(registro_paginas)
    df_medios = pl.DataFrame(registro_medios)

    df_paginas.write_csv(BASE_DIR / "catalogo_paginas.csv")
    df_medios.write_csv(BASE_DIR / "catalogo_medios.csv")
    print("\n[✓] Extracción y respaldo finalizados con éxito.")
    print(f"[✓] Total páginas y posts procesados: {len(df_paginas)}")
    print(f"[✓] Total archivos multimedia catalogados: {len(df_medios)}")

if __name__ == "__main__":
    main()
