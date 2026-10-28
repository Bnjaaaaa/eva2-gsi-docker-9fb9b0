-- Tablas solicitadas en confi.md: Categoria(id, nombre) y
-- Producto(codigo, nombre, precio, stock, unidad, categoriaid), 2 registros cada una.
-- Ejecutar conectado como el usuario de aplicacion: usuario/MyPass123@FREEPDB1

SET FEEDBACK ON

CREATE TABLE categoria (
  id      NUMBER(10)    PRIMARY KEY,
  nombre  VARCHAR2(100) NOT NULL
);

CREATE TABLE producto (
  codigo       VARCHAR2(20)  PRIMARY KEY,
  nombre       VARCHAR2(150) NOT NULL,
  precio       NUMBER(10,2)  NOT NULL,
  stock        NUMBER(10)    DEFAULT 0 NOT NULL,
  unidad       VARCHAR2(20)  NOT NULL,
  categoriaid  NUMBER(10)    NOT NULL,
  CONSTRAINT fk_producto_categoria FOREIGN KEY (categoriaid) REFERENCES categoria (id)
);

INSERT INTO categoria (id, nombre) VALUES (1, 'Herramientas');
INSERT INTO categoria (id, nombre) VALUES (2, 'Electricidad');

INSERT INTO producto (codigo, nombre, precio, stock, unidad, categoriaid)
VALUES ('P001', 'Martillo carpintero 16 oz', 7990, 25, 'unidad', 1);
INSERT INTO producto (codigo, nombre, precio, stock, unidad, categoriaid)
VALUES ('P002', 'Cable electrico 2.5 mm', 890, 300, 'metro', 2);

COMMIT;
EXIT
