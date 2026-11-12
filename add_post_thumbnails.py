import os
import json
import re

# En este script asigno la propiedad 'image:' en el frontmatter YAML de cada post de metodocuanti
# para que el listing en grid de Quarto muestre la miniatura correspondiente.

with open("backup_raw/posts_metodocuanti_extra.json", "r", encoding="utf-8") as f:
    posts = json.load(f)

mapa_slug_media = {
    "998-2": "/media/metodocuanti/text_mining.jpg", # para minería de textos
    "representaciones-sociales-ambientales": "/media/metodocuanti/rio_contaminado.jpg",
    "mi-primer-mapa": "/media/metodocuanti/Van-Schagen-1689.jpg",
    "mi-primer-indice": "/media/metodocuanti/Modelo-PERMA.jpg",
    "mi-primer-sociograma": "/media/metodocuanti/HistoricalNetworkAnalysis.png",
    "mi-primer-formulario": "/media/metodocuanti/primer-formulario.jpg",
    "indice-de-masa-corporal": "/media/metodocuanti/quetelet-quote-1024x233.png",
    "simulador-teorema-limite-central": "/media/metodocuanti/Simulador-Teorema-Límite-Central.png",
    "la-medicion-de-la-tierra-por-eratostenes": "/media/metodocuanti/Eratóstenes-y-la-medición-de-la-tierra.png",
    "los-jovenes-pobres-como-objeto-de-politicas-publicas": "/media/metodocuanti/Jóvenes-pobres-como-objeto-de-políticas-públicas-Salvia-Tuñon.png"
}

dir_metodo = os.path.join("content", "metodocuanti")

for slug, img_path in mapa_slug_media.items():
    qmd_name = f"post_{slug}.qmd"
    qmd_full = os.path.join(dir_metodo, qmd_name)
    if os.path.exists(qmd_full):
        with open(qmd_full, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Si ya tiene image:, lo actualizo, sino lo inserto antes del segundo ---
        if re.search(r'^image:.*$', content, flags=re.MULTILINE):
            content = re.sub(r'^image:.*$', f'image: "{img_path}"', content, flags=re.MULTILINE)
        else:
            # Reemplazo el cierre del frontmatter
            content = re.sub(r'---\n', f'image: "{img_path}"\n---\n', content, count=1)
        
        with open(qmd_full, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Asignada imagen a: {qmd_name} -> {img_path}")

print("[✓] Miniaturas asignadas a todos los posts.")
