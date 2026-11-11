import os
import re
import polars as pl
from urllib.parse import urlparse, parse_qs

# En este script recorro todos los archivos .qmd para recopilar los enlaces que apuntan a diegoteca.com.ar
df_paginas = pl.read_csv("catalogo_paginas.csv")
df_medios = pl.read_csv("catalogo_medios.csv")

enlaces_encontrados = set()
for root, dirs, files in os.walk("content"):
    for file in files:
        if file.endswith(".qmd"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                matches = re.findall(r'https?://[^\s\)\]\"\'><]+', content)
                for m in matches:
                    if "diegoteca.com.ar" in m:
                        enlaces_encontrados.add(m.rstrip(".,;"))

print(f"Total enlaces unicos a diegoteca: {len(enlaces_encontrados)}")
for u in sorted(enlaces_encontrados):
    print(u)
