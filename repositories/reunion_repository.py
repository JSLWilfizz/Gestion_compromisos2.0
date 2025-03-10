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
                    SELECT p.id, p.name, p.lastname, p.cargo,
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
            # Imprimir información de depuración mejorada para comprender los tipos y valores reales
            print(f"DEBUG - insert_reunion recibió:")
            print(f"  nombre={nombre}, type={type(nombre)}")
            print(f"  area_id={area_id}, type={type(area_id)}")
            print(f"  origen_id={origen_id}, type={type(origen_id)}")
            print(f"  asistentes_str={asistentes_str[:30]}..., type={type(asistentes_str)}")
            print(f"  correos_str={correos_str[:30]}..., type={type(correos_str)}")
            
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
                reunion_id = cursor.fetchone()[0]
                self.conn.commit()
                print(f"DEBUG - Reunión creada exitosamente con ID: {reunion_id}")
                return reunion_id
        except Exception as e:
            self.conn.rollback()
            print(f"ERROR - insert_reunion falló: {e}")
            raise e

    def insert_compromiso(self, descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion, id_origen=None, id_area=None):
        try:
            with self.conn.cursor() as cursor:
                # Mejorar la conversión de tipos para asegurar que los IDs sean enteros
                try:
                    id_departamento = int(id_departamento) if id_departamento else None
                    id_origen = int(id_origen) if id_origen else None
                    id_area = int(id_area) if id_area else None
                except (ValueError, TypeError):
                    print(f"ERROR - Conversión de ID fallida: id_departamento={id_departamento}, id_origen={id_origen}, id_area={id_area}")
                
                print(f"DEBUG - insert_compromiso después de conversión:")
                print(f"  id_origen={id_origen}, type={type(id_origen)}")
                print(f"  id_area={id_area}, type={type(id_area)}")
                print(f"  id_departamento={id_departamento}, type={type(id_departamento)}")
                
                # Corregir la consulta SQL para asegurar que los parámetros estén en el orden correcto
                if id_origen is None and id_area is None:
                    cursor.execute("""
                        INSERT INTO compromiso (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion))
                else:
                    # Imprimir los valores antes de la inserción para depuración
                    print(f"DEBUG - Insertando con id_origen={id_origen}, id_area={id_area}")
                    
                    # Usar la consulta explícita con todos los campos
                    cursor.execute("""
                        INSERT INTO compromiso (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion, id_origen, id_area)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion, id_origen, id_area))
                
                row = cursor.fetchone()
                compromiso_id = row[0]
                self.conn.commit()
                
                # Verificar el valor guardado en la base de datos
                cursor.execute("SELECT id_origen, id_area FROM compromiso WHERE id = %s", (compromiso_id,))
                saved_values = cursor.fetchone()
                print(f"DEBUG - Valores guardados en DB: id_origen={saved_values[0]}, id_area={saved_values[1]}")
                
                return compromiso_id
        except Exception as e:
            self.conn.rollback()
            print(f"ERROR - insert_compromiso falló: {e}")
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
                        d.id AS departamento_id,
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
                    GROUP BY c.id, d.id, d.name
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

    def fetch_reunion_by_compromiso_id(self, compromiso_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT r.*
                    FROM reunion r
                    JOIN reunion_compromiso rc ON r.id = rc.id_reunion
                    WHERE rc.id_compromiso = %s
                """, (compromiso_id,))
                return cursor.fetchone()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_origen_name(self, origen_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT name FROM origen WHERE id = %s", (origen_id,))
                result = cursor.fetchone()
                return result['name'] if result else None
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_area_name(self, area_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT name FROM area WHERE id = %s", (area_id,))
                result = cursor.fetchone()
                return result['name'] if result else None
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_reunion_by_id(self, reunion_id):
        query = "SELECT * FROM reunion WHERE id = %s"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (reunion_id,))
            result = cursor.fetchone()  # result is a dict if found
        return result

    def filtrar_reuniones(self, user_id, search, fecha, origen, tema, lugar, referente):
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

                query = """
                    SELECT r.*, o.name AS origen_name
                    FROM reunion r
                    LEFT JOIN origen o ON r.id_origen = o.id
                    WHERE r.asistentes ILIKE %s
                """
                params = [f"%{full_name}%"]

                if search:
                    query += """
                        AND (r.nombre ILIKE %s OR r.tema ILIKE %s OR r.lugar ILIKE %s OR r.asistentes ILIKE %s)
                    """
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
                if fecha:
                    query += " AND DATE(r.fecha_creacion) = %s"
                    params.append(fecha)
                if origen:
                    query += " AND o.id = %s"
                    params.append(origen)
                if tema:
                    query += " AND r.tema ILIKE %s"
                    params.append(f"%{tema}%")
                if lugar:
                    query += " AND r.lugar ILIKE %s"
                    params.append(f"%{lugar}%")
                if referente:
                    query += " AND r.asistentes ILIKE %s"
                    params.append(f"%{referente}%")

                query += " ORDER BY r.fecha_creacion DESC"

                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_areas_by_departamento(self, departamento_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Obtener el departamento padre (primer dígito seguido de dos ceros)
                # Ejemplo: si departamento_id es 320, el padre sería 300
                parent_dept_id = (departamento_id // 100) * 100
                
                # Incluir áreas del departamento actual, del departamento padre y globales
                cursor.execute("""
                    SELECT id, name 
                    FROM area 
                    WHERE id_departamento = %s 
                       OR id_departamento = %s 
                       OR id_departamento IS NULL
                    ORDER BY name
                """, (departamento_id, parent_dept_id))
                
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"Error en fetch_areas_by_departamento: {e}")
            raise e

    def fetch_origenes_by_departamento(self, departamento_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Obtener el departamento padre (primer dígito seguido de dos ceros)
                # Ejemplo: si departamento_id es 320, el padre sería 300
                parent_dept_id = (departamento_id // 100) * 100
                
                # Incluir orígenes del departamento actual, del departamento padre y globales
                cursor.execute("""
                    SELECT id, name 
                    FROM origen 
                    WHERE id_departamento = %s 
                       OR id_departamento = %s 
                       OR id_departamento IS NULL
                    ORDER BY name
                """, (departamento_id, parent_dept_id))
                
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"Error en fetch_origenes_by_departamento: {e}")
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
