#!/bin/sh
# Se ejecuta al iniciar el contenedor, antes del CMD (gunicorn).
set -e

# 1) Esperar a que Oracle acepte conexiones. depends_on no sirve aquí porque
#    Oracle se levanta con otro docker-compose.yml.
python - <<'EOF'
import os, sys, time
import oracledb

for intento in range(1, 61):
    try:
        oracledb.connect(user=os.environ["ORACLE_USER"], password=os.environ["ORACLE_PASSWORD"],
                         dsn=os.environ["ORACLE_DSN"]).close()
        print(f"Oracle disponible (intento {intento})", flush=True)
        break
    except Exception as e:
        print(f"Esperando a Oracle (intento {intento}): {e}", flush=True)
        time.sleep(5)
else:
    sys.exit("Oracle no respondió en 5 minutos")
EOF

# 2) Crear las tablas propias de Django (usuarios, sesiones, admin).
python manage.py migrate --noinput

# 3) Crear el superusuario del admin si se definieron sus variables (solo la primera vez).
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --noinput 2>/dev/null || echo "El superusuario ya existe"
fi

# 4) Reemplazar este proceso por el CMD del Dockerfile (gunicorn).
exec "$@"
