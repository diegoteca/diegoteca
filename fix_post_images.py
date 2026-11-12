import os
import json
import re

# En este script aseguro que cada post de metodocuanti tenga su imagen destacada en el cuerpo
# y corrijo enlaces rotos como Verba2.png y las imágenes de formularios / hojas de cálculo

mapa_featured = {
    "representaciones-sociales-ambientales": ("/media/metodocuanti/rio_contaminado.jpg", "Representaciones Sociales Ambientales"),
    "mi-primer-mapa": ("/media/metodocuanti/Van-Schagen-1689.jpg", "Van Schagen 1689"),
    "mi-primer-indice": ("/media/metodocuanti/Modelo-PERMA.jpg", "Modelo PERMA"),
    "mi-primer-sociograma": ("/media/metodocuanti/HistoricalNetworkAnalysis.png", "Historical Network Analysis"),
    "mi-primer-formulario": ("/media/metodocuanti/primer-formulario.jpg", "Primer Formulario"),
    "indice-de-masa-corporal": ("/media/metodocuanti/quetelet-quote-1024x233.png", "Adolphe Quetelet"),
    "simulador-teorema-limite-central": ("/media/metodocuanti/Simulador-Teorema-Límite-Central.png", "Simulador Teorema Límite Central"),
    "la-medicion-de-la-tierra-por-eratostenes": ("/media/metodocuanti/Eratóstenes-y-la-medición-de-la-tierra.png", "Eratóstenes y la medición de la tierra"),
    "los-jovenes-pobres-como-objeto-de-politicas-publicas": ("/media/metodocuanti/Jóvenes-pobres-como-objeto-de-políticas-públicas-Salvia-Tuñon.png", "Jóvenes pobres como objeto de políticas públicas")
}

dir_metodo = os.path.join("content", "metodocuanti")

# 1. Ajuste especial para post_998-2.qmd
p998_path = os.path.join(dir_metodo, "post_998-2.qmd")
if os.path.exists(p998_path):
    with open(p998_path, "r", encoding="utf-8") as f:
        t = f.read()
    
    # Verba2.png local
    t = t.replace("https://raw.githubusercontent.com/diegoteca/public_files/master/Verba2.png", "/media/metodocuanti/Verba2.png")
    
    # Imagen de nube de palabras para reemplazar el chunk generado
    t = t.replace("Buscando_files/figure-html/unnamed-chunk-12-1.png", "/media/metodocuanti/text_mining.jpg")
    
    # Agregar imagen destacada al principio
    if "/media/metodocuanti/text_mining.jpg" not in t[:500]:
        t = re.sub(r'(---\n\n)', r'\1![](/media/metodocuanti/text_mining.jpg)\n\n', t, count=1)
        
    with open(p998_path, "w", encoding="utf-8") as f:
        f.write(t)
    print("[+] Ajustado post_998-2.qmd")

# 2. Reemplazo en post_mi-primer-formulario.qmd
p_form_path = os.path.join(dir_metodo, "post_mi-primer-formulario.qmd")
if os.path.exists(p_form_path):
    with open(p_form_path, "r", encoding="utf-8") as f:
        t = f.read()
    t = re.sub(r'https?://diegoteca\.com\.ar/[^\s\)]*formularios-150x150\.png', '/media/metodocuanti/formularios-e1523995170673.png', t)
    t = re.sub(r'https?://diegoteca\.com\.ar/[^\s\)]*sheets-150x150\.png', '/media/metodocuanti/sheets-e1566567596132.png', t)
    with open(p_form_path, "w", encoding="utf-8") as f:
        f.write(t)
    print("[+] Ajustado post_mi-primer-formulario.qmd")

# 3. Insertar imagen destacada al inicio de cada post si no está ya presente
for slug, (img_url, alt) in mapa_featured.items():
    qmd_file = os.path.join(dir_metodo, f"post_{slug}.qmd")
    if os.path.exists(qmd_file):
        with open(qmd_file, "r", encoding="utf-8") as f:
            t = f.read()
        
        # Si la imagen ya está en el cuerpo, no la duplico
        img_name = os.path.basename(img_url)
        if img_name not in t:
            # Inserto justo después del frontmatter ---
            t = re.sub(r'(---\n\n)', rf'\1![{alt}]({img_url})\n\n', t, count=1)
            with open(qmd_file, "w", encoding="utf-8") as f:
                f.write(t)
            print(f"[+] Insertada imagen destacada en: post_{slug}.qmd")

print("[✓] Proceso de imágenes en posts finalizado.")
