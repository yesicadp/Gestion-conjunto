INSERT INTO detalle_facturas (id_factura, concepto, monto)
SELECT f.id_factura, 'administracion', 150000
FROM facturas f;