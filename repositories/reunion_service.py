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
        # Traza explícita de los valores antes de procesarlos
        print(f"DEBUG - origen_id y area_id antes de procesarlos: {request_data.get('origen')}, {request_data.get('area')}")
        
        # Arreglando la extracción de origen_id y area_id directamente del formulario
        origen_id = request_data.get('origen')
        area_id = request_data.get('area')
        
        # Verificar y convertir a entero si es necesario
        if origen_id and str(origen_id).strip():
            try:
                origen_id = int(origen_id)
            except ValueError:
                # Si no se puede convertir, posiblemente es un nuevo origen - intentar crear uno nuevo
                new_origen = request_data.get('new_origen', '')
                if new_origen.strip():
                    origen_id = self.repo.insert_origen(new_origen)
                else:
                    origen_id = None
        else:
            origen_id = None
            
        if area_id and str(area_id).strip():
            try:
                area_id = int(area_id)
            except ValueError:
                # Si no se puede convertir, posiblemente es una nueva área - intentar crear una nueva
                new_area = request_data.get('new_area', '')
                if new_area.strip():
                    area_id = self.repo.insert_area(new_area)
                else:
                    area_id = None
        else:
            area_id = None
            
        print(f"DEBUG - create_reunion procesados: origen_id={origen_id}, area_id={area_id}")

        # Validación para asegurar que tengamos valores
        if not origen_id:
            raise ValueError("El campo 'origen' es requerido")
        if not area_id:
            raise ValueError("El campo 'area' es requerido")
            
        # Verificar si hay al menos un compromiso
        compromisos_count = 0
        for key in request_data:
            if key.startswith('compromisos-') and key.endswith('-nombre'):
                if request_data.get(key).strip():
                    compromisos_count += 1
        
        if compromisos_count == 0:
            raise ValueError("Es necesario tener al menos un compromiso por reunión")

        name_list = []
        correo_list = []    
        # Obtener los asistentes existentes (se usan sus correos)
        asistentes_list = request_data.getlist('asistentes[]')
        for asistente_id in asistentes_list:
            user = self.repo.fetch_user_info(asistente_id)
            if not user:
                raise ValueError(f"No se encontró información del usuario con ID {asistente_id}")
            name_list.append(f"{user['name']} {user['lastname']}")
            correo_list.append(user['correo'] or '')

        # Procesar invitados para insertarlos en la tabla (sin afectar los correos finales)
        invitado_nombres = request_data.getlist('invitado-nombre')
        invitado_instituciones = request_data.getlist('invitado-institucion')
        invitado_correos = request_data.getlist('invitado-correo')
        invitado_telefonos = request_data.getlist('invitado-telefono')
        for i in range(len(invitado_nombres)):
            nombre = invitado_nombres[i]
            institucion = invitado_instituciones[i]
            correo = invitado_correos[i]
            telefono = invitado_telefonos[i] if i < len(invitado_telefonos) else ''
            if nombre and institucion and correo:
                self.repo.insert_invitado(nombre, institucion, correo, telefono)
                # Solo se agrega el nombre del invitado a la lista de asistentes
                name_list.append(nombre)

        asistentes_concatenados = ';'.join(name_list)
        correos_final = ';'.join(correo_list)

        # Debug de los valores finales
        print("Correos Final:", correos_final)
        print("Proximas reuniones concatenado:", proximas_reuniones_concatenado)

        lugar = request_data.get('lugar')
        temas = request_data.get('temas')
        proximas_fechas = request_data.get('proximas_fechas')

        tema_values = request_data.getlist('tema')
        descripcion_markdown_values = request_data.getlist('descripcion_markdown')
        proximas_reuniones_values = request_data.getlist('proximas_fechas')

        # Pasar origen_id y area_id a insert_reunion
        reunion_id = self.repo.insert_reunion(
            request_data.get('nombre_reunion'),
            area_id,  # Pasando el area_id procesado
            origen_id,  # Pasando el origen_id procesado
            asistentes_concatenados,
            correos_final,
            acta_pdf_path,
            lugar,
            tema_concatenado,
            temas_analizado_concatenado,
            proximas_reuniones_concatenado,
            fecha_creacion
        )

        # Iterar sobre la lista de formularios de compromisos
        for i, compromiso_form in enumerate(form.compromisos):
            # Obtener los valores específicos de origen y área para este compromiso desde el formulario
            index = i + 1  # Los índices de los compromisos empiezan en 1
            
            # Extraer los valores de origen y área específicos para este compromiso del request
            compromiso_origen_id = request_data.get(f'compromisos-{index}-origen', None)
            compromiso_area_id = request_data.get(f'compromisos-{index}-area', None)
            
            print(f"DEBUG - Compromiso #{index}: usando origen_id={compromiso_origen_id}, area_id={compromiso_area_id}")
            
            # Pasar los valores específicos de este compromiso
            compromiso_id = self.create_compromiso_con_origen_area(
                compromiso_form, 
                compromiso_origen_id, 
                compromiso_area_id
            )
            self.repo.associate_reunion_compromiso(reunion_id, compromiso_id)

            # Acceder a los referentes correctamente como IDs
            for referente_id in compromiso_form.referentes.data:
                self.repo.associate_persona_compromiso(referente_id, compromiso_id)

        self.repo.commit()

    # Nueva función para crear compromisos con origen y área
    def create_compromiso_con_origen_area(self, compromiso_form, origen_id, area_id):
        # Acceso correcto a los datos de los campos del formulario de compromisos
        if not compromiso_form.nombre.data:
            raise ValueError("El campo 'nombre' es requerido")
        if not compromiso_form.prioridad.data:
            raise ValueError("El campo 'prioridad' es requerido")
        if not compromiso_form.fecha_limite.data:
            raise ValueError("El campo 'fecha_limite' es requerido")
        if not compromiso_form.departamento.data:
            raise ValueError("El campo 'departamento' es requerido")
        
        # Verificar y convertir explícitamente los valores
        print(f"DEBUG - create_compromiso_con_origen_area recibió: origen_id={origen_id}, area_id={area_id}")
        
        # Asegurar que los valores sean enteros o None
        try:
            origen_id_clean = int(origen_id) if origen_id is not None else None
            area_id_clean = int(area_id) if area_id is not None else None
        except (ValueError, TypeError):
            print(f"ERROR - No se pudo convertir a entero: origen_id={origen_id}, area_id={area_id}")
            origen_id_clean = None
            area_id_clean = None
        
        print(f"DEBUG - Valores a enviar: origen_id={origen_id_clean}, area_id={area_id_clean}")
        
        # Pasar los valores origen_id y area_id a insert_compromiso
        return self.repo.insert_compromiso(
            compromiso_form.nombre.data,
            compromiso_form.prioridad.data,
            compromiso_form.fecha_limite.data,
            compromiso_form.departamento.data,
            0,  # Nivel de avance
            'Pendiente',
            datetime.now(),
            origen_id_clean,  # Usar valor limpio
            area_id_clean     # Usar valor limpio
        )

    # Mantener la función original create_compromiso para compatibilidad
    def create_compromiso(self, compromiso_form):
        return self.create_compromiso_con_origen_area(compromiso_form, None, None)

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

    def filtrar_reuniones(self, user_id, search, fecha, origen, tema, lugar, referente):
        return self.repo.filtrar_reuniones(user_id, search, fecha, origen, tema, lugar, referente)

    def get_origenes(self):
        return self.repo.fetch_origenes()

    def get_areas_by_departamento(self, departamento_id):
        """
        Obtener áreas asociadas a un departamento específico
        """
        return self.repo.fetch_areas_by_departamento(departamento_id)

    def get_origenes_by_departamento(self, departamento_id):
        """
        Obtener orígenes asociados a un departamento específico
        """
        return self.repo.fetch_origenes_by_departamento(departamento_id)
