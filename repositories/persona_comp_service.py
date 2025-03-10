# ...existing code...
class PersonaCompService:
    def __init__(self, repository=None):
        # Ajusta la obtención de repo_persona al mecanismo que uses (inyección, imports, etc.)
        if repository:
            self.repo_persona = repository
        else:
            from repositories.persona_comp_repository import PersonaCompRepository
            self.repo_persona = PersonaCompRepository()
            
    def get_user_info(self, user_id):
        return self.repo_persona.get_user_info(user_id)

    def archivar_compromiso(self, compromiso_id, user_id):
        return self.repo_persona.archivar_compromiso(compromiso_id, user_id)

    def eliminar_compromiso(self, compromiso_id, user_id):
        return self.repo_persona.eliminar_compromiso(compromiso_id, user_id)

    def recuperar_compromiso(self, compromiso_id):
        return self.repo_persona.recuperar_compromiso(compromiso_id)

    def desarchivar_compromiso(self, compromiso_id):
        return self.repo_persona.desarchivar_compromiso(compromiso_id)

    def eliminar_permanentemente_compromiso(self, compromiso_id):
        return self.repo_persona.eliminar_permanentemente_compromiso(compromiso_id)

    def forzar_eliminacion_compromisos(self, compromiso_ids):
        return self.repo_persona.forzar_eliminacion_compromisos(compromiso_ids)

    def set_current_user_id(self, user_id):
        self.repo_persona.set_current_user_id(user_id)

    def get_compromisos_archivados(self):
        return self.repo_persona.get_compromisos_archivados()

    def get_compromisos_eliminados(self):
        return self.repo_persona.get_compromisos_eliminados()
    
    def create_compromiso(self, descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, user_id, origen=None, area=None):
        return self.repo_persona.create_compromiso(descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, user_id, origen, area)

    def asociar_referentes(self, compromiso_id, referentes):
        self.repo_persona.asociar_referentes(compromiso_id, referentes)

    def get_initial_form_data(self, form):
        departamentos = self.repo_persona.fetch_departamentos()
        referentes = self.repo_persona.fetch_referentes()

        form.id_departamento.choices = [(d['id'], d['name']) for d in departamentos]
        form.referentes.choices = [(r['id'], f"{r['name']} {r['lastname']} - {r['departamento']} - {r['profesion']}") for r in referentes]

        # Inicializar campos de origen y área con opciones vacías
        # Estos se cargarán dinámicamente cuando se seleccione un departamento
        if hasattr(form, 'origen'):
            form.origen.choices = [('', 'Seleccione un departamento primero')]
        
        if hasattr(form, 'area'):
            form.area.choices = [('', 'Seleccione un departamento primero')]

    def add_verificador(self, id_compromiso, nombre_archivo, ruta_archivo, descripcion, user_id):
        """
        Añade un verificador de compromiso
        """
        return self.repo_persona.add_verificador(id_compromiso, nombre_archivo, ruta_archivo, descripcion, user_id)

    def get_verificadores(self, id_compromiso):
        """
        Obtiene los verificadores de un compromiso
        """
        return self.repo_persona.get_verificadores(id_compromiso)

    def delete_verificador(self, verificador_id):
        """
        Elimina un verificador
        """
        return self.repo_persona.delete_verificador(verificador_id)
# ...existing code...
