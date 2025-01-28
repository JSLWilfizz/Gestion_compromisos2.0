from database import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor

class PersonaCompRepository:
    def __init__(self):
        self.conn = get_db_connection()
    
    def get_compromisos_eliminados(self):
        return self.fetch_compromisos_eliminados()

    def get_compromisos_archivados(self):
        return self.fetch_compromisos_archivados()

    def eliminar_compromiso(self, compromiso_id, user_id):
        try:
            with self.conn.cursor() as cursor:
                # Pasar a la tabla de compromiso_eliminado y sus relaciones antes de borrar
                cursor.execute("""
                    INSERT INTO compromiso_eliminado (id, descripcion, estado, prioridad, fecha_creacion, avance,
                                                      fecha_limite, comentario, comentario_direccion, id_departamento, eliminado_por)
                    SELECT id, descripcion, estado, prioridad, fecha_creacion, avance,
                           fecha_limite, comentario, comentario_direccion, id_departamento, %s
                    FROM compromiso
                    WHERE id = %s
                """, (user_id, compromiso_id))
                cursor.execute("""
                    INSERT INTO reunion_compromiso_eliminado (id_reunion, id_compromiso)
                    SELECT id_reunion, id_compromiso
                    FROM reunion_compromiso
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                cursor.execute("""
                    INSERT INTO persona_compromiso_eliminado (id_persona, id_compromiso)
                    SELECT id_persona, id_compromiso
                    FROM persona_compromiso
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                # Eliminar registros originales
                cursor.execute("DELETE FROM reunion_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM persona_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM compromiso WHERE id = %s", (compromiso_id,))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in eliminar_compromiso: {e}")
            raise e
        
    def archivar_compromiso(self, compromiso_id, user_id):
        try:
            with self.conn.cursor() as cursor:
                # Insertar en compromisos_archivados antes de borrar
                cursor.execute("""
                    INSERT INTO compromisos_archivados (
                        id, descripcion, estado, prioridad, fecha_creacion, avance,
                        fecha_limite, comentario, comentario_direccion, id_departamento, archivado_por
                    )
                    SELECT id, descripcion, estado, prioridad, fecha_creacion, avance,
                           fecha_limite, comentario, comentario_direccion, id_departamento, %s
                    FROM compromiso
                    WHERE id = %s
                """, (user_id, compromiso_id))
                
                # Insertar en archivados después de insertar en compromisos_archivados
                cursor.execute("""
                    INSERT INTO reunion_compromiso_archivado (id_reunion, id_compromiso)
                    SELECT id_reunion, id_compromiso
                    FROM reunion_compromiso
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                cursor.execute("""
                    INSERT INTO persona_compromiso_archivado (id_persona, id_compromiso)
                    SELECT id_persona, id_compromiso
                    FROM persona_compromiso
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Eliminar registros originales
                cursor.execute("DELETE FROM reunion_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM persona_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM compromiso WHERE id = %s", (compromiso_id,))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in archivar_compromiso: {e}")
            raise e

    def desarchivar_compromiso(self, compromiso_id):
        try:
            with self.conn.cursor() as cursor:
                # Mover el compromiso de la tabla compromisos_archivados a la tabla compromiso
                cursor.execute("""
                    INSERT INTO compromiso (id, descripcion, estado, prioridad, fecha_creacion, avance, fecha_limite, comentario, comentario_direccion, id_departamento)
                    SELECT id, descripcion, estado, prioridad, fecha_creacion, avance, fecha_limite, comentario, comentario_direccion, id_departamento
                    FROM compromisos_archivados
                    WHERE id = %s
                """, (compromiso_id,))
                
                # Restaurar registros relacionados en persona_compromiso desde persona_compromiso_archivado
                cursor.execute("""
                    INSERT INTO persona_compromiso (id_persona, id_compromiso)
                    SELECT id_persona, id_compromiso
                    FROM persona_compromiso_archivado
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Restaurar registros relacionados en reunion_compromiso desde reunion_compromiso_archivado
                cursor.execute("""
                    INSERT INTO reunion_compromiso (id_reunion, id_compromiso)
                    SELECT id_reunion, id_compromiso
                    FROM reunion_compromiso_archivado
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Eliminar registros relacionados en persona_compromiso_archivado y reunion_compromiso_archivado
                cursor.execute("DELETE FROM persona_compromiso_archivado WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM reunion_compromiso_archivado WHERE id_compromiso = %s", (compromiso_id,))
                
                # Eliminar el compromiso
                cursor.execute("DELETE FROM compromisos_archivados WHERE id = %s", (compromiso_id,))
                
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in desarchivar_compromiso: {e}")
            raise e

    def eliminar_permanentemente_compromiso(self, compromiso_id):
        try:
            with self.conn.cursor() as cursor:
                # Eliminar registros relacionados en persona_compromiso_eliminado y reunion_compromiso_eliminado
                cursor.execute("DELETE FROM persona_compromiso_eliminado WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM reunion_compromiso_eliminado WHERE id_compromiso = %s", (compromiso_id,))
                # Eliminar el compromiso
                cursor.execute("DELETE FROM compromiso_eliminado WHERE id = %s", (compromiso_id,))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in eliminar_permanentemente_compromiso: {e}")
            raise e

    def forzar_eliminacion_compromisos(self, compromiso_ids):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM compromisos_archivados WHERE id = ANY(%s)", (compromiso_ids,))
                cursor.execute("DELETE FROM compromiso_eliminado WHERE id = ANY(%s)", (compromiso_ids,))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in forzar_eliminacion_compromisos: {e}")
            raise e

    def fetch_compromisos_archivados(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT ca.*, d.name AS departamento_name, p.name AS archivado_por_nombre,
                           STRING_AGG(r.nombre, ', ') AS reuniones_asociadas
                    FROM compromisos_archivados ca
                    LEFT JOIN reunion_compromiso_archivado rca ON ca.id = rca.id_compromiso
                    LEFT JOIN reunion r ON rca.id_reunion = r.id
                    LEFT JOIN departamento d ON ca.id_departamento = d.id
                    LEFT JOIN persona p ON ca.archivado_por = p.id
                    GROUP BY ca.id, d.name, p.name
                """)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in fetch_compromisos_archivados: {e}")
            raise e

    def fetch_compromisos_eliminados(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT ce.*, d.name AS departamento_name, p.name AS eliminado_por_nombre,
                           STRING_AGG(r.nombre, ', ') AS reuniones_asociadas
                    FROM compromiso_eliminado ce
                    LEFT JOIN reunion_compromiso_eliminado rce ON ce.id = rce.id_compromiso
                    LEFT JOIN reunion r ON rce.id_reunion = r.id
                    LEFT JOIN departamento d ON ce.id_departamento = d.id
                    LEFT JOIN persona p ON ce.eliminado_por = p.id
                    GROUP BY ce.id, d.name, p.name
                """)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in fetch_compromisos_eliminados: {e}")
            raise e

    def recuperar_compromiso(self, compromiso_id):
        try:
            with self.conn.cursor() as cursor:
                # Mover de compromiso_eliminado a compromiso
                cursor.execute("""
                    INSERT INTO compromiso (id, descripcion, estado, prioridad, fecha_creacion, avance, fecha_limite, comentario, comentario_direccion, id_departamento)
                    SELECT id, descripcion, estado, prioridad, fecha_creacion, avance, fecha_limite, comentario, comentario_direccion, id_departamento
                    FROM compromiso_eliminado
                    WHERE id = %s
                """, (compromiso_id,))
                
                # Restaurar registros relacionados en persona_compromiso desde persona_compromiso_eliminado
                cursor.execute("""
                    INSERT INTO persona_compromiso (id_persona, id_compromiso)
                    SELECT id_persona, id_compromiso
                    FROM persona_compromiso_eliminado
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Restaurar registros relacionados en reunion_compromiso desde reunion_compromiso_eliminado
                cursor.execute("""
                    INSERT INTO reunion_compromiso (id_reunion, id_compromiso)
                    SELECT id_reunion, id_compromiso
                    FROM reunion_compromiso_eliminado
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Eliminar registros relacionados en persona_compromiso_eliminado y reunion_compromiso_eliminado
                cursor.execute("DELETE FROM persona_compromiso_eliminado WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM reunion_compromiso_eliminado WHERE id_compromiso = %s", (compromiso_id,))
                
                # Eliminar el compromiso
                cursor.execute("DELETE FROM compromiso_eliminado WHERE id = %s", (compromiso_id,))
                
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in recuperar_compromiso: {e}")
            raise e

    def create_compromiso(self, descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, user_id):
        query = """
        INSERT INTO compromiso (descripcion, estado, prioridad, fecha_creacion, avance, fecha_limite, comentario, comentario_direccion, id_departamento)
        VALUES (%s, %s, %s, %s, 0, %s, %s, %s, %s)
        RETURNING id
        """
        params = (descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento)
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                compromiso_id = cursor.fetchone()['id']
                print(f"Compromiso creado con ID: {compromiso_id}")
                self.conn.commit()
                return compromiso_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error al insertar compromiso en la base de datos: {e}")
            raise e

    def asociar_referentes(self, compromiso_id, referentes):
        try:
            with self.conn.cursor() as cursor:
                for referente_id in referentes:
                    cursor.execute("""
                        INSERT INTO persona_compromiso (id_persona, id_compromiso)
                        VALUES (%s, %s)
                    """, (referente_id, compromiso_id))
                self.conn.commit()
                print("Referentes asociados exitosamente")
        except Exception as e:
            self.conn.rollback()
            print(f"Error al asociar referentes en la base de datos: {e}")
            raise e

    def fetch_departamentos(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id, name FROM departamento")
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in fetch_departamentos: {e}")
            raise e

    def fetch_referentes(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT p.id, p.name, p.lastname, d.name AS departamento, p.profesion, p.cargo
                    FROM persona p
                    JOIN persona_departamento pd ON p.id = pd.id_persona
                    JOIN departamento d ON pd.id_departamento = d.id
                """)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in fetch_referentes: {e}")
            raise e

    def set_current_user_id(self, user_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SET myapp.current_user_id = %s", (user_id,))
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in set_current_user_id: {e}")
            raise e

    def get_user_info(self, user_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM persona WHERE id = %s", (user_id,))
                return cursor.fetchone()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in get_user_info: {e}")
            raise e

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()