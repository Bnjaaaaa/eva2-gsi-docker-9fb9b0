# Imagen base oficial de Python 3.12 en su variante "slim" (Debian reducido, más liviana).
FROM python:3.12-slim

# No generar archivos .pyc y mostrar los logs de Python al instante (sin búfer).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo dentro de la imagen; los comandos siguientes se ejecutan aquí.
WORKDIR /app

# Se copian primero solo las dependencias: si no cambian, Docker reutiliza esta capa en cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Se copia el código de la aplicación (lo listado en .dockerignore, como .env, queda fuera).
COPY . .

# Reúne los archivos estáticos (CSS, admin) en /app/staticfiles para que WhiteNoise los sirva.
# La clave usada aquí solo existe durante la construcción; la real llega por variable de entorno.
RUN DJANGO_SECRET_KEY=solo-para-construir python manage.py collectstatic --noinput

# Usuario sin privilegios: la aplicación no se ejecuta como root dentro del contenedor.
RUN useradd --create-home --uid 10001 app && chmod +x entrypoint.sh
USER app

# Documenta el puerto en que escucha gunicorn dentro del contenedor (no lo publica).
EXPOSE 8000

# Docker revisa cada 30 s que la aplicación responda en /salud/.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/salud/', timeout=4)" || exit 1

# entrypoint.sh espera a Oracle y aplica las migraciones; luego ejecuta el CMD.
ENTRYPOINT ["./entrypoint.sh"]

# Servidor de producción gunicorn con 3 procesos, escuchando en todas las interfaces del contenedor.
CMD ["gunicorn", "ferreteria.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
