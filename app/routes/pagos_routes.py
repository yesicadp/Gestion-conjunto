from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from database import obtener_conexion

pagos = Blueprint('pagos', __name__)

@pagos.route('/pagos', methods=['GET'])
def gestion_pagos():
    mes = request.args.get('mes')

    if not mes:
        mes = datetime.now().strftime('%Y-%m')

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT 
            f.id_factura,
            v.id_vivienda,
            u.nombres,
            u.apellidos,
            v.estado_financiero,
            f.fecha,
            f.fecha_pago_oportuno,
            f.fecha_limite,
            f.estado AS estado_factura
        FROM viviendas v
        LEFT JOIN usuarios u ON v.id_usuario = u.id_usuario
        LEFT JOIN facturas f ON v.id_vivienda = f.id_vivienda
        WHERE DATE_FORMAT(f.fecha, '%Y-%m') = %s
        ORDER BY v.id_vivienda ASC
    """

    cursor.execute(query, (mes,))
    pagos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'pagos_admin.html',
        pagos=pagos,
        mes=mes
    )

@pagos.route('/pagos-residente')
def pagos_residente():
    if 'rol' not in session or session['rol'] != 'residente':
        return redirect(url_for('auth.login'))

    usuario_id = session['usuario_id']
    nombre = session['nombre']

    conexion = obtener_conexion()
    if not conexion:
        return "Error de conexión a la base de datos", 500

    cursor = conexion.cursor(dictionary=True)

    # 1. Obtener vivienda
    query_vivienda = """
        SELECT v.id_vivienda
        FROM viviendas v
        WHERE v.id_usuario = %s
    """
    cursor.execute(query_vivienda, (usuario_id,))
    vivienda = cursor.fetchone()

    # 2. Obtener factura de esa vivienda (última)
    query_factura = """
        SELECT *
        FROM facturas
        WHERE id_vivienda = %s
        ORDER BY fecha DESC
        LIMIT 1
    """
    cursor.execute(query_factura, (vivienda['id_vivienda'],))
    factura = cursor.fetchone()

    meses = {
        "January": "Enero", "February": "Febrero", "March": "Marzo",
        "April": "Abril", "May": "Mayo", "June": "Junio",
        "July": "Julio", "August": "Agosto", "September": "Septiembre",
        "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
    }

    if not factura:
        detalles = []
        total = 0
        mes = "Sin datos"
    else:
        fecha = factura['fecha']

        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, "%Y-%m-%d")

        mes = fecha.strftime("%B")
        mes = meses.get(mes, mes)

        cursor.execute("""
            SELECT concepto, monto
            FROM detalle_facturas
            WHERE id_factura = %s
        """, (factura['id_factura'],))
        
        detalles = cursor.fetchall()
        total = sum(d['monto'] for d in detalles)
        
    query_historial = """
        SELECT f.id_factura, f.fecha, SUM(df.monto) AS total
        FROM facturas f
        LEFT JOIN detalle_facturas df ON f.id_factura = df.id_factura
        WHERE f.id_vivienda = %s
        GROUP BY f.id_factura, f.fecha
        ORDER BY f.fecha DESC
    """
    cursor.execute(query_historial, (vivienda['id_vivienda'],))
    historial = cursor.fetchall()

    # Agregar total a cada factura
    for h in historial:
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM detalle_facturas
            WHERE id_factura = %s
        """, (h['id_factura'],))
        
        total_factura = cursor.fetchone()
        h['total'] = total_factura['total'] if total_factura['total'] else 0

    cursor.close()
    conexion.close()

    return render_template(
        'pagos_residente.html',
        nombre=nombre,
        correo=session['correo'],
        vivienda=vivienda,
        factura=factura,
        detalles=detalles,
        total=total,
        mes=mes,
        historial=historial
    )