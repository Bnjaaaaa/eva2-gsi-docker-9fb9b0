"""Capturas de la aplicación web en el navegador (Edge headless con Playwright).

Uso: python capturas_app.py <url_base> <carpeta_capturas> <archivo_.env>
Genera: 19 listado, 20 búsqueda, 21a login admin, 21b panel admin, 21c productos en admin.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

base, out, env = sys.argv[1].rstrip("/"), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
vars_env = dict(l.split("=", 1) for l in env.read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
usuario, clave = vars_env["DJANGO_SUPERUSER_USERNAME"], vars_env["DJANGO_SUPERUSER_PASSWORD"]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720}, locale="es-CL")

    page.goto(f"{base}/", wait_until="load")
    page.screenshot(path=str(out / "19-app-listado-productos.png"))

    page.fill("#q", "martillo")
    page.click("button[type=submit]")
    page.wait_for_load_state("load")
    page.screenshot(path=str(out / "20-app-busqueda.png"))

    page.goto(f"{base}/admin/login/", wait_until="load")
    page.fill("#id_username", usuario)
    page.screenshot(path=str(out / "21a-app-admin-login.png"))
    page.fill("#id_password", clave)
    page.click("input[type=submit]")
    page.wait_for_load_state("load")
    page.screenshot(path=str(out / "21b-app-admin-panel.png"))

    page.goto(f"{base}/admin/catalogo/producto/", wait_until="load")
    page.screenshot(path=str(out / "21c-app-admin-productos.png"))

    browser.close()
print("OK capturas app")
