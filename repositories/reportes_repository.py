from database import get_db_connection

class ReportesRepository:
    def get_total_compromisos(self):
        conn = get_db_connection()
        query = "SELECT COUNT(*) FROM compromiso"
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_pendientes(self):
        conn = get_db_connection()
        query = "SELECT COUNT(*) FROM compromiso WHERE estado = 'Pendiente'"
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_completados(self):
        conn = get_db_connection()
        query = "SELECT COUNT(*) FROM compromiso WHERE estado = 'Completado'"
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_funcionarios(self):
        conn = get_db_connection()
        query = "SELECT COUNT(*) FROM persona"
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_departamentos(self):
        conn = get_db_connection()
        query = "SELECT COUNT(*) FROM departamento"
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_compromisos_por_departamento(self):
        conn = get_db_connection()
        query = """
            SELECT d.name as nombre, COUNT(c.id) as total
            FROM compromiso c
            JOIN departamento d ON c.id_departamento = d.id
            GROUP BY d.name
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'nombre': row[0], 'total': row[1]} for row in result]

    def get_personas_mas(self):
        conn = get_db_connection()
        query = """
            SELECT p.name || ' ' || p.lastname as persona, 
                   SUM(CASE WHEN c.estado = 'Pendiente' THEN 1 ELSE 0 END) as pendientes,
                   SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) as completados
            FROM persona p
            JOIN persona_compromiso pc ON p.id = pc.id_persona
            JOIN compromiso c ON pc.id_compromiso = c.id
            GROUP BY p.name, p.lastname
            ORDER BY pendientes DESC, completados DESC
            LIMIT 10
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'persona': row[0], 'pendientes': row[1], 'completados': row[2]} for row in result]

    def get_compromisos_por_dia(self):
        conn = get_db_connection()
        query = """
            SELECT DATE(c.fecha_creacion) as dia, COUNT(*) as total
            FROM compromiso c
            GROUP BY DATE(c.fecha_creacion)
            ORDER BY dia
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'dia': row[0], 'total': row[1]} for row in result]
    
    def get_compromisos_por_dia_por_departamento(self):
        conn = get_db_connection()
        query = """
            SELECT DATE(c.fecha_creacion) as dia, d.name as departamento, COUNT(*) as total
            FROM compromiso c
            JOIN departamento d ON c.id_departamento = d.id
            GROUP BY DATE(c.fecha_creacion), d.name
            ORDER BY dia
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'dia': row[0], 'departamento': row[1], 'total': row[2]} for row in result]
    

    def get_total_reuniones(self):
        conn = get_db_connection()
        query = "SELECT COUNT(*) FROM reunion"
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_archived_compromisos(self):
        conn = get_db_connection()
        query = "SELECT COUNT(*) FROM compromisos_archivados"
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_deleted_compromisos(self):
        conn = get_db_connection()
        query = "SELECT COUNT(*) FROM compromiso_eliminado"
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_avg_compromisos_por_reunion(self):
        conn = get_db_connection()
        query = """
            SELECT AVG(compromisos_por_reunion) 
            FROM (
                SELECT COUNT(rc.id_compromiso) as compromisos_por_reunion
                FROM reunion r
                LEFT JOIN reunion_compromiso rc ON r.id = rc.id_reunion
                GROUP BY r.id
            ) subquery
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_percentage_completados(self):
        conn = get_db_connection()
        query = """
            SELECT 
                (SELECT COUNT(*) FROM compromiso WHERE estado = 'Completado') * 100.0 / 
                (SELECT COUNT(*) FROM compromiso) AS porcentaje_completados
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_percentage_pendientes(self):
        conn = get_db_connection()
        query = """
            SELECT 
                (SELECT COUNT(*) FROM compromiso WHERE estado = 'Pendiente') * 100.0 / 
                (SELECT COUNT(*) FROM compromiso) AS porcentaje_pendientes
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_percentage_completados_por_persona(self):
        conn = get_db_connection()
        query = """
            SELECT p.name || ' ' || p.lastname as persona, 
                   (SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(c.id), 0)) as porcentaje_completados
            FROM persona p
            JOIN persona_compromiso pc ON p.id = pc.id_persona
            JOIN compromiso c ON pc.id_compromiso = c.id
            GROUP BY p.name, p.lastname
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'persona': row[0], 'porcentaje_completados': row[1] or 0} for row in result]

    def get_percentage_completados_por_departamento(self):
        conn = get_db_connection()
        query = """
            SELECT d.name as departamento, 
                   (SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(c.id), 0)) as porcentaje_completados
            FROM compromiso c
            JOIN departamento d ON c.id_departamento = d.id
            GROUP BY d.name
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'departamento': row[0], 'porcentaje_completados': row[1] or 0} for row in result]
    
    def get_reuniones_por_dia(self):
        conn = get_db_connection()
        query = """
            SELECT DATE(fecha_creacion) as dia, COUNT(*) as total
            FROM reunion
            GROUP BY DATE(fecha_creacion)
            ORDER BY dia
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'dia': row[0], 'total': row[1]} for row in result]
