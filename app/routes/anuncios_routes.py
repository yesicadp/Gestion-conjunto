from flask import Blueprint, request, redirect, jsonify, session
from datetime import datetime
from database import obtener_conexion


anuncios = Blueprint('anuncios', __name__)

@anuncios.route('/anuncios', methods=['GET', 'POST'])
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