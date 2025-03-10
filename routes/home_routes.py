# /routes/home_routes.py
import traceback
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from repositories.compromiso_service import CompromisoService
from repositories.reunion_service import ReunionService
from repositories.persona_comp_service import PersonaCompService
from .auth_routes import login_required
from forms import CompromisoForm, CreateCompromisoForm
from exceptions.compromiso_exceptions import ResponsablePrincipalError
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
import psycopg2  # Añadir esta importación
from psycopg2 import extras  # También necesitamos importar extras

home = Blueprint('home', __name__)
compromiso_service = CompromisoService()
reunion_service = ReunionService()
persona_comp_service = PersonaCompService()

# Configurar extensiones permitidas para archivos
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@home.route('/')
def redirect_home():
    return redirect(url_for('home.home_view'))


@home.route('/home')
@login_required
def home_view():
    alert = session.pop('alert', None)
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

    return render_template('home.html', user=user, es_director=es_director,the_big_boss=the_big_boss, alert=alert)


def set_alert(message, alert_type='info'):
    session['alert'] = {'message': message, 'type': alert_type}

@home.route('/ver_compromisos', methods=['GET', 'POST'])
@login_required
def ver_compromisos():
    if request.method == 'POST':
        compromiso_id = request.form.get('compromiso_id')
        if compromiso_id:
            try:
                compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
                if not compromiso:
                    set_alert('Compromiso no encontrado.', 'danger')
                    return redirect(url_for('home.ver_compromisos'))

                user_id = session['user_id']
                # Eliminar la verificación de permisos
                es_director = session.get('es_director')
                the_big_boss = session.get('the_big_boss')

                # Obtener los nuevos valores del formulario
                nuevo_estado = request.form.get('estado')
                nuevo_avance = request.form.get('nivel_avance')
                nuevo_comentario = request.form.get('comentario')
                comentario_director = request.form.get('comentario_direccion')

                # Eliminar la lógica de nuevos referentes basada en permisos
                nuevos_referentes = request.form.getlist('referentes')
                if not nuevos_referentes:
                    nuevos_referentes = compromiso['referentes_ids']

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

                set_alert('Compromiso actualizado con éxito.', 'success')
            except Exception as e:
                print(e)
                set_alert(f'Error al actualizar el compromiso: {str(e)}', 'danger')

        return redirect(url_for('home.ver_compromisos'))

    alert = session.pop('alert', None)  # Added alert retrieval
    user_id = session['user_id']
    es_director = session.get('es_director')
    the_big_boss = session.get('the_big_boss')

    # Obtener parámetros de búsqueda y filtro
    search = request.args.get('search', '')
    prioridad = request.args.get('prioridad', '')
    estado = request.args.get('estado', '')
    fecha_limite = request.args.get('fecha_limite', '')

    if es_director:
        compromisos = compromiso_service.get_compromisos_by_departamento(compromiso_service.get_director_info(user_id)['id_departamento'], search, prioridad, estado, fecha_limite)
    elif the_big_boss:
        compromisos = compromiso_service.get_compromisos_by_user(user_id, search, prioridad, estado, fecha_limite)
    else:
        compromisos = compromiso_service.get_compromisos_by_user(user_id, search, prioridad, estado, fecha_limite)

    todos_referentes = compromiso_service.get_referentes()

    return render_template(
        'ver_compromisos.html',
        compromisos=compromisos,
        todos_referentes=todos_referentes,
        es_director=es_director,
        the_big_boss=the_big_boss,
        user_id=user_id,
        user=compromiso_service.get_user_info(user_id),  # Pass the user variable to the template
        alert=alert    # Pass alert to the template
    )

