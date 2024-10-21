import os

import psycopg2

# Conexión a la base de datos
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="PyCG",
        user="postgres",
        password="fede0628"
    )
    return conn

# Conexión a la base de datos
conn = get_db_connection()
# Listado de tablas a exportar
# Listado de tablas a exportar
tablas = ['persona', 'departamento', 'persona_departamento', 'users', 'staff', 'staff_persona',
          'calendario', 'area', 'origen', 'reunion', 'compromiso', 'persona_compromiso',
          'reunion_compromiso', 'compromiso_modificaciones']

# Crear la carpeta 'data' si no existe
output_dir = 'data'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Exportar cada tabla a CSV dentro de la carpeta 'data'
try:
    for tabla in tablas:
        archivo_csv = os.path.join(output_dir, f"{tabla}.csv")
        with open(archivo_csv, 'w') as f:
            cursor = conn.cursor()
            cursor.copy_expert(f"COPY {tabla} TO STDOUT WITH CSV HEADER", f)
            print(f"Datos de {tabla} exportados a {archivo_csv}")
finally:
    conn.close()  # Cerrar la conexión al final