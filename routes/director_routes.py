from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from repositories.compromiso_service import CompromisoService
from .auth_routes import not_funcionario_required
from repositories.gestion_service import GestionService
from repositories.reportes_service import ReportesService
from routes.auth_routes import not_funcionario_required  # Asegúrate de importar el decorador

director_bp = Blueprint('director', __name__)
compromiso_service = CompromisoService()
gestion_service = GestionService()
reportes_service = ReportesService()

def set_alert(message, alert_type='info'):
    session['alert'] = {'message': message, 'type': alert_type}


@director_bp.route('/director/resumen_compromisos', methods=['GET', 'POST'])
@not_funcionario_required
def resumen_compromisos():
    alert = session.pop('alert', None)
    mes = request.args.get('month', 'Todos')
    area_id = request.args.get('area_id')
    year = request.args.get('year', 'Todos')
    departamento_id = request.args.get('departamento_id', '')

    if area_id:
        area_id = int(area_id)
    if departamento_id:
        departamento_id = int(departamento_id)

    resumen = compromiso_service.get_resumen_compromisos(mes, area_id, year, departamento_id)
    areas = compromiso_service.get_areas()
    departamentos = compromiso_service.get_departamentos()

    return render_template('resumen_compromisos.html', 
                         resumen=resumen,
                         areas=areas,
                         departamentos=departamentos,
                         selected_area=area_id,
                         selected_mes=mes,
                         selected_year=year,
                         selected_departamento=departamento_id,
                         alert=alert)

@director_bp.route('/director/ver_compromisos', methods=['GET', 'POST'])
@not_funcionario_required
def ver_compromisos_director():
    alert = session.pop('alert', None)
    mes = request.args.get('month')
    departamento_id = request.args.get('departamento_id')
    year = request.args.get("year")

    if not mes or not departamento_id:
        set_alert("Faltan parámetros para filtrar los compromisos.", "danger")
        return redirect(url_for('director.resumen_compromisos'))

    mappeo_meses = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5,
        "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9,
        "Octubre": 10, "Noviembre": 11, "Diciembre": 12, "Todos": "Todos"
    }
    mes_numero = mappeo_meses.get(mes)

    if request.method == 'POST':
        compromisos = compromiso_service.get_compromisos_by_mes_departamento(mes_numero, departamento_id, year)
        try:
            compromiso_service.actualizar_compromisos(request, compromisos, session['user_id'], es_director=True)
            set_alert("Los compromisos se han actualizado con éxito.", "success")
        except Exception as e:
            set_alert(f"Error al actualizar los compromisos: {str(e)}", "danger")

        return redirect(url_for('director.ver_compromisos_director', month=mes, departamento_id=departamento_id, year=year))

    compromisos = compromiso_service.get_compromisos_by_mes_departamento(mes_numero, departamento_id, year)
    todos_referentes = compromiso_service.get_referentes()

    return render_template('director_ver_compromisos.html', compromisos=compromisos, todos_referentes=todos_referentes, alert=alert)

@director_bp.route('/director/compromisos_por_mes', methods=['GET', 'POST'])
@not_funcionario_required
def resumen_compromisos_por_mes():
    alert = session.pop('alert', None)
    month = request.args.get('month', None)
    year = request.args.get('year', None)

    print(year)

    if month and year:
        compromisos = compromiso_service.get_compromisos_by_month(month, year)
    else:
        compromisos = []

    return render_template('resumen_compromisos_mes.html', compromisos=compromisos, month=month, year=year, alert=alert)

@director_bp.route('/director/editar_compromisos', methods=['GET', 'POST'])
@not_funcionario_required
def editar_compromisos():
    alert = session.pop('alert', None)
    departamento_id = request.args.get('departamento_id')
    mes = request.args.get('month')
    area_id = request.args.get('area_id')
    print(area_id, mes, departamento_id)

    compromisos = compromiso_service.get_compromisos_by_filtro(departamento_id, mes, area_id)
    todos_referentes = compromiso_service.get_referentes()
    print(f"Comentarios: {compromisos[0]['comentario_direccion']}")

    if request.method == 'POST':
        compromiso_service.actualizar_compromisos(request, compromisos, session['user_id'], es_director=True)
        set_alert('Compromisos actualizados con éxito.', 'success')
        return redirect(
            url_for('director.resumen_compromisos', departamento_id=departamento_id, month=mes, area_id=area_id))

    return render_template('editar_compromisos.html', compromisos=compromisos, todos_referentes=todos_referentes, alert=alert)

