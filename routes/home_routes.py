# /routes/home_routes.py
import traceback
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from flask_login import login_required
from repositories.compromiso_service import CompromisoService
from repositories.reunion_service import ReunionService
from repositories.persona_comp_service import PersonaCompService
from .auth_routes import login_required
from forms import CompromisoForm, CreateCompromisoForm
from exceptions.compromiso_exceptions import ResponsablePrincipalError

home = Blueprint('home', __name__)
compromiso_service = CompromisoService()
reunion_service = ReunionService()
persona_comp_service = PersonaCompService()


@home.route('/')
def redirect_home():
    return redirect(url_for('home.home_view'))


@home.route('/home')
@login_required
def home_view():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    print(f"User ID: {user_id}")
    user = compromiso_service.get_user_info(user_id)
    es_director_info = compromiso_service.get_director_info(user_id)
    if user['cargo'] == 'DIRECTOR DE SERVICIO':
        the_big_boss = True
        session['the_big_boss'] = the_big_boss
        es_director = True
    else:
        the_big_boss = False
        es_director_info = compromiso_service.get_director_info(user_id)
        es_director = es_director_info['es_director']
        session['es_director'] = es_director  # Guardamos esta info en la sesión

    if not user:
        return redirect(url_for('auth.login'))

    return render_template('home.html', user=user, es_director=es_director,the_big_boss=the_big_boss)


