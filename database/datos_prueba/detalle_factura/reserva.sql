INSERT INTO detalle_facturas (id_factura, concepto, monto)
SELECT f.id_factura, 'reserva', 50000
FROM facturas f
WHERE MOD(f.id_factura, 7) = 0;