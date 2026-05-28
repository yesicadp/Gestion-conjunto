from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from database import obtener_conexion
from datetime import datetime, timedelta, date
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import string
import secrets
import os
import random

main = Blueprint('main', __name__)
# Configuración para imágenes de anuncios
UPLOAD_FOLDER = 'app/static/uploads/anuncios'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ruta de inicio que redirige al login
@main.route('/')
def inicio():
    return redirect(url_for('main.login'))

#Ruta de login
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

# Ruta de logout
@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

# Ruta de dashboard para residentes
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
            u.telefono,
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
    
    # Obtener la factura más reciente de la vivienda
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

    # Obtener los 5 anuncios más recientes para el dashboard
    cursor.execute("SELECT titulo, contenido, imagen, fecha_creacion FROM anuncios ORDER BY fecha_creacion DESC LIMIT 5")
    anuncios_recientes = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template(
        'dashboard_residente.html',
        nombre=nombre,
        correo=datos['correo_electronico'],
        telefono=datos['telefono'] if datos['telefono'] else "No registrado",
        vivienda=datos,
        parqueaderos_disponibles=disponibles,
        factura=factura,
        total=total,
        parqueadero_asignado=parqueadero_asignado,
        reservas=reservas,
        anuncios=anuncios_recientes
    )

