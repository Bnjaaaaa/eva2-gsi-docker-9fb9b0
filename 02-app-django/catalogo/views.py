from django.db import connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Producto


def lista(request):
    """Listado de productos con su categoría y búsqueda por nombre (?q=)."""
    q = request.GET.get("q", "").strip()
    productos = Producto.objects.select_related("categoria")
    if q:
        productos = productos.filter(nombre__icontains=q)
    return render(request, "catalogo/lista.html", {"productos": productos, "q": q})


def detalle(request, codigo):
    producto = get_object_or_404(Producto.objects.select_related("categoria"), codigo=codigo)
    return render(request, "catalogo/detalle.html", {"producto": producto})


def salud(request):
    """Chequeo de salud: confirma que la aplicación responde y que Oracle está accesible."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
        return JsonResponse({"estado": "ok", "base_de_datos": "ok"})
    except Exception:
        return JsonResponse({"estado": "error", "base_de_datos": "sin conexión"}, status=503)
