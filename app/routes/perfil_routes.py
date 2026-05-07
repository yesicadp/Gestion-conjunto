from flask import Blueprint, render_template, redirect, url_for, session

perfil = Blueprint('perfil', __name__)

@perfil.route('/perfil')
def perfil_usuario():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    return render_template(
        'perfil.html',
        nombre=session.get('nombre'),
        correo=session.get('correo'),
        rol=session.get('rol')
    )