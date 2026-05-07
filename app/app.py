from flask import Flask
from routes.main_routes import main
from database import obtener_conexion

app = Flask(__name__)
app.secret_key = 'clave_secreta_cipres_123'
app.json.ensure_ascii = False

app.register_blueprint(main)

if __name__ == '__main__':
    print("Probando conexión a la base de datos...")
    conexion_prueba = obtener_conexion()

    if conexion_prueba:
        conexion_prueba.close()

    app.run(debug=True)