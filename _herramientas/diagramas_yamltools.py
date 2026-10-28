"""Sube cada docker-compose.yml (con contraseñas tapadas) a yamltools.dev y captura el diagrama.

Uso: python diagramas_yamltools.py <carpeta_salida> <vista> <compose1> [<compose2> ...]
  vista: "arbol" (vista por defecto), texto de otro botón de diagrama, o "?" para listar los controles.
No se envían credenciales: los valores de *PASSWORD* y api.key se reemplazan por "[oculto]".
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

out, vista, composes = Path(sys.argv[1]), sys.argv[2], [Path(c) for c in sys.argv[3:]]
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    for c in composes:
        texto = c.read_text(encoding="utf-8")
        texto = re.sub(r"(PASSWORD\w*:\s*)\S+", r'\1"[oculto]"', texto)
        texto = re.sub(r"api\.key=\S+", "api.key=[oculto]", texto)
        enmascarado = out / f"{c.parent.name}-compose-enmascarado.yml"
        enmascarado.write_text(texto, encoding="utf-8")

        pg = b.new_page(viewport={"width": 1600, "height": 1500}, locale="es-CL")
        pg.goto("https://yamltools.dev/es/visualizer", wait_until="load", timeout=60000)
        pg.wait_for_timeout(3000)
        for n in ("Rechazar", "Reject", "Aceptar"):
            if pg.get_by_role("button", name=n).count():
                pg.get_by_role("button", name=n).first.click()
                break
        pg.locator("input[type=file]").first.set_input_files(str(enmascarado))
        pg.wait_for_timeout(4000)
        if vista == "?":
            pg.get_by_text("Diagrama de", exact=False).first.click()
            pg.wait_for_timeout(1500)
            for t in pg.locator("[role=option], [role=menuitem], [role=tab], button").all():
                txt = (t.inner_text() or "").strip().replace("\n", " ")
                if txt and len(txt) < 40:
                    print("control:", txt.encode("ascii", "replace").decode())
        elif vista != "arbol":
            boton = pg.locator(f"button[title*='{vista}'], button[aria-label*='{vista}']")
            (boton.first if boton.count() else pg.get_by_text(vista, exact=False).first).click()
            pg.wait_for_timeout(4000)
        # Encuadre: desde la barra "Subir archivo" (YAML) hasta el diagrama, en la ventana visible
        y = pg.locator("text=Subir archivo").first.bounding_box()["y"]
        pg.mouse.wheel(0, y - 70)
        pg.wait_for_timeout(2500)
        destino = out / f"diagrama-{c.parent.name}.png"
        pg.screenshot(path=str(destino), clip={"x": 225, "y": 65, "width": 1150, "height": 1060})
        print("OK", destino, flush=True)
        pg.close()
    b.close()
