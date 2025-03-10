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
                                                      fecha_limite, comentario, comentario_direccion, id_departamento, 
                                                      eliminado_por, id_origen, id_area)
                    SELECT id, descripcion, estado, prioridad, fecha_creacion, avance,
                           fecha_limite, comentario, comentario_direccion, id_departamento, %s, id_origen, id_area
                    FROM compromiso
                    WHERE id = %s
                """, (user_id, compromiso_id))
                
                # Resto de las consultas para transferir datos a tablas de elementos eliminados
                cursor.execute("""
                    INSERT INTO reunion_compromiso_eliminado (id_reunion, id_compromiso)
                    SELECT id_reunion, id_compromiso
                    FROM reunion_compromiso
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                cursor.execute("""
                    INSERT INTO persona_compromiso_eliminado (id_persona, id_compromiso, es_responsable_principal)
                    SELECT id_persona, id_compromiso, es_responsable_principal
                    FROM persona_compromiso
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # NUEVO: Transferir verificadores a la tabla de verificadores eliminados
                cursor.execute("""
                    INSERT INTO compromiso_eliminado_verificador
                    (id_compromiso, nombre_archivo, ruta_archivo, descripcion, fecha_subida, subido_por)
                    SELECT id_compromiso, nombre_archivo, ruta_archivo, descripcion, fecha_subida, subido_por
                    FROM compromiso_verificador
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Eliminar registros originales
                cursor.execute("DELETE FROM reunion_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM persona_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM compromiso_verificador WHERE id_compromiso = %s", (compromiso_id,))
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
                        fecha_limite, comentario, comentario_direccion, id_departamento, 
                        archivado_por, id_origen, id_area
                    )
                    SELECT id, descripcion, estado, prioridad, fecha_creacion, avance,
                           fecha_limite, comentario, comentario_direccion, id_departamento, 
                           %s, id_origen, id_area
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
                    INSERT INTO persona_compromiso_archivado (id_persona, id_compromiso, es_responsable_principal)
                    SELECT id_persona, id_compromiso, es_responsable_principal
                    FROM persona_compromiso
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # NUEVO: Transferir verificadores a la tabla de verificadores archivados
                cursor.execute("""
                    INSERT INTO compromiso_archivado_verificador
                    (id_compromiso, nombre_archivo, ruta_archivo, descripcion, fecha_subida, subido_por)
                    SELECT id_compromiso, nombre_archivo, ruta_archivo, descripcion, fecha_subida, subido_por
                    FROM compromiso_verificador
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Eliminar registros originales
                cursor.execute("DELETE FROM reunion_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM persona_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM compromiso_verificador WHERE id_compromiso = %s", (compromiso_id,))
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
                    INSERT INTO compromiso (id, descripcion, estado, prioridad, fecha_creacion, avance, 
                                           fecha_limite, comentario, comentario_direccion, id_departamento,
                                           id_origen, id_area)
                    SELECT id, descripcion, estado, prioridad, fecha_creacion, avance, 
                           fecha_limite, comentario, comentario_direccion, id_departamento,
                           id_origen, id_area
                    FROM compromisos_archivados
                    WHERE id = %s
                """, (compromiso_id,))
                
                # Restaurar registros relacionados en persona_compromiso desde persona_compromiso_archivado
                cursor.execute("""
                    INSERT INTO persona_compromiso (id_persona, id_compromiso, es_responsable_principal)
                    SELECT id_persona, id_compromiso, es_responsable_principal
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
                
                # NUEVO: Restaurar verificadores desde los archivados
                cursor.execute("""
                    INSERT INTO compromiso_verificador 
                    (id_compromiso, nombre_archivo, ruta_archivo, descripcion, fecha_subida, subido_por)
                    SELECT id_compromiso, nombre_archivo, ruta_archivo, descripcion, fecha_subida, subido_por
                    FROM compromiso_archivado_verificador
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Eliminar registros relacionados en persona_compromiso_archivado y reunion_compromiso_archivado
                cursor.execute("DELETE FROM persona_compromiso_archivado WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM reunion_compromiso_archivado WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM compromiso_archivado_verificador WHERE id_compromiso = %s", (compromiso_id,))
                
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
                cursor.execute("DELETE FROM compromiso_eliminado_verificador WHERE id_compromiso = %s", (compromiso_id,))
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
                    SELECT 
                        ca.*, 
                        d.name AS departamento_name, 
                        p.name AS archivado_por_nombre,
                        MAX(r.nombre) AS reuniones_asociadas,
                        STRING_AGG(
                            p2.name || ' ' || p2.lastname || 
                            CASE WHEN pca.es_responsable_principal THEN ' (*)' ELSE '' END,
                            ', '
                            ORDER BY pca.es_responsable_principal DESC, p2.name, p2.lastname
                        ) AS referentes
                    FROM compromisos_archivados ca
                    LEFT JOIN reunion_compromiso_archivado rca ON ca.id = rca.id_compromiso
                    LEFT JOIN reunion r ON rca.id_reunion = r.id
                    LEFT JOIN departamento d ON ca.id_departamento = d.id
                    LEFT JOIN persona p ON ca.archivado_por = p.id
                    LEFT JOIN persona_compromiso_archivado pca ON ca.id = pca.id_compromiso
                    LEFT JOIN persona p2 ON pca.id_persona = p2.id
                    GROUP BY ca.id, d.name, p.name
                """)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_compromisos_eliminados(self):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        ce.*, 
                        d.name AS departamento_name, 
                        p.name AS eliminado_por_nombre,
                        MAX(r.nombre) AS reuniones_asociadas,
                        STRING_AGG(
                            p2.name || ' ' || p2.lastname || 
                            CASE WHEN pce.es_responsable_principal THEN ' (*)' ELSE '' END,
                            ', '
                            ORDER BY pce.es_responsable_principal DESC, p2.name, p2.lastname
                        ) AS referentes
                    FROM compromiso_eliminado ce
                    LEFT JOIN reunion_compromiso_eliminado rce ON ce.id = rce.id_compromiso
                    LEFT JOIN reunion r ON rce.id_reunion = r.id
                    LEFT JOIN departamento d ON ce.id_departamento = d.id
                    LEFT JOIN persona p ON ce.eliminado_por = p.id
                    LEFT JOIN persona_compromiso_eliminado pce ON ce.id = pce.id_compromiso
                    LEFT JOIN persona p2 ON pce.id_persona = p2.id
                    GROUP BY ce.id, d.name, p.name
                """)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def recuperar_compromiso(self, compromiso_id):
        try:
            with self.conn.cursor() as cursor:
                # Mover de compromiso_eliminado a compromiso
                cursor.execute("""
                    INSERT INTO compromiso (id, descripcion, estado, prioridad, fecha_creacion, avance, 
                                           fecha_limite, comentario, comentario_direccion, id_departamento,
                                           id_origen, id_area)
                    SELECT id, descripcion, estado, prioridad, fecha_creacion, avance, 
                           fecha_limite, comentario, comentario_direccion, id_departamento, 
                           id_origen, id_area
                    FROM compromiso_eliminado
                    WHERE id = %s
                """, (compromiso_id,))
                
                # Restaurar registros relacionados en persona_compromiso desde persona_compromiso_eliminado
                cursor.execute("""
                    INSERT INTO persona_compromiso (id_persona, id_compromiso, es_responsable_principal)
                    SELECT id_persona, id_compromiso, es_responsable_principal
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
                
                # NUEVO: Restaurar verificadores desde los eliminados
                cursor.execute("""
                    INSERT INTO compromiso_verificador 
                    (id_compromiso, nombre_archivo, ruta_archivo, descripcion, fecha_subida, subido_por)
                    SELECT id_compromiso, nombre_archivo, ruta_archivo, descripcion, fecha_subida, subido_por
                    FROM compromiso_eliminado_verificador
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                
                # Eliminar registros relacionados en persona_compromiso_eliminado y reunion_compromiso_eliminado
                cursor.execute("DELETE FROM persona_compromiso_eliminado WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM reunion_compromiso_eliminado WHERE id_compromiso = %s", (compromiso_id,))
                cursor.execute("DELETE FROM compromiso_eliminado_verificador WHERE id_compromiso = %s", (compromiso_id,))
                
                # Eliminar el compromiso
                cursor.execute("DELETE FROM compromiso_eliminado WHERE id = %s", (compromiso_id,))
                
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error in recuperar_compromiso: {e}")
            raise e

    def create_compromiso(self, descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, user_id, origen=None, area=None):
        try:
            # Asegurarse de convertir strings vacías a None y strings numéricas a enteros
            origen = int(origen) if origen and str(origen).strip() else None
            area = int(area) if area and str(area).strip() else None
            
            print(f"DEBUG - Valores a insertar: id_origen={origen} (tipo: {type(origen)}), id_area={area} (tipo: {type(area)})")
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO compromiso 
                    (descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, id_origen, id_area, avance) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                    RETURNING id
                    """, 
                    (descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, origen, area, 0)
                )
                compromiso_id = cursor.fetchone()['id']
                self.conn.commit()
                print(f"Compromiso creado exitosamente con ID: {compromiso_id}, id_origen={origen}, id_area={area}, avance=0")
                return compromiso_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error en create_compromiso: {e}")
            raise e

    def asociar_referentes(self, compromiso_id, referentes):
        try:
            with self.conn.cursor() as cursor:
                for index, referente_id in enumerate(referentes):
                    es_responsable = True if index == 0 else False
                    cursor.execute("""
                        INSERT INTO persona_compromiso (id_persona, id_compromiso, es_responsable_principal)
                        VALUES (%s, %s, %s)
                    """, (referente_id, compromiso_id, es_responsable))
                self.conn.commit()
                print("Referentes asociados exitosamente")
        except Exception as e:
            self.conn.rollback()
            print(f"Error al asociar referentes en la base de datos: {e}")
            raise e

    def update_referentes(self, compromiso_id, nuevos_referentes):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id_persona, es_responsable_principal
                    FROM persona_compromiso
                    WHERE id_compromiso = %s
                """, (compromiso_id,))
                antiguos = cursor.fetchall()

                for ref in antiguos:
                    if ref[1] and str(ref[0]) not in map(str, nuevos_referentes):
                        raise ResponsablePrincipalError()

                # Convertir los valores de nuevos_referentes a integer
                nuevos_referentes_int = list(map(int, nuevos_referentes))

                # Eliminar referentes que no son principales y que no están en la nueva lista
                cursor.execute("""
                    DELETE FROM persona_compromiso 
                    WHERE id_compromiso = %s 
                    AND es_responsable_principal = FALSE 
                    AND id_persona != ALL(%s)
                """, (compromiso_id, nuevos_referentes_int))

                # Agregar nuevos referentes que no existan
                for nuevo_ref in nuevos_referentes_int:
                    cursor.execute("""
                        INSERT INTO persona_compromiso (id_persona, id_compromiso, es_responsable_principal)
                        SELECT %s, %s, FALSE
                        WHERE NOT EXISTS (
                            SELECT 1 FROM persona_compromiso 
                            WHERE id_persona = %s AND id_compromiso = %s
                        )
                    """, (nuevo_ref, compromiso_id, nuevo_ref, compromiso_id))

                self.conn.commit()
        except ResponsablePrincipalError:
            self.conn.rollback()
            raise
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

    def add_verificador(self, id_compromiso, nombre_archivo, ruta_archivo, descripcion, user_id):
        """
        Añade un verificador de compromiso a la base de datos
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO compromiso_verificador
                    (id_compromiso, nombre_archivo, ruta_archivo, descripcion, subido_por)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (id_compromiso, nombre_archivo, ruta_archivo, descripcion, user_id))
                
                resultado = cursor.fetchone()
                self.conn.commit()
                return resultado['id']
        except Exception as e:
            self.conn.rollback()
            print(f"Error al añadir verificador: {e}")
            raise e

    def get_verificadores(self, id_compromiso):
        """
        Obtiene todos los verificadores asociados a un compromiso
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT v.*, p.name || ' ' || p.lastname AS subido_por_nombre
                    FROM compromiso_verificador v
                    LEFT JOIN persona p ON v.subido_por = p.id
                    WHERE v.id_compromiso = %s
                    ORDER BY v.fecha_subida DESC
                """, (id_compromiso,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener verificadores: {e}")
            raise e

    def delete_verificador(self, verificador_id):
        """
        Elimina un verificador por su ID
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Primero obtener la ruta del archivo para devolverla
                cursor.execute("SELECT ruta_archivo FROM compromiso_verificador WHERE id = %s", (verificador_id,))
                resultado = cursor.fetchone()
                
                if not resultado:
                    raise ValueError("Verificador no encontrado")
                    
                # Ahora eliminar el registro
                cursor.execute("DELETE FROM compromiso_verificador WHERE id = %s", (verificador_id,))
                self.conn.commit()
                
                return resultado['ruta_archivo']
        except Exception as e:
            self.conn.rollback()
            print(f"Error al eliminar verificador: {e}")
            raise e