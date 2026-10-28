"""Gestión de OpenVAS por GMP (gvm-cli dentro del contenedor, vía docker exec).

Uso: python openvas_gmp.py info                      → versiones, configs, escáneres, listas de puertos, formatos
     python openvas_gmp.py crear <ip> <nombre>       → crea objetivo + tarea "Full and fast" (imprime ids)
     python openvas_gmp.py iniciar <task_id>         → inicia una pasada (imprime report_id)
     python openvas_gmp.py esperar <task_id>         → espera a que la tarea quede Done (muestra avance)
     python openvas_gmp.py resumen <report_id>       → hallazgos por severidad
     python openvas_gmp.py exportar <report_id> <prefijo_salida>  → XML, CSV y PDF
La contraseña de admin se lee de 04-openvas/.env (no se imprime).
"""
import base64
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
clave = next(l.split("=", 1)[1].strip() for l in (raiz / "04-openvas" / ".env").read_text(encoding="utf-8").splitlines()
             if l.startswith("OPENVAS_PASSWORD="))

FULL_AND_FAST = "daba56c8-73ec-11df-a475-002264764cea"
OPENVAS_DEFAULT = "08b69003-5fc2-4037-a479-93b440211c73"
IANA_TCP = "33d0cd82-57c6-11e1-8ed1-406186ea4fc5"
FORMATOS = {"xml": "a994b278-1f62-11e1-96ac-406186ea4fc5", "csv": "c1645568-627a-11e3-a660-406186ea4fc5",
            "pdf": "c402cc3e-b531-11e1-9163-406186ea4fc5"}


def gmp(xml, timeout=600):
    r = subprocess.run(["docker", "exec", "-u", "gvm", "openvas", "gvm-cli", "--timeout", str(timeout),
                        "--gmp-username", "admin", "--gmp-password", clave, "socket",
                        "--socketpath", "/run/gvmd/gvmd.sock", "--xml", xml],
                       capture_output=True, timeout=timeout + 60)
    salida = r.stdout.decode("utf-8", "replace")
    if r.returncode != 0 or not salida.strip():
        raise SystemExit(f"Error GMP: {r.stderr.decode('utf-8', 'replace')[:500]}")
    raiz_xml = ET.fromstring(salida)
    if not raiz_xml.get("status", "200").startswith("2"):
        raise SystemExit(f"GMP respondió {raiz_xml.get('status')}: {raiz_xml.get('status_text')}")
    return raiz_xml


accion = sys.argv[1]
if accion == "info":
    print("GMP", gmp("<get_version/>").findtext("version"))
    for c in gmp("<get_configs/>").findall("config"):
        print("config:", c.get("id"), c.findtext("name"))
    for s in gmp("<get_scanners/>").findall("scanner"):
        print("scanner:", s.get("id"), s.findtext("name"))
    for p in gmp("<get_port_lists/>").findall("port_list"):
        print("port_list:", p.get("id"), p.findtext("name"))
    for f in gmp("<get_report_formats/>").findall("report_format"):
        print("formato:", f.get("id"), f.findtext("name"), f.findtext("extension"))
elif accion == "crear":
    ip, nombre = sys.argv[2], sys.argv[3]
    t = gmp(f"<create_target><name>{nombre}</name><hosts>{ip}</hosts><port_list id=\"{IANA_TCP}\"/>"
            f"<alive_tests>Consider Alive</alive_tests>"
            f"<comment>Contenedor de la aplicacion web en la red soc-net</comment></create_target>").get("id")
    print("target_id", t)
    k = gmp(f"<create_task><name>Escaneo infraestructura - {nombre}</name>"
            f"<comment>Full and fast sobre {ip}; se ejecuta dos veces (dos pasadas)</comment>"
            f"<config id=\"{FULL_AND_FAST}\"/><target id=\"{t}\"/><scanner id=\"{OPENVAS_DEFAULT}\"/>"
            f"</create_task>").get("id")
    print("task_id", k)
elif accion == "iniciar":
    print("report_id", gmp(f"<start_task task_id=\"{sys.argv[2]}\"/>").findtext("report_id"))
elif accion == "esperar":
    tid = sys.argv[2]
    while True:
        t = gmp(f"<get_tasks task_id=\"{tid}\"/>").find("task")
        estado, avance = t.findtext("status"), t.findtext("progress")
        print(time.strftime("%H:%M:%S"), estado, avance + "%", flush=True)
        if estado in ("Done", "Stopped", "Interrupted"):
            break
        time.sleep(30)
elif accion == "resumen":
    r = gmp(f"<get_reports report_id=\"{sys.argv[2]}\" details=\"1\" ignore_pagination=\"1\" "
            f"filter=\"apply_overrides=0 min_qod=70 rows=-1 levels=chmlg sort-reverse=severity\"/>")
    rep = r.find("report/report")
    print("Inicio:", rep.findtext("scan_start"), "| Fin:", rep.findtext("scan_end"))
    print("Puertos:", [p.text for p in rep.findall("ports/port")])
    for res in rep.findall("results/result"):
        print(f"  [{res.findtext('threat')} {res.findtext('severity')}] {res.findtext('name')} "
              f"| puerto {res.findtext('port')} | NVT {res.find('nvt').get('oid')}")
elif accion == "exportar":
    rid, prefijo = sys.argv[2], Path(sys.argv[3])
    prefijo.parent.mkdir(parents=True, exist_ok=True)
    filtro = "apply_overrides=0 min_qod=70 rows=-1 levels=chmlg sort-reverse=severity"
    for ext, fid in FORMATOS.items():
        r = gmp(f"<get_reports report_id=\"{rid}\" format_id=\"{fid}\" details=\"1\" ignore_pagination=\"1\" "
                f"filter=\"{filtro}\"/>", timeout=900)
        rep = r.find("report")
        destino = prefijo.with_suffix("." + ext)
        if ext == "xml":
            destino.write_bytes(ET.tostring(rep, encoding="utf-8"))
        else:
            # El contenido en base64 es texto directo de <report> (no de sus hijos): se toma el trozo más largo
            trozos = [rep.text or ""] + [h.tail or "" for h in rep]
            contenido = max(trozos, key=lambda t: len(t.strip())).strip()
            destino.write_bytes(base64.b64decode(contenido))
        print("exportado", destino, destino.stat().st_size, "bytes")
