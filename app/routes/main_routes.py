from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from database import obtener_conexion
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
import smtplib
from email.mime.text import MIMEText
import string
import secrets

main = Blueprint('main', __name__)

@main.route('/')
def inicio():
    return redirect(url_for('main.login'))

# LOGIN 
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo_ingresado = request.form.get('correo')
        contrasena_ingresada = request.form.get('contrasena')

        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor(dictionary=True)

            query = """
                SELECT id_usuario, nombres, apellidos, correo_electronico, contrasena, rol
                FROM usuarios
                WHERE correo_electronico = %s
            """
            cursor.execute(query, (correo_ingresado,))
            usuario = cursor.fetchone()

            cursor.close()
            conexion.close()

            if usuario and check_password_hash(usuario['contrasena'], contrasena_ingresada):
                session['usuario_id'] = usuario['id_usuario']
                session['nombre'] = f"{usuario['nombres']} {usuario['apellidos']}"
                session['rol'] = usuario['rol']
                session['correo'] = usuario['correo_electronico']

                if usuario['rol'] == 'administrador':
                    return redirect(url_for('main.dashboard_admin'))
                else:
                    return redirect(url_for('main.dashboard_residente'))

        return render_template('login.html', error="Correo o contraseña incorrectos.")

    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main.route('/dashboard-residente')
def dashboard_residente():
    if 'rol' not in session or session['rol'] != 'residente':
        return redirect(url_for('main.login'))

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

@main.route('/dashboard-admin')
def dashboard_admin():
    # Verificar acceso del administrador
    if 'rol' not in session or session['rol'] != 'administrador':
        return redirect(url_for('main.login'))

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

# VIVIENDAS
@main.route('/viviendas', methods=['GET'])
def listado_viviendas():
    conexion = obtener_conexion()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_vivienda, id_usuario, tiene_vehiculo, estado_financiero FROM viviendas")
        viviendas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return jsonify({"viviendas": viviendas})
    return jsonify({"error": "No hay conexión"}), 500

@main.route('/admin/vivienda/<int:id_vivienda>')
def detalle_vivienda(id_vivienda):
    if 'rol' not in session or session['rol'] != 'administrador':
        return redirect(url_for('main.login'))

    conexion = obtener_conexion()
    if not conexion:
        return "Error de conexión a la base de datos", 500

    cursor = conexion.cursor(dictionary=True)

    query = """
        SELECT 
            v.id_vivienda,
            v.estado_financiero,
            v.tiene_vehiculo,
            u.nombres,
            u.apellidos,
            u.correo_electronico
        FROM viviendas v
        LEFT JOIN usuarios u ON v.id_usuario = u.id_usuario
        WHERE v.id_vivienda = %s
    """
    cursor.execute(query, (id_vivienda,))
    vivienda = cursor.fetchone()

    cursor.close()
    conexion.close()

    return render_template('detalle_vivienda.html', vivienda=vivienda)

# FACTURAS
@main.route('/pagos', methods=['GET', 'POST'])
def gestion_pagos():
    conexion = obtener_conexion()
    if not conexion: return jsonify({"error": "No hay conexión"}), 500
    
    cursor = conexion.cursor(dictionary=True)
    if request.method == 'POST':
        id_vivienda = request.form.get('id_vivienda')
        fecha = request.form.get('fecha')
        fecha_oportuno = request.form.get('fecha_pago_oportuno')
        fecha_limite = request.form.get('fecha_limite')
        estado = request.form.get('estado')
        query = "INSERT INTO facturas (id_vivienda, fecha, fecha_pago_oportuno, fecha_limite, estado) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (id_vivienda, fecha, fecha_oportuno, fecha_limite, estado))
        conexion.commit()
        mensaje = "Factura registrada en BD"
    else:
        cursor.execute("SELECT * FROM facturas")
        pagos = cursor.fetchall()
        # Convertimos las fechas a string para evitar errores JSON
        for p in pagos:
            p['fecha'] = str(p['fecha'])
            p['fecha_pago_oportuno'] = str(p['fecha_pago_oportuno'])
            p['fecha_limite'] = str(p['fecha_limite'])
        return jsonify({"pagos": pagos})

    cursor.close()
    conexion.close()
    return jsonify({"mensaje": mensaje}), 201

@main.route('/pagos-residente')
def pagos_residente():
    if 'rol' not in session or session['rol'] != 'residente':
        return redirect(url_for('main.login'))

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

