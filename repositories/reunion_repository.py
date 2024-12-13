# /repositories/reunion_repository.py
from database import get_db_connection
from psycopg2.extras import RealDictCursor

class ReunionRepository:
    def __init__(self):
        self.conn = get_db_connection()

    def fetch_user_info(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT p.id, p.name, p.lastname, p.position, d.id AS id_departamento, d.name AS departamento
                FROM persona p
                JOIN persona_departamento pd ON p.id = pd.id_persona
                JOIN departamento d ON pd.id_departamento = d.id
                WHERE p.id = %s
            """, (user_id,))
            user = cursor.fetchone()
            if not user:
                return None  # Devuelve None si no se encuentra un usuario
            return user  # Devuelve el resultado como un diccionario

    def fetch_origenes(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, name FROM origen")
            return cursor.fetchall()

    def fetch_areas(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, name FROM area")
            return cursor.fetchall()


    def fetch_departamentos(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, name FROM departamento")
            return cursor.fetchall()

    def fetch_personas(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT p.id, p.name, p.lastname, d.name AS departamento, p.position
                FROM persona p
                JOIN persona_departamento pd ON p.id = pd.id_persona
                JOIN departamento d ON pd.id_departamento = d.id
            """)
            return cursor.fetchall()

    def insert_origen(self, new_origen):
        with self.conn.cursor() as cursor:
            cursor.execute("INSERT INTO origen (name) VALUES (%s) RETURNING id", (new_origen,))
            return cursor.fetchone()[0]

    def insert_area(self, new_area):
        with self.conn.cursor() as cursor:
            cursor.execute("INSERT INTO area (name) VALUES (%s) RETURNING id", (new_area,))
            return cursor.fetchone()[0]

    def insert_reunion(self, nombre, area_id, origen_id, asistentes_str,correos_str,temas_analizado, acta_pdf_path):
        print(f"Inserting reunion with nombre={nombre}, area_id={area_id}, origen_id={origen_id}, asistentes={asistentes_str},correos={correos_str}, acta_pdf={acta_pdf_path}")

        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reunion (nombre, id_staff, id_area, id_origen, fecha_creacion, asistentes,correos,temas_analizado, acta_pdf)
                VALUES (%s, %s, %s, %s, NOW(), %s,%s,%s, %s) RETURNING id
            """, (str(nombre), None, str(area_id), str(origen_id), str(asistentes_str),str(correos_str),str(temas_analizado), acta_pdf_path))
            return cursor.fetchone()[0]

    def insert_compromiso(self, descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO compromiso (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion))
            return cursor.fetchone()[0]

    def associate_reunion_compromiso(self, reunion_id, compromiso_id):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reunion_compromiso (id_reunion, id_compromiso)
                VALUES (%s, %s)
            """, (reunion_id, compromiso_id))

    def associate_persona_compromiso(self, persona_id, compromiso_id):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO persona_compromiso (id_persona, id_compromiso)
                VALUES (%s, %s)
            """, (persona_id, compromiso_id))

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()
