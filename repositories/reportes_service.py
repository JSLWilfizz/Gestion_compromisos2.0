from .reportes_repository import ReportesRepository

class ReportesService:
    def __init__(self):
        self.repo = ReportesRepository()

    def get_report_data(self, user_id=None):
        # If user_id is provided, filter by department hierarchy
        if user_id:
            return self.get_filtered_report_data(user_id)
        # Otherwise, return all data (for admin/director)
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
            'compromisos_por_jerarquia_departamento': self.repo.get_compromisos_por_jerarquia_departamento(),  # New key for commitments by department hierarchy data
            'user_is_filtered': False
        }
    
    def get_filtered_report_data(self, user_id):
        # Get user's department hierarchy
        dept_hierarchy = self.repo.get_user_department_hierarchy(user_id)
        if not dept_hierarchy:
            # If user doesn't belong to any department, return all data
            data = self.get_report_data()
            data['user_is_filtered'] = False
            return data
            
        # Get list of department IDs
        dept_ids = [d['id'] for d in dept_hierarchy]
        
        # Get filtered data
        total_compromisos = self.repo.get_total_compromisos_by_dept_hierarchy(dept_ids)
        pendientes = self.repo.get_pendientes_by_dept_hierarchy(dept_ids)
        completados = self.repo.get_completados_by_dept_hierarchy(dept_ids)
        
        # Calculate percentages
        percentage_pendientes = (pendientes * 100.0 / total_compromisos) if total_compromisos > 0 else 0
        percentage_completados = (completados * 100.0 / total_compromisos) if total_compromisos > 0 else 0
        
        # Get number of employees in the department hierarchy
        funcionarios_by_dept = self.repo.get_funcionarios_by_dept_hierarchy(dept_ids)
        
        return {
            'total_compromisos': total_compromisos,
            'pendientes': pendientes,
            'completados': completados,
            'funcionarios': funcionarios_by_dept,  # Now filtered by department hierarchy
            'departamentos': len(dept_hierarchy),
            'compromisos_por_departamento': self.repo.get_compromisos_por_departamento_filtered(dept_ids),
            'personas_mas': self.repo.get_personas_mas_by_dept_hierarchy(dept_ids),
            'compromisos_por_dia': self.repo.get_compromisos_por_dia_by_dept_hierarchy(dept_ids),
            'total_reuniones': self.repo.get_total_reuniones(),  # Could be filtered but difficult to associate meetings with departments
            'archived_compromisos': self.repo.get_archived_compromisos(),  # Could be filtered but not necessary
            'deleted_compromisos': self.repo.get_deleted_compromisos(),  # Could be filtered but not necessary
            'avg_compromisos_por_reunion': self.repo.get_avg_compromisos_por_reunion(),  # Could be filtered but not necessary
            'percentage_completados': percentage_completados,
            'percentage_pendientes': percentage_pendientes,
            'percentage_completados_por_persona': self.repo.get_percentage_completados_por_persona(),  # Could be filtered but not necessary
            'percentage_completados_por_departamento': self.repo.get_percentage_completados_por_departamento(),  # Could be filtered but not necessary
            'compromisos_por_dia_por_departamento': self.repo.get_compromisos_por_dia_por_departamento_filtered(dept_ids),
            'reuniones_por_dia': self.repo.get_reuniones_por_dia_filtered_by_dept(dept_ids),
            'compromisos_por_jerarquia_departamento': self.repo.get_compromisos_por_jerarquia_departamento_filtered(dept_ids),
            'user_dept_hierarchy': dept_hierarchy,
            'user_is_filtered': True
        }

    def get_reuniones_por_dia_filtered(self, day=None, month=None, year=None):
        return self.repo.get_reuniones_por_dia(day, month, year)

    def get_compromisos_por_dia_filtered(self, day=None, month=None, year=None):
        return self.repo.get_compromisos_por_dia(day, month, year)

    def get_personas_mas_filtered(self, search_name=None):
        return self.repo.get_personas_mas(search_name)
