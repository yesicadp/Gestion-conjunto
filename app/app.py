from flask import Flask
from routes.main_routes import main
from database import obtener_conexion

app = Flask(__name__)
app.secret_key = 'clave_secreta_cipres_123'
app.json.ensure_ascii = False

# Registramos las rutas en la aplicación
app.register_blueprint(main)

if __name__ == '__main__':
    # Hacemos una prueba de conexión al arrancar el servidor
    print("Probando conexión a la base de datos...")
    conexion_prueba = obtener_conexion()

    # Si la conexión se logró, la cerramos inmediatamente para no dejarla abierta sin uso
    if conexion_prueba:
        conexion_prueba.close()


    app.run(debug=True)