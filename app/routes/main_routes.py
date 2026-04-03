from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session

# Creamos un 'Blueprint' que es como un módulo de rutas
main = Blueprint('main', __name__)

usuarios_mock = [
    {
        "id": 1, 
        "nombre": "Administrador Principal", 
        "contrasena": "1234", 
        "correo": "admin@cipres.com", 
        "telefono": "3001112233", 
        "rol": "administrador"
    },
    {
        "id": 2, 
        "nombre": "Thomas", 
        "contrasena": "1234", 
        "correo": "thomas@correo.com", 
        "telefono": "3004445566", 
        "rol": "residente"
    }
]

# --- DATOS SIMULADOS ALINEADOS CON EL MER ---

viviendas_mock = [
    {"id": 1, "Numero": "Casa 1", "Estado": "Al día"},
    {"id": 2, "Numero": "Casa 2", "Estado": "En mora"},
    {"id": 3, "Numero": "Casa 3", "Estado": "Al día"},
    {"id": 4, "Numero": "Casa 4", "Estado": "Al día"}

    
]

pagos_mock = [
    {
        "id": 1, 
        "fecha": "2026-04-01", 
        "monto": 150000, 
        "estado": "Aprobado"
    },
    {
        "id": 2, 
        "fecha": "2026-04-02", 
        "monto": 150000, 
        "estado": "Pendiente"
    }
]
reservas_mock = [
    {
        "id": 1, 
        "fecha": "2026-04-15", 
        "Hora de inicio": "14:00", 
        "Hora de fin": "18:00", 
        "Estado": "Confirmada"
    },
    {
        "id": 2, 
        "fecha": "2026-04-20", 
        "Hora de inicio": "08:00", 
        "Hora de fin": "12:00", 
        "Estado": "Pendiente"
    }
]

anuncios_mock = [
    {
        "id": 1, 
        "titulo": "Mantenimiento de zonas verdes", 
        "contenido": "El día de mañana se realizará poda en los jardines principales.", 
        "fecha": "2026-04-03"
    },
    {
        "id": 2, 
        "titulo": "Asamblea General", 
        "contenido": "Se convoca a todos los residentes a la reunión anual el próximo sábado.", 
        "fecha": "2026-04-10"
    }
]

@main.route('/')
def inicio():
    return "Ruta de Inicio - Conjunto Ciprés"

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo_ingresado = request.form.get('correo')
        contrasena_ingresada = request.form.get('contrasena')

        usuario_encontrado = next(
            (u for u in usuarios_mock if u['correo'] == correo_ingresado and u['contrasena'] == contrasena_ingresada), 
            None
        )

        if usuario_encontrado:
            # GUARDAMOS EN LA SESIÓN
            session['usuario_id'] = usuario_encontrado['id']
            session['nombre'] = usuario_encontrado['nombre']
            session['rol'] = usuario_encontrado['rol']
            
            if usuario_encontrado['rol'] == 'administrador':
                return redirect(url_for('main.dashboard_admin'))
            else:
                return redirect(url_for('main.dashboard_residente'))
        
        return "Correo o contraseña incorrectos."

    return "Página de Login"

@main.route('/logout')
def logout():
    session.clear() # Borra toda la información de la sesión
    return redirect(url_for('main.login'))

@main.route('/dashboard-residente')
def dashboard_residente():
    if 'rol' not in session or session['rol'] != 'residente':
        return redirect(url_for('main.login'))
    return f"Bienvenido al Panel del Residente, {session['nombre']}"

@main.route('/dashboard-admin')
def dashboard_admin():
    if 'rol' not in session or session['rol'] != 'administrador':
        # Si no es admin, lo mandamos al login por seguridad
        return redirect(url_for('main.login'))
    
    return f"Bienvenido al Panel del Administrador, {session['nombre']}"

@main.route('/viviendas', methods=['GET'])
def listado_viviendas():
    # El día que Jhonsito nos entregue la base de datos, 
    # borraremos el "viviendas_mock" y aquí pondremos la consulta SQL.
    # El return seguirá siendo exactamente igual.
    return jsonify({
        "mensaje": "Listado de viviendas obtenido con éxito",
        "total_casas_registradas": len(viviendas_mock),
        "viviendas": viviendas_mock
    })

