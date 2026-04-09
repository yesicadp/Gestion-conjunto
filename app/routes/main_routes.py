from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from database import obtener_conexion
from datetime import datetime

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

            if usuario and usuario['contrasena'] == contrasena_ingresada:
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
    
    return render_template(
        'dashboard_residente.html',
        nombre=session.get('nombre'),
        correo=session.get('correo')
    )

@main.route('/dashboard-admin')
def dashboard_admin():
    if 'rol' not in session or session['rol'] != 'administrador':
        return redirect(url_for('main.login'))
    
    return render_template(
        'dashboard_admin.html',
        nombre=session.get('nombre'),
        correo=session.get('correo')
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