@director_bp.route('/funcionarios', methods=['GET'])
def funcionarios():
    alert = session.pop('alert', None)
    search = request.args.get('search', '')
    departamento_raw = request.args.get('departamento', '')
    nivel_jerarquico = request.args.get('nivel_jerarquico', '')

    departamento = None
    if departamento_raw.strip():
        try:
            departamento = int(departamento_raw)
        except ValueError:
            departamento = None

    funcionarios = gestion_service.get_funcionarios(search, departamento, nivel_jerarquico)
    departamentos = gestion_service.get_departamentos()
    niveles_jerarquicos = gestion_service.get_niveles_jerarquicos()
    return render_template(
        'funcionarios.html',
        funcionarios=funcionarios,
        departamentos=departamentos,
        niveles_jerarquicos=niveles_jerarquicos,
        search=search,
        departamento=departamento_raw,
        nivel_jerarquico=nivel_jerarquico,
        alert=alert
    )

@director_bp.route('/departamentos')
def departamentos():
    alert = session.pop('alert', None)
    jerarquia = request.args.get('jerarquia', '').strip()
    all_departamentos = gestion_service.get_departamentos()
    departamentos = all_departamentos
    if (jerarquia):
        jerarquia_chain = gestion_service.get_departamento_chain_by_name(jerarquia)
        departamentos = jerarquia_chain
    return render_template(
        'departamentos.html',
        departamentos=departamentos,
        all_departamentos=all_departamentos,
        selected_jerarquia=jerarquia,
        alert=alert
    )

@director_bp.route('/director/editar_funcionario/<int:funcionario_id>', methods=['GET', 'POST'])
@not_funcionario_required
def editar_funcionario(funcionario_id):
    alert = session.pop('alert', None)
    funcionario = gestion_service.get_funcionario_by_id(funcionario_id)
    departamentos = gestion_service.get_departamentos()
    niveles_jerarquicos = gestion_service.get_niveles_jerarquicos()

    if request.method == 'POST':
        rut = request.form.get('rut')
        name = request.form.get('name')
        lastname = request.form.get('lastname')
        profesion = request.form.get('profesion')
        departamento_id = request.form.get('departamento')
        nivel_jerarquico = request.form.get('nivel_jerarquico')
        cargo = request.form.get('cargo')
        correo = request.form.get('correo')
        anexo_telefonico = request.form.get('anexo_telefonico')

        gestion_service.update_funcionario(funcionario_id, rut, name, lastname, profesion, departamento_id, nivel_jerarquico, cargo, correo, anexo_telefonico)
        set_alert('Funcionario actualizado con éxito.', 'success')
        return redirect(url_for('director.funcionarios'))

    return render_template('editar_funcionario.html', funcionario=funcionario, departamentos=departamentos, niveles_jerarquicos=niveles_jerarquicos, alert=alert)

@director_bp.route('/director/editar_departamento/<int:departamento_id>', methods=['GET', 'POST'])
@not_funcionario_required
def editar_departamento(departamento_id):
    alert = session.pop('alert', None)
    departamento = gestion_service.get_departamento_by_id(departamento_id)
    all_departamentos = gestion_service.get_departamentos()

    if request.method == 'POST':
        name = request.form.get('name')
        id_departamento_padre = request.form.get('id_departamento_padre')

        gestion_service.update_departamento(departamento_id, name, id_departamento_padre)
        set_alert('Departamento actualizado con éxito.', 'success')
        return redirect(url_for('director.departamentos'))

    return render_template('editar_departamento.html', departamento=departamento, all_departamentos=all_departamentos, alert=alert)