@main.route('/pagos', methods=['GET', 'POST'])
def gestion_pagos():
    # Si la petición es POST, significa que el administrador o el sistema está registrando un pago
    if request.method == 'POST':
        fecha_pago = request.form.get('fecha')
        monto_pago = request.form.get('monto')
        estado_pago = request.form.get('estado')
        
        # 1. Validar que no falten datos
        if not fecha_pago or not monto_pago or not estado_pago:
            return jsonify({"error": "Faltan datos para registrar el pago (fecha, monto o estado)"}), 400
            
        # 2. Guardar el nuevo pago en nuestra lista simulada
        nuevo_pago = {
            "id": len(pagos_mock) + 1,
            "fecha": fecha_pago,
            "monto": float(monto_pago), # Aseguramos que el monto sea un número
            "estado": estado_pago
        }
        pagos_mock.append(nuevo_pago)
        
        # Devolvemos el código 201 (Created)
        return jsonify({
            "mensaje": "Pago registrado con éxito",
            "pago": nuevo_pago
        }), 201

    # Si la petición es GET, simplemente retornamos los pagos registrados
    return jsonify({
        "mensaje": "Historial de pagos obtenido con éxito",
        "total_pagos": len(pagos_mock),
        "pagos": pagos_mock
    })

@main.route('/parqueaderos')
def parqueaderos():
    return "Gestión de Parqueaderos"

@main.route('/reservas', methods=['GET', 'POST'])
def gestion_reservas():
    # Si se envía un formulario para crear una nueva reserva
    if request.method == 'POST':
        fecha_solicitada = request.form.get('fecha')
        hora_inicio = request.form.get('Hora de inicio')
        hora_fin = request.form.get('Hora de fin')
        
        # 1. Validar que vengan los datos exactos
        if not fecha_solicitada or not hora_inicio or not hora_fin:
            return jsonify({"error": "Faltan datos para la reserva (fecha, Hora de inicio o Hora de fin)"}), 400
            
        # 2. Validar disponibilidad básica 
        for reserva in reservas_mock:
            if reserva['fecha'] == fecha_solicitada and reserva['Hora de inicio'] == hora_inicio:
                return jsonify({"error": f"El salón ya está reservado el {fecha_solicitada} a esa hora"}), 400
                
        # 3. Guardar la nueva reserva adaptada al diseño de Jhonsito
        nueva_reserva = {
            "id": len(reservas_mock) + 1,
            "fecha": fecha_solicitada,
            "Hora de inicio": hora_inicio,
            "Hora de fin": hora_fin,
            "Estado": "Confirmada"
        }
        reservas_mock.append(nueva_reserva)
        
        return jsonify({
            "mensaje": "Reserva registrada con éxito",
            "reserva": nueva_reserva
        }), 201

    # Si es GET, retornamos las reservas existentes
    return jsonify({
        "mensaje": "Reservas obtenidas con éxito",
        "total_reservas": len(reservas_mock),
        "reservas": reservas_mock
    })


@main.route('/anuncios', methods=['GET', 'POST'])
def gestion_anuncios():
    # Si la petición es POST, el administrador está creando un nuevo anuncio
    if request.method == 'POST':
        titulo_anuncio = request.form.get('titulo')
        contenido_anuncio = request.form.get('contenido')
        fecha_anuncio = request.form.get('fecha')
        
        # 1. Validar que vengan todos los datos del MER
        if not titulo_anuncio or not contenido_anuncio or not fecha_anuncio:
            return jsonify({"error": "Faltan datos para crear el anuncio (titulo, contenido o fecha)"}), 400
            
        # 2. Guardar el nuevo anuncio
        nuevo_anuncio = {
            "id": len(anuncios_mock) + 1,
            "titulo": titulo_anuncio,
            "contenido": contenido_anuncio,
            "fecha": fecha_anuncio
        }
        anuncios_mock.append(nuevo_anuncio)
        
        return jsonify({
            "mensaje": "Anuncio publicado con éxito",
            "anuncio": nuevo_anuncio
        }), 201

    # Si es GET, retornamos la lista de anuncios
    return jsonify({
        "mensaje": "Anuncios obtenidos con éxito",
        "total_anuncios": len(anuncios_mock),
        "anuncios": anuncios_mock
    })