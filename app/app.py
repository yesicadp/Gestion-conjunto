from flask import Flask

from routes.main_routes import main
from routes.auth_routes import auth
from routes.dashboard_routes import dashboard
from routes.pagos_routes import pagos
from routes.reservas_routes import reservas
from routes.viviendas_routes import viviendas
from routes.anuncios_routes import anuncios
from routes.perfil_routes import perfil
from routes.recuperacion_routes import recuperacion
from database import obtener_conexion

app = Flask(__name__)

app.secret_key = 'clave_secreta_cipres_123'
app.json.ensure_ascii = False

# Registramos las rutas en la aplicación
# app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(pagos)
app.register_blueprint(reservas)
app.register_blueprint(viviendas)
app.register_blueprint(anuncios)
app.register_blueprint(perfil)
app.register_blueprint(recuperacion)


if __name__ == '__main__':
    # Hacemos una prueba de conexión al arrancar el servidor
    print("Probando conexión a la base de datos...")
    conexion_prueba = obtener_conexion()

    # Si la conexión se logró, la cerramos inmediatamente para no dejarla abierta sin uso
    if conexion_prueba:
        conexion_prueba.close()


    app.run(debug=True)