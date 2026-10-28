"""Capturas de la interfaz web de OpenVAS (GSA) con Edge headless.

Uso: python openvas_gsa.py <url_base> <carpeta_salida> [login=archivo.png] ruta=archivo.png [ruta=archivo.png ...]
  "login=x.png" captura el formulario de ingreso (solo con el usuario escrito).
  ruta (sin "/" inicial): por ejemplo dashboards, tasks, targets, task/<id>, report/<id>
La contraseña de admin se lee de 04-openvas/.env.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

raiz = Path(__file__).resolve().parent.parent
clave = next(l.split("=", 1)[1].strip() for l in (raiz / "04-openvas" / ".env").read_text(encoding="utf-8").splitlines()
             if l.startswith("OPENVAS_PASSWORD="))
base, salida = sys.argv[1].rstrip("/"), Path(sys.argv[2])
salida.mkdir(parents=True, exist_ok=True)
# Rutas sin "/" inicial (Git Bash convierte "/x" en una ruta de Windows); se agrega aquí.
pedidos = [a.split("=", 1) for a in sys.argv[3:]]
pedidos = [(r if r == "login" else "/" + r.split("/Git/")[-1].lstrip("/"), f) for r, f in pedidos]

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 900}, locale="en-US")
    pg.goto(f"{base}/login", wait_until="load", timeout=90000)
    pg.wait_for_selector("input[name=username]", timeout=90000)
    pg.fill("input[name=username]", "admin")
    for ruta, archivo in pedidos:
        if ruta == "login":
            pg.screenshot(path=str(salida / archivo))
    pg.fill("input[name=password]", clave)
    pg.keyboard.press("Enter")
    pg.wait_for_url(lambda u: "/login" not in u, timeout=90000)
    pg.wait_for_timeout(6000)
    for ruta, archivo in pedidos:
        if ruta == "login":
            continue
        ruta, _, pestana = ruta.partition("|")      # "report/<id>|Results" abre además esa pestaña
        pg.goto(f"{base}{ruta}", wait_until="load", timeout=90000)
        pg.wait_for_timeout(7000)          # GSA carga los datos por GMP después del "load"
        if pestana.startswith("@"):                  # "@x,y": clic en coordenadas (pestañas sin texto único)
            x, y = (int(v) for v in pestana[1:].split(","))
            pg.mouse.click(x, y)
            pg.wait_for_timeout(5000)
        elif pestana:
            pg.get_by_text(pestana, exact=True).first.click()
            pg.wait_for_timeout(4000)
        pg.screenshot(path=str(salida / archivo))
        print("OK", ruta, "->", archivo, flush=True)
    b.close()
