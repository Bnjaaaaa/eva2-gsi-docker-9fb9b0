"""Cabeceras de seguridad adicionales (mitigación de los hallazgos de ZAP, versión 1.1).

Django 5.2 no trae Content-Security-Policy integrada, por eso se agrega con este middleware.
"""

CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "     # el admin de Django usa algunos estilos en línea
    "img-src 'self' data:; "
    "frame-ancestors 'none'; "               # complementa X-Frame-Options: DENY (anti-clickjacking)
    "form-action 'self'; "
    "base-uri 'self'"
)


class CabecerasSeguridadMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        respuesta.setdefault("Content-Security-Policy", CSP)
        return respuesta
