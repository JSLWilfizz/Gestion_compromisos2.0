# /repositories/compromiso_repository.py
from database import get_db_connection
from psycopg2.extras import RealDictCursor

class CompromisoRepository:
    def __init__(self):
        self.conn = get_db_connection()

    def fetch_user_info(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT p.id, p.name, p.lastname, p.position, d.name AS departamento_name
                FROM persona p
                JOIN persona_departamento pd ON p.id = pd.id_persona
                JOIN departamento d ON pd.id_departamento = d.id
                WHERE p.id = %s
            """, (user_id,))
            return cursor.fetchone()

    def fetch_director_info(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT pd.es_director, pd.id_departamento
                FROM persona_departamento pd
                JOIN persona p ON p.id = pd.id_persona
                WHERE p.id = %s
            """, (user_id,))
            return cursor.fetchone()

    def fetch_responsables(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT p.id, p.name, p.lastname, d.name AS departamento, p.position
                FROM persona p
                JOIN persona_departamento pd ON p.id = pd.id_persona
                JOIN departamento d ON pd.id_departamento = d.id
            """)
            return cursor.fetchall()

    def fetch_compromisos_by_departamento(self, departamento_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id AS compromiso_id,c.prioridad, c.descripcion, c.estado, c.avance, c.fecha_limite, 
                       c.comentario, c.comentario_direccion,
                       ARRAY_AGG(DISTINCT p.id) AS responsables_ids, -- Obtenemos una lista de IDs de responsables
                       STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables -- Nombres concatenados
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                WHERE c.id_departamento = %s
                GROUP BY c.id
            """, (departamento_id,))
            return cursor.fetchall()

    def fetch_compromisos_by_responsable(self, user_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id AS compromiso_id,c.prioridad, c.descripcion, c.estado, c.avance, c.fecha_limite,
                       c.comentario, c.comentario_direccion,
                       ARRAY_AGG(DISTINCT p.id) AS responsables_ids,
                       STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                WHERE c.id IN (
                    SELECT c2.id
                    FROM compromiso c2
                    LEFT JOIN persona_compromiso pc2 ON c2.id = pc2.id_compromiso
                    WHERE pc2.id_persona = %s -- Filtrar por el ID del usuario responsable
                )
                GROUP BY c.id
            """, (user_id,))
            return cursor.fetchall()

    def update_compromiso(self, compromiso_id, estado, avance, comentario,comentario_director):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE compromiso
                SET estado = %s, avance = %s, comentario = %s, comentario_direccion = %s
                WHERE id = %s
            """, (estado, avance, comentario, comentario_director,compromiso_id))

    def update_responsables(self, compromiso_id, nuevos_responsables):
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM persona_compromiso WHERE id_compromiso = %s", (compromiso_id,))
            for responsable_id in nuevos_responsables:
                cursor.execute("""
                    INSERT INTO persona_compromiso (id_persona, id_compromiso)
                    VALUES (%s, %s)
                """, (responsable_id, compromiso_id))

    def log_modificacion(self, compromiso_id, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO compromiso_modificaciones (id_compromiso, id_usuario)
                VALUES (%s, %s)
            """, (compromiso_id, user_id))

    def fetch_departamentos(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, name FROM departamento")
            return cursor.fetchall()

    def fetch_compromisos_by_departamento(self, departamento_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id AS compromiso_id,c.prioridad, c.descripcion, c.estado, c.avance, c.fecha_limite, 
                       c.comentario, c.comentario_direccion,
                       ARRAY_AGG(DISTINCT p.id) AS responsables_ids, -- IDs de los responsables
                       STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables -- Nombres de los responsables
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                WHERE c.id_departamento = %s
                GROUP BY c.id
            """, (departamento_id,))
            return cursor.fetchall()

    def fetch_compromisos_by_month(self, month, year):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id AS compromiso_id,c.prioridad, c.descripcion, c.estado, c.avance, c.fecha_limite, 
                       c.comentario_director, d.name AS departamento, 
                       STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables
                FROM compromiso c
                JOIN departamento d ON c.id_departamento = d.id
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                WHERE EXTRACT(MONTH FROM c.fecha_limite) = %s
                AND EXTRACT(YEAR FROM c.fecha_limite) = %s
                GROUP BY c.id, d.name
            """, (month, year))
            return cursor.fetchall()

    def get_resumen_compromisos(self, month):
        # Convertir el nombre del mes en su número (Ej: "Enero" -> 1)
        month_number = self.convert_month_to_number(month) if month else None

        # Obtener el resumen general
        total_compromisos = self.repo.count_total_compromisos(month_number)
        completados = self.repo.count_compromisos_completados(month_number)
        pendientes = self.repo.count_compromisos_pendientes(month_number)

        # Obtener el resumen por departamento
        departamentos = self.repo.fetch_compromisos_por_departamento(month_number)

        return total_compromisos, completados, pendientes, departamentos

    def convert_month_to_number(self, month):
        months = {
            "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5,
            "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9,
            "Octubre": 10, "Noviembre": 11, "Diciembre": 12
        }
        return months.get(month, None)

    def count_total_compromisos(self, month):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM compromiso
                WHERE EXTRACT(MONTH FROM fecha_limite) = %s
            """, (month,))
            result = cursor.fetchone()
            print(result)
            return result

    def count_compromisos_completados(self, month):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM compromiso
                WHERE EXTRACT(MONTH FROM fecha_limite) = %s
                AND estado = 'Completado'
            """, (month,))
            return cursor.fetchone()[0]

    def count_compromisos_pendientes(self, month):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM compromiso
                WHERE EXTRACT(MONTH FROM fecha_limite) = %s
                AND estado = 'Pendiente'
            """, (month,))
            return cursor.fetchone()[0]

    def fetch_departamentos_resumen(self, month=None):
        # Diccionario que convierte el nombre del mes en su número correspondiente
        month_mapping = {
            'Enero': 1,
            'Febrero': 2,
            'Marzo': 3,
            'Abril': 4,
            'Mayo': 5,
            'Junio': 6,
            'Julio': 7,
            'Agosto': 8,
            'Septiembre': 9,
            'Octubre': 10,
            'Noviembre': 11,
            'Diciembre': 12,
            'Todos': False
        }

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Convertir el mes de texto a su representación numérica
            month_number = month_mapping.get(month) if month else None

            # Si month_number es None, no filtramos por mes
            if month_number:
                cursor.execute("""
                    SELECT d.id, d.name AS nombre, 
                        COUNT(c.id) AS total_compromisos, 
                        SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) AS completados,
                        SUM(CASE WHEN c.estado != 'Completado' THEN 1 ELSE 0 END) AS pendientes
                    FROM departamento d
                    LEFT JOIN compromiso c ON d.id = c.id_departamento
                    WHERE EXTRACT(MONTH FROM c.fecha_limite) = %s
                    GROUP BY d.id
                """, (month_number,))
            else:
                cursor.execute("""
                    SELECT d.id, d.name AS nombre, 
                        COUNT(c.id) AS total_compromisos, 
                        SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) AS completados,
                        SUM(CASE WHEN c.estado != 'Completado' THEN 1 ELSE 0 END) AS pendientes
                    FROM departamento d
                    LEFT JOIN compromiso c ON d.id = c.id_departamento
                    WHERE c.fecha_limite IS NOT NULL 
                    GROUP BY d.id
                """)
            return cursor.fetchall()

    def get_months(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT EXTRACT(MONTH FROM fecha_limite) AS month FROM compromiso")
            return cursor.fetchall()

    def fetch_compromisos_by_mes_departamento(self, mes, departamento_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id AS compromiso_id, c.descripcion, c.estado, c.avance, c.fecha_limite,c.comentario, c.comentario_direccion, 
                       ARRAY_AGG(DISTINCT p.id) AS responsables_ids, 
                       STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                WHERE c.id_departamento = %s AND EXTRACT(MONTH FROM c.fecha_limite) = %s
                GROUP BY c.id
            """, (departamento_id, mes))
            return cursor.fetchall()

    def fetch_compromisos_by_filtro(self, mes=None, area_id=None):
        # Debug: Mostrar los parámetros que se están pasando
        print(f" Mes: {mes}, Área ID: {area_id}")

        query = """
            SELECT c.id AS compromiso_id, c.descripcion, c.estado, c.avance, c.fecha_limite, 
                   c.comentario, c.comentario_direccion, 
                   STRING_AGG(DISTINCT p.id::text, ', ') AS responsables_ids,
                   STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables
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

    def fetch_areas(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, name FROM area")
            return cursor.fetchall()

    def fetch_departamentos_resumen(self, mes=None, area_id=None):
        """
        Obtiene el resumen de compromisos por departamento filtrado por mes y área (opcional).
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

        # Filtro opcional por mes
        if mes and mes != "Todos":
            query += " AND EXTRACT(MONTH FROM c.fecha_limite) = %s"
            params.append(mes)

        # Filtro opcional por área
        if area_id:
            query += " AND a.id = %s"
            params.append(area_id)

        query += """
            GROUP BY d.id
            ORDER BY d.name
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def obtener_compromisos_por_mes_y_anio(mes, year=None):
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

    def get_meses(self):
        meses = {}

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def fetch_all_compromisos(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT c.id AS compromiso_id,c.prioridad, c.descripcion, c.estado, c.avance, c.fecha_limite, 
                       c.comentario, c.comentario_direccion,
                       ARRAY_AGG(DISTINCT p.id) AS responsables_ids, -- Obtenemos una lista de IDs de responsables
                       STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables -- Nombres concatenados
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                GROUP BY c.id
            """)
            return cursor.fetchall()
