from flask import Blueprint, render_template

# Creamos un 'Blueprint' que es como un módulo de rutas
main = Blueprint('main', __name__)

@main.route('/')
def inicio():
    return "Ruta de Inicio - Conjunto Ciprés"

@main.route('/login')
def login():
    return "Ruta de Login"

@main.route('/dashboard-residente')
def dashboard_residente():
    return "Panel del Residente"

@main.route('/dashboard-admin')
def dashboard_admin():
    return "Panel del Administrador"

@main.route('/pagos')
def pagos():
    return "Sección de Pagos"

@main.route('/parqueaderos')
def parqueaderos():
    return "Gestión de Parqueaderos"

@main.route('/reservas')
def reservas():
    return "Reservas del Salón Comunal"

@main.route('/anuncios')
def anuncios():
    return "Anuncios de la Administración"