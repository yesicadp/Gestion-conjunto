from flask import Blueprint, render_template, request, redirect, url_for, session
from database import obtener_conexion
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import smtplib
from email.mime.text import MIMEText
import string
import secrets

recuperacion = Blueprint('recuperacion', __name__)

@recuperacion.route('/en-proceso')
def en_proceso():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
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
    
@recuperacion.route('/recuperar-contrasena')
def recuperar_contrasena():
    return render_template('recuperar_contrasena.html')

# RUTA 1: EL USUARIO PIDE RECUPERAR SU CONTRASEÑA
@recuperacion.route('/solicitar-recuperacion', methods=['POST'])
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
@recuperacion.route('/cambiar-contrasena', methods=['POST'])
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