# RESERVAS
@main.route('/reservas', methods=['GET', 'POST'])
def gestion_reservas():
    conexion = obtener_conexion()
    if not conexion: return jsonify({"error": "No hay conexión"}), 500
    
    cursor = conexion.cursor(dictionary=True)
    if request.method == 'POST':
        fecha_evento = request.form.get('fecha_evento')
        usuario_id = session.get('usuario_id')
        
        query = "INSERT INTO reservas (id_usuario, fecha_evento, estado) VALUES (%s, %s, 'pendiente')"
        cursor.execute(query, (usuario_id, fecha_evento))
        conexion.commit()
        return jsonify({"mensaje": "Reserva guardada"}), 201
    
    cursor.execute("SELECT * FROM reservas")
    reservas = cursor.fetchall()
    for r in reservas:
        r['fecha_evento'] = str(r['fecha_evento'])
        
    cursor.close()
    conexion.close()
    return jsonify({"reservas": reservas})

# ANUNCIOS
@main.route('/anuncios', methods=['GET', 'POST'])
def gestion_anuncios():
    conexion = obtener_conexion()
    if not conexion: return jsonify({"error": "No hay conexión"}), 500
    
    cursor = conexion.cursor(dictionary=True)
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        contenido = request.form.get('contenido')
        fecha_creacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = session.get('usuario_id')
        
        query = "INSERT INTO anuncios (id_usuario, titulo, contenido, fecha_creacion) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, titulo, contenido, fecha_creacion))
        conexion.commit()
        return jsonify({"mensaje": "Anuncio publicado"}), 201

    cursor.execute("SELECT * FROM anuncios")
    anuncios = cursor.fetchall()
    for a in anuncios:
        a['fecha_creacion'] = str(a['fecha_creacion'])
        
    cursor.close()
    conexion.close()
    return jsonify({"anuncios": anuncios})

@main.route('/en-proceso')
def en_proceso():
    if 'usuario_id' not in session:
        return redirect(url_for('main.login'))
    return render_template('en_proceso.html')

def enviar_correo_recuperacion(destinatario, codigo):
    remitente = "elcipresadmin@gmail.com"
    password = "dvtd jvca fbxx ncpv"

    msg = MIMEText(f"Hola, tu código de recuperación para el Conjunto Ciprés es: {codigo}. Este código expirará en 15 minutos.")
    msg['Subject'] = 'Recuperación de Contraseña - Conjunto Ciprés'
    msg['From'] = remitente
    msg['To'] = destinatario

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
    
@main.route('/recuperar-contrasena')
def recuperar_contrasena():
    return render_template('recuperar_contrasena.html')

# RUTA 1: EL USUARIO PIDE RECUPERAR SU CONTRASEÑA
@main.route('/solicitar-recuperacion', methods=['POST'])
def solicitar_recuperacion():
    correo = request.form.get('correo')
    
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute(
        "SELECT id_usuario FROM usuarios WHERE correo_electronico = %s",
        (correo,)
    )
    usuario = cursor.fetchone()

    if usuario:
        alfabeto = string.ascii_letters + string.digits
        codigo = ''.join(secrets.choice(alfabeto) for i in range(8))

        vencimiento = datetime.now() + timedelta(minutes=15)

        cursor.execute("""
            UPDATE usuarios 
            SET codigo_recuperacion = %s, vencimiento_codigo = %s 
            WHERE correo_electronico = %s
        """, (codigo, vencimiento, correo))

        conexion.commit()

        print("CÓDIGO:", codigo)

    cursor.close()
    conexion.close()

    return render_template(
        'recuperar_contrasena.html',
        paso=2,
        correo=correo,
    )


# RUTA 2: EL USUARIO INGRESA EL CÓDIGO Y LA NUEVA CONTRASEÑA 
@main.route('/cambiar-contrasena', methods=['POST'])
def cambiar_contrasena():
    correo = request.form.get('correo')
    codigo = request.form.get('codigo')
    nueva = request.form.get('nueva_contrasena')
    confirmar = request.form.get('confirmar_contrasena')

    if nueva != confirmar:
        return render_template(
            'recuperar_contrasena.html',
            paso=2,
            correo=correo,
            error="Las contraseñas no coinciden"
        )

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT codigo_recuperacion, vencimiento_codigo 
        FROM usuarios 
        WHERE correo_electronico = %s
    """, (correo,))
    usuario = cursor.fetchone()

    if not usuario or usuario['codigo_recuperacion'] != codigo:
        cursor.close()
        conexion.close()
        return render_template(
            'recuperar_contrasena.html',
            paso=2,
            correo=correo,
            error="Código incorrecto"
        )

    if datetime.now() > usuario['vencimiento_codigo']:
        cursor.close()
        conexion.close()
        return render_template(
            'recuperar_contrasena.html',
            paso=2,
            correo=correo,
            error="El código expiró"
        )

    nuevo_hash = generate_password_hash(nueva)

    cursor.execute("""
        UPDATE usuarios 
        SET contrasena = %s,
            codigo_recuperacion = NULL,
            vencimiento_codigo = NULL
        WHERE correo_electronico = %s
    """, (nuevo_hash, correo))

    conexion.commit()
    cursor.close()
    conexion.close()

    return render_template(
        'login.html',
        mensaje="Contraseña cambiada con éxito"
    )