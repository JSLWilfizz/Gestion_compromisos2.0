from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from repositories.compromiso_service import CompromisoService
from .auth_routes import is_director
from repositories.gestion_service import GestionService

director_bp = Blueprint('director', __name__)
compromiso_service = CompromisoService()
gestion_service = GestionService()

@director_bp.route('/director/resumen_compromisos', methods=['GET', 'POST'])
@is_director
def resumen_compromisos():
    mes = request.args.get('month', 'Todos')
    area_id = request.args.get('area_id')
    year = request.args.get('year', 'Todos')
    departamento_id = request.args.get('departamento_id', '')

    # Convertir area_id y departamento_id a entero si existen
    if area_id:
        area_id = int(area_id)
    if departamento_id:
        departamento_id = int(departamento_id)

    # Obtener el resumen de compromisos con todos los filtros
    resumen = compromiso_service.get_resumen_compromisos(mes, area_id, year, departamento_id)

    # Obtener todas las áreas y departamentos para los filtros
    areas = compromiso_service.get_areas()
    departamentos = compromiso_service.get_departamentos()

    return render_template('resumen_compromisos.html', 
                         resumen=resumen,
                         areas=areas,
                         departamentos=departamentos,
                         selected_area=area_id,
                         selected_mes=mes,
                         selected_year=year,
                         selected_departamento=departamento_id)

@director_bp.route('/director/ver_compromisos', methods=['GET', 'POST'])
@is_director
def ver_compromisos_director():
    # Obtener el mes y el departamento de los parámetros de consulta
    mes = request.args.get('month')
    departamento_id = request.args.get('departamento_id')
    year = request.args.get("year")

    # Comprobar si ambos parámetros están presentes
    print(mes, departamento_id)
    if not mes or not departamento_id:
        # Redirigir a la página de resumen si faltan parámetros
        flash("Faltan parámetros para filtrar los compromisos.", "error")
        return redirect(url_for('director.resumen_compromisos'))

    # Mapear el mes a su valor numérico
    mappeo_meses = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5,
        "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9,
        "Octubre": 10, "Noviembre": 11, "Diciembre": 12, "Todos": "Todos"
    }
    mes_numero = mappeo_meses.get(mes)
    print(year) 
    if request.method == 'POST':
        # Si se está enviando el formulario, procesar la actualización de los compromisos
        compromisos = compromiso_service.get_compromisos_by_mes_departamento(mes_numero, departamento_id, year)
        try:
            compromiso_service.actualizar_compromisos(request, compromisos, session['user_id'], es_director=True)
            flash("Los compromisos se han actualizado con éxito.", "success")
        except Exception as e:
            flash(f"Error al actualizar los compromisos: {str(e)}", "error")

        # Redirigir de nuevo a la misma página para evitar múltiples envíos del formulario
        return redirect(url_for('director.ver_compromisos_director', mes=mes, departamento_id=departamento_id))

    # Obtener los compromisos filtrados por mes y departamento
    compromisos = compromiso_service.get_compromisos_by_mes_departamento(mes_numero, departamento_id, year)
    print(f"Compromisos: {compromisos}")
    todos_referentes = compromiso_service.get_referentes()

    return render_template('director_ver_compromisos.html', compromisos=compromisos, todos_referentes=todos_referentes)

@director_bp.route('/director/compromisos_por_mes', methods=['GET', 'POST'])
@is_director
def resumen_compromisos_por_mes():
    month = request.args.get('month', None)
    year = request.args.get('year', None)

    print(year)

    if month and year:
        compromisos = compromiso_service.get_compromisos_by_month(month, year)
    else:
        compromisos = []

    return render_template('resumen_compromisos_mes.html', compromisos=compromisos, month=month, year=year)

@director_bp.route('/director/editar_compromisos', methods=['GET', 'POST'])
@is_director
def editar_compromisos():
    # Obtener filtros de mes, departamento y área
    departamento_id = request.args.get('departamento_id')
    mes = request.args.get('month')
    area_id = request.args.get('area_id')
    print(area_id,mes,departamento_id)

    # Obtener compromisos filtrados por mes, departamento y área
    compromisos = compromiso_service.get_compromisos_by_filtro(departamento_id, mes, area_id)

    # Obtener todos los referentes para mostrarlos en los select
    todos_referentes = compromiso_service.get_referentes()
    print(f"Comentarios: {compromisos[0]['comentario_direccion']}")

    if request.method == 'POST':
        # Si se envía el formulario, procesar la actualización
        compromiso_service.actualizar_compromisos(request, compromisos, session['user_id'], es_director=True)
        flash('Compromisos actualizados con éxito.', 'success')
        return redirect(
            url_for('director.resumen_compromisos', departamento_id=departamento_id, month=mes, area_id=area_id))

    return render_template('editar_compromisos.html', compromisos=compromisos, todos_referentes=todos_referentes)

@director_bp.route('/funcionarios', methods=['GET'])
def funcionarios():
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
        nivel_jerarquico=nivel_jerarquico
    )

@director_bp.route('/departamentos')
def departamentos():
    jerarquia = request.args.get('jerarquia', '').strip()
    all_departamentos = gestion_service.get_departamentos()
    departamentos = all_departamentos
    if jerarquia:
        jerarquia_chain = gestion_service.get_departamento_chain_by_name(jerarquia)
        departamentos = jerarquia_chain  # Display filtered departments in the main table
    return render_template(
        'departamentos.html',
        departamentos=departamentos,
        all_departamentos=all_departamentos,
        selected_jerarquia=jerarquia
    )

@director_bp.route('/director/editar_funcionario/<int:funcionario_id>', methods=['GET', 'POST'])
@is_director
def editar_funcionario(funcionario_id):
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
        flash('Funcionario actualizado con éxito.', 'success')
        return redirect(url_for('director.funcionarios'))

    return render_template('editar_funcionario.html', funcionario=funcionario, departamentos=departamentos, niveles_jerarquicos=niveles_jerarquicos)

@director_bp.route('/director/editar_departamento/<int:departamento_id>', methods=['GET', 'POST'])
@is_director
def editar_departamento(departamento_id):
    departamento = gestion_service.get_departamento_by_id(departamento_id)
    all_departamentos = gestion_service.get_departamentos()

    if request.method == 'POST':
        name = request.form.get('name')
        id_departamento_padre = request.form.get('id_departamento_padre')

        gestion_service.update_departamento(departamento_id, name, id_departamento_padre)
        flash('Departamento actualizado con éxito.', 'success')
        return redirect(url_for('director.departamentos'))

    return render_template('editar_departamento.html', departamento=departamento, all_departamentos=all_departamentos)