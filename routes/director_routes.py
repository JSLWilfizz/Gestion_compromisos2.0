from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from repositories.compromiso_service import CompromisoService
from .auth_routes import is_director


director_bp = Blueprint('director', __name__)
compromiso_service = CompromisoService()


@director_bp.route('/director/resumen_compromisos', methods=['GET', 'POST'])
@is_director
def resumen_compromisos():
    mes = request.args.get('month', 'Todos')
    area_id = request.args.get('area_id', None)
    year = request.args.get('year','Todos')
    print(year)
    # Obtener el resumen de compromisos filtrados por departamento, mes y área
    resumen = compromiso_service.get_resumen_compromisos(mes, area_id)

    print(resumen)

    # Obtener todas las áreas para el filtro
    areas = compromiso_service.get_areas()

    # Definir los meses disponibles manualmente
    meses = ['Todos', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

    # Convertir area_id a entero si existe, para compararlo correctamente con el ID del área
    if area_id:
        area_id = int(area_id)

    return render_template('resumen_compromisos.html', resumen=resumen, areas=areas, meses=meses, selected_area=area_id, selected_mes=mes)


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
        compromisos = compromiso_service.get_compromisos_by_mes_departamento(mes_numero, departamento_id,year)
        try:

            compromiso_service.actualizar_compromisos(request, compromisos, session['user_id'], es_director=True)
            flash("Los compromisos se han actualizado con éxito.", "success")
        except Exception as e:
            flash(f"Error al actualizar los compromisos: {str(e)}", "error")

        # Redirigir de nuevo a la misma página para evitar múltiples envíos del formulario
        return redirect(url_for('director.ver_compromisos_director', mes=mes, departamento_id=departamento_id))

    # Obtener los compromisos filtrados por mes y departamento
    compromisos = compromiso_service.get_compromisos_by_mes_departamento(mes_numero, departamento_id)
    print(f"Compromisos: {compromisos}")
    todos_responsables = compromiso_service.get_responsables()

    return render_template('director_ver_compromisos.html', compromisos=compromisos, todos_responsables=todos_responsables)



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

    # Obtener todos los responsables para mostrarlos en los select
    todos_responsables = compromiso_service.get_responsables()
    print(f"Comentarios: {compromisos[0]['comentario_direccion']}")

    if request.method == 'POST':
        # Si se envía el formulario, procesar la actualización
        compromiso_service.actualizar_compromisos(request, compromisos, session['user_id'], es_director=True)
        flash('Compromisos actualizados con éxito.', 'success')
        return redirect(
            url_for('director.resumen_compromisos', departamento_id=departamento_id, month=mes, area_id=area_id))

    return render_template('editar_compromisos.html', compromisos=compromisos, todos_responsables=todos_responsables)