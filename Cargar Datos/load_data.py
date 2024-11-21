import psycopg2
import pandas as pd


# Conexión a la base de datos
def get_db_connection():
    conn = psycopg2.connect(
        host="10.7.196.122",
        database="pbi",
        user="usuariopbi",
        password="@@usuariopbi@@"
    )
    return conn




# Función para cargar datos desde un CSV y crear usuarios
# Función para cargar datos desde un CSV y crear usuarios
def cargar_datos_csv_y_crear_usuarios(ruta_csv):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Leer el archivo CSV con la codificación UTF-16 y evitar conversión automática
        data = pd.read_csv(ruta_csv, encoding='utf-8', sep=';', dtype=str)

        # Reemplazar cualquier valor NaN por cadenas vacías
        data = data.fillna('')

        # Definir palabras clave que indican un rol de director o jefe
        roles_director = ['Jefe', 'Director', 'Directora']

        # Iterar sobre cada fila del CSV
        for index, row in data.iterrows():
            departamento = row['DEPARTAMENTO'].strip().replace("DEPARTAMENTO","Depto.").title()
            nombre = row['NOMBRE'].strip().title()
            apellido = ''  # Asume que los apellidos están separados de los nombres en la columna 'NOMBRE'
            cargo = row['CARGO'].strip().title()

            # Verificar si el cargo indica que es un director/jefe
            es_director = any(rol in cargo for rol in roles_director)

            # Verificar si el departamento ya existe
            cursor.execute("SELECT id FROM departamento WHERE name = %s", (departamento,))
            id_departamento = cursor.fetchone()
            if not id_departamento:
                cursor.execute("INSERT INTO departamento (name) VALUES (%s) RETURNING id", (departamento,))
                id_departamento = cursor.fetchone()[0]

            # Verificar si la persona ya existe (nombre y apellido separados)
            cursor.execute("SELECT id FROM persona WHERE name = %s AND lastname = %s", (nombre, apellido))
            id_persona = cursor.fetchone()
            if not id_persona:
                cursor.execute("""
                        INSERT INTO persona (name, lastname, position) VALUES (%s, %s, %s) RETURNING id
                    """, (nombre, apellido, cargo))
                id_persona = cursor.fetchone()[0]

            # Relacionar persona con departamento y si es director, actualizar 'es_director'
            cursor.execute("""
                    INSERT INTO persona_departamento (id_persona, id_departamento, es_director)
                    VALUES (%s, %s, %s) ON CONFLICT (id_persona, id_departamento) DO UPDATE 
                    SET es_director = EXCLUDED.es_director
                """, (id_persona, id_departamento, es_director))

            # Verificar si el usuario ya existe
            correo = row['CORREO ELECTRONICO '].strip()
            password = row['ANEXO MINSAL'].strip()

            cursor.execute("SELECT id_persona FROM users WHERE username = %s", (correo,))
            if not cursor.fetchone():
                # Insertar el usuario si no existe
                cursor.execute("""
                        INSERT INTO users (username, password, id_persona)
                        VALUES (%s, %s, %s)
                    """, (correo, password, id_persona))

        # Guardar los cambios
        conn.commit()
        print("Datos y usuarios cargados con éxito")

    except Exception as e:
        conn.rollback()
        print(f"Error al cargar los datos: {e}")

    finally:
        cursor.close()
        conn.close()

# Llamar a la función con la ruta del archivo CSV
cargar_datos_csv_y_crear_usuarios('FuncionariosVigentesOctubre2024-DSSM.csv')
