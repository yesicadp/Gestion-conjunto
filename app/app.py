from flask import Flask
from routes.main_routes import main # Importamos nuestras rutas

app = Flask(__name__)
app.secret_key = 'clave_secreta_cipres_123'

# Registramos las rutas en la aplicación
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)