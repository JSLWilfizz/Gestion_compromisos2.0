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

        referentes = self.repo.fetch_referentes()

        referentes = [
            (p['id'], f"{p['name']} {p['lastname']} - {p['departamento']} - {p['profesion']}")
            for p in referentes
        ]
        # Si el usuario es director, obtener los compromisos del departamento
        if (es_director):
            compromisos = self.repo.fetch_compromisos_by_departamento(id_departamento)
        else:
            # Si el usuario no es director, obtener los compromisos donde es referente
            compromisos = self.repo.fetch_compromisos_by_referente(user_id)

        # Retornar exactamente tres valores
        print(f"Compromisos: {compromisos}")
        print(f"Referentes: {referentes}")
        print(f"Es director: {es_director}")
        return compromisos, referentes, es_director

    def actualizar_compromisos(self, request, compromisos, user_id, es_director):
        for compromiso in compromisos:
            compromiso_id = compromiso['compromiso_id']

            # Obtener los valores enviados por el formulario
            nuevo_estado = request.form.get(f'estado-{compromiso_id}')
            nuevo_avance = request.form.get(f'nivel_avance-{compromiso_id}')
            nuevo_comentario = request.form.get(f'comentario-{compromiso_id}')
            nuevo_comentario_direccion = request.form.get(f'comentario_direccion-{compromiso_id}')

            # Si es director, obtener nuevos referentes
            if es_director:
                nuevos_referentes = request.form.getlist(f'referentes-{compromiso_id}')
            else:
                nuevos_referentes = compromiso['referentes_ids'].split(',')

            # Verificar los valores y actualizar el compromiso
            if nuevo_estado and nuevo_avance and nuevo_comentario:
                try:
                    self.update_compromiso(
                        compromiso_id,
                        compromiso['descripcion'],
                        nuevo_estado,
                        compromiso['prioridad'],
                        nuevo_avance,
                        nuevo_comentario,
                        nuevo_comentario_direccion,
                        user_id,  # Asegurar que user_id se pasa correctamente
                        nuevos_referentes  # Asegurar que referentes se pasa correctamente
                    )
                    self.repo.log_modificacion(compromiso_id, user_id)

                    # Si es director, actualizar referentes
                    if es_director and nuevos_referentes:
                        print("en espanol")
                        self.repo.update_referentes(compromiso_id, nuevos_referentes)
                    self.repo.commit()
                except Exception as e:
                    self.repo.rollback()
                    raise e



    def get_resumen_compromisos(self, mes=None, area_id=None, year=None, departamento_id=None):
        """
        Obtiene el resumen de compromisos por departamento, incluyendo el total,
        los completados y los pendientes.
        """
        # Si el mes no es "Todos", convertirlo a número
        if mes and mes != "Todos":
            mes = self.convert_month_to_number(mes)

        # Llamar al repositorio para obtener el resumen por departamento
        # Agregamos el parámetro year a la llamada
        departamentos_resumen = self.repo.fetch_departamentos_resumen(mes=mes, area_id=area_id, year=year, departamento_id=departamento_id)

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
        
    def convert_month_to_number(self, month):
        months = {
            "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5,
            "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9,
            "Octubre": 10, "Noviembre": 11, "Diciembre": 12
        }
        return months.get(month, None)

    def get_compromisos_by_mes_departamento(self, mes, departamento_id, year):
        """
        Obtiene compromisos por departamento aplicando filtros de mes y año.
        """
        # Manejar el caso 'Todos' para mes y año
        if mes == "Todos" and year == "Todos":
            return self.repo.fetch_compromisos_by_departamento(departamento_id)
        
        return self.repo.fetch_compromisos_by_mes_departamento(mes, departamento_id, year)
    
    def get_referentes(self):
        referentes = self.repo.fetch_referentes()
        return [
            (p['id'], f"{p['name']} {p['lastname']} - {p['departamento']} - {p['profesion']}")
            for p in referentes
        ]

    def get_compromisos_by_user(self, user_id):
        # Obtener los compromisos del usuario (director o no director)
        return self.repo.fetch_compromisos_by_referente(user_id)

    def update_compromiso(self, compromiso_id, descripcion, estado, prioridad, avance, comentario, comentario_direccion, user_id, referentes):
        self.repo.update_compromiso(compromiso_id, descripcion, estado, prioridad, avance, comentario, comentario_direccion, user_id, referentes)
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

    def obtener_compromisos_por_mes_y_anio(self,mes, year=None):
        return self.repo.obtener_compromisos_por_mes_y_anio(mes, year)

    def get_areas(self):
        return self.repo.fetch_areas()  # Método para obtener todas las áreas

    def get_meses(self):
        return self.repo.fetch_meses()
    
    def get_departamentos(self):
        return self.repo.fetch_departamentos()

    def get_all_compromisos(self):
        return self.repo.fetch_all_compromisos()
        pass

    def get_compromisos_compartidos(self, user_id, is_director, search='', estado='', avance='', fecha_limite=''):
        if not user_id:
            raise ValueError("Invalid user_id")
        return self.repo.fetch_compromisos_compartidos(user_id, is_director, search, estado, avance, fecha_limite)
    
    def es_jefe_de_departamento(self, user_id, departamento_id):
        return self.repo.es_jefe_de_departamento(user_id, departamento_id)

    def get_compromiso_by_id(self, compromiso_id):
        return self.repo.fetch_compromiso_by_id(compromiso_id)

    def create_compromiso(self, descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, user_id, referentes):
        self.repo.create_compromiso(descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, user_id, referentes)

    def get_initial_form_data(self, form):
        departamentos = self.get_departamentos()
        referentes = self.get_referentes()

        form.id_departamento.choices = [(d['id'], d['name']) for d in departamentos]
        form.referentes.choices = [(r[0], r[1]) for r in referentes]

    def set_current_user_id(self, user_id):
        self.repo.set_current_user_id(user_id)



