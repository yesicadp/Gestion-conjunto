from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from database import obtener_conexion

main = Blueprint('main', __name__)

@main.route('/')
def inicio():
    return "Ruta de Inicio - Conjunto Ciprés"

# LOGIN REAL CON BASE DE DATOS
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo_ingresado = request.form.get('correo')
        contrasena_ingresada = request.form.get('contrasena')

        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor(dictionary=True)
            # Buscamos el usuario por su correo
            query = "SELECT id_usuario, nombre, contraseña, rol FROM usuario WHERE correo = %s"
            cursor.execute(query, (correo_ingresado,))
            usuario = cursor.fetchone()
            cursor.close()
            conexion.close()

            # Verificamos si existe y si la contraseña coincide
            if usuario and usuario['contraseña'] == contrasena_ingresada:
                session['usuario_id'] = usuario['id_usuario']
                session['nombre'] = usuario['nombre']
                session['rol'] = usuario['rol']
                
                if usuario['rol'] == 'administrador':
                    return redirect(url_for('main.dashboard_admin'))
                else:
                    return redirect(url_for('main.dashboard_residente'))
        
        return "Correo o contraseña incorrectos."

    return "Página de Login"

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

# DASHBOARDS PROTEGIDOS
@main.route('/dashboard-residente')
def dashboard_residente():
    if 'rol' not in session or session['rol'] != 'residente':
        return redirect(url_for('main.login'))
    return f"Bienvenido al Panel del Residente, {session['nombre']}"

@main.route('/dashboard-admin')
def dashboard_admin():
    if 'rol' not in session or session['rol'] != 'administrador':
        return redirect(url_for('main.login'))
    return f"Bienvenido al Panel del Administrador, {session['nombre']}"

# LISTADO DE VIVIENDAS
@main.route('/viviendas', methods=['GET'])
def listado_viviendas():
    conexion = obtener_conexion()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id_vivienda, numero, estado FROM vivienda")
        viviendas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return jsonify({"viviendas": viviendas})
    return jsonify({"error": "No hay conexión"}), 500

# GESTIÓN DE PAGOS
@main.route('/pagos', methods=['GET', 'POST'])
def gestion_pagos():
    conexion = obtener_conexion()
    if not conexion: return jsonify({"error": "No hay conexión"}), 500
    
    cursor = conexion.cursor(dictionary=True)
    if request.method == 'POST':
        fecha = request.form.get('fecha')
        monto = request.form.get('monto')
        estado = request.form.get('estado')
        vivienda_id = request.form.get('vivienda_id') # Importante para la FK de Jhon
        
        query = "INSERT INTO pago (fecha, monto, estado, vivienda_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (fecha, monto, estado, vivienda_id))
        conexion.commit()
        mensaje = "Pago registrado en BD"
    else:
        cursor.execute("SELECT * FROM pago")
        pagos = cursor.fetchall()
        return jsonify({"pagos": pagos})

    cursor.close()
    conexion.close()
    return jsonify({"mensaje": mensaje}), 201

# RESERVAS DEL SALÓN
@main.route('/reservas', methods=['GET', 'POST'])
def gestion_reservas():
    conexion = obtener_conexion()
    if not conexion: return jsonify({"error": "No hay conexión"}), 500
    
    cursor = conexion.cursor(dictionary=True)
    if request.method == 'POST':
        fecha = request.form.get('fecha')
        h_inicio = request.form.get('hora_inicio')
        h_fin = request.form.get('hora_fin')
        usuario_id = session.get('usuario_id')
        
        query = "INSERT INTO reserva (fecha, hora_inicio, hora_fin, estado, usuario_id) VALUES (%s, %s, %s, 'Confirmada', %s)"
        cursor.execute(query, (fecha, h_inicio, h_fin, usuario_id))
        conexion.commit()
        return jsonify({"mensaje": "Reserva guardada"}), 201
    
    cursor.execute("SELECT * FROM reserva")
    reservas = cursor.fetchall()
    for reserva in reservas:
        if reserva['hora_inicio']:
            reserva['hora_inicio'] = str(reserva['hora_inicio'])
        if reserva['hora_fin']:
            reserva['hora_fin'] = str(reserva['hora_fin'])
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
        fecha = request.form.get('fecha')
        user_id = session.get('usuario_id')
        
        query = "INSERT INTO anuncio (titulo, contenido, fecha, usuario_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (titulo, contenido, fecha, user_id))
        conexion.commit()
        return jsonify({"mensaje": "Anuncio publicado"}), 201

    cursor.execute("SELECT * FROM anuncio")
    anuncios = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify({"anuncios": anuncios})