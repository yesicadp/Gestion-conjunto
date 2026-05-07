from flask import Blueprint, request, jsonify, session
from database import obtener_conexion


reservas = Blueprint('reservas', __name__)

@reservas.route('/reservas', methods=['GET', 'POST'])
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