# Ruta de dashboard para administradores
@main.route('/dashboard-admin')
def dashboard_admin():
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
            u.telefono,
            v.estado_financiero
        FROM viviendas v
        LEFT JOIN usuarios u 
            ON v.id_usuario = u.id_usuario
        ORDER BY v.id_vivienda ASC
    """
    cursor.execute(query)
    viviendas = cursor.fetchall()

    # Obtener los 5 anuncios más recientes para el dashboard
    cursor.execute("SELECT titulo, contenido, imagen, fecha_creacion FROM anuncios ORDER BY fecha_creacion DESC LIMIT 5")
    anuncios_recientes = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template(
        'dashboard_admin.html',
        viviendas=viviendas,
        anuncios=anuncios_recientes
    )

# Rutas para gestionar viviendas (administrador)
@main.route('/viviendas', methods=['GET'])
def listado_viviendas():
    if 'rol' not in session or session['rol'] != 'administrador':
        return jsonify({"error": "Acceso no autorizado"}), 403
    
    conexion = obtener_conexion()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_vivienda, id_usuario, tiene_vehiculo, estado_financiero FROM viviendas")
        viviendas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return jsonify({"viviendas": viviendas})
    return jsonify({"error": "No hay conexión"}), 500

# Detalle de vivienda (administrador)
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
            u.telefono,
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

# Ruta para gestionar pagos (administrador)
@main.route('/pagos', methods=['GET'])
def gestion_pagos():
    if 'rol' not in session or session['rol'] != 'administrador':
        return jsonify({"error": "Acceso no autorizado"}), 403
    
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

# Ruta para que el residente vea sus pagos
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

    # 2. Obtener factura de esa vivienda (ultima)
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

# Ruta para gestionar reservas del residente
@main.route('/reservas-residente', methods=['GET', 'POST'])
def reservas_residente():
    if 'rol' not in session or session['rol'] != 'residente':
        return redirect(url_for('main.login'))

    usuario_id = session['usuario_id']

    conexion = obtener_conexion()
    if not conexion:
        return "Error de conexión a la base de datos", 500

    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':
        fecha_evento = request.form.get('fecha_evento')

        if fecha_evento:
            cursor.execute("""
                INSERT INTO reservas (id_usuario, fecha_evento, estado)
                VALUES (%s, %s, 'pendiente')
            """, (usuario_id, fecha_evento))

            conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for('main.reservas_residente'))

    cursor.execute("""
        SELECT id_reserva, fecha_evento, estado
        FROM reservas
        WHERE id_usuario = %s
        ORDER BY fecha_evento DESC
    """, (usuario_id,))

    mis_reservas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'reservas_residente.html',
        mis_reservas=mis_reservas
    )

# Ruta para gestionar reservas del administrador
@main.route('/reservas-admin', methods=['GET', 'POST'])
def reservas_admin():
    if 'rol' not in session or session['rol'] != 'administrador':
        return redirect(url_for('main.login'))

    conexion = obtener_conexion()
    if not conexion:
        return "Error de conexión a la base de datos", 500

    cursor = conexion.cursor(dictionary=True)

    if request.method == 'POST':
        accion = request.form.get('accion')
        id_reserva = request.form.get('id_reserva')

        if accion in ['aprobada', 'rechazada'] and id_reserva:
            cursor.execute("""
                UPDATE reservas
                SET estado = %s
                WHERE id_reserva = %s
            """, (accion, id_reserva))

            conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for('main.reservas_admin'))

    cursor.execute("""
        SELECT 
            r.id_reserva,
            r.fecha_evento,
            r.estado,
            u.nombres,
            u.apellidos
        FROM reservas r
        JOIN usuarios u ON r.id_usuario = u.id_usuario
        ORDER BY r.fecha_evento DESC
    """)

    reservas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        'reservas_admin.html',
        reservas=reservas
    )

# Ruta para gestionar anuncios
@main.route('/anuncios', methods=['GET', 'POST'])
def gestion_anuncios():
    conexion = obtener_conexion()
    if not conexion: 
        return jsonify({"error": "No hay conexión con la base de datos"}), 500
    
    cursor = conexion.cursor(dictionary=True)
    
    # Publicación de anuncio (solo administradores)
    if request.method == 'POST':
        if 'rol' not in session or session['rol'] != 'administrador':
            return jsonify({"error": "Acceso denegado. Solo administradores pueden publicar anuncios."}), 403
            
        titulo = request.form.get('titulo')
        contenido = request.form.get('contenido')
        user_id = session.get('usuario_id')
        
        if not titulo or not contenido:
            return jsonify({"error": "El título y el contenido son obligatorios"}), 400

        # Procesamiento de la imagen
        ruta_imagen_bd = None
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Nos aseguramos de que la carpeta exista y si no, la crea
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Guardamos la imagen fisicamente en el server
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                
                # Guardamos solo la ruta para la base de datos
                ruta_imagen_bd = f'uploads/anuncios/{filename}'

        try:
            fecha_creacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            query = "INSERT INTO anuncios (id_usuario, titulo, contenido, imagen, fecha_creacion) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (user_id, titulo, contenido, ruta_imagen_bd, fecha_creacion))
            conexion.commit()
            return jsonify({"mensaje": "Anuncio publicado exitosamente"}), 201         
        except Exception as e:
            return jsonify({"error": f"Error al publicar: {str(e)}"}), 500

    # Consulta de anuncios
    try:
        cursor.execute("SELECT * FROM anuncios ORDER BY fecha_creacion DESC")
        anuncios = cursor.fetchall()
        
        for a in anuncios:
            a['fecha_creacion'] = str(a['fecha_creacion'])
            
        return jsonify({"anuncios": anuncios})
        
    except Exception as e:
        return jsonify({"error": f"Error al cargar anuncios: {str(e)}"}), 500
    finally:
        cursor.close()
        conexion.close()

# Ruta para gestionar parqueaderos de administrador
@main.route('/parqueaderos', methods=['GET', 'POST'])
def parqueaderos_admin():
    if 'rol' not in session or session['rol'] != 'administrador':
        return jsonify({"error": "Acceso no autorizado"}), 403
    
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # === LÓGICA DE DÍAS RESTANTES DEL TRIMESTRE EN TIEMPO REAL ===
    hoy = date.today()
    año_actual = hoy.year
    
    # Determinar las fechas de fin de cada trimestre
    if hoy.month <= 3:
        fecha_fin_trimestre = date(año_actual, 3, 31)
    elif hoy.month <= 6:
        fecha_fin_trimestre = date(año_actual, 6, 30)
    elif hoy.month <= 9:
        fecha_fin_trimestre = date(año_actual, 9, 30)
    else:
        fecha_fin_trimestre = date(año_actual, 12, 31)
    
    # Calcular días restantes
    dias_restantes = (fecha_fin_trimestre - hoy).days

    # === CONSULTA BASE: TRAER VIVIENDAS Y USUARIOS ===
    query_viviendas = """
        SELECT 
            v.id_vivienda, 
            v.tiene_vehiculo,
            u.nombres AS nombres_residente, 
            u.apellidos AS apellidos_residente
        FROM viviendas v
        LEFT JOIN usuarios u ON v.id_usuario = u.id_usuario
        ORDER BY v.id_vivienda ASC
    """
    cursor.execute(query_viviendas)
    lista_viviendas = cursor.fetchall()
    
    # Filtrar en Python quiénes tienen vehículo registrado (Aptos para sorteo)
    casas_con_carro = [c for c in lista_viviendas if c['tiene_vehiculo'] == 1]
    total_casas_con_carro = len(casas_con_carro)

    # === MANEJO DE ACCIONES (POST) ===
    if request.method == 'POST':
        accion = request.form.get('accion')

        # CASO A: EL ADMINISTRADOR DICTAMINÓ UN SORTEO AUTOMÁTICO
        if accion == 'sorteo_aleatorio':
            # Elegimos un máximo de 8 casas al azar que tengan carro
            cupos_disponibles = min(8, len(casas_con_carro))
            casas_ganadoras = random.sample(casas_con_carro, cupos_disponibles)
            
            # Guardamos el resultado del sorteo en la sesión para simular persistencia sin alterar tablas
            resultado_sorteo = {}
            for i, casa in enumerate(casas_ganadoras):
                resultado_sorteo[str(i + 1)] = casa  # Guarda el parqueadero 1 al 8
            
            session['parqueaderos_sorteados'] = resultado_sorteo
            session.modified = True

        # CASO B: ASIGNACIÓN MANUAL INDIVIDUAL
        elif accion == 'asignacion_manual':
            id_parqueadero = request.form.get('id_parqueadero')
            id_vivienda = request.form.get('id_vivienda')
            
            # Buscamos los datos de la casa seleccionada
            casa_seleccionada = next((c for c in lista_viviendas if str(c['id_vivienda']) == str(id_vivienda)), None)
            
            if casa_seleccionada:
                # Si no existe el almacén del sorteo en sesión, lo creamos vacío
                if 'parqueaderos_sorteados' not in session:
                    session['parqueaderos_sorteados'] = {}
                
                # Desasignar la casa de cualquier otro parqueadero para que no se repita
                session['parqueaderos_sorteados'] = {k: v for k, v in session['parqueaderos_sorteados'].items() if str(v['id_vivienda']) != str(id_vivienda)}
                
                # Asignar al nuevo parqueadero
                session['parqueaderos_sorteados'][str(id_parqueadero)] = casa_seleccionada
                session.modified = True

        cursor.close()
        conexion.close()
        return redirect(url_for('main.parqueaderos_admin'))

    # === CONSTRUCCIÓN DEL MAPA VISUAL PARA EL GET ===
    # Consultamos los 8 parqueaderos físicos de tu tabla
    cursor.execute("SELECT id_parqueadero, estado FROM parqueaderos ORDER BY id_parqueadero ASC")
    parqueaderos_db = cursor.fetchall()

    parqueaderos_finales = []
    sorteo_actual = session.get('parqueaderos_sorteados', {})

    for p in parqueaderos_db:
        id_p_str = str(p['id_parqueadero'])
        
        # Si este parqueadero fue asignado en el sorteo de la sesión
        if id_p_str in sorteo_actual:
            info_casa = sorteo_actual[id_p_str]
            parqueaderos_finales.append({
                'id_parqueadero': p['id_parqueadero'],
                'estado': 'ocupado',
                'id_vivienda': info_casa['id_vivienda'],
                'nombres_residente': info_casa['nombres_residente'],
                'apellidos_residente': info_casa['apellidos_residente']
            })
        else:
            # Si está libre
            parqueaderos_finales.append({
                'id_parqueadero': p['id_parqueadero'],
                'estado': 'disponible',
                'id_vivienda': None,
                'nombres_residente': None,
                'apellidos_residente': None
            })

    cursor.close()
    conexion.close()

    return render_template(
        'parqueaderos_admin.html',
        parqueaderos=parqueaderos_finales,
        lista_viviendas=lista_viviendas,
        casas_con_carro=casas_con_carro,
        total_casas_vehiculo=total_casas_con_carro,
        dias_restantes=dias_restantes
    )
    
@main.route('/parqueadero-residente')
def parqueadero_residente():
    if 'rol' not in session or session['rol'] != 'residente':
        return jsonify({"error": "Acceso no autorizado"}), 403

    id_usuario = session.get('id_usuario')

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_vivienda
        FROM viviendas
        WHERE id_usuario = %s
    """, (id_usuario,))
    vivienda = cursor.fetchone()

    parqueadero_asignado = None

    if vivienda:
        sorteo_actual = session.get('parqueaderos_sorteados', {})

        for id_parqueadero, casa in sorteo_actual.items():
            if str(casa['id_vivienda']) == str(vivienda['id_vivienda']):
                parqueadero_asignado = {
                    'id_parqueadero': id_parqueadero,
                    'id_vivienda': vivienda['id_vivienda']
                }
                break

    cursor.close()
    conexion.close()

    return render_template(
        'parqueadero_residente.html',
        parqueadero_asignado=parqueadero_asignado,
        fecha_fin='30 de junio de 2026'
    )    
    
