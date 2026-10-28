# Evaluación 2 GSI — Ciclo de gestión de vulnerabilidades con Docker

**Asignatura:** Gestión de Seguridad de la Información (TI3062) — INACAP · **Docente:** Héctor Tejo
**Integrantes:** Benjamín Cifuentes · Benjamín Contesso · Victor Cancino

Infraestructura de 4 contenedores en la red externa `soc-net`: una aplicación web propia (Django) conectada a Oracle, escaneada con ZAP (aplicación web) y OpenVAS (infraestructura). Cada contenedor tiene su propio `docker-compose.yml`.

| Contenedor | Carpeta | Imagen | IP en soc-net | Puerto | URL |
|---|---|---|---|---|---|
| `oracle-db` | `01-oracle` | `gvenzl/oracle-free` | dinámica | 1521 | — |
| `app-web` | `02-app-django` | `ferreteria-web:1.1` (propia, con Dockerfile) | 172.28.0.20 | 8088 | http://localhost:8088 |
| `zap` | `03-zap` | `zaproxy/zap-stable` (2.17.0) | dinámica | 8080 / 8090 | http://localhost:8080/zap/ |
| `openvas` | `04-openvas` | `immauss/openvas` | dinámica | 9392 | http://localhost:9392 |

## Contenido del repositorio

| Ruta | Qué es |
|---|---|
| `informe/` | Informe final en Word y PDF (APA 6) |
| `Dockerfile.md` | Actividad: 11 preguntas sobre Dockerfile + ejemplo Django → Oracle |
| `DEMO.md` | Guion de la demo y comandos que pide el profesor |
| `01-oracle/` … `04-openvas/` | Un `docker-compose.yml` por contenedor (+ `.env.example` donde hay secretos) |
| `02-app-django/` | Código de la aplicación, `Dockerfile`, `.dockerignore` y `entrypoint.sh` |
| `reportes/` | Reportes de ZAP (JSON/HTML) y de OpenVAS (XML/CSV/PDF) |
| `capturas/` | Evidencias de cada paso (numeradas en orden) |
| `diagramas/` | Diagramas de los compose (YAMLTools) y figuras del enunciado |
| `_herramientas/` | Scripts usados para capturas, escaneos e informe (opcionales) |

## Requisitos

- Docker Desktop (Windows con WSL 2, macOS o Linux) con unos **16 GB de RAM** y **~20 GB libres** en disco.
- Conexión a internet para descargar las imágenes (~5,5 GB) y las dependencias de Python.

## Cómo replicarlo paso a paso

> Los comandos funcionan en PowerShell, Git Bash o Linux, salvo donde se indica.

### 1. Clonar y crear los archivos `.env`

Los `.env` con contraseñas **no están en el repositorio**. Se crean a partir de las plantillas:

```bash
cp 02-app-django/.env.example 02-app-django/.env
cp 03-zap/.env.example        03-zap/.env
cp 04-openvas/.env.example    04-openvas/.env
```

Editar cada `.env` y poner valores propios (claves largas y aleatorias). En `02-app-django/.env`, `ORACLE_PASSWORD` debe coincidir con `APP_USER_PASSWORD` del compose de Oracle (`MyPass123`, el valor que dejó el profesor).

### 2. Crear la red externa (una sola vez)

```bash
docker network create --driver bridge --subnet 172.28.0.0/16 soc-net
```

### 3. OpenVAS (primero, porque tarda en cargar)

```bash
cd 04-openvas && docker compose up -d && cd ..
```

Tarda varios minutos en quedar listo (`docker ps` muestra `healthy`). El compose usa `SKIPSYNC: "true"` porque la descarga de feeds desde Greenbone se cortaba y dejaba el contenedor reiniciándose; se usan los feeds incluidos en la imagen.

### 4. Oracle y las tablas

```bash
cd 01-oracle && docker compose up -d && cd ..
docker logs -f oracle-db        # esperar "DATABASE IS READY TO USE!" y salir con Ctrl+C
```

**Importante:** con la versión actual de la imagen, el compose del profesor no crea el usuario de aplicación (error `ORA-65012` al crear `FREEPDB1`, que ya existe). Crearlo a mano:

```bash
docker exec oracle-db createAppUser usuario MyPass123 FREEPDB1
```

Crear las tablas `CATEGORIA` y `PRODUCTO` con sus datos:

```powershell
# PowerShell
Get-Content 01-oracle\sql\01_tablas.sql | docker exec -i oracle-db sqlplus -s usuario/MyPass123@//localhost:1521/FREEPDB1
```

```bash
# Git Bash / Linux
docker exec -i oracle-db sqlplus -s usuario/MyPass123@//localhost:1521/FREEPDB1 < 01-oracle/sql/01_tablas.sql
```

### 5. Aplicación web (imagen propia)

```bash
cd 02-app-django
docker build -t ferreteria-web:1.1 .
docker compose up -d
cd ..
```

Abrir http://localhost:8088. La ruta http://localhost:8088/salud/ debe responder `{"estado": "ok", "base_de_datos": "ok"}`. El panel está en `/admin/` (usuario y contraseña definidos en `02-app-django/.env`).

### 6. ZAP

```bash
cd 03-zap && docker compose up -d && cd ..
```

Abrir http://localhost:8080/zap/ (la primera carga demora ~1 minuto). Como objetivo usar **`http://172.28.0.20:8000`**: la IP de la app dentro de `soc-net` y su puerto interno.

> Si ZAP falla, **no usar `docker restart zap`** (Xvfb no vuelve a iniciar). Usar `docker compose up -d --force-recreate` en `03-zap`.

### 7. Verificar la red (comando del profesor)

```bash
# Git Bash / Linux
docker network inspect soc-net -f '{{range .Containers}}{{.Name}} - {{.IPv4Address}}{{"\n"}}{{end}}'
```

```powershell
# PowerShell (hay que escapar las comillas internas)
docker network inspect soc-net -f '{{range .Containers}}{{.Name}} - {{.IPv4Address}}{{\"\n\"}}{{end}}'
```

### 8. Escaneos

- **ZAP:** escaneo 1 = *spider* + análisis pasivo; escaneo 2 = escaneo activo. Exportar como `Reporte1.json` / `Reporte2.json` (Report → Generate Report).
- **OpenVAS:** en http://localhost:9392 (usuario `admin`, contraseña de `04-openvas/.env`) crear un *Target* con `172.28.0.20`, una *Task* con la configuración *Full and fast* y ejecutarla **dos veces** (dos pasadas).

Los resultados obtenidos y su análisis están en `reportes/` y en el informe.

## Scripts opcionales (`_herramientas/`)

Se usaron para automatizar capturas, escaneos y la generación del informe. Requieren Python 3.12 en Windows y un entorno virtual propio:

```powershell
python -m venv _herramientas\venv
_herramientas\venv\Scripts\pip install playwright python-docx pymupdf
```

Ejemplos: `zap_escaneo.py` (escaneos ZAP por API), `openvas_gmp.py` (OpenVAS por GMP), `generar_informe.py` (informe Word) y `word_actualizar.ps1` (índices y PDF con Word).

## Detener y volver a iniciar

- Para apagar: cerrar Docker Desktop (o `docker desktop stop`). **No** detener los contenedores uno a uno si se quiere que vuelvan solos: tienen `restart: unless-stopped`.
- Al abrir Docker Desktop, los cuatro contenedores se inician automáticamente.
