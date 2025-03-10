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

    def get_personas_mas(self, search_name=None):
        conn = get_db_connection()
        query = """
            SELECT p.name || ' ' || p.lastname as persona, 
                   SUM(CASE WHEN c.estado = 'Pendiente' THEN 1 ELSE 0 END) as pendientes,
                   SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) as completados
            FROM persona p
            JOIN persona_compromiso pc ON p.id = pc.id_persona
            JOIN compromiso c ON pc.id_compromiso = c.id
        """
        params = []
        if search_name:
            query += " WHERE (p.name || ' ' || p.lastname) ILIKE %s"
            params.append(f'%{search_name}%')
        query += """
            GROUP BY p.name, p.lastname
            ORDER BY pendientes DESC, completados DESC
            LIMIT 10
        """
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            result = cursor.fetchall()
            return [{'persona': row[0], 'pendientes': row[1], 'completados': row[2]} for row in result]

    def get_compromisos_por_dia(self, day=None, month=None, year=None):
        conn = get_db_connection()
        query = """
            SELECT to_char(c.fecha_creacion, 'YYYY-MM-DD') as dia, COUNT(*) as total
            FROM compromiso c
        """
        conditions = []
        params = []
        if day:
            conditions.append("EXTRACT(DAY FROM c.fecha_creacion) = %s")
            params.append(day)
        if month:
            conditions.append("EXTRACT(MONTH FROM c.fecha_creacion) = %s")
            params.append(month)
        if year:
            conditions.append("EXTRACT(YEAR FROM c.fecha_creacion) = %s")
            params.append(year)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " GROUP BY to_char(c.fecha_creacion, 'YYYY-MM-DD') ORDER BY dia"
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            result = cursor.fetchall()
            return [{'dia': row[0], 'total': row[1]} for row in result]
    
    def get_compromisos_por_dia_por_departamento(self):
        conn = get_db_connection()
        query = """
            SELECT to_char(c.fecha_creacion, 'YYYY-MM-DD') as dia, d.name as departamento, COUNT(*) as total
            FROM compromiso c
            JOIN departamento d ON c.id_departamento = d.id
            GROUP BY to_char(c.fecha_creacion, 'YYYY-MM-DD'), d.name
            ORDER BY dia
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'dia': row[0], 'departamento': row[1], 'total': row[2]} for row in result]
    
    def get_compromisos_por_jerarquia_departamento(self):
        conn = get_db_connection()
        query = """
            WITH RECURSIVE dept_hierarchy AS (
                SELECT id, name, id_departamento_padre
                FROM departamento
                WHERE id_departamento_padre IS NULL
                UNION ALL
                SELECT d.id, d.name, d.id_departamento_padre
                FROM departamento d
                INNER JOIN dept_hierarchy dh ON dh.id = d.id_departamento_padre
            )
            SELECT dh.id, dh.name as departamento, dh.id_departamento_padre,
                   COUNT(c.id) as total,
                   (SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(c.id), 0)) as porcentaje_completados
            FROM dept_hierarchy dh
            LEFT JOIN compromiso c ON dh.id = c.id_departamento
            GROUP BY dh.id, dh.name, dh.id_departamento_padre
            ORDER BY dh.name
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return [{'id': row[0], 'departamento': row[1], 'id_departamento_padre': row[2], 'total': row[3], 'porcentaje_completados': row[4] or 0} for row in result]

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
    
    def get_reuniones_por_dia(self, day=None, month=None, year=None):
        conn = get_db_connection()
        query = "SELECT to_char(fecha_creacion, 'YYYY-MM-DD') as dia, COUNT(*) as total FROM reunion"
        conditions = []
        params = []
        if day:
            conditions.append("EXTRACT(DAY FROM fecha_creacion) = %s")
            params.append(day)
        if month:
            conditions.append("EXTRACT(MONTH FROM fecha_creacion) = %s")
            params.append(month)
        if year:
            conditions.append("EXTRACT(YEAR FROM fecha_creacion) = %s")
            params.append(year)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " GROUP BY to_char(fecha_creacion, 'YYYY-MM-DD') ORDER BY dia"
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            result = cursor.fetchall()
            # Devolver la fecha sin conversión ISO para que JS la formatee según corresponda
            return [{'dia': row[0], 'total': row[1]} for row in result]

    def get_user_department_hierarchy(self, user_id):
        """Get the department hierarchy for a user including their own department and all subordinate departments."""
        conn = get_db_connection()
        query = """
            WITH RECURSIVE user_dept AS (
                -- Get user's department
                SELECT d.id, d.name
                FROM departamento d
                JOIN persona_departamento pd ON d.id = pd.id_departamento
                WHERE pd.id_persona = %s
            ), dept_hierarchy AS (
                -- Start with user's department
                SELECT d.id, d.name
                FROM departamento d
                JOIN user_dept ud ON d.id = ud.id
                UNION
                -- Add all subordinate departments
                SELECT d.id, d.name
                FROM departamento d
                JOIN dept_hierarchy dh ON d.id_departamento_padre = dh.id
            )
            SELECT * FROM dept_hierarchy
        """
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            result = cursor.fetchall()
            return [{'id': row[0], 'name': row[1]} for row in result]
    
    def get_total_compromisos_by_dept_hierarchy(self, dept_ids):
        """Get total commitments filtered by department hierarchy."""
        if not dept_ids:
            return self.get_total_compromisos()
            
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        query = f"SELECT COUNT(*) FROM compromiso WHERE id_departamento IN ({placeholders})"
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(dept_ids))
            return cursor.fetchone()[0]
    
    def get_pendientes_by_dept_hierarchy(self, dept_ids):
        """Get pending commitments filtered by department hierarchy."""
        if not dept_ids:
            return self.get_pendientes()
            
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        query = f"SELECT COUNT(*) FROM compromiso WHERE estado = 'Pendiente' AND id_departamento IN ({placeholders})"
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(dept_ids))
            return cursor.fetchone()[0]
    
    def get_completados_by_dept_hierarchy(self, dept_ids):
        """Get completed commitments filtered by department hierarchy."""
        if not dept_ids:
            return self.get_completados()
            
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        query = f"SELECT COUNT(*) FROM compromiso WHERE estado = 'Completado' AND id_departamento IN ({placeholders})"
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(dept_ids))
            return cursor.fetchone()[0]
    
    def get_compromisos_por_departamento_filtered(self, dept_ids):
        """Get commitments by department filtered by department hierarchy with order."""
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        query = f"""
            WITH RECURSIVE dept_hierarchy AS (
                SELECT 
                    d.id, 
                    d.name, 
                    d.id_departamento_padre,
                    CAST(d.name as VARCHAR) as path
                FROM departamento d
                WHERE d.id_departamento_padre IS NULL AND d.id IN ({placeholders})
                
                UNION ALL
                
                SELECT 
                    d.id, 
                    d.name, 
                    d.id_departamento_padre,
                    dh.path || ' > ' || d.name
                FROM departamento d
                JOIN dept_hierarchy dh ON d.id_departamento_padre = dh.id
                WHERE d.id IN ({placeholders})
            )
            SELECT 
                d.id,
                d.name as nombre, 
                COUNT(c.id) as total,
                d.path as hierarchy_path,
                (SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(c.id), 0)) as porcentaje_completados
            FROM dept_hierarchy d
            LEFT JOIN compromiso c ON d.id = c.id_departamento
            GROUP BY d.id, d.name, d.path
            ORDER BY d.path
        """
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(dept_ids) + tuple(dept_ids))
            result = cursor.fetchall()
            return [{'id': row[0], 'nombre': row[1], 'total': row[2], 'path': row[3], 'porcentaje_completados': row[4] or 0} for row in result]
    
    def get_personas_mas_by_dept_hierarchy(self, dept_ids, search_name=None):
        """Get people with most commitments filtered by department hierarchy."""
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        query = f"""
            WITH personas_departamentos AS (
                -- Get all people in these departments
                SELECT DISTINCT p.id, p.name, p.lastname, d.id as dept_id, d.name as dept_name, d.id_departamento_padre
                FROM persona p
                JOIN persona_departamento pd ON p.id = pd.id_persona
                JOIN departamento d ON pd.id_departamento = d.id
                WHERE d.id IN ({placeholders})
            ),
            dept_paths AS (
                -- Get department paths for better display
                SELECT 
                    d.id,
                    (
                        WITH RECURSIVE dept_path AS (
                            SELECT d2.id, d2.name, d2.id_departamento_padre
                            FROM departamento d2
                            WHERE d2.id = d.id
                            UNION ALL
                            SELECT d3.id, d3.name, d3.id_departamento_padre
                            FROM departamento d3
                            JOIN dept_path dp ON d3.id = dp.id_departamento_padre
                        )
                        SELECT string_agg(name, ' > ' ORDER BY id DESC)
                        FROM dept_path
                    ) as path
                FROM departamento d
                WHERE d.id IN ({placeholders})
            ),
            compromiso_counts AS (
                -- Count commitments per person
                SELECT 
                    pc.id_persona,
                    SUM(CASE WHEN c.estado = 'Pendiente' THEN 1 ELSE 0 END) as pendientes,
                    SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) as completados
                FROM persona_compromiso pc
                JOIN compromiso c ON pc.id_compromiso = c.id
                WHERE c.id_departamento IN ({placeholders})
                GROUP BY pc.id_persona
            )
            SELECT 
                pd.id,
                pd.name || ' ' || pd.lastname as persona,
                COALESCE(cc.pendientes, 0) as pendientes,
                COALESCE(cc.completados, 0) as completados,
                pd.dept_id,
                pd.dept_name,
                pd.id_departamento_padre,
                dp.path as dept_path
            FROM personas_departamentos pd
            LEFT JOIN compromiso_counts cc ON pd.id = cc.id_persona
            LEFT JOIN dept_paths dp ON pd.dept_id = dp.id
        """
        
        conditions = []
        params = list(dept_ids) + list(dept_ids) + list(dept_ids)
        
        if search_name:
            conditions.append("(pd.name || ' ' || pd.lastname) ILIKE %s")
            params.append(f'%{search_name}%')
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            ORDER BY 
                dept_path,
                pendientes DESC, 
                completados DESC
            LIMIT 100
        """
        
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            result = cursor.fetchall()
            return [{'id': row[0], 'persona': row[1], 'pendientes': row[2], 'completados': row[3], 
                    'id_departamento': row[4], 'nombre_departamento': row[5], 
                    'id_departamento_padre': row[6], 'dept_path': row[7]} 
                    for row in result]
    
    def get_compromisos_por_dia_by_dept_hierarchy(self, dept_ids, day=None, month=None, year=None):
        """Get commitments by day filtered by department hierarchy."""
        conn = get_db_connection()
        query = """
            SELECT to_char(c.fecha_creacion, 'YYYY-MM-DD') as dia, COUNT(*) as total
            FROM compromiso c
            WHERE c.id_departamento IN ({})
        """
        conditions = ["c.id_departamento IN ({})"]
        params = list(dept_ids)
        if day:
            conditions.append("EXTRACT(DAY FROM c.fecha_creacion) = %s")
            params.append(day)
        if month:
            conditions.append("EXTRACT(MONTH FROM c.fecha_creacion) = %s")
            params.append(month)
        if year:
            conditions.append("EXTRACT(YEAR FROM c.fecha_creacion) = %s")
            params.append(year)
            
        query = """
            SELECT to_char(c.fecha_creacion, 'YYYY-MM-DD') as dia, COUNT(*) as total
            FROM compromiso c
            WHERE """ + " AND ".join(conditions).format(', '.join(['%s'] * len(dept_ids))) + """
            GROUP BY to_char(c.fecha_creacion, 'YYYY-MM-DD') 
            ORDER BY dia
        """
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            result = cursor.fetchall()
            return [{'dia': row[0], 'total': row[1]} for row in result]
    
    def get_compromisos_por_dia_por_departamento_filtered(self, dept_ids):
        """Get commitments by day and department filtered by department hierarchy."""
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        query = f"""
            SELECT to_char(c.fecha_creacion, 'YYYY-MM-DD') as dia, d.name as departamento, COUNT(*) as total
            FROM compromiso c
            JOIN departamento d ON c.id_departamento = d.id
            WHERE c.id_departamento IN ({placeholders})
            GROUP BY to_char(c.fecha_creacion, 'YYYY-MM-DD'), d.name
            ORDER BY dia
        """
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(dept_ids))
            result = cursor.fetchall()
            return [{'dia': row[0], 'departamento': row[1], 'total': row[2]} for row in result]
    
    def get_compromisos_por_jerarquia_departamento_filtered(self, dept_ids):
        """Get commitments by department hierarchy filtered by department hierarchy."""
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        query = f"""
            WITH RECURSIVE dept_hierarchy AS (
                -- Find all departments that are either in our list or have parents in our list
                SELECT 
                    d.id, 
                    d.name, 
                    d.id_departamento_padre,
                    ARRAY[d.id] as path_ids,
                    CAST(d.name as VARCHAR) as path,
                    0 as level
                FROM departamento d
                WHERE d.id IN ({placeholders})
                
                UNION ALL
                
                SELECT 
                    d.id, 
                    d.name, 
                    d.id_departamento_padre,
                    dh.path_ids || d.id,
                    dh.path || ' > ' || d.name,
                    dh.level + 1
                FROM departamento d
                JOIN dept_hierarchy dh ON d.id_departamento_padre = dh.id
            )
            SELECT 
                dh.id, 
                dh.name as departamento, 
                dh.id_departamento_padre,
                dh.path,
                dh.level,
                COUNT(c.id) as total,
                (SUM(CASE WHEN c.estado = 'Completado' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(c.id), 0)) as porcentaje_completados
            FROM dept_hierarchy dh
            LEFT JOIN compromiso c ON dh.id = c.id_departamento
            GROUP BY dh.id, dh.name, dh.id_departamento_padre, dh.path, dh.path_ids, dh.level
            ORDER BY dh.path, dh.level
        """
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(dept_ids))
            result = cursor.fetchall()
            return [{'id': row[0], 'departamento': row[1], 'id_departamento_padre': row[2], 
                    'path': row[3], 'level': row[4], 'total': row[5], 'porcentaje_completados': row[6] or 0} 
                    for row in result]

    def get_reuniones_por_dia_filtered_by_dept(self, dept_ids, day=None, month=None, year=None):
        """Get meetings by day filtered by departments that participated."""
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        
        query = f"""
            SELECT to_char(r.fecha_creacion, 'YYYY-MM-DD') as dia, COUNT(DISTINCT r.id) as total
            FROM reunion r
            JOIN reunion_compromiso rc ON r.id = rc.id_reunion
            JOIN compromiso c ON rc.id_compromiso = c.id
            WHERE c.id_departamento IN ({placeholders})
        """
        params = list(dept_ids)
        
        if day:
            query += " AND EXTRACT(DAY FROM r.fecha_creacion) = %s"
            params.append(day)
        if month:
            query += " AND EXTRACT(MONTH FROM r.fecha_creacion) = %s"
            params.append(month)
        if year:
            query += " AND EXTRACT(YEAR FROM r.fecha_creacion) = %s"
            params.append(year)
            
        query += " GROUP BY to_char(r.fecha_creacion, 'YYYY-MM-DD') ORDER BY dia"
        
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            result = cursor.fetchall()
            return [{'dia': row[0], 'total': row[1]} for row in result]

    def get_funcionarios_by_dept_hierarchy(self, dept_ids):
        """Get the number of employees within the specified department hierarchy."""
        if not dept_ids:
            return self.get_funcionarios()
            
        conn = get_db_connection()
        placeholders = ', '.join(['%s'] * len(dept_ids))
        query = f"""
            SELECT COUNT(DISTINCT p.id)
            FROM persona p
            JOIN persona_departamento pd ON p.id = pd.id_persona
            WHERE pd.id_departamento IN ({placeholders})
        """
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(dept_ids))
            return cursor.fetchone()[0]
