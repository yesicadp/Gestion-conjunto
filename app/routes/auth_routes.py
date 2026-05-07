from flask import Blueprint, render_template, request, redirect, url_for, session
from database import obtener_conexion

from werkzeug.security import check_password_hash


auth = Blueprint('auth', __name__)

# LOGIN 
@auth.route('/login', methods=['GET', 'POST'])
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
                    return redirect(url_for('dashboard.dashboard_admin'))
                else:
                    return redirect(url_for('dashboard.dashboard_residente'))

        return render_template('login.html', error="Correo o contraseña incorrectos.")

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
 