# Ruta para mostrar página en proceso
@main.route('/en-proceso')
def en_proceso():
    if 'usuario_id' not in session:
        return redirect(url_for('main.login'))
    return render_template('en_proceso.html')

# Función para enviar correo de recuperación
def enviar_correo_recuperacion(destinatario, nombre, codigo):
    remitente = "JhonAPL08@gmail.com"
    password = "zfuz fjcw dxjc pwna"

    msg = MIMEMultipart()
    msg['From'] = f"Administración El Ciprés <{remitente}>"
    msg['To'] = destinatario
    msg['Subject'] = '🔑 Código de Seguridad - Conjunto El Ciprés'

    cuerpo = f"""
    Hola, {nombre}.
    
    Has solicitado un código para restablecer tu contraseña en el sistema del Conjunto Residencial El Ciprés.
    
    Tu código de seguridad es: {codigo}
    
    Este código expirará en 15 minutos por motivos de seguridad. Si no has solicitado este cambio, por favor ignora este mensaje y asegúrate de que tu cuenta esté segura.
    
    Saludos,
    Equipo de Soporte - El Ciprés.
    """
    
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        print(f"Correo personalizado enviado con éxito a {nombre} ({destinatario})")
        return True
    except Exception as e:
        print(f"Error al enviar el correo a {destinatario}: {e}")
        return False

