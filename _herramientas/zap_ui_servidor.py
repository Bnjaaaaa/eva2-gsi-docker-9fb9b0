"""Mantiene abierta la interfaz web de ZAP (Webswing) en Edge headless y atiende órdenes.

Uso: python zap_ui_servidor.py <url_ui> <carpeta_control> <carpeta_perfil>
Órdenes: se escribe <carpeta_control>/orden.json con una de estas acciones:
  {"accion": "captura", "ruta": "C:/.../x.png"}
  {"accion": "click", "x": 100, "y": 200, "veces": 1, "boton": "left"}
  {"accion": "teclas", "texto": "http://..."}       (escribe texto)
  {"accion": "tecla", "nombre": "Enter"}            (pulsa una tecla)
  {"accion": "esperar", "ms": 2000}
  {"accion": "recargar"}
  {"accion": "salir"}
El resultado queda en <carpeta_control>/respuesta.txt.
"""
import json
import sys
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

ui, control, perfil = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
control.mkdir(parents=True, exist_ok=True)
orden, respuesta = control / "orden.json", control / "respuesta.txt"
for f in (orden, respuesta):
    f.unlink(missing_ok=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(perfil), channel="msedge", headless=True, viewport={"width": 1600, "height": 900}
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(ui, wait_until="load", timeout=120000)
    print("UI abierta", time.strftime("%H:%M:%S"), flush=True)
    activo = True
    while activo:
        if not orden.exists():
            page.wait_for_timeout(500)
            continue
        try:
            o = json.loads(orden.read_text(encoding="utf-8"))
            orden.unlink()
            a = o["accion"]
            if a == "captura":
                Path(o["ruta"]).parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=o["ruta"])
            elif a == "click":
                page.mouse.click(o["x"], o["y"], click_count=o.get("veces", 1), button=o.get("boton", "left"))
            elif a == "teclas":
                page.keyboard.type(o["texto"], delay=30)
            elif a == "tecla":
                page.keyboard.press(o["nombre"])
            elif a == "esperar":
                page.wait_for_timeout(o["ms"])
            elif a == "recargar":
                page.reload(wait_until="load")
            elif a == "salir":
                activo = False
            res = f"OK {a}"
        except Exception:
            res = "ERROR " + traceback.format_exc(limit=2)
        respuesta.write_text(res, encoding="utf-8")
        print(time.strftime("%H:%M:%S"), res.splitlines()[0], flush=True)
    ctx.close()