@home.route('/ver_compromisos', methods=['GET', 'POST'])
@login_required
def ver_compromisos():
    if request.method == 'POST':
        compromiso_id = request.form.get('compromiso_id')
        if compromiso_id:
            try:
                compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
                if not compromiso:
                    flash('Compromiso no encontrado.', 'danger')
                    return redirect(url_for('home.ver_compromisos'))

                user_id = session['user_id']
                es_director = session.get('es_director')
                the_big_boss = session.get('the_big_boss')

                # Verificar permisos
                if not (es_director or the_big_boss or compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento'])):
                    flash('No tienes permiso para actualizar este compromiso.', 'danger')
                    return redirect(url_for('home.ver_compromisos'))

                # Obtener los nuevos valores del formulario
                nuevo_estado = request.form.get('estado')
                nuevo_avance = request.form.get('nivel_avance')
                nuevo_comentario = request.form.get('comentario')
                comentario_director = request.form.get('comentario_direccion')

                if es_director or the_big_boss:
                    nuevos_referentes = request.form.getlist('referentes')
                    if not nuevos_referentes:
                        nuevos_referentes = compromiso['referentes_ids']
                else:
                    nuevos_referentes = compromiso['referentes_ids']
                    comentario_director = compromiso['comentario_direccion']

                # Actualizar el compromiso
                compromiso_service.update_compromiso(
                    compromiso_id=compromiso_id,
                    descripcion=compromiso['descripcion'],
                    estado=nuevo_estado,
                    prioridad=compromiso['prioridad'],
                    avance=nuevo_avance,
                    comentario=nuevo_comentario,
                    comentario_direccion=comentario_director,
                    referentes=nuevos_referentes,
                    user_id=user_id
                )

                flash('Compromiso actualizado con éxito.', 'success')
            except Exception as e:
                print(e)
                flash(f'Error al actualizar el compromiso: {str(e)}', 'danger')

        return redirect(url_for('home.ver_compromisos'))

    # Si es un GET, obtener los compromisos para mostrar
    user_id = session['user_id']
    es_director = session.get('es_director')
    the_big_boss = session.get('the_big_boss')

    if es_director:
        compromisos = compromiso_service.get_compromisos_by_departamento(compromiso_service.get_director_info(user_id)['id_departamento'])
    elif the_big_boss:
        compromisos = compromiso_service.get_all_compromisos()
    else:
        compromisos = compromiso_service.get_compromisos_by_user(user_id)

    todos_referentes = compromiso_service.get_referentes()

    return render_template(
        'ver_compromisos.html',
        compromisos=compromisos,
        todos_referentes=todos_referentes,
        es_director=es_director,
        the_big_boss=the_big_boss,
        user_id=user_id,
        user=compromiso_service.get_user_info(user_id)  # Pass the user variable to the template
    )

@home.route('/ver_compromisos_compartidos')
@login_required
def ver_compromisos_compartidos():
    user_id = session['user_id']
    es_director = session.get('es_director')
    the_big_boss = session.get('the_big_boss')
    user = compromiso_service.get_user_info(user_id)
    
    # Obtener parámetros de búsqueda y filtro
    search = request.args.get('search', '')
    estado = request.args.get('estado', '')
    avance = request.args.get('avance', '')
    fecha_limite = request.args.get('fecha_limite', '')

    # Obtener compromisos compartidos con filtros aplicados
    compromisos_compartidos = compromiso_service.get_compromisos_compartidos(user_id, the_big_boss or es_director, search, estado, avance, fecha_limite)
    for comp in compromisos_compartidos:
        reunion_item = reunion_service.get_reunion_by_compromiso_id(comp['compromiso_id'])
        comp['tiene_reunion'] = bool(reunion_item)
    
    return render_template('ver_compromisos_compartidos.html', compromisos=compromisos_compartidos, user=user)

@home.route('/editar_compromiso/<int:compromiso_id>', methods=['GET', 'POST'])
@login_required
def editar_compromiso(compromiso_id):
    try:
        user_id = session['user_id']
        user = compromiso_service.get_user_info(user_id)
        compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
        todos_referentes = compromiso_service.get_referentes()
        direccion = session.get('the_big_boss') or session.get('es_director')

        # Verificar si el usuario es el jefe del departamento correspondiente al compromiso
        if not (compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento']) or direccion):
            flash('No tienes permiso para editar este compromiso.', 'danger')
            return redirect(url_for('home.ver_compromisos_compartidos'))

        if request.method == 'POST':
            descripcion = request.form.get('descripcion')
            estado = request.form.get('estado')
            prioridad = request.form.get('prioridad')
            avance = request.form.get('avance')
            fecha_limite = request.form.get('fecha_limite')
            referentes = request.form.getlist('referentes')
            comentario = request.form.get('comentario')
            comentario_direccion = request.form.get('comentario_direccion')

            try:
                compromiso_service.update_compromiso(
                    compromiso_id, descripcion, estado, prioridad, avance, comentario, 
                    comentario_direccion, user_id, referentes
                )
                flash('Compromiso actualizado con éxito.', 'success')
                return redirect(url_for('home.ver_compromisos_compartidos'))
            except ResponsablePrincipalError:
                flash('Error: No se puede eliminar al responsable principal del compromiso. ' 
                      'Por favor, asegúrese de mantener al responsable principal en la lista de referentes.', 'error')
                return redirect(request.url)

    except Exception as e:
        flash(f'Error inesperado: {str(e)}', 'error')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    return render_template('editar_derivar_compromiso.html', 
                           compromiso=compromiso, 
                           todos_referentes=todos_referentes,
                           direccion=direccion,
                           title="Editar Compromiso",
                           derivar=False)

@home.route('/derivar_compromiso/<int:compromiso_id>', methods=['GET', 'POST'])
@login_required
def derivar_compromiso(compromiso_id):
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
    todos_referentes = compromiso_service.get_referentes()
    direccion = session.get('the_big_boss') or session.get('es_director')

    # Verificar si el usuario es el jefe del departamento correspondiente al compromiso
    if not (compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento']) or direccion):
        flash('No tienes permiso para derivar este compromiso.', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    if request.method == 'POST':
        referentes = request.form.getlist('referentes')

        compromiso_service.update_referentes(compromiso_id, referentes)
        flash('Compromiso derivado con éxito.', 'success')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    return render_template('editar_derivar_compromiso.html', 
                           compromiso=compromiso, 
                           todos_referentes=todos_referentes,
                           direccion=direccion,
                           title="Derivar Compromiso",
                           derivar=True)

@home.route('/resumen_compromisos', methods=['GET'])
@login_required
def resumen_compromisos():
    user_id = session['user_id']
    es_director = session.get('es_director')
    the_big_boss = session.get('the_big_boss')

    # Obtener los parámetros de filtro
    selected_mes = request.args.get('month', 'Todos')
    selected_year = request.args.get('year', 'Todos')
    selected_area = request.args.get('area_id', '')
    selected_departamento = request.args.get('departamento_id', '')

    # Obtener el resumen de compromisos filtrado
    resumen = compromiso_service.get_resumen_compromisos(
        mes=selected_mes,
        area_id=selected_area,
        year=selected_year,
        departamento_id=selected_departamento
    )

    # Obtener las áreas y departamentos para los filtros
    areas = compromiso_service.get_areas()
    departamentos = compromiso_service.get_departamentos()

    return render_template(
        'resumen_compromisos.html',
        resumen=resumen,
        areas=areas,
        departamentos=departamentos,
        selected_mes=selected_mes,
        selected_year=selected_year,
        selected_area=selected_area,
        selected_departamento=selected_departamento
    )

@home.route('/mis_reuniones')
@login_required
def mis_reuniones():
    user_id = session['user_id']
    reuniones = reunion_service.get_mis_reuniones(user_id)
    return render_template('mis_reuniones.html', reuniones=reuniones)

@home.route('/mis_reuniones/compromisos/<int:reunion_id>')
@login_required
def ver_compromisos_reunion(reunion_id):
    compromisos = reunion_service.get_compromisos_por_reunion(reunion_id)
    return render_template('compromisos_reuniones.html', compromisos=compromisos)

@home.route('/eliminar_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def eliminar_compromiso(compromiso_id):
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)

    # Verificar si el usuario tiene permiso para eliminar el compromiso
    if not (compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento']) or session.get('the_big_boss') or session.get('es_director')):
        flash('No tienes permiso para eliminar este compromiso.', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    try:
        # Establecer el id_persona en el contexto de la sesión
        persona_comp_service.set_current_user_id(user_id)
        
        # Eliminar el compromiso usando el servicio
        persona_comp_service.eliminar_compromiso(compromiso_id, user_id)
        flash('Compromiso eliminado con éxito.', 'success')
    except Exception as e:
        print(f"Error al eliminar el compromiso: {e}")
        traceback.print_exc()
        flash(f'Error al eliminar el compromiso: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_compartidos'))

@home.route('/ver_compromisos_eliminados')
@login_required
def ver_compromisos_eliminados():
    user_id = session['user_id']
    if not session.get('the_big_boss'):
        flash('No tienes permiso para ver los compromisos eliminados.', 'danger')
        return redirect(url_for('home.home_view'))

    compromisos_eliminados = persona_comp_service.get_compromisos_eliminados()
    return render_template('ver_compromisos_eliminados.html', compromisos=compromisos_eliminados)

@home.route('/archivar_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def archivar_compromiso(compromiso_id):
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)

    # Verificar si el usuario tiene permiso para archivar el compromiso
    if not (compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento']) or session.get('the_big_boss') or session.get('es_director')):
        flash('No tienes permiso para archivar este compromiso.', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    try:
        # Establecer el id_persona en el contexto de la sesión
        persona_comp_service.set_current_user_id(user_id)
        
        # Archivar el compromiso usando el servicio
        persona_comp_service.archivar_compromiso(compromiso_id, user_id)
        flash('Compromiso archivado con éxito.', 'success')
    except Exception as e:
        flash(f'Error al archivar el compromiso: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_compartidos'))

@home.route('/ver_compromisos_archivados')
@login_required
def ver_compromisos_archivados():
    user_id = session['user_id']
    if not session.get('the_big_boss'):
        flash('No tienes permiso para ver los compromisos archivados.', 'danger')
        return redirect(url_for('home.home_view'))

    compromisos_archivados = persona_comp_service.get_compromisos_archivados()
    return render_template('ver_compromisos_archivados.html', compromisos=compromisos_archivados)

@home.route('/desarchivar_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def desarchivar_compromiso(compromiso_id):
    user_id = session['user_id']
    if not session.get('the_big_boss'):
        flash('No tienes permiso para desarchivar este compromiso.', 'danger')
        return redirect(url_for('home.home_view'))

    try:
        persona_comp_service.desarchivar_compromiso(compromiso_id)
        flash('Compromiso desarchivado con éxito.', 'success')
    except Exception as e:
        flash(f'Error al desarchivar el compromiso: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_archivados'))

@home.route('/eliminar_permanentemente_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def eliminar_permanentemente_compromiso(compromiso_id):
    user_id = session['user_id']
    if not session.get('the_big_boss'):
        flash('No tienes permiso para eliminar permanentemente este compromiso.', 'danger')
        return redirect(url_for('home.home_view'))

    try:
        persona_comp_service.eliminar_permanentemente_compromiso(compromiso_id)
        flash('Compromiso eliminado permanentemente con éxito.', 'success')
    except Exception as e:
        print(f"Error al eliminar permanentemente el compromiso: {e}")
        traceback.print_exc()
        flash(f'Error al eliminar permanentemente el compromiso: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_eliminados'))

@home.route('/forzar_eliminacion_compromisos', methods=['POST'])
@login_required
def forzar_eliminacion_compromisos():
    try:
        compromiso_ids = [20, 21]
        persona_comp_service.forzar_eliminacion_compromisos(compromiso_ids)
        flash('Compromisos eliminados forzosamente con éxito.', 'success')
    except Exception as e:
        print(f"Error al forzar la eliminación de los compromisos: {e}")
        traceback.print_exc()
        flash(f'Error al forzar la eliminación de los compromisos: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_compartidos'))

@home.route('/recuperar_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def recuperar_compromiso(compromiso_id):
    user_id = session['user_id']
    if not session.get('the_big_boss'):
        flash('No tienes permiso para recuperar este compromiso.', 'danger')
        return redirect(url_for('home.home_view'))

    try:
        persona_comp_service.recuperar_compromiso(compromiso_id)
        flash('Compromiso recuperado con éxito.', 'success')
    except Exception as e:
        flash(f'Error al recuperar el compromiso: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_eliminados'))

@home.route('/crear_compromiso', methods=['GET', 'POST'])
@login_required
def crear_compromiso():
    user_id = session['user_id']
    user = persona_comp_service.get_user_info(user_id)
    form = CreateCompromisoForm()

    # Cargar opciones para el formulario
    persona_comp_service.get_initial_form_data(form)

    if request.method == 'POST':
        print("Formulario enviado")
        if form.validate_on_submit():
            print("Formulario validado")
            descripcion = form.descripcion.data
            estado = form.estado.data
            prioridad = form.prioridad.data
            fecha_creacion = form.fecha_creacion.data
            fecha_limite = form.fecha_limite.data
            comentario = form.comentario.data
            comentario_direccion = form.comentario_direccion.data
            id_departamento = form.id_departamento.data
            referentes = form.referentes.data

            print(f"Datos del formulario: {descripcion}, {estado}, {prioridad}, {fecha_creacion}, {fecha_limite}, {comentario}, {comentario_direccion}, {id_departamento}, {referentes}")

            try:
                # Crear el compromiso
                compromiso_id = persona_comp_service.create_compromiso(
                    descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, comentario_direccion, id_departamento, user_id
                )
                # Asociar los referentes al compromiso
                persona_comp_service.asociar_referentes(compromiso_id, referentes)
                
                flash('Compromiso creado con éxito.', 'success')
                return redirect(url_for('home.home_view'))
            except Exception as e:
                print(f"Error al crear compromiso: {e}")
                flash(f"Error al crear compromiso: {e}", 'danger')
        else:
            print("Formulario no válido")
            print(form.errors)

    return render_template('crear_compromiso.html', form=form, user=user)

@home.route('/exportar_acta', methods=['GET'])
def exportar_acta():
    # Esta ruta puede ser opcional si se utiliza solo el front-end para manejar la exportación
    return render_template('actas_reuniones.html')

@home.route('/actas_reuniones')
@login_required
def actas_reuniones():
    return render_template('actas_reuniones.html')

