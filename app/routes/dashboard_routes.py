from flask import Blueprint, render_template, redirect, url_for, session
from database import obtener_conexion

dashboard = Blueprint('dashboard', __name__)


# Ruta Residente
@dashboard.route('/dashboard-residente')
def dashboard_residente():
    if 'rol' not in session or session['rol'] != 'residente':
        return redirect(url_for('auth.login'))

    usuario_id = session['usuario_id']
    nombre = session['nombre']

    conexion = obtener_conexion()
    if not conexion:
        return "Error de conexión a la base de datos", 500

    cursor = conexion.cursor(dictionary=True)

    # Obtener datos del usuario y su vivienda
    query = """
        SELECT 
            u.nombres,
            u.apellidos,
            u.correo_electronico,
            v.id_vivienda,
            v.tiene_vehiculo,
            v.estado_financiero
        FROM usuarios u
        JOIN viviendas v ON u.id_usuario = v.id_usuario
        WHERE u.id_usuario = %s
    """
    cursor.execute(query, (usuario_id,))
    datos = cursor.fetchone()

    # Contar parqueaderos disponibles
    cursor.execute("""
        SELECT COUNT(*) AS disponibles
        FROM parqueaderos
        WHERE estado = 'disponible'
    """)
    parqueaderos = cursor.fetchone()
    disponibles = parqueaderos['disponibles']
    
    cursor.execute("""
        SELECT f.id_factura, f.fecha_limite, f.estado
        FROM facturas f
        WHERE f.id_vivienda = %s
        ORDER BY f.fecha DESC
        LIMIT 1
    """, (datos['id_vivienda'],))
    factura = cursor.fetchone()

    if factura:
        cursor.execute("""
            SELECT SUM(monto) AS total
            FROM detalle_facturas
            WHERE id_factura = %s
        """, (factura['id_factura'],))
        resultado_total = cursor.fetchone()
        total = resultado_total['total'] if resultado_total['total'] else 0
    else:
        total = 0
        
    # Parqueadero asignado a la vivienda
    cursor.execute("""
        SELECT 
            ap.id_parqueadero,
            ap.fecha_inicio,
            ap.fecha_fin
        FROM asignacion_parqueaderos ap
        WHERE ap.id_vivienda = %s
        ORDER BY ap.fecha_inicio DESC
        LIMIT 1
    """, (datos['id_vivienda'],))
    parqueadero_asignado = cursor.fetchone()


    # Reservas del residente
    cursor.execute("""
        SELECT 
            fecha_evento,
            estado
        FROM reservas
        WHERE id_usuario = %s
        ORDER BY fecha_evento DESC
        LIMIT 3
    """, (usuario_id,))
    reservas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'dashboard_residente.html',
        nombre=nombre,
        correo=datos['correo_electronico'],
        vivienda=datos,
        parqueaderos_disponibles=disponibles,
        factura=factura,
        total=total,
        parqueadero_asignado=parqueadero_asignado,
        reservas=reservas
    )

@dashboard.route('/dashboard-admin')
def dashboard_admin():
    # Verificar acceso del administrador
    if 'rol' not in session or session['rol'] != 'administrador':
        return redirect(url_for('auth.login'))

    conexion = obtener_conexion()
    if not conexion:
        return "Error de conexión a la base de datos", 500

    cursor = conexion.cursor(dictionary=True)

    # Consulta para obtener las viviendas con sus residentes
    query = """
        SELECT 
            v.id_vivienda,
            u.nombres,
            u.apellidos,
            u.correo_electronico,
            v.estado_financiero
        FROM viviendas v
        LEFT JOIN usuarios u 
            ON v.id_usuario = u.id_usuario
        ORDER BY v.id_vivienda ASC
    """
    cursor.execute(query)
    viviendas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'dashboard_admin.html',
        viviendas=viviendas
    )