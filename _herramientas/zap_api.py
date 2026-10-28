"""Llamadas a la API de ZAP a través de su proxy (http://zap/... vía localhost:8090).

Uso: python zap_api.py <ruta_api> [param=valor ...]
Ej.:  python zap_api.py JSON/core/view/version/
      python zap_api.py JSON/spider/action/scan/ url=http://172.28.0.20:8000/
(sin "/" inicial: Git Bash convierte "/JSON/..." en una ruta de Windows)
La clave se lee de 03-zap/.env. Imprime la respuesta JSON.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
clave = next(l.split("=", 1)[1].strip() for l in (raiz / "03-zap" / ".env").read_text(encoding="utf-8").splitlines()
             if l.startswith("ZAP_API_KEY="))


def api(ruta, **params):
    # Se acepta la ruta sin "/" inicial (Git Bash convierte "/JSON/..." en una ruta de Windows)
    ruta = "/" + re.search(r"(JSON|OTHER)/.*", ruta).group(0)
    params["apikey"] = clave
    url = f"http://zap{ruta}?{urllib.parse.urlencode(params)}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": "http://localhost:8090"}))
    with opener.open(url, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


if __name__ == "__main__":
    ruta = sys.argv[1]
    params = dict(a.split("=", 1) for a in sys.argv[2:])
    print(json.dumps(api(ruta, **params), ensure_ascii=False, indent=1))
