# /services/reunion_service.py
import re

from psutil import users

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
        responsables_choices = [
            (p['id'], f"{p['name']} {p['lastname']} - {p['departamento']} - {p['position']}")
            for p in personas
        ]
        form.compromisos[0].responsables.choices = responsables_choices

        # Cargar departamentos para el formulario de compromisos
        departamentos = self.repo.fetch_departamentos()
        form.compromisos[0].departamento.choices = [(d['id'], d['name']) for d in departamentos]

    def create_reunion(self, form, request_data, acta_pdf_path):
        origen_id = self.get_origen_id(form, request_data)
        area_id = self.get_area_id(form, request_data)

        if not origen_id:
            raise ValueError("El campo 'origen' es requerido")
        if not area_id:
            raise ValueError("El campo 'area' es requerido")

            # Obtener los asistentes como una lista
        asistentes_list = request_data.getlist('asistentes[]')
        temas_analizados = request_data.get('descripcion_markdown')
        name_list = []
        for asistentes in asistentes_list:
            if not asistentes:
                raise ValueError("El campo 'asistentes' es requerido")
            user = self.repo.fetch_user_info(asistentes)
            if not user:
                raise ValueError(f"No se encontró información del usuario con ID {asistentes}")
            name_list.append(f"{user['name']} {user['lastname']}")

        # Concatenar los asistentes en un único string separado por ";"
        asistentes_concatenados = ';'.join(name_list)
        correos_concatenados = []

        correo_pattern = re.compile(r'correo-\d+')  # Patrón para buscar "correo-{id}"

        for key, value in request_data.items():
            if correo_pattern.match(key) and value.strip():  # Si la clave coincide con el patrón y no está vacía
                correos_concatenados.append(value.strip())

        # Concatenar todos los correos con ";"
        correos_final = ';'.join(correos_concatenados)

        # Guardar o procesar los correos concatenados
        print("Correos concatenados:", correos_final)

        reunion_id = self.repo.insert_reunion(
            request_data.get('nombre_reunion'), area_id, origen_id, asistentes_concatenados,correos_final,temas_analizados, acta_pdf_path
        )

        # Iterar sobre la lista de formularios de compromisos
        for compromiso_form in form.compromisos:
            compromiso_id = self.create_compromiso(compromiso_form)
            self.repo.associate_reunion_compromiso(reunion_id, compromiso_id)

            # Acceder a los responsables correctamente como IDs
            for responsable_id in compromiso_form.responsables.data:
                self.repo.associate_persona_compromiso(responsable_id, compromiso_id)

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