# Ruta para mostrar formulario de recuperación de contraseña
@main.route('/recuperar-contrasena')
def recuperar_contrasena():
    return render_template('recuperar_contrasena.html')

# Ruta 1: Generación de token y envío de correo
@main.route('/solicitar-recuperacion', methods=['POST'])
def solicitar_recuperacion():
    correo = request.form.get('correo')
    
    conexion = obtener_conexion()
    if not conexion:
        return jsonify({"error": "Fallo de conexión a la base de datos"}), 500
        
    cursor = conexion.cursor(dictionary=True)

    try:
        # Buscamos al usuario y traemos su nombre para personalizar el correo
        cursor.execute(
            "SELECT id_usuario, nombres FROM usuarios WHERE correo_electronico = %s",
            (correo,)
        )
        usuario = cursor.fetchone()

        if usuario:
            # Generación de código criptográficamente seguro
            alfabeto = string.ascii_letters + string.digits
            codigo = ''.join(secrets.choice(alfabeto) for i in range(8))

            # Definimos el tiempo de vida del código
            vencimiento = datetime.now() + timedelta(minutes=15)

            # Actualizamos la base de datos con el token y el vencimiento
            cursor.execute("""
                UPDATE usuarios 
                SET codigo_recuperacion = %s, vencimiento_codigo = %s 
                WHERE correo_electronico = %s
            """, (codigo, vencimiento, correo))
            conexion.commit()

            # Usamos la función que ya tenemos lista
            # Pasamos correo, el nombre real de la DB y el código generado
            enviar_correo_recuperacion(correo, usuario['nombres'], codigo)
            
            print(f"Proceso iniciado para {usuario['nombres']}. Código enviado.")

        cursor.close()
        conexion.close()

        # Enviamos a la ruta de ingreso del código, pasando el correo para que se muestre en el formulario
        return render_template(
            'recuperar_contrasena.html',
            paso=2,
            correo=correo,
            mensaje="Revisa tu bandeja de entrada (y la carpeta de spam)."
        )

    except Exception as e:
        print(f"Error en solicitar_recuperacion: {e}")
        return jsonify({"error": "Hubo un problema al procesar la solicitud"}), 500

