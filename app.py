from flask import Flask

# Inicializamos la aplicación de Flask
app = Flask(__name__)

# Definimos la ruta principal (la raíz de la página)
@app.route('/')
def inicio():
    # Por ahora solo retornamos un texto para comprobar que el servidor responde
    return "¡Backend del Conjunto Ciprés funcionando correctamente!"

# Este bloque asegura que el servidor solo arranque si ejecutamos este archivo directamente
if __name__ == '__main__':
    # debug=True permite que el servidor se reinicie automáticamente si guardamos cambios en el código
    app.run(debug=True)