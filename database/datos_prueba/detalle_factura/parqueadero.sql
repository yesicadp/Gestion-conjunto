INSERT INTO detalle_facturas (id_factura, concepto, monto)
SELECT f.id_factura, 'parqueadero', 80000
FROM facturas f
JOIN viviendas v ON f.id_vivienda = v.id_vivienda
WHERE v.tiene_vehiculo = 1;