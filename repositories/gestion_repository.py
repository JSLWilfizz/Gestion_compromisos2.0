from database import get_db_connection

class GestionRepository:
    def fetch_funcionarios(self, search=None, departamento=None, nivel_jerarquico=None):
        conn = get_db_connection()
        query = """
            SELECT p.id, p.rut, p.name, p.lastname, p.profesion, d.name AS departamento_name, p.nivel_jerarquico, p.cargo, p.correo, p.anexo_telefonico
            FROM persona p
            JOIN persona_departamento pd ON p.id = pd.id_persona
            JOIN departamento d ON pd.id_departamento = d.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (p.name ILIKE %s OR p.lastname ILIKE %s OR p.rut ILIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        if departamento:
            query += " AND d.id = %s"
            params.append(departamento)

        if nivel_jerarquico:
            query += " AND p.nivel_jerarquico = %s"
            params.append(nivel_jerarquico)

        query += " GROUP BY p.id, p.rut, p.name, p.lastname, p.profesion, d.name, p.nivel_jerarquico, p.cargo, p.correo, p.anexo_telefonico"

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            funcionarios = cursor.fetchall()
            print("Funcionarios Query Result:", funcionarios)  # Agrega este mensaje de depuración
            return funcionarios

    def fetch_funcionario_by_id(self, funcionario_id):
        conn = get_db_connection()
        query = """
            SELECT p.id, p.rut, p.name, p.lastname, p.profesion, d.name AS departamento_name, p.nivel_jerarquico, p.cargo, p.correo, p.anexo_telefonico
            FROM persona p
            JOIN persona_departamento pd ON p.id = pd.id_persona
            JOIN departamento d ON pd.id_departamento = d.id
            WHERE p.id = %s
        """
        with conn.cursor() as cursor:
            cursor.execute(query, (funcionario_id,))
            return cursor.fetchone()

    def update_funcionario(self, funcionario_id, rut, name, lastname, profesion, departamento_id, nivel_jerarquico, cargo, correo, anexo_telefonico):
        conn = get_db_connection()
        query = """
            UPDATE persona
            SET rut = %s, name = %s, lastname = %s, profesion = %s, nivel_jerarquico = %s, cargo = %s, correo = %s, anexo_telefonico = %s
            WHERE id = %s
        """
        with conn.cursor() as cursor:
            cursor.execute(query, (rut, name, lastname, profesion, nivel_jerarquico, cargo, correo, anexo_telefonico, funcionario_id))
            conn.commit()

        # Actualizar la relación entre el funcionario y el departamento
        query = """
            UPDATE persona_departamento
            SET id_departamento = %s
            WHERE id_persona = %s
        """
        with conn.cursor() as cursor:
            cursor.execute(query, (departamento_id, funcionario_id))
            conn.commit()

    def fetch_departamentos(self):
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, id_departamento_padre FROM departamento ORDER BY id")
            return cur.fetchall()

    def fetch_departamento_by_id(self, departamento_id):
        conn = get_db_connection()
        query = "SELECT id, name, id_departamento_padre FROM departamento WHERE id = %s"
        with conn.cursor() as cursor:
            cursor.execute(query, (departamento_id,))
            return cursor.fetchone()

    def update_departamento(self, departamento_id, name, id_departamento_padre):
        conn = get_db_connection()
        query = "UPDATE departamento SET name = %s, id_departamento_padre = %s WHERE id = %s"
        with conn.cursor() as cursor:
            cursor.execute(query, (name, id_departamento_padre, departamento_id))
            conn.commit()

    def fetch_niveles_jerarquicos(self):
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT nivel_jerarquico FROM persona ORDER BY nivel_jerarquico")
            return [row[0] for row in cur.fetchall()]

    def fetch_departamento_chain_by_name(self, name):
        conn = get_db_connection()
        query = """
            WITH RECURSIVE child_chain AS (
                SELECT id, name, id_departamento_padre, 1 AS level
                FROM departamento
                WHERE name = %s
                UNION ALL
                SELECT d.id, d.name, d.id_departamento_padre, cc.level + 1
                FROM departamento d
                JOIN child_chain cc ON d.id_departamento_padre = cc.id
            )
            SELECT id, name, id_departamento_padre, level FROM child_chain
            ORDER BY level, id
        """
        with conn.cursor() as cur:
            cur.execute(query, (name,))
            return cur.fetchall()

    def fetch_areas_by_departamento(self, departamento_id=None, search=None):
        conn = get_db_connection()
        query = """
            SELECT a.id, a.name, a.id_departamento, d.name as departamento_name
            FROM area a
            LEFT JOIN departamento d ON a.id_departamento = d.id
            WHERE 1=1
        """
        params = []
        
        if departamento_id:
            if departamento_id == 'null':
                query += " AND a.id_departamento IS NULL"
            else:
                query += " AND a.id_departamento = %s"
                params.append(departamento_id)
            
        if search:
            query += " AND a.name ILIKE %s"
            params.append(f"%{search}%")
            
        query += " ORDER BY a.name"
        
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def fetch_origenes_by_departamento(self, departamento_id=None, search=None):
        conn = get_db_connection()
        query = """
            SELECT o.id, o.name, o.id_departamento, d.name as departamento_name
            FROM origen o
            LEFT JOIN departamento d ON o.id_departamento = d.id
            WHERE 1=1
        """
        params = []
        
        if departamento_id:
            if departamento_id == 'null':
                query += " AND o.id_departamento IS NULL"
            else:
                query += " AND o.id_departamento = %s"
                params.append(departamento_id)
            
        if search:
            query += " AND o.name ILIKE %s"
            params.append(f"%{search}%")
            
        query += " ORDER BY o.name"
        
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def crear_area(self, name, id_departamento):
        conn = get_db_connection()
        
        try:
            # First reset the sequence to avoid UniqueViolation error
            with conn.cursor() as cursor:
                # Get the current max ID
                cursor.execute("SELECT MAX(id) FROM area")
                max_id = cursor.fetchone()[0]
                
                # Reset the sequence to be one higher than the max ID
                if max_id is not None:
                    cursor.execute("SELECT setval('area_id_seq', %s)", (max_id,))
            
            # Now insert the new record
            query = """
                INSERT INTO area (name, id_departamento)
                VALUES (%s, %s)
                RETURNING id
            """
            with conn.cursor() as cursor:
                cursor.execute(query, (name, id_departamento))
                area_id = cursor.fetchone()[0]
                conn.commit()
                return area_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def crear_origen(self, name, id_departamento):
        conn = get_db_connection()
        
        try:
            # First reset the sequence to avoid UniqueViolation error
            with conn.cursor() as cursor:
                # Get the current max ID
                cursor.execute("SELECT MAX(id) FROM origen")
                max_id = cursor.fetchone()[0]
                
                # Reset the sequence to be one higher than the max ID
                if max_id is not None:
                    cursor.execute("SELECT setval('origen_id_seq', %s)", (max_id,))
            
            # Now insert the new record
            query = """
                INSERT INTO origen (name, id_departamento)
                VALUES (%s, %s)
                RETURNING id
            """
            with conn.cursor() as cursor:
                cursor.execute(query, (name, id_departamento))
                origen_id = cursor.fetchone()[0]
                conn.commit()
                return origen_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def actualizar_area(self, area_id, name, id_departamento):
        conn = get_db_connection()
        query = """
            UPDATE area
            SET name = %s, id_departamento = %s
            WHERE id = %s
        """
        with conn.cursor() as cursor:
            cursor.execute(query, (name, id_departamento, area_id))
            conn.commit()
    
    def actualizar_origen(self, origen_id, name, id_departamento):
        conn = get_db_connection()
        query = """
            UPDATE origen
            SET name = %s, id_departamento = %s
            WHERE id = %s
        """
        with conn.cursor() as cursor:
            cursor.execute(query, (name, id_departamento, origen_id))
            conn.commit()
    
    def eliminar_area(self, area_id):
        conn = get_db_connection()
        query = "DELETE FROM area WHERE id = %s"
        with conn.cursor() as cursor:
            cursor.execute(query, (area_id,))
            conn.commit()
    
    def eliminar_origen(self, origen_id):
        conn = get_db_connection()
        query = "DELETE FROM origen WHERE id = %s"
        with conn.cursor() as cursor:
            cursor.execute(query, (origen_id,))
            conn.commit()
