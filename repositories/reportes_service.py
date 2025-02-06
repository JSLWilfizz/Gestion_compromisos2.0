from .reportes_repository import ReportesRepository

class ReportesService:
    def __init__(self):
        self.repo = ReportesRepository()

    def get_report_data(self):
        return {
            'total_compromisos': self.repo.get_total_compromisos(),
            'pendientes': self.repo.get_pendientes(),
            'completados': self.repo.get_completados(),
            'funcionarios': self.repo.get_funcionarios(),
            'departamentos': self.repo.get_departamentos(),
            'compromisos_por_departamento': self.repo.get_compromisos_por_departamento(),
            'personas_mas': self.repo.get_personas_mas(),
            'compromisos_por_dia': self.repo.get_compromisos_por_dia(),
            'total_reuniones': self.repo.get_total_reuniones(),
            'archived_compromisos': self.repo.get_archived_compromisos(),
            'deleted_compromisos': self.repo.get_deleted_compromisos(),
            'avg_compromisos_por_reunion': self.repo.get_avg_compromisos_por_reunion(),
            'percentage_completados': self.repo.get_percentage_completados(),
            'percentage_pendientes': self.repo.get_percentage_pendientes(),
            'percentage_completados_por_persona': self.repo.get_percentage_completados_por_persona(),
            'percentage_completados_por_departamento': self.repo.get_percentage_completados_por_departamento(),
            'compromisos_por_dia_por_departamento': self.repo.get_compromisos_por_dia_por_departamento(),
            'reuniones_por_dia': self.repo.get_reuniones_por_dia(),  # New key for meetings by day data
            'compromisos_por_jerarquia_departamento': self.repo.get_compromisos_por_jerarquia_departamento()  # New key for commitments by department hierarchy data
        }

    def get_reuniones_por_dia_filtered(self, day=None, month=None, year=None):
        return self.repo.get_reuniones_por_dia(day, month, year)

    def get_compromisos_por_dia_filtered(self, day=None, month=None, year=None):
        return self.repo.get_compromisos_por_dia(day, month, year)

    def get_personas_mas_filtered(self, search_name=None):
        return self.repo.get_personas_mas(search_name)
