import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()
""" 
    Función para obtener una conexión a la base de datos
    Retorna una conexión a la base de datos
"""

def get_db_connection():
    conn = psycopg2.connect(
        host= '10.7.196.122',
        database= 'gestion',
        user= 'usuariopbi',
        password= '@@usuariopbi@@'
    )
    return conn
"""
def get_db_connection():
    conn = psycopg2.connect(
        host= 'localhost',
        database= 'SGC',
        user= 'postgres', 
        password= "fede0628"
    )
    return conn
"""
"""
    Función para obtener un usuario por su nombre de usuario
"""
def get_user_by_username(conn, username):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
"""
    Función para obtener un usuario por su ID
"""
def get_user_compromisos(conn, user_id):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT c.descripcion, c.estado, c.fecha_limite 
            FROM compromiso c 
            JOIN persona p ON c.id_persona = p.id 
            WHERE p.id = %s
        """, (user_id,))
        return cursor.fetchall()

"""
    Función para obtener los compromisos de un departamento
"""
def get_departamento_compromisos(conn, user_id):
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT c.descripcion, c.estado, c.fecha_limite 
            FROM compromiso c 
            JOIN persona p ON c.id_persona = p.id 
            WHERE p.id_departamento = (
                SELECT id_departamento FROM persona WHERE id = %s
            )
        """, (user_id,))
        return cursor.fetchall()


def create_reunion(conn, form):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO reunion (fecha, id_staff) 
            VALUES (%s, %s) RETURNING id
        """, (form.fecha.data, form.id_staff.data))
        reunion_id = cursor.fetchone()[0]

        for compromiso_id in form.compromisos.data:
            cursor.execute("""
                INSERT INTO reunion_compromiso (id_reunion, id_compromiso) 
                VALUES (%s, %s)
            """, (reunion_id, compromiso_id))

        for asistente_id in form.asistentes.data:
            cursor.execute("""
                INSERT INTO reunion_asistentes (id_reunion, id_persona) 
                VALUES (%s, %s)
            """, (reunion_id, asistente_id))

        conn.commit()

def get_departamento_compromisos(conn, user_id):
    try:
        es_dir, id_departamento = es_director(conn, user_id)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if es_dir:
                cursor.execute("""
                           SELECT 
                               c.id AS compromiso_id,
                               c.descripcion,
                               c.estado,
                               c.prioridad,
                               c.fecha_limite,
                               c.fecha_creacion,
                               c.avance,
                               d.name AS departamento,
                               r.nombre AS reunion,
                               r.acta_pdf,  
                               STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables
                           FROM compromiso c
                           LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                           LEFT JOIN persona p ON pc.id_persona = p.id
                           LEFT JOIN departamento d ON c.id_departamento = d.id_departamento
                           LEFT JOIN reunion_compromiso rc ON c.id = rc.id_compromiso
                           LEFT JOIN reunion r ON rc.id_reunion = r.id
                           WHERE c.id_departamento = %s
                           GROUP BY c.id, d.name, r.nombre, r.acta_pdf
                       """, (id_departamento,))
            else:
                cursor.execute("""
                           SELECT 
                               c.id AS compromiso_id,
                               c.descripcion,
                               c.estado,
                               c.prioridad,
                               c.fecha_limite,
                               c.fecha_creacion,
                               c.avance,
                               d.name AS departamento,
                               r.nombre AS reunion,
                               r.acta_pdf,  
                               STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables
                           FROM compromiso c
                           LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                           LEFT JOIN persona p ON pc.id_persona = p.id
                           LEFT JOIN departamento d ON c.id_departamento = d.id_departamento
                           LEFT JOIN reunion_compromiso rc ON c.id = rc.id_compromiso
                           LEFT JOIN reunion r ON rc.id_reunion = r.id
                           WHERE p.id = %s
                           GROUP BY c.id, d.name, r.nombre, r.acta_pdf
                       """, (user_id,))

            compromisos = cursor.fetchall()

        # Separar los compromisos por estado
        compromisos_por_estado = {
            'Pendiente': [],
            'Completado': [],
            'Otro': []  # Aquí puedes agregar otros estados si es necesario
        }

        for compromiso in compromisos:
            if compromiso['estado'] == 'Pendiente':
                compromisos_por_estado['Pendiente'].append(compromiso)
            elif compromiso['estado'] == 'Completado':
                compromisos_por_estado['Completado'].append(compromiso)
            else:
                compromisos_por_estado['Otro'].append(compromiso)

        return compromisos_por_estado

    except Exception as e:
        print(f"Error al obtener los compromisos: {e}")
        return {}


def es_director(conn, user_id):
    """ Verifica si el usuario es director de su departamento """
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT es_director, id_departamento
            FROM persona_departamento
            WHERE id_persona = %s
        """, (user_id,))
        result = cursor.fetchone()

    if result and result[0]:  # Si 'es_director' es True
        return True, result[1]  # Devuelve True y el id_departamento
    return False, None  # No es director

def get_reuniones_y_compromisos(conn, user_id):
    try:
        es_dir, id_departamento = es_director(conn, user_id)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if es_dir:
                # Si el usuario es director, mostramos todas las reuniones del departamento
                cursor.execute("""
                    SELECT 
                        r.id AS reunion_id,
                        r.nombre AS reunion_nombre,
                        r.fecha AS reunion_fecha,
                        STRING_AGG(DISTINCT CONCAT(p.name, ' ', p.lastname), ', ') AS asistentes,
                        c.id AS compromiso_id,
                        c.descripcion AS compromiso_descripcion,
                        c.estado AS compromiso_estado,
                        c.prioridad AS compromiso_prioridad,
                        c.fecha_limite AS compromiso_fecha_limite,
                        c.nivel_avance AS compromiso_nivel_avance
                    FROM reunion r
                    LEFT JOIN reunion_compromiso rc ON r.id = rc.id_reunion
                    LEFT JOIN compromiso c ON rc.id_compromiso = c.id
                    LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                    LEFT JOIN persona p ON pc.id_persona = p.id
                    WHERE r.id_staff IN (
                        SELECT id_staff FROM staff_persona WHERE id_persona = %s
                    )
                    GROUP BY r.id, c.id
                    ORDER BY r.fecha DESC
                """, (user_id,))
            else:
                # Si no es director, mostramos solo las reuniones donde participa el usuario
                cursor.execute("""
                    SELECT 
                        r.id AS reunion_id,
                        r.nombre AS reunion_nombre,
                        r.fecha AS reunion_fecha,
                        STRING_AGG(DISTINCT CONCAT(p.name, ' ', p.lastname), ', ') AS asistentes,
                        c.id AS compromiso_id,
                        c.descripcion AS compromiso_descripcion,
                        c.estado AS compromiso_estado,
                        c.prioridad AS compromiso_prioridad,
                        c.fecha_limite AS compromiso_fecha_limite,
                        c.nivel_avance AS compromiso_nivel_avance
                    FROM reunion r
                    LEFT JOIN reunion_compromiso rc ON r.id = rc.id_reunion
                    LEFT JOIN compromiso c ON rc.id_compromiso = c.id
                    LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                    LEFT JOIN persona p ON pc.id_persona = p.id
                    WHERE p.id = %s
                    GROUP BY r.id, c.id
                    ORDER BY r.fecha DESC
                """, (user_id,))

            reuniones_y_compromisos = cursor.fetchall()  # Obtener todas las reuniones y sus compromisos
        return reuniones_y_compromisos

    except Exception as e:
        print(f"Error al obtener reuniones y compromisos: {e}")
        return []