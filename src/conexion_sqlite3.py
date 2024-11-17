import sqlite3

try:
    mi_conexion=sqlite3.connect("src/database/usuarios")
    cursor=mi_conexion.cursor()
    cursor.execute("CREATE TABLE usuario (id_discord INT(30),  rut VARCHAR(20))")

except Exception as ex:
    print(ex)