@director_bp.route('/api/report_data', methods=['GET'])
@not_funcionario_required
def get_report_data():
    try:
        # Get the user_id from session
        user_id = session.get('user_id')
        # Check if request wants unfiltered data (for admin/director)
        unfiltered = request.args.get('unfiltered', 'false').lower() == 'true'
        
        if unfiltered:
            report_data = reportes_service.get_report_data()
        else:
            report_data = reportes_service.get_report_data(user_id)
        
        return jsonify(report_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@director_bp.route('/director/reportes', methods=['GET'])
@not_funcionario_required
def reportes():
    alert = session.pop('alert', None)
    # Determine if the user has admin privileges to see the toggle for unfiltered data
    user_id = session.get('user_id')
    is_admin = False  # You could implement logic to determine if user is admin
    return render_template('reportes.html', alert=alert, is_admin=is_admin)

@director_bp.route('/director/origen-area', methods=['GET', 'POST'])
@not_funcionario_required
def origen_area():
    alert = session.pop('alert', None)
    departamento_id = request.args.get('departamento_id', None)
    search = request.args.get('search', '')
    departamentos = gestion_service.get_departamentos()
    
    # Get user from session directly - no need to fetch it again
    user = session.get('user', {})
    
    # Obtener áreas y orígenes, según los filtros seleccionados
    areas = gestion_service.get_areas_by_departamento(departamento_id, search)
    origenes = gestion_service.get_origenes_by_departamento(departamento_id, search)
    
    return render_template(
        'origen_area.html', 
        departamentos=departamentos, 
        areas=areas, 
        origenes=origenes,
        selected_departamento=departamento_id,
        search=search,
        alert=alert,
        user=user  # Pass the user from session to the template
    )

@director_bp.route('/director/crear-area', methods=['POST'])
@not_funcionario_required
def crear_area():
    name = request.form.get('name')
    departamento_id = request.form.get('departamento_id')
    
    if not name:
        set_alert('El nombre del área es obligatorio', 'danger')
        return redirect(url_for('director.origen_area', departamento_id=departamento_id))
    
    # Convert empty string to None for NULL in the database
    if departamento_id == '':
        departamento_id = None
    
    gestion_service.crear_area(name, departamento_id)
    set_alert('Área creada correctamente', 'success')
    return redirect(url_for('director.origen_area', departamento_id=departamento_id))

@director_bp.route('/director/crear-origen', methods=['POST'])
@not_funcionario_required
def crear_origen():
    name = request.form.get('name')
    departamento_id = request.form.get('departamento_id')
    
    if not name:
        set_alert('El nombre del origen es obligatorio', 'danger')
        return redirect(url_for('director.origen_area', departamento_id=departamento_id))
    
    # Convert empty string to None for NULL in the database
    if departamento_id == '':
        departamento_id = None
    
    gestion_service.crear_origen(name, departamento_id)
    set_alert('Origen creado correctamente', 'success')
    return redirect(url_for('director.origen_area', departamento_id=departamento_id))

@director_bp.route('/director/actualizar-area/<int:area_id>', methods=['POST'])
@not_funcionario_required
def actualizar_area(area_id):
    name = request.form.get('name')
    departamento_id = request.form.get('departamento_id')
    
    if not name:
        set_alert('El nombre del área es obligatorio', 'danger')
        return redirect(url_for('director.origen_area', departamento_id=departamento_id))
    
    # Convert empty string to None for NULL in the database
    if departamento_id == '':
        departamento_id = None
    
    gestion_service.actualizar_area(area_id, name, departamento_id)
    set_alert('Área actualizada correctamente', 'success')
    return redirect(url_for('director.origen_area', departamento_id=departamento_id))

@director_bp.route('/director/actualizar-origen/<int:origen_id>', methods=['POST'])
@not_funcionario_required
def actualizar_origen(origen_id):
    name = request.form.get('name')
    departamento_id = request.form.get('departamento_id')
    
    if not name:
        set_alert('El nombre del origen es obligatorio', 'danger')
        return redirect(url_for('director.origen_area', departamento_id=departamento_id))
    
    # Convert empty string to None for NULL in the database
    if departamento_id == '':
        departamento_id = None
    
    gestion_service.actualizar_origen(origen_id, name, departamento_id)
    set_alert('Origen actualizado correctamente', 'success')
    return redirect(url_for('director.origen_area', departamento_id=departamento_id))

@director_bp.route('/director/eliminar-area/<int:area_id>', methods=['POST'])
@not_funcionario_required
def eliminar_area(area_id):
    departamento_id = request.form.get('departamento_id')
    gestion_service.eliminar_area(area_id)
    set_alert('Área eliminada correctamente', 'success')
    return redirect(url_for('director.origen_area', departamento_id=departamento_id))

@director_bp.route('/director/eliminar-origen/<int:origen_id>', methods=['POST'])
@not_funcionario_required
def eliminar_origen(origen_id):
    departamento_id = request.form.get('departamento_id')
    gestion_service.eliminar_origen(origen_id)
    set_alert('Origen eliminado correctamente', 'success')
    return redirect(url_for('director.origen_area', departamento_id=departamento_id))
