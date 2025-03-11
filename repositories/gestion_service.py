from repositories.gestion_repository import GestionRepository

class GestionService:
    def __init__(self):
        self.repo = GestionRepository()

    def get_funcionarios(self, search=None, departamento=None, nivel_jerarquico=None):
        raw_funcionarios = self.repo.fetch_funcionarios(search, departamento, nivel_jerarquico)
        return [self._convert_funcionario_to_dict(row) for row in raw_funcionarios]

    def get_departamentos(self):
        raw_departamentos = self.repo.fetch_departamentos()
        return [self._convert_departamento_to_dict(row) for row in raw_departamentos]

    def get_niveles_jerarquicos(self):
        return self.repo.fetch_niveles_jerarquicos()

    def get_departamento_chain_by_name(self, name):
        rows = self.repo.fetch_departamento_chain_by_name(name)
        return [self._convert_departamento_to_dict_with_level(r) for r in rows]

    def get_funcionario_by_id(self, funcionario_id):
        row = self.repo.fetch_funcionario_by_id(funcionario_id)
        return self._convert_funcionario_to_dict(row)

    def update_funcionario(self, funcionario_id, rut, name, lastname, profesion, departamento_id, nivel_jerarquico, cargo, correo, anexo_telefonico):
        self.repo.update_funcionario(funcionario_id, rut, name, lastname, profesion, departamento_id, nivel_jerarquico, cargo, correo, anexo_telefonico)

    def get_departamento_by_id(self, departamento_id):
        row = self.repo.fetch_departamento_by_id(departamento_id)
        return self._convert_departamento_to_dict(row)

    def update_departamento(self, departamento_id, name, id_departamento_padre):
        self.repo.update_departamento(departamento_id, name, id_departamento_padre)

    def get_areas_by_departamento(self, departamento_id=None, search=None):
        areas = self.repo.fetch_areas_by_departamento(departamento_id, search)
        return [self._convert_area_to_dict(area) for area in areas]
    
    def get_origenes_by_departamento(self, departamento_id=None, search=None):
        origenes = self.repo.fetch_origenes_by_departamento(departamento_id, search)
        return [self._convert_origen_to_dict(origen) for origen in origenes]
    
    def crear_area(self, name, id_departamento):
        return self.repo.crear_area(name, id_departamento)
    
    def crear_origen(self, name, id_departamento):
        return self.repo.crear_origen(name, id_departamento)
    
    def actualizar_area(self, area_id, name, id_departamento):
        self.repo.actualizar_area(area_id, name, id_departamento)
    
    def actualizar_origen(self, origen_id, name, id_departamento):
        self.repo.actualizar_origen(origen_id, name, id_departamento)
    
    def eliminar_area(self, area_id):
        self.repo.eliminar_area(area_id)
    
    def eliminar_origen(self, origen_id):
        self.repo.eliminar_origen(origen_id)

    def _convert_funcionario_to_dict(self, row):
        return {
            'id': row[0],  # Add the id attribute
            'rut': row[1],
            'name': row[2],
            'lastname': row[3],
            'profesion': row[4],
            'departamento_name': row[5],
            'nivel_jerarquico': row[6],
            'cargo': row[7],
            'correo': row[8],
            'anexo_telefonico': row[9]
        }

    def _convert_departamento_to_dict(self, row):
        return {
            'id': row[0],
            'name': row[1],
            'id_departamento_padre': row[2]
        }

    def _convert_departamento_to_dict_with_level(self, row):
        return {
            'id': row[0],
            'name': row[1],
            'id_departamento_padre': row[2],
            'level': row[3]
        }

    def _convert_area_to_dict(self, row):
        return {
            'id': row[0],
            'name': row[1],
            'id_departamento': row[2],
            'departamento_name': row[3]
        }
    
    def _convert_origen_to_dict(self, row):
        return {
            'id': row[0],
            'name': row[1],
            'id_departamento': row[2],
            'departamento_name': row[3]
        }
