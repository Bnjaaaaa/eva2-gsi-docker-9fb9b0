"""Escaneos de ZAP sobre la aplicación web, vía API (la interfaz web muestra el avance en vivo).

Uso: python zap_escaneo.py spider  <url>     → Escaneo 1: spider + análisis pasivo
     python zap_escaneo.py activo  <url>     → Escaneo 2: escaneo activo (ataques)
     python zap_escaneo.py reporte <n> <titulo> <url>   → Reporte<n>.json y Reporte<n>.html en /zap/wrk
     python zap_escaneo.py resumen <url>
     python zap_escaneo.py nuevasesion <nombre>     → sesión limpia (escaneo de verificación)
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # con -I Python no agrega la carpeta del script
from zap_api import api  # noqa: E402


def esperar(nombre, estado, limite_s):
    inicio = time.time()
    while time.time() - inicio < limite_s:
        v = estado()
        print(f"{time.strftime('%H:%M:%S')} {nombre}: {v}", flush=True)
        if v is True:
            return True
        time.sleep(10)
    print(f"{nombre}: tiempo agotado", flush=True)
    return False


def pasivo_terminado():
    n = int(api("JSON/pscan/view/recordsToScan/")["recordsToScan"])
    return True if n == 0 else f"{n} registros por analizar"


def resumen(url):
    r = api("JSON/alert/view/alertsSummary/", baseurl=url)["alertsSummary"]
    print("Resumen de alertas (instancias):", r, flush=True)
    grupos = {}
    for al in api("JSON/alert/view/alerts/", baseurl=url, start="0", count="9999")["alerts"]:
        clave = (al["risk"], al["alert"], al.get("pluginId", ""))
        grupos[clave] = grupos.get(clave, 0) + 1
    orden = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}
    for (riesgo, nombre, pid), n in sorted(grupos.items(), key=lambda x: (orden.get(x[0][0], 9), x[0][1])):
        print(f"  [{riesgo}] {nombre} (regla {pid}): {n} instancias", flush=True)


accion = sys.argv[1]
if accion == "spider":
    url = sys.argv[2]
    api("JSON/core/action/accessUrl/", url=url, followRedirects="true")
    sid = api("JSON/spider/action/scan/", url=url, recurse="true")["scan"]
    print("Spider iniciado, id", sid, flush=True)
    esperar("spider", lambda: True if api("JSON/spider/view/status/", scanId=sid)["status"] == "100"
            else api("JSON/spider/view/status/", scanId=sid)["status"] + "%", 900)
    urls = api("JSON/spider/view/results/", scanId=sid)["results"]
    print(f"URLs encontradas por el spider: {len(urls)}", flush=True)
    for u in urls:
        print("  ", u, flush=True)
    esperar("pasivo", pasivo_terminado, 900)
    resumen(url)
elif accion == "activo":
    url = sys.argv[2]
    aid = api("JSON/ascan/action/scan/", url=url, recurse="true", inScopeOnly="false")["scan"]
    print("Escaneo activo iniciado, id", aid, flush=True)
    esperar("activo", lambda: True if api("JSON/ascan/view/status/", scanId=aid)["status"] == "100"
            else api("JSON/ascan/view/status/", scanId=aid)["status"] + "%", 5400)
    esperar("pasivo", pasivo_terminado, 900)
    resumen(url)
elif accion == "reporte":
    n, titulo, url = sys.argv[2], sys.argv[3], sys.argv[4]
    for plantilla, ext in (("traditional-json", "json"), ("traditional-html", "html")):
        r = api("JSON/reports/action/generate/", title=titulo, template=plantilla, sites=url,
                reportDir="/zap/wrk", reportFileName=f"Reporte{n}.{ext}")
        print(plantilla, "->", r, flush=True)
elif accion == "resumen":
    resumen(sys.argv[2])
elif accion == "nuevasesion":
    # Sesión limpia para el escaneo de verificación (no mezcla alertas de los escaneos anteriores)
    print(api("JSON/core/action/newSession/", name=f"/home/zap/{sys.argv[2]}", overwrite="true"), flush=True)
