import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            database='el_cipres'
        )
        
        if conexion.is_connected():
            print("Conexión exitosa a la base de datos")
            return conexion

    except Error as e:
        print(f"Error al conectar con MySQL: {e}")
        return None