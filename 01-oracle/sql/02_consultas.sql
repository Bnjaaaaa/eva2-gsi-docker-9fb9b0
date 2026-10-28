-- Verificacion de los datos cargados en FREEPDB1 (usuario de aplicacion)
SET LINESIZE 160
SET PAGESIZE 50
COLUMN nombre    FORMAT A28
COLUMN categoria FORMAT A14
COLUMN unidad    FORMAT A8
COLUMN codigo    FORMAT A6

SELECT id, nombre FROM categoria ORDER BY id;

SELECT codigo, nombre, precio, stock, unidad, categoriaid FROM producto ORDER BY codigo;

SELECT p.codigo, p.nombre, c.nombre AS categoria, p.precio, p.stock
FROM producto p JOIN categoria c ON c.id = p.categoriaid
ORDER BY p.codigo;
EXIT
