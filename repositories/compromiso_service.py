# /services/compromiso_service.py
from repositories.compromiso_repository import CompromisoRepository

class CompromisoService:
    def __init__(self):
        self.repo = CompromisoRepository()

    def get_user_info(self, user_id):
        return self.repo.fetch_user_info(user_id)

    def get_director_info(self, user_id):
        return self.repo.fetch_director_info(user_id)

    def get_compromisos(self, user_id):
        director_info = self.repo.fetch_director_info(user_id)

        # Validar que se obtenga la información de director correctamente
        if not director_info:
            raise ValueError("No se pudo obtener la información del director")

        es_director = director_info['es_director']
        id_departamento = director_info['id_departamento']

        responsables = self.repo.fetch_responsables()

        responsables = [
            (p['id'], f"{p['name']} {p['lastname']} - {p['departamento']} - {p['position']}")
            for p in responsables
        ]
        # Si el usuario es director, obtener los compromisos del departamento
        if es_director:
            compromisos = self.repo.fetch_compromisos_by_departamento(id_departamento)
        else:
            # Si el usuario no es director, obtener los compromisos donde es responsable
            compromisos = self.repo.fetch_compromisos_by_responsable(user_id)

        # Retornar exactamente tres valores
        print(f"Compromisos: {compromisos}")
        print(f"Responsables: {responsables}")
        print(f"Es director: {es_director}")
        return compromisos, responsables, es_director

    def actualizar_compromisos(self, request, compromisos, user_id, es_director):
        for compromiso in compromisos:
            compromiso_id = compromiso['compromiso_id']

            # Obtener los valores enviados por el formulario
            nuevo_estado = request.form.get(f'estado-{compromiso_id}')
            nuevo_avance = request.form.get(f'nivel_avance-{compromiso_id}')
            nuevo_comentario = request.form.get(f'comentario-{compromiso_id}')
            nuevo_comentario_direccion = request.form.get(f'comentario_direccion-{compromiso_id}')

            # Si es director, obtener nuevos responsables
            if es_director:
                nuevos_responsables = request.form.getlist(f'responsables-{compromiso_id}')
            else:
                nuevos_responsables = compromiso['responsables_ids'].split(',')

            # Verificar los valores y actualizar el compromiso
            if nuevo_estado and nuevo_avance and nuevo_comentario:
                self.repo.update_compromiso(compromiso_id, nuevo_estado, nuevo_avance,nuevo_comentario, nuevo_comentario_direccion)
                self.repo.log_modificacion(compromiso_id, user_id)

                # Si es director, actualizar responsables
                if es_director and nuevos_responsables:
                    self.repo.update_responsables(compromiso_id, nuevos_responsables)

        self.repo.commit()

    def get_resumen_compromisos(self, month=None):
        departamentos = self.repo.fetch_departamentos_resumen(month)

        total_compromisos = sum(dep['total_compromisos'] for dep in departamentos)
        completados = sum(dep['completados'] for dep in departamentos)
        pendientes = sum(dep['pendientes'] for dep in departamentos)

        return total_compromisos, completados, pendientes, departamentos


    def convert_month_to_number(self, month):
        months = {
            "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5,
            "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9,
            "Octubre": 10, "Noviembre": 11, "Diciembre": 12
        }
        return months.get(month, None)

    def get_compromisos_by_mes_departamento(self, mes, departamento_id):
        # Filtrar compromisos por mes y departamento en el repositorio
        if mes == "Todos":
            return self.repo.fetch_compromisos_by_departamento(departamento_id)
        return self.repo.fetch_compromisos_by_mes_departamento(mes, departamento_id)

    def get_responsables(self):
        responsables = self.repo.fetch_responsables()
        return [
            (p['id'], f"{p['name']} {p['lastname']} - {p['departamento']} - {p['position']}")
            for p in responsables
        ]

    def get_compromisos_by_user(self, user_id):
        # Obtener los compromisos del usuario (director o no director)
        return self.repo.fetch_compromisos_by_responsable(user_id)

    def update_compromiso(self, compromiso_id, estado, avance, comentario, user_id,comentario_direccion,nuevos_responsables):
        # Actualizar los campos modificables por el usuario
        self.repo.update_compromiso(compromiso_id, estado, avance, comentario,comentario_direccion)
        self.repo.update_responsables(compromiso_id, nuevos_responsables)
        self.repo.log_modificacion(compromiso_id, user_id)
        self.repo.commit()

    def get_compromisos_by_departamento(self, departamento_id):
        """
        Obtener compromisos de un departamento.
        """
        return self.repo.fetch_compromisos_by_departamento(departamento_id)

    def get_compromisos_by_filtro(self, departamento_id=None, mes=None, area_id=None):
        # Si el mes es "Todos" o no está presente, no filtramos por mes
        if mes == "Todos":
            mes = None
        elif mes:
            mes = self.convert_month_to_number(mes)

        # Realizar la consulta en el repositorio con estos parámetros
        return self.repo.fetch_compromisos_by_filtro(departamento_id, mes, area_id)

    def get_resumen_compromisos(self, mes=None, area_id=None):
        """
        Obtiene el resumen de compromisos por departamento, incluyendo el total,
        los completados y los pendientes.
        """
        # Si el mes no es "Todos", convertirlo a número
        if mes and mes != "Todos":
            mes = self.convert_month_to_number(mes)

        # Llamar al repositorio para obtener el resumen por departamento
        departamentos_resumen = self.repo.fetch_departamentos_resumen(mes, area_id)

        # Calcular el total de compromisos, completados y pendientes globalmente
        total_compromisos = sum(dep['total_compromisos'] for dep in departamentos_resumen)
        total_completados = sum(dep['completados'] for dep in departamentos_resumen)
        total_pendientes = sum(dep['pendientes'] for dep in departamentos_resumen)

        return {
            'total_compromisos': total_compromisos,
            'completados': total_completados,
            'pendientes': total_pendientes,
            'departamentos': departamentos_resumen
        }

    def obtener_compromisos_por_mes_y_anio(self,mes, year=None):
        return self.repo.obtener_compromisos_por_mes_y_anio(mes, year)

    def get_areas(self):
        return self.repo.fetch_areas()  # Método para obtener todas las áreas

    def get_meses(self):
        return self.repo.fetch_meses()

    def get_all_compromisos(self):
        return self.repo.fetch_all_compromisos()
        pass



