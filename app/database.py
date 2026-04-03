import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    """
    Esta función intenta establecer la conexión con la base de datos MySQL.
    Retorna el objeto de conexión si es exitoso, o None si falla.
    """
    try:
        # Estos datos (host, user, password, database) los cambiaremos 
        # por los reales cuando Jhonsito nos entregue la base de datos local o en la nube.
        conexion = mysql.connector.connect(
            host='localhost',        # Normalmente es localhost si trabajamos en nuestro PC
            user='root',             # Usuario por defecto en XAMPP/MySQL
            password='1234',         # Contraseña de tu MySQL local
            database='cipres_db'     # El nombre de la base de datos que creará Jhonsito
        )
        
        if conexion.is_connected():
            print("¡Conexión exitosa a la base de datos MySQL!")
            return conexion

    except Error as e:
        print(f"Error al conectar con MySQL: {e}")
        return None