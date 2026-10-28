"""Modelos sobre las tablas CATEGORIA y PRODUCTO creadas en Oracle (01-oracle/sql/01_tablas.sql).

managed = False: Django lee y escribe en las tablas existentes, pero no las crea ni las
modifica con migraciones (la estructura la define el script SQL).
"""
from django.db import models


class Categoria(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "categoria"
        ordering = ["id"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(primary_key=True, max_length=20)
    nombre = models.CharField(max_length=150)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    unidad = models.CharField(max_length=20)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, db_column="categoriaid", related_name="productos"
    )

    class Meta:
        managed = False
        db_table = "producto"
        ordering = ["codigo"]
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"
