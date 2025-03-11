# /repositories/compromiso_repository.py
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from exceptions.compromiso_exceptions import ResponsablePrincipalError

class CompromisoRepository:
    def __init__(self):
        self.conn = get_db_connection()

    def fetch_user_info(self, user_id):
        if not user_id:
            raise ValueError("Invalid user_id")
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT p.id, p.name, p.lastname, p.profesion, p.cargo, pd.id_departamento, d.name AS departamento_name , p.nivel_jerarquico
                    FROM persona p
                    JOIN persona_departamento pd ON p.id = pd.id_persona
                    JOIN departamento d ON pd.id_departamento = d.id
                    WHERE p.id = %s
                """, (user_id,))
                return cursor.fetchone()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_director_info(self, user_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT pd.es_director, pd.id_departamento
                    FROM persona_departamento pd
                    JOIN persona p ON p.id = pd.id_persona
                    WHERE p.id = %s
                """, (user_id,))
                return cursor.fetchone()
        except Exception as e:
            self.conn.rollback()
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
            raise e

    def fetch_compromisos_by_departamento(self, departamento_id, search='', prioridad='', estado='', fecha_limite=''):
        try:
            query = """
                SELECT 
                    c.id AS compromiso_id,
                    c.prioridad,
                    c.descripcion,
                    c.estado,
                    c.avance,
                    c.fecha_limite,
                    c.comentario,
                    c.comentario_direccion,
                    d.name AS departamento_name,
                    o.name AS origen_name,
                    a.name AS area_name,
                    ARRAY_AGG(p.id) AS referentes_ids,
                    STRING_AGG(
                        p.name || ' ' || p.lastname || 
                        CASE WHEN pc.es_responsable_principal THEN ' (*)' ELSE '' END,
                        ', '
                        ORDER BY pc.es_responsable_principal DESC, p.name, p.lastname
                    ) AS referentes
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                LEFT JOIN departamento d ON c.id_departamento = d.id
                LEFT JOIN origen o ON c.id_origen = o.id
                LEFT JOIN area a ON c.id_area = a.id
                WHERE c.id_departamento = %s
            """
            params = [departamento_id]

            if search:
                query += """
                    AND c.id IN (
                        SELECT c2.id
                        FROM compromiso c2
                        LEFT JOIN persona_compromiso pc2 ON c2.id = pc2.id_compromiso
                        LEFT JOIN persona p2 ON pc2.id_persona = p2.id
                        WHERE c2.descripcion ILIKE %s OR d.name ILIKE %s OR CONCAT(p2.name, ' ', p2.lastname) ILIKE %s
                    )
                """
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            if prioridad:
                query += " AND c.prioridad = %s"
                params.append(prioridad)

            if estado:
                query += " AND c.estado = %s"
                params.append(estado)

            if fecha_limite:
                query += " AND c.fecha_limite = %s"
                params.append(fecha_limite)

            query += """
                GROUP BY 
                    c.id,
                    c.prioridad,
                    c.descripcion,
                    c.estado,
                    c.avance,
                    c.fecha_limite,
                    c.comentario,
                    c.comentario_direccion,
                    d.name,
                    o.name,
                    a.name
            """

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_compromisos_by_referente(self, user_id, search='', prioridad='', estado='', fecha_limite=''):
        try:
            query = """
                SELECT 
                    c.id AS compromiso_id,
                    c.prioridad,
                    c.descripcion,
                    c.estado,
                    c.avance,
                    c.fecha_limite,
                    c.comentario,
                    c.comentario_direccion,
                    d.name AS departamento_name,
                    o.name AS origen_name,
                    a.name AS area_name,
                    ARRAY_AGG(p.id) AS referentes_ids,
                    STRING_AGG(
                        CASE 
                            WHEN pc.es_responsable_principal THEN p.name || ' ' || p.lastname || ' (*)'
                            ELSE p.name || ' ' || p.lastname
                        END,
                        ', '
                    ) AS referentes
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                LEFT JOIN departamento d ON c.id_departamento = d.id
                LEFT JOIN origen o ON c.id_origen = o.id
                LEFT JOIN area a ON c.id_area = a.id
                WHERE c.id IN (
                    SELECT c2.id
                    FROM compromiso c2
                    LEFT JOIN persona_compromiso pc2 ON c2.id = pc2.id_compromiso
                    LEFT JOIN persona p2 ON pc2.id_persona = p2.id
                    WHERE pc2.id_persona = %s
                )
            """
            params = [user_id]

            if search:
                query += """
                    AND c.id IN (
                        SELECT c3.id
                        FROM compromiso c3
                        LEFT JOIN persona_compromiso pc3 ON c3.id = pc3.id_compromiso
                        LEFT JOIN persona p3 ON pc3.id_persona = p3.id
                        WHERE c3.descripcion ILIKE %s OR d.name ILIKE %s OR CONCAT(p3.name, ' ', p3.lastname) ILIKE %s
                    )
                """
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            if prioridad:
                query += " AND c.prioridad = %s"
                params.append(prioridad)

            if estado:
                query += " AND c.estado = %s"
                params.append(estado)

            if fecha_limite:
                query += " AND c.fecha_limite = %s"
                params.append(fecha_limite)

            query += """
                GROUP BY 
                    c.id,
                    c.prioridad,
                    c.descripcion,
                    c.estado,
                    c.avance,
                    c.fecha_limite,
                    c.comentario,
                    c.comentario_direccion,
                    d.name,
                    o.name,
                    a.name
                ORDER BY c.fecha_limite
            """

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_compromiso(self, compromiso_id, descripcion, estado, prioridad, avance, comentario, comentario_direccion, user_id, referentes):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE compromiso
                    SET descripcion = %s, estado = %s, prioridad = %s, avance = %s, comentario = %s, comentario_direccion = %s
                    WHERE id = %s
                """, (descripcion, estado, prioridad, avance, comentario, comentario_direccion, compromiso_id))
            self.update_referentes(compromiso_id, referentes)
            self.log_modificacion(compromiso_id, user_id)  # Añadir user_id
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
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

    def log_modificacion(self, compromiso_id, user_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO compromiso_modificaciones (id_compromiso, id_usuario)
                    VALUES (%s, %s)
                """, (compromiso_id, user_id))
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

    def fetch_compromisos_by_month(self, month, year):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT c.id AS compromiso_id, c.prioridad, c.descripcion, c.estado, c.avance, c.fecha_limite, 
                           c.comentario_director, d.name AS departamento,
                           STRING_AGG(
                               p.name || ' ' || p.lastname || 
                               CASE WHEN pc.es_responsable_principal THEN ' (*)' ELSE '' END,
                               ', '
                               ORDER BY pc.es_responsable_principal DESC, p.name, p.lastname
                           ) AS referentes
                    FROM compromiso c
                    JOIN departamento d ON c.id_departamento = d.id
                    LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                    LEFT JOIN persona p ON pc.id_persona = p.id
                    WHERE EXTRACT(MONTH FROM c.fecha_limite) = %s
                    AND EXTRACT(YEAR FROM c.fecha_limite) = %s
                    GROUP BY c.id, d.name
                """, (month, year))
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_resumen_compromisos(self, month):
        try:
            # Convertir el nombre del mes en su número (Ej: "Enero" -> 1)
            month_number = self.convert_month_to_number(month) if month else None

            # Obtener el resumen general
            total_compromisos = self.repo.count_total_compromisos(month_number)
            completados = self.repo.count_compromisos_completados(month_number)
            pendientes = self.repo.count_compromisos_pendientes(month_number)

            # Obtener el resumen por departamento
            departamentos = self.repo.fetch_compromisos_por_departamento(month_number)

            return total_compromisos, completados, pendientes, departamentos
        except Exception as e:
            self.conn.rollback()
            raise e

    def convert_month_to_number(self, month):
        months = {
            "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5,
            "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9,
            "Octubre": 10, "Noviembre": 11, "Diciembre": 12
        }
        return months.get(month, None)

    def count_total_compromisos(self, month):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM compromiso
                    WHERE EXTRACT(MONTH FROM fecha_limite) = %s
                """, (month,))
                result = cursor.fetchone()
                print(result)
                return result
        except Exception as e:
            self.conn.rollback()
            raise e

    def count_compromisos_completados(self, month):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM compromiso
                    WHERE EXTRACT(MONTH FROM fecha_limite) = %s
                    AND estado = 'Completado'
                """, (month,))
                return cursor.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            raise e

    def count_compromisos_pendientes(self, month):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM compromiso
                    WHERE EXTRACT(MONTH FROM fecha_limite) = %s
                    AND estado = 'Pendiente'
                """, (month,))
                return cursor.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_departamentos_resumen(self, mes=None, area_id=None, year=None, departamento_id=None):
        try:
            """
            Obtiene el resumen de compromisos por departamento filtrado por mes, área y año.
            """
            query = """
                SELECT d.id AS departamento_id, d.name AS nombre_departamento,
                    COUNT(c.id) AS total_compromisos,
                    SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) AS completados,
                    SUM(CASE WHEN c.estado != 'Completado' THEN 1 ELSE 0 END) AS pendientes
                FROM departamento d
                LEFT JOIN compromiso c ON d.id = c.id_departamento
                LEFT JOIN reunion_compromiso rc ON c.id = rc.id_compromiso
                LEFT JOIN reunion r ON rc.id_reunion = r.id
                LEFT JOIN area a ON r.id_area = a.id
                WHERE 1=1 AND c.fecha_limite IS NOT NULL
            """
            params = []

            # Filtro por mes
            if mes and mes != "Todos":
                query += " AND EXTRACT(MONTH FROM c.fecha_limite) = %s"
                params.append(mes)

            # Filtro por área
            if area_id:
                query += " AND a.id = %s"
                params.append(area_id)
            
            # Filtro por año
            if year and year != "Todos":
                query += " AND EXTRACT(YEAR FROM c.fecha_limite) = %s"
                params.append(int(year))

            # Filtro por departamento
            if departamento_id:
                query += " AND c.id_departamento = %s"
                params.append(departamento_id)

            query += """
                GROUP BY d.id, d.name
                ORDER BY d.name
            """

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e
        
    def get_months(self):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT DISTINCT EXTRACT(MONTH FROM fecha_limite) AS month FROM compromiso")
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_compromisos_by_mes_departamento(self, mes, departamento_id, year=None):
        try:
            """
            Obtiene compromisos filtrados por mes, año y departamento.
            """
            query = """
                SELECT 
                    c.id AS compromiso_id,
                    c.descripcion,
                    c.estado,
                    c.prioridad,
                    c.avance,
                    c.fecha_limite,
                    c.comentario,
                    c.comentario_direccion,
                    ARRAY_AGG(DISTINCT p.id) AS referentes_ids,
                    STRING_AGG(
                        p.name || ' ' || p.lastname || 
                        CASE WHEN pc.es_responsable_principal THEN ' (*)' ELSE '' END,
                        ', '
                        ORDER BY pc.es_responsable_principal DESC, p.name, p.lastname
                    ) AS referentes
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                WHERE c.id_departamento = %s
            """
            params = [departamento_id]

            # Aplicar filtros solo si no son 'Todos'
            if mes and mes != "Todos":
                query += " AND EXTRACT(MONTH FROM c.fecha_limite) = %s"
                params.append(int(mes))
            
            if year and year != "Todos":
                query += " AND EXTRACT(YEAR FROM c.fecha_limite) = %s"
                params.append(int(year))

            query += " GROUP BY c.id ORDER BY c.fecha_limite"

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e
        
    def fetch_compromisos_by_filtro(self, mes=None, area_id=None):
        try:
            # Debug: Mostrar los parámetros que se están pasando
            print(f" Mes: {mes}, Área ID: {area_id}")

            query = """
                SELECT c.id AS compromiso_id, c.descripcion, c.estado, c.avance, c.fecha_limite, 
                    c.comentario, c.comentario_direccion, 
                    STRING_AGG(DISTINCT p.id::text, ', ') AS referentes_ids,
                    STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS referentes
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                LEFT JOIN reunion_compromiso rc ON c.id = rc.id_compromiso
                LEFT JOIN reunion r ON rc.id_reunion = r.id
                LEFT JOIN area a ON r.id_area = a.id
                WHERE 1=1
            """
            params = []

            # Filtro por mes
            if mes and mes != "Todos":
                query += " AND EXTRACT(MONTH FROM c.fecha_limite) = %s"
                params.append(self.convert_month_to_number(mes))
                print(f"Aplicando filtro por mes: {mes}")

            # Filtro por área
            if area_id:
                query += " AND r.id_area = %s"
                params.append(area_id)
                print(f"Aplicando filtro por área: {area_id}")

            query += """
                GROUP BY c.id
                ORDER BY c.fecha_limite ASC
            """

            # Debug: Mostrar la consulta generada
            print(f"Query final: {query}")
            print(f"Parámetros de la query: {params}")

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()

            # Debug: Verificar los resultados obtenidos
            print(f"Resultados obtenidos: {result}")

            return result
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

    def obtener_compromisos_por_mes_y_anio(mes, year=None):
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if year:
                    cursor.execute("""
                        SELECT * FROM compromiso
                        WHERE EXTRACT(MONTH FROM fecha_limite) = %s AND EXTRACT(YEAR FROM fecha_limite) = %s
                    """, (mes, year))
                else:
                    cursor.execute("""
                        SELECT * FROM compromiso
                        WHERE EXTRACT(MONTH FROM fecha_limite) = %s
                    """, (mes,))
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback() # type: ignore
            raise e

    def get_meses(self):
        try:
            meses = {}
            return meses
        except Exception as e:
            self.conn.rollback()
            raise e

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def fetch_all_compromisos(self, search='', prioridad='', estado='', fecha_limite=''):
        try:
            query = """
                SELECT 
                    c.id AS compromiso_id,
                    c.prioridad,
                    c.descripcion,
                    c.estado,
                    c.avance,
                    c.fecha_limite,
                    c.comentario,
                    c.comentario_direccion,
                    d.name AS departamento_name,
                    ARRAY_AGG(p.id) AS referentes_ids,
                    STRING_AGG(
                        p.name || ' ' || p.lastname || 
                        CASE WHEN pc.es_responsable_principal THEN ' (*)' ELSE '' END,
                        ', '
                        ORDER BY pc.es_responsable_principal DESC, p.name, p.lastname
                    ) AS referentes
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                LEFT JOIN departamento d ON c.id_departamento = d.id
                WHERE 1=1
            """
            params = []

            if search:
                query += " AND (c.descripcion ILIKE %s OR d.name ILIKE %s OR p.name ILIKE %s OR p.lastname ILIKE %s)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

            if prioridad:
                query += " AND c.prioridad = %s"
                params.append(prioridad)

            if estado:
                query += " AND c.estado = %s"
                params.append(estado)

            if fecha_limite:
                query += " AND c.fecha_limite = %s"
                params.append(fecha_limite)

            query += """
                GROUP BY 
                    c.id,
                    c.prioridad,
                    c.descripcion,
                    c.estado,
                    c.avance,
                    c.fecha_limite,
                    c.comentario,
                    c.comentario_direccion,
                    d.name
            """

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_compromisos_compartidos(self, user_id, is_director, search='', estado='', avance='', fecha_limite=''):
        user_info = self.fetch_user_info(user_id)
        query = """
            WITH RECURSIVE jerarquia_departamentos AS (
                -- Punto de partida: departamento asociado al usuario actual
                SELECT
                    d.id AS id_departamento,
                    d.id_departamento_padre,
                    d.name AS nombre_departamento,
                    1 as nivel  -- Agregamos un nivel para controlar la profundidad
                FROM
                    departamento d
                JOIN persona_departamento pd ON d.id = pd.id_departamento
                JOIN persona p ON pd.id_persona = p.id
                WHERE
                    pd.id_persona = %s

                UNION ALL

                -- Recorre jerárquicamente hacia abajo solo si no es FUNCIONARIO
                SELECT
                    d.id AS id_departamento,
                    d.id_departamento_padre,
                    d.name AS nombre_departamento,
                    jd.nivel + 1  -- Incrementamos el nivel
                FROM
                    departamento d
                JOIN jerarquia_departamentos jd ON d.id_departamento_padre = jd.id_departamento
                JOIN persona p ON p.id = %s  -- Joins para verificar el nivel jerárquico
                WHERE
                    p.nivel_jerarquico != 'FUNCIONARIO/A'  -- Solo continúa la recursión si no es FUNCIONARIO
            )
            SELECT DISTINCT  -- Agregamos DISTINCT para evitar duplicados
                c.id AS compromiso_id,
                c.descripcion,
                c.estado,
                c.prioridad,
                c.fecha_creacion,
                c.fecha_limite,
                c.avance,
                c.comentario,
                c.comentario_direccion,
                d.id AS departamento_id,
                d.name AS departamento_name,
                o.name AS origen_name,
                a.name AS area_name,
                STRING_AGG(
                    p.name || ' ' || p.lastname || 
                    CASE WHEN pc.es_responsable_principal THEN ' (*)' ELSE '' END,
                    ', '
                    ORDER BY pc.es_responsable_principal DESC, p.name, p.lastname
                ) AS referentes,
                STRING_AGG(
                    p.nivel_jerarquico,
                    ', '
                    ORDER BY pc.es_responsable_principal DESC, p.name, p.lastname
                ) AS niveles_jerarquicos,
                CASE
                    WHEN %s = c.id_departamento AND %s != 'FUNCIONARIO/A' THEN TRUE
                    ELSE FALSE
                END AS permiso_editar,
                CASE
                    WHEN %s = c.id_departamento AND %s != 'FUNCIONARIO/A' THEN TRUE
                    ELSE FALSE
                END AS permiso_derivar
            FROM
                compromiso c
            JOIN departamento d ON c.id_departamento = d.id
            LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
            LEFT JOIN persona p ON pc.id_persona = p.id
            LEFT JOIN origen o ON c.id_origen = o.id
            LEFT JOIN area a ON c.id_area = a.id
            JOIN persona usuario_actual ON usuario_actual.id = %s  -- Join para acceder al nivel jerárquico del usuario actual
            WHERE
                CASE
                    WHEN usuario_actual.nivel_jerarquico = 'FUNCIONARIO/A' THEN
                        -- Para FUNCIONARIO: solo ver compromisos de su departamento directo
                        c.id_departamento = (
                            SELECT pd2.id_departamento
                            FROM persona_departamento pd2
                            WHERE pd2.id_persona = %s
                            LIMIT 1
                        )
                    ELSE
                        -- Para otros niveles: ver compromisos según la jerarquía
                        d.id IN (SELECT id_departamento FROM jerarquia_departamentos)
                END
        """
        params = [user_id, user_id, user_info['id_departamento'], user_info['nivel_jerarquico'], user_info['id_departamento'], user_info['nivel_jerarquico'], user_id, user_id]

        # Add search filter
        if search:
            query += """
                AND c.id IN (
                    SELECT c2.id
                    FROM compromiso c2
                    LEFT JOIN persona_compromiso pc2 ON c2.id = pc2.id_compromiso
                    LEFT JOIN persona p2 ON pc2.id_persona = p2.id
                    WHERE p2.name ILIKE %s OR p2.lastname ILIKE %s OR d.name ILIKE %s OR c2.descripcion ILIKE %s
                )
            """
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

        # Add estado filter
        if estado:
            query += " AND c.estado = %s"
            params.append(estado)

        # Add avance filter
        if avance:
            min_avance, max_avance = map(int, avance.split('-'))
            query += " AND c.avance BETWEEN %s AND %s"
            params.extend([min_avance, max_avance])

        query += " GROUP BY c.id, d.id, d.name, o.name, a.name, c.descripcion, c.estado, c.prioridad, c.fecha_creacion, c.fecha_limite, c.avance, c.comentario, c.comentario_direccion"

        # Add fecha_limite sorting
        if fecha_limite:
            query += " ORDER BY c.fecha_limite " + ("ASC" if fecha_limite == 'asc' else "DESC")

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def es_jefe_de_departamento(self, user_id, departamento_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 1
                    FROM persona_departamento pd
                    JOIN persona p ON pd.id_persona = p.id
                    WHERE pd.id_persona = %s
                    AND pd.id_departamento = %s
                    AND (p.nivel_jerarquico = 'DIRECTOR DE SERVICIO' OR p.nivel_jerarquico = 'SUBDIRECTOR/A' OR p.nivel_jerarquico = 'JEFE/A DE DEPARTAMENTO' OR p.nivel_jerarquico = 'JEFE/A DE UNIDAD')
                """, (user_id, departamento_id))
                return cursor.fetchone() is not None
        except Exception as e:
            self.conn.rollback()
            raise e

    def fetch_compromiso_by_id(self, compromiso_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id AS compromiso_id, c.descripcion, c.estado, c.prioridad, 
                       c.fecha_creacion, c.fecha_limite, c.avance, c.comentario, 
                       c.comentario_direccion, c.id_departamento,
                       o.name AS origen_name,
                       a.name AS area_name,
                       STRING_AGG(
                           p.name || ' ' || p.lastname || 
                           CASE WHEN pc.es_responsable_principal THEN ' (*)' ELSE '' END,
                           ', '
                           ORDER BY pc.es_responsable_principal DESC, p.name, p.lastname
                       ) AS referentes,
                       ARRAY_AGG(p.id) AS referentes_ids
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                LEFT JOIN origen o ON c.id_origen = o.id
                LEFT JOIN area a ON c.id_area = a.id
                WHERE c.id = %s
                GROUP BY c.id, o.name, a.name
            """, (compromiso_id,))
            return cursor.fetchone()

    def create_compromiso(self, descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, user_id, referentes):
        query = """
        INSERT INTO compromiso (descripcion, estado, prioridad, fecha_creacion, avance, fecha_limite, comentario, comentario_direccion, id_departamento)
        VALUES (%s, %s, %s, %s, 0, %s, %s, %s, %s)
        RETURNING id
        """
        params = (descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento)
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                compromiso_id = cursor.fetchone()['id']
                for referente_id in referentes:
                    cursor.execute("""
                        INSERT INTO persona_compromiso (id_persona, id_compromiso)
                        VALUES (%s, %s)
                    """, (referente_id, compromiso_id))
                self.conn.commit()
                print("Compromiso creado exitosamente")
        except Exception as e:
            self.conn.rollback()
            print(f"Error al insertar compromiso en la base de datos: {e}")
            raise e

    def insert_compromiso(self, descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion, id_origen=None, id_area=None):
        try:
            with self.conn.cursor() as cursor:
                print(f"DEBUG - Insertando compromiso con origen={id_origen}, area={id_area}")
                cursor.execute("""
                    INSERT INTO compromiso (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion, id_origen, id_area)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion, id_origen, id_area))
                return cursor.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            print(f"Error en insert_compromiso: {e}")
            raise e

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

    def is_principal_responsible(self, user_id, compromiso_id):
        """
        Checks if the user is the principal responsible for the commitment
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM persona_compromiso 
                        WHERE id_persona = %s 
                        AND id_compromiso = %s 
                        AND es_responsable_principal = TRUE
                    )
                """, (user_id, compromiso_id))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error checking if user is principal responsible: {e}")
            return False

    def fetch_areas_by_departamento(self, departamento_id):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Convertir departamento_id a entero antes de realizar operaciones matemáticas
                departamento_id = int(departamento_id)
                
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
                # Convertir departamento_id a entero antes de realizar operaciones matemáticas
                departamento_id = int(departamento_id)
                
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


