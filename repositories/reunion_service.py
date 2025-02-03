from repositories.reunion_repository import ReunionRepository
from datetime import datetime


class ReunionService:
    def __init__(self):
        self.repo = ReunionRepository()

    def get_origen_id(self, form, request_data):
        new_origen = request_data.get('new_origen')
        if new_origen:
            return self.repo.insert_origen(new_origen)
        return form.origen.data

    def get_area_id(self, form, request_data):
        new_area = request_data.get('new_area')
        if new_area:
            return self.repo.insert_area(new_area)
        return form.area.data

    def get_user_info(self, user_id):
        return self.repo.fetch_user_info(user_id)

    def get_initial_form_data(self, form):
        origenes = self.repo.fetch_origenes()
        form.origen.choices = [(o['id'], o['name']) for o in origenes]

        areas = self.repo.fetch_areas()
        form.area.choices = [(a['id'], a['name']) for a in areas]

        personas = self.repo.fetch_personas()
        referentes_choices = [
            (p['id'], f"{p['name']} {p['lastname']}", p['departamento'], p['cargo'])
            for p in personas
        ]
        form.compromisos[0].referentes.choices = referentes_choices

        # Cargar departamentos para el formulario de compromisos
        departamentos = self.repo.fetch_departamentos()
        form.compromisos[0].departamento.choices = [(d['id'], d['name']) for d in departamentos]

        invitados = self.repo.fetch_invitados()
        form.invitados.choices = [(i['id_invitado'], f"{i['nombre_completo']} - {i['institucion']} - {i['correo']} - {i['telefono']}") for i in invitados]

    def create_reunion(self, form, request_data, acta_pdf_path, tema_concatenado, temas_analizado_concatenado, proximas_reuniones_concatenado, fecha_creacion, fecha_limite):
        origen_id = self.get_origen_id(form, request_data)
        area_id = self.get_area_id(form, request_data)

        if not origen_id:
            raise ValueError("El campo 'origen' es requerido")
        if not area_id:
            raise ValueError("El campo 'area' es requerido")

        name_list = []
        departamento_list = []
        profesion_list = []
        correo_list = []    
        # Obtener los asistentes existentes
        asistentes_list = request_data.getlist('asistentes[]')
        for asistente_id in asistentes_list:
            user = self.repo.fetch_user_info(asistente_id)
            if not user:
                raise ValueError(f"No se encontró información del usuario con ID {asistente_id}")
            name_list.append(f"{user['name']} {user['lastname']}")
            departamento_list.append(user['departamento'] or '')
            profesion_list.append(user['profesion'] or '')

        # Recoger invitados y crearlos en la tabla persona
        invitado_nombres = request_data.getlist('invitado-nombre')
        invitado_instituciones = request_data.getlist('invitado-institucion')
        invitado_correos = request_data.getlist('invitado-correo')

        for i in range(len(invitado_nombres)):
            nombre = invitado_nombres[i]
            institucion = invitado_instituciones[i]
            correo = invitado_correos[i]
            if nombre and institucion and correo:
                invitado_id = self.repo.insert_invitado(nombre, institucion, correo)
                invitado_user = self.repo.fetch_user_info(invitado_id)
                name_list.append(f"{invitado_user['name']} {invitado_user['lastname']}")
                correo_list.append(invitado_user['correo'] or '')

        asistentes_concatenados = ';'.join(name_list)
        correos_final = ';'.join(correo_list)

        lugar = request_data.get('lugar')
        temas = request_data.get('temas')
        proximas_fechas = request_data.get('proximas_fechas')

        tema_values = request_data.getlist('tema')
        descripcion_markdown_values = request_data.getlist('descripcion_markdown')
        proximas_reuniones_values = request_data.getlist('proximas_fechas')

        reunion_id = self.repo.insert_reunion(
            request_data.get('nombre_reunion'),
            area_id,
            origen_id,
            asistentes_concatenados,
            correos_final,
            acta_pdf_path,  # now possibly contains multiple paths separated by semicolons
            lugar,
            tema_concatenado,
            temas_analizado_concatenado,
            proximas_reuniones_concatenado,
            fecha_creacion
        )

        # Iterar sobre la lista de formularios de compromisos
        for compromiso_form in form.compromisos:
            compromiso_id = self.create_compromiso(compromiso_form)
            self.repo.associate_reunion_compromiso(reunion_id, compromiso_id)

            # Acceder a los referentes correctamente como IDs
            for referente_id in compromiso_form.referentes.data:
                self.repo.associate_persona_compromiso(referente_id, compromiso_id)

        self.repo.commit()

    def create_compromiso(self, compromiso_form):
        # Acceso correcto a los datos de los campos del formulario de compromisos
        if not compromiso_form.nombre.data:
            raise ValueError("El campo 'nombre' es requerido")
        if not compromiso_form.prioridad.data:
            raise ValueError("El campo 'prioridad' es requerido")
        if not compromiso_form.fecha_limite.data:
            raise ValueError("El campo 'fecha_limite' es requerido")
        if not compromiso_form.departamento.data:
            raise ValueError("El campo 'departamento' es requerido")
        return self.repo.insert_compromiso(
            compromiso_form.nombre.data,
            compromiso_form.prioridad.data,
            compromiso_form.fecha_limite.data,
            compromiso_form.departamento.data,
            0,  # Nivel de avance
            'Pendiente',
            datetime.now()
        )

    def get_origen_id(self, form, request_data):
        new_origen = request_data.get('new_origen')
        if new_origen:
            return self.repo.insert_origen(new_origen)
        return form.origen.data

    def get_area_id(self, form, request_data):
        new_area = request_data.get('new_area')
        if new_area:
            return self.repo.insert_area(new_area)
        return form.area.data

    def get_origen_name(self, origen_id):
        return self.repo.fetch_origen_name(origen_id)

    def get_area_name(self, area_id):
        return self.repo.fetch_area_name(area_id)

    def get_mis_reuniones(self, user_id):
        return self.repo.fetch_mis_reuniones(user_id)

    def get_compromisos_por_reunion(self, reunion_id):
        return self.repo.fetch_compromisos_by_reunion(reunion_id)

    def add_invitado(self, nombre, institucion, correo, telefono):
        return self.repo.insert_invitado(nombre, institucion, correo, telefono)

    def get_reunion_by_compromiso_id(self, compromiso_id):
        return self.repo.fetch_reunion_by_compromiso_id(compromiso_id)
    
    def get_reunion_by_id(self, reunion_id):
        return self.repo.fetch_reunion_by_id(reunion_id)
