INSERT INTO detalle_facturas (id_factura, concepto, monto)
SELECT f.id_factura, 'multa', 20000
FROM facturas f
WHERE f.estado = 'vencido';