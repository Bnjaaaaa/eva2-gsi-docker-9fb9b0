"""Cliente del servidor de la interfaz de ZAP: envía una orden y espera la respuesta.

Uso: python zap_ui.py captura <ruta.png>
     python zap_ui.py click <x> <y> [veces] [boton]
     python zap_ui.py teclas "<texto>"
     python zap_ui.py tecla <nombre>
     python zap_ui.py esperar <ms>
     python zap_ui.py recargar | salir
"""
import json
import sys
import time
from pathlib import Path

control = Path(__file__).parent / "zap_ui"
orden, respuesta = control / "orden.json", control / "respuesta.txt"

args = sys.argv[1:]
a = args[0]
o = {"accion": a}
if a == "captura":
    o["ruta"] = str(Path(args[1]).resolve())
elif a == "click":
    o.update(x=int(args[1]), y=int(args[2]), veces=int(args[3]) if len(args) > 3 else 1,
             boton=args[4] if len(args) > 4 else "left")
elif a == "teclas":
    o["texto"] = args[1]
elif a == "tecla":
    o["nombre"] = args[1]
elif a == "esperar":
    o["ms"] = int(args[1])

respuesta.unlink(missing_ok=True)
orden.write_text(json.dumps(o), encoding="utf-8")
limite = time.time() + 120
while time.time() < limite:
    if respuesta.exists():
        print(respuesta.read_text(encoding="utf-8"))
        respuesta.unlink()
        sys.exit(0)
    time.sleep(0.3)
print("SIN RESPUESTA del servidor de la UI")
sys.exit(1)