# Ruta 2: Validación del código y actualización de contraseña
@main.route('/cambiar-contrasena', methods=['POST'])
def cambiar_contrasena():
    correo = request.form.get('correo')
    codigo = request.form.get('codigo')
    nueva = request.form.get('nueva_contrasena')
    confirmar = request.form.get('confirmar_contrasena')

    # Validación de integridad básica
    if nueva != confirmar:
        return render_template(
            'recuperar_contrasena.html',
            paso=2,
            correo=correo,
            error="Las contraseñas no coinciden. Inténtalo de nuevo."
        )

    conexion = obtener_conexion()
    if not conexion:
        return jsonify({"error": "Error de conexión"}), 500
        
    cursor = conexion.cursor(dictionary=True)

    try:
        # Buscamos el token y el vencimiento guardados para ese correo
        cursor.execute("""
            SELECT codigo_recuperacion, vencimiento_codigo 
            FROM usuarios 
            WHERE correo_electronico = %s
        """, (correo,))
        usuario = cursor.fetchone()

        # Validación de autenticidad del código
        if not usuario or usuario['codigo_recuperacion'] != codigo:
            return render_template(
                'recuperar_contrasena.html',
                paso=2,
                correo=correo,
                error="El código de seguridad es incorrecto."
            )

        # Validación de la ventana de tiempo
        if datetime.now() > usuario['vencimiento_codigo']:
            return render_template(
                'recuperar_contrasena.html',
                paso=2,
                correo=correo,
                error="Este código ha expirado. Solicita uno nuevo."
            )

        # Generamos el hash y actualizamos
        # Importante: Limpiamos los campos de recuperación (NULL)
        nuevo_hash = generate_password_hash(nueva)

        cursor.execute("""
            UPDATE usuarios 
            SET contrasena = %s,
                codigo_recuperacion = NULL,
                vencimiento_codigo = NULL
            WHERE correo_electronico = %s
        """, (nuevo_hash, correo))

        conexion.commit()
        print(f"Contraseña actualizada exitosamente para: {correo}")

        # Redirigimos al Login con mensaje de éxito
        return render_template(
            'login.html',
            mensaje="Tu contraseña ha sido actualizada. Ya puedes iniciar sesión."
        )

    except Exception as e:
        print(f"Error en cambiar_contrasena: {e}")
        return jsonify({"error": "Error interno al actualizar la contraseña"}), 500
    finally:
        cursor.close()
        conexion.close()