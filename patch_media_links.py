"""
Script de normalización de enlaces de medios en los documentos .qmd.
Reemplazo los enlaces remotos de diegoteca.com.ar/wp-content/uploads/
por enlaces relativos a la carpeta local de media descargada.
Comento el código en primera persona.
"""

from pathlib import Path
import re
import polars as pl

BASE_DIR = Path(r"C:\Users\dquar\positron_projects\diegoteca")
CONTENT_DIR = BASE_DIR / "content"
CATALOGO_MEDIOS = BASE_DIR / "catalogo_medios.csv"

def normalizar_enlaces():
    print("[*] Iniciando reemplazo de enlaces a medios locales...")
    if not CATALOGO_MEDIOS.exists():
        print("[!] No encontré el catálogo de medios.")
        return

    df_medios = pl.read_csv(CATALOGO_MEDIOS)
    
    # Armo un diccionario de mapeo de nombres de archivo y URLs a la ruta relativa de Quarto
    mapa_reemplazos = {}
    for fila in df_medios.iter_rows(named=True):
        source_url = fila["source_url"]
        local_path = fila["local_path"].replace("\\", "/")
        # Quito query params si los tiene
        clean_url = source_url.split("?")[0]
        nombre_archivo = Path(clean_url).name
        
        # Mapeo tanto la URL completa como patrones comunes
        mapa_reemplazos[clean_url] = f"../../{local_path}"
        mapa_reemplazos[nombre_archivo] = f"../../{local_path}"

    archivos_qmd = list(CONTENT_DIR.rglob("*.qmd"))
    print(f"[*] Total archivos .qmd a procesar: {len(archivos_qmd)}")

    for qmd in archivos_qmd:
        with open(qmd, "r", encoding="utf-8") as f:
            contenido = f.read()

        nuevo_contenido = contenido
        
        # Reemplazo URLs de wp-content/uploads por referencias relativas locales
        # Busco patrones https://diegoteca.com.ar/.../uploads/.../nombre.ext
        patron_wp = r'https?://diegoteca\.com\.ar/[^\s\)\]\"\'<>]*/wp-content/uploads/[^\s\)\]\"\'<>]+/([^/\s\)\]\"\'<>]+)'
        
        def sustituir_url(match):
            nombre = match.group(1)
            # Busco en nuestro catálogo si el archivo existe
            for fila in df_medios.iter_rows(named=True):
                loc = fila["local_path"].replace("\\", "/")
                if loc.endswith(nombre):
                    return f"../../{loc}"
            return match.group(0)

        nuevo_contenido = re.sub(patron_wp, sustituir_url, nuevo_contenido)

        if nuevo_contenido != contenido:
            with open(qmd, "w", encoding="utf-8") as f:
                f.write(nuevo_contenido)
            print(f"[+] Enlaces actualizados en: {qmd.name}")

    print("[✓] Proceso de normalización de enlaces finalizado.")

if __name__ == "__main__":
    normalizar_enlaces()
