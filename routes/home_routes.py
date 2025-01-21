# /routes/home_routes.py
import traceback

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from repositories.compromiso_service import CompromisoService
from repositories.reunion_service import ReunionService
from .auth_routes import login_required

home = Blueprint('home', __name__)
compromiso_service = CompromisoService()
reunion_service = ReunionService()


@home.route('/')
def redirect_home():
    return redirect(url_for('home.home_view'))


@home.route('/home')
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
    user_id = session['user_id']
    es_director = session.get('es_director')
    the_big_boss = session.get('the_big_boss')
    print(request.method)
    print(es_director)
    if request.method == 'POST':
        # Obtener compromisos actuales (directores ven todos, usuarios solo sus compromisos)
        if es_director:
            departamento_id = compromiso_service.get_director_info(user_id)['id_departamento']
            compromisos = compromiso_service.get_compromisos_by_departamento(departamento_id)
            
        else:
            print("No es director")
            compromisos = compromiso_service.get_compromisos_by_user(user_id)
        if the_big_boss:
            print("es el jefe")
            compromisos = compromiso_service.get_all_compromisos()
        print(compromisos)
        # Actualizar los compromisos
        for compromiso in compromisos:
            compromiso_id = compromiso['compromiso_id']
            print(f"Responsables: {compromiso['responsables_ids']}")

            # Directores pueden cambiar responsables y comentario de dirección
            if es_director:
                nuevos_responsables = request.form.getlist(f'nuevos_responsables-{compromiso_id}')
                comentario_director = request.form.get(f'comentario-{compromiso_id}') # director es parte de direccion?
                if nuevos_responsables == []:
                    nuevos_responsables = compromiso['responsables_ids']

            if the_big_boss:
                nuevos_responsables = request.form.getlist(f'nuevos_responsables-{compromiso_id}')
                comentario_director = request.form.get(f'comentario_direccion-{compromiso_id}')
                if nuevos_responsables == []:
                    nuevos_responsables = compromiso['responsables_ids']
            else:
                nuevos_responsables = compromiso['responsables_ids']  # Mantiene los responsables actuales
                comentario_director = compromiso['comentario_direccion']  # Mantiene el comentario actual

            # Obtener los nuevos valores del formulario
            nuevo_estado = request.form.get(f'estado-{compromiso_id}')
            nuevo_avance = request.form.get(f'nivel_avance-{compromiso_id}')
            nuevo_comentario = request.form.get(f'comentario-{compromiso_id}')
            print(f"Actualizando compromiso {compromiso_id}")
            # Actualizar el compromiso
            try:
                print(f"Actualizando compromiso {compromiso_id}")
                compromiso_service.update_compromiso(
                    compromiso_id,
                    nuevo_estado,
                    nuevo_avance,
                    nuevo_comentario,
                    user_id,
                    comentario_director,
                    nuevos_responsables
                )
            except Exception as e:
                print(e)

        flash('Compromisos actualizados con éxito.', 'success')
        return redirect(url_for('home.ver_compromisos'))

    # Si es un GET, obtener los compromisos para mostrar
    if es_director:
        print("es director")
        departamento_id = compromiso_service.get_director_info(user_id)['id_departamento']
        compromisos = compromiso_service.get_compromisos_by_departamento(departamento_id)
    else:
        print("No es director")
        compromisos = compromiso_service.get_compromisos_by_user(user_id)
    if the_big_boss:
        print("es el jefe")
        compromisos = compromiso_service.get_all_compromisos()
    print(compromisos)
    todos_responsables = compromiso_service.get_responsables()

    return render_template(
        'ver_compromisos.html',
        compromisos=compromisos,
        todos_responsables=todos_responsables,
        es_director=es_director,
        the_big_boss=the_big_boss
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
    
    return render_template('ver_compromisos_compartidos.html', compromisos=compromisos_compartidos, user=user)

@home.route('/editar_compromiso/<int:compromiso_id>', methods=['GET', 'POST'])
@login_required
def editar_compromiso(compromiso_id):
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
    todos_responsables = compromiso_service.get_responsables()
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
        responsables = request.form.getlist('responsables')
        comentario = request.form.get('comentario')
        comentario_direccion = request.form.get('comentario_direccion')

        compromiso_service.update_compromiso(
            compromiso_id, estado, avance, comentario, user_id, comentario_direccion, responsables
        )
        flash('Compromiso actualizado con éxito.', 'success')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    return render_template('editar_derivar_compromiso.html', 
                           compromiso=compromiso, 
                           todos_responsables=todos_responsables,
                           direccion=direccion,
                           title="Editar Compromiso",
                           derivar=False)

@home.route('/derivar_compromiso/<int:compromiso_id>', methods=['GET', 'POST'])
@login_required
def derivar_compromiso(compromiso_id):
    user_id = session['user_id']
    user = compromiso_service.get_user_info(user_id)
    compromiso = compromiso_service.get_compromiso_by_id(compromiso_id)
    todos_responsables = compromiso_service.get_responsables()
    direccion = session.get('the_big_boss') or session.get('es_director')

    # Verificar si el usuario es el jefe del departamento correspondiente al compromiso
    if not (compromiso_service.es_jefe_de_departamento(user_id, compromiso['id_departamento']) or direccion):
        flash('No tienes permiso para derivar este compromiso.', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    if request.method == 'POST':
        responsables = request.form.getlist('responsables')

        compromiso_service.update_responsables(compromiso_id, responsables)
        flash('Compromiso derivado con éxito.', 'success')
        return redirect(url_for('home.ver_compromisos_compartidos'))

    return render_template('editar_derivar_compromiso.html', 
                           compromiso=compromiso, 
                           todos_responsables=todos_responsables,
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
