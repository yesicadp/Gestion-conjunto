from flask import Blueprint, render_template, redirect, url_for, jsonify, session
from database import obtener_conexion

viviendas = Blueprint('viviendas', __name__)

@viviendas.route('/viviendas', methods=['GET'])
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

@viviendas.route('/admin/vivienda/<int:id_vivienda>')
def detalle_vivienda(id_vivienda):
    if 'rol' not in session or session['rol'] != 'administrador':
        return redirect(url_for('auth.login'))

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
