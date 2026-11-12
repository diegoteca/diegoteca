"""
Script integral para normalizar y endogenizar todos los enlaces a medios (PDFs, imágenes, etc.)
en los documentos .qmd hacia la carpeta /media/...
Comento el código en primera persona.
"""

from pathlib import Path
import re
import polars as pl
from urllib.parse import unquote

BASE_DIR = Path(r"C:\Users\dquar\positron_projects\diegoteca")
CONTENT_DIR = BASE_DIR / "content"
CATALOGO_MEDIOS = BASE_DIR / "catalogo_medios.csv"

def normalizar_todos_los_medios():
    print("[*] Iniciando normalización completa de medios...")
    if not CATALOGO_MEDIOS.exists():
        print("[!] No encontré catalogo_medios.csv")
        return

    df_medios = pl.read_csv(CATALOGO_MEDIOS)
    
    # Armo un mapa por nombre de archivo decodificado (URL-decoded) y minúsculas para machear seguro
    mapa_archivos = {}
    for fila in df_medios.iter_rows(named=True):
        local_path = fila["local_path"].replace("\\", "/") # ej: media/sociologiadeltrabajo/2016-Programa-...pdf
        filename = Path(local_path).name
        web_path = "/" + local_path
        
        mapa_archivos[filename] = web_path
        mapa_archivos[filename.lower()] = web_path
        mapa_archivos[unquote(filename)] = web_path
        mapa_archivos[unquote(filename).lower()] = web_path

    archivos_qmd = list(CONTENT_DIR.rglob("*.qmd")) + [BASE_DIR / "index.qmd"]

    total_modificados = 0

    # Expresión regular que detecta cualquier link que termine en un archivo de uploads o /wp-content/uploads/
    patron_media = re.compile(r'(?:https?://[^\s\)\]\"\'<>]*)?/wp-content/uploads/(?:sites/\d+/)?(?:\d{4}/\d{2}/)?([^/\s\)\]\"\'<>]+)')

    for qmd in archivos_qmd:
        if not qmd.exists():
            continue
        with open(qmd, "r", encoding="utf-8") as f:
            contenido = f.read()

        def reemplazar(match):
            raw_filename = match.group(1)
            decoded_filename = unquote(raw_filename)
            
            # Si tiene sufijos de escala tipo -150x150, -500x500 antes de la extensión
            base_cleaned = re.sub(r'-\d+x\d+(\.[a-zA-Z0-9]+)$', r'\1', decoded_filename)

            for cand in [raw_filename, decoded_filename, base_cleaned, base_cleaned.lower()]:
                if cand in mapa_archivos:
                    return mapa_archivos[cand]
            
            # Si no está en el mapa, devolvemos el original
            return match.group(0)

        nuevo_contenido = patron_media.sub(reemplazar, contenido)

        # También reemplazo enlaces relativos tipo "../../media/..." por ruta absoluta del sitio "/media/..."
        nuevo_contenido = re.sub(r'\.\./\.\./media/', '/media/', nuevo_contenido)

        if nuevo_contenido != contenido:
            with open(qmd, "w", encoding="utf-8") as f:
                f.write(nuevo_contenido)
            total_modificados += 1
            print(f"[+] Actualizado: {qmd.name}")

    print(f"[✓] Proceso terminado. Total archivos modificados: {total_modificados}")

if __name__ == "__main__":
    normalizar_todos_los_medios()
