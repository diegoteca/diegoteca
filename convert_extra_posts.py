import os
import json
import re
from urllib.parse import urlparse, parse_qs
from markdownify import markdownify as md
import polars as pl

# En este script convierto los posts adicionales de metodocuanti a .qmd y los catalogo
with open("backup_raw/posts_metodocuanti_extra.json", "r", encoding="utf-8") as f:
    posts = json.load(f)

nuevas_filas = []

for item in posts:
    item_id = item.get("id")
    slug = item.get("slug")
    title = item.get("title", {}).get("rendered", "")
    date = item.get("date", "")
    link = item.get("link", "")
    content_html = item.get("content", {}).get("rendered", "")

    # Limpio etiquetas de tiempo de lectura
    content_html = re.sub(r'<span class="[^"]*rt-reading-time[^"]*">.*?</span>', '', content_html, flags=re.DOTALL)

    # Si contiene un documento html completo dentro (como el post 998), extraigo el body o convierto
    markdown_content = md(content_html, heading_style="ATX").strip()

    qmd_filename = f"post_{slug}.qmd"
    qmd_path = os.path.join("content", "metodocuanti", qmd_filename)

    qmd_text = f"""---
title: "{title.replace('"', '\\"')}"
date: "{date}"
original_url: "{link}"
subsite: "metodocuanti"
---

{markdown_content}
"""
    with open(qmd_path, "w", encoding="utf-8") as out:
        out.write(qmd_text)

    nuevas_filas.append({
        "subsite": "metodocuanti",
        "type": "post",
        "id": item_id,
        "slug": slug,
        "title": title,
        "link": link,
        "date": date,
        "qmd_path": qmd_path
    })

print(f"Creados {len(nuevas_filas)} archivos .qmd en content/metodocuanti/")

# Actualizo catalogo_paginas.csv usando Polars
df_existente = pl.read_csv("catalogo_paginas.csv")
df_nuevos = pl.DataFrame(nuevas_filas)
df_final = pl.concat([df_existente, df_nuevos]).unique(subset=["subsite", "id"])
df_final.write_csv("catalogo_paginas.csv")
print(f"Catalogo actualizado. Total paginas/posts: {len(df_final)}")