@home.route('/ver_compromisos_compartidos')
@login_required
def ver_compromisos_compartidos():
    alert = session.pop('alert', None)  # Retrieve alert
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
        # Establecer permisos de edición y derivación
        comp['permiso_editar'] = user['nivel_jerarquico'] == 'DIRECTOR DE SERVICIO' or user['nivel_jerarquico'] == 'SUBDIRECTOR/A' or user['nivel_jerarquico'] == 'JEFE/A DE DEPARTAMENTO' or user['nivel_jerarquico'] == 'JEFE/A DE UNIDAD'
        comp['permiso_derivar'] = user['nivel_jerarquico'] == 'DIRECTOR DE SERVICIO' or user['nivel_jerarquico'] == 'SUBDIRECTOR/A' or user['nivel_jerarquico'] == 'JEFE/A DE DEPARTAMENTO' or user['nivel_jerarquico'] == 'JEFE/A DE UNIDAD'
    
    return render_template('ver_compromisos_compartidos.html', compromisos=compromisos_compartidos, user=user, alert=alert)

@home.route('/editar_compromiso/<int:compromiso_id>', methods=['GET', 'POST'])
@login_required
def editar_compromiso(compromiso_id):
    alert = session.pop('alert', None)
    try:
        user_id = session['user_id']
        user = compromiso_service.get_user_info(user_id)
        compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
        todos_referentes = compromiso_service.get_referentes()
        direccion = session.get('the_big_boss') or session.get('es_director') or user['nivel_jerarquico'] == 'DIRECTOR DE SERVICIO' or user['nivel_jerarquico'] == 'SUBDIRECTOR/A' or user['nivel_jerarquico'] == 'JEFE/A DE DEPARTAMENTO' or user['nivel_jerarquico'] == 'JEFE/A DE UNIDAD'

        # Verificar si el usuario es el jefe del departamento correspondiente al compromiso
        if not (compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento']) or direccion):
            set_alert('No tienes permiso para editar este compromiso.', 'danger')
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
                set_alert('Compromiso actualizado con éxito.', 'success')
                return redirect(url_for('home.ver_compromisos_compartidos'))
            except ResponsablePrincipalError:
                set_alert('Error: No se puede eliminar al responsable principal del compromiso. ' 
                      'Por favor, asegúrese de mantener al responsable principal en la lista de referentes.', 'danger')
                return redirect(request.url)

    except Exception as e:
        set_alert(f'Error inesperado: {str(e)}', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    return render_template('editar_derivar_compromiso.html', 
                           compromiso=compromiso, 
                           todos_referentes=todos_referentes,
                           direccion=direccion,
                           title="Editar Compromiso",
                           derivar=False,
                           alert=alert)

@home.route('/derivar_compromiso/<int:compromiso_id>', methods=['GET', 'POST'])
@login_required
def derivar_compromiso(compromiso_id):
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
    todos_referentes = compromiso_service.get_referentes()
    direccion = session.get('the_big_boss') or session.get('es_director') or user['nivel_jerarquico'] == 'DIRECTOR DE SERVICIO' or user['nivel_jerarquico'] == 'SUBDIRECTOR/A' or user['nivel_jerarquico'] == 'JEFE/A DE DEPARTAMENTO' or user['nivel_jerarquico'] == 'JEFE/A DE UNIDAD'

    # Verificar si el usuario es el jefe del departamento correspondiente al compromiso
    if not (compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento']) or direccion):
        set_alert('No tienes permiso para derivar este compromiso.', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    if request.method == 'POST':
        referentes = request.form.getlist('referentes')

        compromiso_service.update_referentes(compromiso_id, referentes)
        set_alert('Compromiso derivado con éxito.', 'success')
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
    origenes = reunion_service.get_origenes()  # Ensure this line fetches the origenes
    return render_template('mis_reuniones.html', reuniones=reuniones, origenes=origenes)  # Pass origenes to the template

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
    
    # Verificar si hay verificadores asociados (opcional, informativo)
    verificadores = compromiso_service.get_verificadores(compromiso_id)
    tiene_verificadores = len(verificadores) > 0

    # Verificar si el usuario tiene permiso para eliminar el compromiso
    if not (compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento']) or session.get('the_big_boss') or session.get('es_director')):
        set_alert('No tienes permiso para eliminar este compromiso.', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    try:
        # Establecer el id_persona en el contexto de la sesión
        persona_comp_service.set_current_user_id(user_id)
        
        # Eliminar el compromiso usando el servicio - ahora preserva los verificadores
        persona_comp_service.eliminar_compromiso(compromiso_id, user_id)
        
        mensaje = 'Compromiso eliminado con éxito.'
        if tiene_verificadores:
            mensaje += f' Se han preservado {len(verificadores)} verificadores asociados.'
            
        set_alert(mensaje, 'success')
    except Exception as e:
        print(f"Error al eliminar el compromiso: {e}")
        traceback.print_exc()
        set_alert(f'Error al eliminar el compromiso: {str(e)}', 'danger')
        
    return redirect(url_for('home.ver_compromisos_compartidos'))

@home.route('/ver_compromisos_eliminados')
@login_required
def ver_compromisos_eliminados():
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    if user['nivel_jerarquico'] == 'FUNCIONARIO':
        set_alert('No tienes permiso para ver los compromisos eliminados.', 'danger')
        return redirect(url_for('home.home_view'))

    compromisos_eliminados = persona_comp_service.get_compromisos_eliminados()
    
    # Modificar para incluir información sobre verificadores en la vista
    for compromiso in compromisos_eliminados:
        cursor = persona_comp_service.repo_persona.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT COUNT(*) as num_verificadores
            FROM compromiso_eliminado_verificador
            WHERE id_compromiso = %s
        """, (compromiso['id'],))
        result = cursor.fetchone()
        compromiso['num_verificadores'] = result['num_verificadores'] if result else 0
    
    alert = session.pop('alert', None)  # Retrieve alert for the template
    return render_template('ver_compromisos_eliminados.html', compromisos=compromisos_eliminados, alert=alert, user=user)

@home.route('/archivar_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def archivar_compromiso(compromiso_id):
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
    
    if not compromiso:
        set_alert('Compromiso no encontrado', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))
    
    # Verificar si el compromiso está en estado "Completado"
    if compromiso['estado'] != 'Completado':
        set_alert('Solo se pueden archivar compromisos completados', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))
    
    # Verificar si hay verificadores asociados (opcional, informativo)
    verificadores = compromiso_service.get_verificadores(compromiso_id)
    tiene_verificadores = len(verificadores) > 0
    
    # Simplificar la verificación de permisos
    the_big_boss = session.get('the_big_boss', False)
    es_director = session.get('es_director', False)
    nivel_permitido = user['nivel_jerarquico'] in ['DIRECTOR DE SERVICIO', 'SUBDIRECTOR/A', 'JEFE/A DE DEPARTAMENTO', 'JEFE/A DE UNIDAD']
    es_jefe = compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento'])
    
    # Agregar logs para depuración
    print(f"User ID: {user_id}")
    print(f"Es the_big_boss: {the_big_boss}")
    print(f"Es director: {es_director}")
    print(f"Nivel jerárquico: {user['nivel_jerarquico']}")
    print(f"Nivel permitido: {nivel_permitido}")
    print(f"Es jefe del departamento: {es_jefe}")
    print(f"ID del departamento del compromiso: {compromiso['id_departamento']}")
    print(f"ID del departamento del usuario: {user.get('id_departamento')}")
    print(f"Tiene verificadores asociados: {tiene_verificadores} ({len(verificadores)} archivos)")
    
    # Simplificar la lógica de permisos para que sea más clara
    tiene_permiso = the_big_boss or es_director or nivel_permitido or es_jefe
    
    if not tiene_permiso:
        set_alert('No tienes permiso para archivar este compromiso. Se requiere ser responsable o tener un cargo superior.', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    try:
        # Establecer el id_persona en el contexto de la sesión
        persona_comp_service.set_current_user_id(user_id)
        
        # Archivar el compromiso usando el servicio - ahora preserva los verificadores
        persona_comp_service.archivar_compromiso(compromiso_id, user_id)
        
        mensaje = 'Compromiso archivado con éxito.'
        if tiene_verificadores:
            mensaje += f' Se han preservado {len(verificadores)} verificadores asociados.'
            
        set_alert(mensaje, 'success')
    except Exception as e:
        set_alert(f'Error al archivar el compromiso: {str(e)}', 'danger')
    
    return redirect(url_for('home.ver_compromisos_compartidos'))

@home.route('/ver_compromisos_archivados')
@login_required
def ver_compromisos_archivados():
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    if not (session.get('the_big_boss') or user['cargo'] != 'FUNCIONARIO'):
        set_alert('No tienes permiso para ver los compromisos archivados.', 'danger')
        return redirect(url_for('home.home_view'))

    compromisos_archivados = persona_comp_service.get_compromisos_archivados()
    
    # Modificar para incluir información sobre verificadores en la vista
    for compromiso in compromisos_archivados:
        cursor = persona_comp_service.repo_persona.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT COUNT(*) as num_verificadores
            FROM compromiso_archivado_verificador
            WHERE id_compromiso = %s
        """, (compromiso['id'],))
        result = cursor.fetchone()
        compromiso['num_verificadores'] = result['num_verificadores'] if result else 0
    
    alert = session.pop('alert', None)  # Retrieve alert to display after recovery
    return render_template('ver_compromisos_archivados.html', compromisos=compromisos_archivados, user=user, alert=alert)

@home.route('/desarchivar_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def desarchivar_compromiso(compromiso_id):
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)

    # Verificar si el usuario tiene permiso para desarchivar el compromiso
    if not (session.get('the_big_boss') or user['nivel_jerarquico'] != 'FUNCIONARIO/A'):
        set_alert('No tienes permiso para desarchivar este compromiso.', 'danger')
        return redirect(url_for('home.home_view'))

    try:
        persona_comp_service.desarchivar_compromiso(compromiso_id)
        set_alert('Compromiso desarchivado con éxito.', 'success')
    except Exception as e:
        set_alert(f'Error al desarchivar el compromiso: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_archivados'))

@home.route('/eliminar_permanentemente_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def eliminar_permanentemente_compromiso(compromiso_id):
    user_id = session['user_id']
    if not session.get('the_big_boss'):
        set_alert('No tienes permiso para eliminar permanentemente este compromiso.', 'danger')
        return redirect(url_for('home.home_view'))

    try:
        persona_comp_service.eliminar_permanentemente_compromiso(compromiso_id)
        set_alert('Compromiso eliminado permanentemente con éxito.', 'success')
    except Exception as e:
        print(f"Error al eliminar permanentemente el compromiso: {e}")
        traceback.print_exc()
        set_alert(f'Error al eliminar permanentemente el compromiso: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_eliminados'))

@home.route('/forzar_eliminacion_compromisos', methods=['POST'])
@login_required
def forzar_eliminacion_compromisos():
    try:
        compromiso_ids = [20, 21]
        persona_comp_service.forzar_eliminacion_compromisos(compromiso_ids)
        set_alert('Compromisos eliminados forzosamente con éxito.', 'success')
    except Exception as e:
        print(f"Error al forzar la eliminación de los compromisos: {e}")
        traceback.print_exc()
        set_alert(f'Error al forzar la eliminación de los compromisos: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_compartidos'))

@home.route('/recuperar_compromiso/<int:compromiso_id>', methods=['POST'])
@login_required
def recuperar_compromiso(compromiso_id):
    user_id = session['user_id']
    if not session.get('the_big_boss'):
        set_alert('No tienes permiso para recuperar este compromiso.', 'danger')
        return redirect(url_for('home.home_view'))

    try:
        persona_comp_service.recuperar_compromiso(compromiso_id)
        set_alert('Compromiso recuperado con éxito.', 'success')
    except Exception as e:
        set_alert(f'Error al recuperar el compromiso: {str(e)}', 'danger')
    return redirect(url_for('home.ver_compromisos_eliminados'))

@home.route('/crear_compromiso', methods=['GET', 'POST'])
@login_required
def crear_compromiso():
    alert = session.pop('alert', None)
    user_id = session['user_id']
    user = persona_comp_service.get_user_info(user_id)
    form = CreateCompromisoForm()

    # Cargar opciones para el formulario
    persona_comp_service.get_initial_form_data(form)

    if request.method == 'POST':
        print("Formulario enviado")
        
        # Si se ha seleccionado un departamento, cargar las opciones de origen y area
        departamento_id = request.form.get('id_departamento')
        if departamento_id:
            # Cargar áreas y orígenes para el departamento seleccionado
            areas = compromiso_service.get_areas_by_departamento(departamento_id)
            origenes = compromiso_service.get_origenes_by_departamento(departamento_id)
            
            # Actualizar las opciones en el formulario
            form.origen.choices = [(str(o['id']), o['name']) for o in origenes]
            form.area.choices = [(str(a['id']), a['name']) for a in areas]
        
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
            
            # Mejorar la verificación de los valores de origen y área
            origen = form.origen.data if (hasattr(form, 'origen') and form.origen.data and form.origen.data.strip() != '') else None
            area = form.area.data if (hasattr(form, 'area') and form.area.data and form.area.data.strip() != '') else None
            
            print(f"Datos del formulario: {descripcion}, {estado}, {prioridad}, {fecha_creacion}, {fecha_limite}, {comentario}, {comentario_direccion}, {id_departamento}, {referentes}, {origen}, {area}")
            
            # Imprimir tipos de datos para depuración
            print(f"Tipo de origen: {type(origen)}, Tipo de area: {type(area)}")

            try:
                # Crear el compromiso
                compromiso_id = persona_comp_service.create_compromiso(
                    descripcion, estado, prioridad, fecha_creacion, fecha_limite, comentario, 
                    comentario_direccion, id_departamento, user_id, origen, area
                )
                # Asociar los referentes al compromiso
                persona_comp_service.asociar_referentes(compromiso_id, referentes)
                
                set_alert('Compromiso creado con éxito.', 'success')
                return redirect(url_for('home.home_view'))
            except Exception as e:
                print(f"Error al crear compromiso: {e}")
                set_alert(f"Error al crear compromiso: {e}", 'danger')
        else:
            print("Formulario no válido")
            print(form.errors)

    return render_template('crear_compromiso.html', form=form, user=user, alert=alert)

@home.route('/exportar_acta', methods=['GET'])
def exportar_acta():
    # Esta ruta puede ser opcional si se utiliza solo el front-end para manejar la exportación
    return render_template('actas_reuniones.html')

@home.route('/actas_reuniones')
@login_required
def actas_reuniones():
    return render_template('actas_reuniones.html')

@home.route('/ver_verificadores/<int:compromiso_id>', methods=['GET', 'POST'])
@login_required
def ver_verificadores(compromiso_id):
    user_id = session.get('user_id')
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
    
    if not compromiso:
        set_alert('Compromiso no encontrado', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))
    
    # Check if the current user is the principal responsible - ONLY THIS CHECK MATTERS NOW
    is_principal = compromiso_service.is_principal_responsible(user_id, compromiso_id)
    
    # Get user info just for display purposes
    user = compromiso_service.get_user_info(user_id)
    
    # Determine if the user can upload files (ONLY principal responsible)
    can_upload = is_principal
    
    # Obtener verificadores del compromiso
    verificadores = compromiso_service.get_verificadores(compromiso_id)
    alert = session.pop('alert', None)
    
    return render_template(
        'ver_verificadores.html',
        compromiso=compromiso,
        verificadores=verificadores,
        can_upload=can_upload,
        is_principal=is_principal,
        alert=alert
    )

@home.route('/agregar_verificador/<int:compromiso_id>', methods=['POST'])
@login_required
def agregar_verificador(compromiso_id):
    user_id = session.get('user_id')
    
    # ONLY check if the current user is the principal responsible
    is_principal = compromiso_service.is_principal_responsible(user_id, compromiso_id)
    
    # Only allow upload if user is principal responsible - NO EXCEPTIONS
    if not is_principal:
        set_alert('Solo el responsable principal puede subir verificadores para este compromiso.', 'danger')
        return redirect(url_for('home.ver_verificadores', compromiso_id=compromiso_id))
    
    # Continue with the existing upload logic
    # Verificar que se haya enviado un archivo
    if 'archivo' not in request.files:
        set_alert('No se seleccionó ningún archivo', 'danger')
        return redirect(url_for('home.ver_verificadores', compromiso_id=compromiso_id))
    
    archivo = request.files['archivo']
    descripcion = request.form.get('descripcion', '')
    
    # Verificar que el archivo tenga un nombre
    if archivo.filename == '':
        set_alert('No se seleccionó ningún archivo', 'danger')
        return redirect(url_for('home.ver_verificadores', compromiso_id=compromiso_id))
    
    # Verificar que el archivo tenga una extensión permitida
    if archivo and allowed_file(archivo.filename):
        # Obtener la extensión del archivo
        ext = archivo.filename.rsplit('.', 1)[1].lower()
        
        # Crear estructura de directorios por tipo de archivo, año, mes y día
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        # Build folder path: uploads/verificadores/{ext}/{year}/{month}/{day}
        folder_path = os.path.join('verificadores', ext, year, month, day)
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_path)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Guardar el archivo con un nombre seguro
        filename = secure_filename(archivo.filename)
        # Añadir timestamp para evitar nombres duplicados
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        file_path = os.path.join(upload_folder, filename)
        
        try:
            # Guardar el archivo en trozos para manejar archivos grandes
            with open(file_path, 'wb') as f:
                chunk_size = 4096  # 4KB por trozo
                while True:
                    chunk = archivo.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
            
            # Guardar la referencia en la base de datos con la ruta relativa organizada
            ruta_relativa = os.path.join(folder_path, filename)
            # Asegurar que usamos forward slashes en la BD para consistencia
            ruta_relativa = ruta_relativa.replace('\\', '/')
            
            compromiso_service.add_verificador(
                compromiso_id, 
                archivo.filename,  # Nombre original del archivo
                ruta_relativa,     # Ruta relativa para acceder al archivo
                descripcion,
                user_id
            )
            set_alert('Verificador agregado con éxito', 'success')
        except Exception as e:
            set_alert(f'Error al guardar el verificador: {str(e)}', 'danger')
        
    else:
        set_alert('Tipo de archivo no permitido', 'danger')
    
    return redirect(url_for('home.ver_verificadores', compromiso_id=compromiso_id))

@home.route('/eliminar_verificador/<int:verificador_id>/<int:compromiso_id>', methods=['POST'])
@login_required
def eliminar_verificador(verificador_id, compromiso_id):
    user_id = session.get('user_id')
    
    try:
        # Eliminar la referencia en la base de datos
        compromiso_service.delete_verificador(verificador_id)
        set_alert('Verificador eliminado con éxito', 'success')
    except Exception as e:
        set_alert(f'Error al eliminar el verificador: {str(e)}', 'danger')
    
    return redirect(url_for('home.ver_verificadores', compromiso_id=compromiso_id))

@home.route('/get_areas_by_departamento', methods=['GET'])
@login_required
def get_areas_by_departamento():
    departamento_id = request.args.get('departamento_id', type=int)
    if not departamento_id:
        return jsonify([])
    
    try:
        areas = compromiso_service.get_areas_by_departamento(departamento_id)
        return jsonify(areas)
    except Exception as e:
        print(f"Error en get_areas_by_departamento: {e}")
        return jsonify({'error': str(e)}), 500

@home.route('/get_origenes_by_departamento', methods=['GET'])
@login_required
def get_origenes_by_departamento():
    departamento_id = request.args.get('departamento_id', type=int)
    if not departamento_id:
        return jsonify([])
    
    try:
        print(f"Obteniendo orígenes para departamento ID: {departamento_id}")
        origenes = compromiso_service.get_origenes_by_departamento(departamento_id)
        print(f"Orígenes obtenidos: {origenes}")
        return jsonify(origenes)
    except Exception as e:
        print(f"Error en get_origenes_by_departamento: {e}")
        return jsonify({'error': str(e)}), 500

