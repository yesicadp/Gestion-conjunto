import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    """
    Esta función intenta establecer la conexión con la base de datos MySQL.
    Retorna el objeto de conexión si es exitoso, o None si falla.
    """
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234', 
            database='el_cipres'  # Conectamos a la DB de Jhonsito
        )
        
        if conexion.is_connected():
            print("Conexión exitosa a la base de datos")
            return conexion

    except Error as e:
        print(f"Error al conectar con MySQL: {e}")
        return None