# Guion de la demo — Evaluación 2 GSI (2 a 5 minutos)

**Grupo:** Benjamín Cifuentes · Benjamín Contesso · Victor Cancino
**Objetivo de la demo:** mostrar al profesor que los 4 contenedores y la aplicación funcionan, y que todos están en la red `soc-net`.

---

## Antes de presentar (10 minutos antes)

1. Abrir **Docker Desktop** y esperar a que la ballena quede quieta (motor iniciado).
   - Los 4 contenedores tienen `restart: unless-stopped`: se inician solos cuando arranca Docker.
2. Abrir una terminal **PowerShell** en `D:\inacap\seguridad\eva 2`.
3. Comprobar que todo está arriba (OpenVAS puede tardar 3 a 5 minutos en quedar `healthy`):
   ```powershell
   docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
   ```
4. Dejar abiertas en el navegador:
   - Aplicación: http://localhost:8088
   - ZAP: http://localhost:8080/zap/ (la primera vez tarda ~1 minuto en cargar ZAP)
   - OpenVAS: http://localhost:9392 (usuario `admin`; la contraseña está en `04-openvas/.env`)
5. Tener a mano el informe (`informe/…pdf`) abierto en la sección 5.6 y la carpeta `reportes/`.

> Si algún contenedor no está arriba: ir a su carpeta (`01-oracle`, `02-app-django`, `03-zap`, `04-openvas`) y ejecutar `docker compose up -d`. Orden recomendado: red → Oracle → app → ZAP → OpenVAS.
> Si la red no existe: `docker network create --driver bridge --subnet 172.28.0.0/16 soc-net`.

---

## Guion (≈ 3 minutos)

### 1. Los contenedores (30 s) — comando 1 del profesor (probable)

```powershell
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

**Decir:** "Tenemos 4 contenedores: Oracle en el 1521, nuestra aplicación Django en el 8088, ZAP en el 8080 y OpenVAS en el 9392. Cada uno se levanta con su propio `docker-compose.yml`; la única imagen que construimos nosotros es `ferreteria-web`, con nuestro Dockerfile."

### 2. La red soc-net con las IP (30 s) — comando 2 del profesor (el que pidió en clase)

Comando tal como está en el archivo `confi.md` del profesor (funciona en Linux o Git Bash):

```bash
docker network inspect soc-net -f '{{range .Containers}}{{.Name}} - {{.IPv4Address}}{{"\n"}}{{end}}'
```

En **PowerShell de Windows** hay que escapar las comillas internas (si no, da `template parsing error`):

```powershell
docker network inspect soc-net -f '{{range .Containers}}{{.Name}} - {{.IPv4Address}}{{\"\n\"}}{{end}}'
```

Alternativa equivalente sin comillas internas:

```powershell
docker network inspect soc-net -f '{{range .Containers}}{{.Name}} - {{.IPv4Address}}{{println}}{{end}}'
```

Resultado esperado:

```text
openvas - 172.28.0.2/16
oracle-db - 172.28.0.3/16
zap - 172.28.0.4/16
app-web - 172.28.0.20/16
```

**Decir:** "Los cuatro están en `soc-net`, red externa creada antes con la subred 172.28.0.0/16. La app tiene IP fija 172.28.0.20; esa IP y el puerto interno 8000 son los que usamos como objetivo en ZAP (`http://172.28.0.20:8000`) y en OpenVAS."

### 3. La aplicación funcionando (40 s)

- Abrir http://localhost:8088 → catálogo con los productos **leídos desde Oracle**.
- Buscar "martillo".
- (Opcional) http://localhost:8088/salud/ → `{"estado": "ok", "base_de_datos": "ok"}` (la app consulta Oracle en ese momento).
- (Opcional) http://localhost:8088/admin/ → usuario `admin`, contraseña en `02-app-django/.env`.

**Decir:** "Es una app Django que se conecta al contenedor `oracle-db` por su nombre, gracias al DNS de la red Docker. Las tablas CATEGORIA y PRODUCTO las creamos con el script `01-oracle/sql/01_tablas.sql`."

### 4. Los escáneres (60 s)

- Mostrar ZAP en http://localhost:8080/zap/ (interfaz web, no de escritorio).
- Mostrar OpenVAS en http://localhost:9392 → *Scans → Tasks*: la tarea con **2 reportes** (las dos pasadas).
- Abrir la carpeta `reportes/`:
  - `reportes/zap/Reporte1.json` y `Reporte2.json` (+ HTML)
  - `reportes/openvas/OpenVAS-pasada1.*` y `OpenVAS-pasada2.*`

**Decir:** "Hicimos 2 escaneos con ZAP (uno pasivo con spider y uno activo) y 2 pasadas de OpenVAS, que dieron los mismos resultados. No hubo riesgos altos en la aplicación; los riesgos altos los encontramos revisando la configuración: las credenciales de Oracle en texto plano en el compose."

### 5. Cierre: el ciclo (20 s)

**Decir:** "Priorizamos los 18 hallazgos, aplicamos 3 correcciones (CSP, CORS y versión del driver de Oracle), construimos la versión 1.1 y volvimos a escanear: dos alertas desaparecieron y apareció una nueva más pequeña. Por eso el proceso es cíclico."

---

## Preguntas probables y respuestas cortas

| Pregunta | Respuesta |
|---|---|
| ¿Por qué un compose por contenedor? | Para que la configuración quede guardada y se pueda recrear igual, sin depender de un comando suelto. |
| ¿Qué significa `external: true`? | Que la red `soc-net` ya existe (se creó antes con `docker network create`) y el compose solo se conecta a ella. |
| ¿Por qué el escáner usa el puerto 8000 y no el 8088? | Porque escanea desde dentro de `soc-net`; el 8088 es el puerto publicado en el equipo. |
| ¿Qué hace el Dockerfile? | Parte de `python:3.12-slim`, instala dependencias, copia el código, crea un usuario sin privilegios y arranca gunicorn. Ver `Dockerfile.md`. |
| ¿Por qué OpenVAS tardó? | Al iniciar intentó descargar feeds por rsync y la conexión se cortaba; se usó `SKIPSYNC=true` con los feeds de la imagen. |
| ¿Por qué falló Oracle al principio? | El compose pide crear FREEPDB1, que ya existe en la imagen; el usuario de aplicación no se creó y se creó con `createAppUser`. |

## Si algo falla durante la demo

| Problema | Solución |
|---|---|
| ZAP muestra pantalla en blanco o error | En la carpeta `03-zap`: `docker compose up -d --force-recreate`, esperar 30 s y recargar http://localhost:8080/zap/. **No usar `docker restart zap`**: deja un archivo de bloqueo de la pantalla virtual (Xvfb) y el contenedor queda reiniciándose |
| OpenVAS no carga la página | Esperar: tarda unos minutos tras iniciar. Ver avance con `docker logs --tail 20 openvas` |
| La app responde 503 en /salud/ | Oracle aún no está listo: `docker logs --tail 5 oracle-db` hasta ver `DATABASE IS READY TO USE!` |
| Un contenedor no aparece en `docker ps` | En su carpeta: `docker compose up -d` |
