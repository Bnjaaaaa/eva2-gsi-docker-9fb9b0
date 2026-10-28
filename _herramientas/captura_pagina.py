"""Captura una página (URL o archivo local) con Edge headless.

Uso: python captura_pagina.py <url_o_ruta> <salida.png> [ancho] [alto] [completa]
  completa = 1 para capturar la página entera (desplazamiento incluido).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

origen, salida = sys.argv[1], Path(sys.argv[2])
ancho = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
alto = int(sys.argv[4]) if len(sys.argv) > 4 else 900
completa = len(sys.argv) > 5 and sys.argv[5] == "1"
if not origen.startswith(("http://", "https://", "file:")):
    origen = Path(origen).resolve().as_uri()

salida.parent.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": ancho, "height": alto})
    pg.goto(origen, wait_until="load", timeout=60000)
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(salida), full_page=completa)
    b.close()
print("OK", salida)
