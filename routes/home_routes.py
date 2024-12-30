# /routes/home_routes.py
import traceback

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from repositories.compromiso_service import CompromisoService
from .auth_routes import login_required

home = Blueprint('home', __name__)
compromiso_service = CompromisoService()


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
    if user["position"] == 'DIRECTOR DE SERVICIO':
        the_big_boss = True
        session['the_big_boss'] = the_big_boss
        es_director = False
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
                comentario_director = request.form.get(f'comentario-{compromiso_id}')
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