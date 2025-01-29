# /repositories/reunion_repository.py
from database import get_db_connection
from psycopg2.extras import RealDictCursor
import logging

class ReunionRepository:
    def __init__(self):
        self.conn = get_db_connection()

    def fetch_user_info(self, user_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT p.id, p.name, p.lastname, p.cargo, p.profesion, p.correo,
                           d.id AS id_departamento, d.name AS departamento
                    FROM persona p
                    JOIN persona_departamento pd ON p.id = pd.id_persona
                    JOIN departamento d ON pd.id_departamento = d.id
                    WHERE p.id = %s
                """, (user_id,))
                user = cursor.fetchone()
                if not user:
                    return None  # Devuelve None si no se encuentra un usuario
                return user  # Devuelve el resultado como un diccionario
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_origenes(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id, name FROM origen")
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_areas(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id, name FROM area")
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_departamentos(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id, name FROM departamento")
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_personas(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT p.id, p.name, p.lastname, p.correo, p.profesion,
                           d.name AS departamento
                    FROM persona p
                    JOIN persona_departamento pd ON p.id = pd.id_persona
                    JOIN departamento d ON pd.id_departamento = d.id
                """)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def insert_origen(self, new_origen):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("INSERT INTO origen (name) VALUES (%s) RETURNING id", (new_origen,))
                return cursor.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            raise e

    def insert_area(self, new_area):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("INSERT INTO area (name) VALUES (%s) RETURNING id", (new_area,))
                return cursor.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            raise e

    def insert_reunion(self, nombre, area_id, origen_id, asistentes_str, correos_str, acta_pdf_path, lugar, tema, temas_analizado, proximas_reuniones, fecha_creacion):
        try:
            print(f"Inserting reunion with nombre={nombre}, area_id={area_id}, origen_id={origen_id}, asistentes={asistentes_str}, correos={correos_str}, acta_pdf={acta_pdf_path}, lugar={lugar}, tema={tema}, temas_analizado={temas_analizado}, proximas_reuniones={proximas_reuniones}, fecha_creacion={fecha_creacion}")
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO reunion (nombre, id_staff, id_area, id_origen, fecha_creacion, asistentes, correos, acta_pdf, lugar, tema, temas_analizado, proximas_reuniones)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    nombre,
                    None,
                    area_id,
                    origen_id,
                    fecha_creacion,
                    asistentes_str,
                    correos_str,
                    acta_pdf_path,
                    lugar,
                    tema,
                    temas_analizado,
                    proximas_reuniones
                ))
                return cursor.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            raise e

    def insert_compromiso(self, descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO compromiso (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion))
                return cursor.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            raise e

    def insert_invitado(self, nombre, institucion, correo, telefono):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO invitados (nombre_completo, institucion, correo, telefono)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id_invitado
                """, (nombre, institucion, correo, telefono))
                self.conn.commit()  # Commit the transaction
                return cursor.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error en insert_invitado: {str(e)}")
            raise e

    def associate_reunion_compromiso(self, reunion_id, compromiso_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO reunion_compromiso (id_reunion, id_compromiso)
                    VALUES (%s, %s)
                """, (reunion_id, compromiso_id))
        except Exception as e:
            self.conn.rollback()
            raise e

    def associate_persona_compromiso(self, persona_id, compromiso_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO persona_compromiso (id_persona, id_compromiso)
                    VALUES (%s, %s)
                """, (persona_id, compromiso_id))
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_reunion_asistentes(self, reunion_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT asistentes FROM reunion WHERE id = %s", (reunion_id,))
                row = cursor.fetchone()
                return row[0] if row and row[0] else None
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_mis_reuniones(self, user_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First, get the user's full name
                cursor.execute("""
                    SELECT COALESCE(name, '') || ' ' || COALESCE(lastname, '') AS full_name
                    FROM persona
                    WHERE id = %s
                    LIMIT 1
                """, (user_id,))
                row = cursor.fetchone()
                full_name = row['full_name'] if row else ''

                # Then query reuniones using that full name
                cursor.execute("""
                    SELECT r.*, o.name AS origen_name
                    FROM reunion r
                    LEFT JOIN origen o ON r.id_origen = o.id
                    WHERE r.asistentes ILIKE %s
                    ORDER BY r.fecha_creacion DESC
                """, (f"%{full_name}%",))

                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_compromisos_by_reunion(self, reunion_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        c.id, 
                        c.descripcion, 
                        c.estado, 
                        c.fecha_limite, 
                        c.prioridad, 
                        c.avance,
                        d.name AS departamento,
                        STRING_AGG(
                            p.name || ' ' || p.lastname || 
                            CASE WHEN pc.es_responsable_principal THEN ' (*)' ELSE '' END,
                            ', '
                            ORDER BY pc.es_responsable_principal DESC, p.name, p.lastname
                        ) AS referentes
                    FROM compromiso c
                    JOIN reunion_compromiso rc ON c.id = rc.id_compromiso
                    JOIN departamento d ON c.id_departamento = d.id
                    LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                    LEFT JOIN persona p ON pc.id_persona = p.id
                    WHERE rc.id_reunion = %s
                    GROUP BY c.id, d.name
                """, (reunion_id,))
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_invitados(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id_invitado, nombre_completo, institucion, correo, telefono FROM invitados")
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def commit(self):
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()
