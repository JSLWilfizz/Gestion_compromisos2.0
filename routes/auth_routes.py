from datetime import datetime

import psycopg2
from flask import Blueprint, render_template, redirect, url_for, flash, session, jsonify, request
from forms import LoginForm
from database import get_db_connection, get_user_by_username
from repositories.compromiso_service import CompromisoService

auth = Blueprint('auth', __name__)

compromiso_service = CompromisoService()

from functools import wraps
from flask import redirect, url_for, session, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si hay un usuario en la sesión
        if 'user_id' not in session:
            flash("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for('auth.login'))  # Redirigir a la página de login si no está autenticado
        return f(*args, **kwargs)
    return decorated_function

def is_director(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si el usuario es director
        if 'the_big_boss' not in session or not session['the_big_boss']:
            print("No es director")
            flash("No tienes permisos para acceder a esta página.", "danger")
            return redirect(url_for('home.home_view'))  # Redirigir a la página de inicio si no es director
        return f(*args, **kwargs)
    return decorated_function


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rut = request.form['rut']
        password = request.form['password']  # Capturamos la contraseña desde el formulario
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query para buscar el usuario en la tabla users usando el rut como username
        cursor.execute("""
            SELECT u.id_persona, u.username, u.password, p.name, p.lastname
            FROM users u
            INNER JOIN persona p ON u.id_persona = p.id
            WHERE u.username = %s
        """, (rut,))
        user = cursor.fetchone()  # Recupera el usuario si existe
        print(user)

        if user:
            # Validar la contraseña ingresada con la almacenada
            stored_password = user[2]  # Contraseña almacenada en la base de datos
            if password == stored_password:  # Cambiar a `check_password_hash` si están encriptadas
                # Autenticación exitosa: configurar la sesión
                session['user_id'] = user[0]  # ID del usuario
                print(user[0])
                flash('Bienvenido/a, {}!'.format(user[3]), 'success')
                return redirect(url_for('home.home_view'))
            else:
                flash('Contraseña incorrecta.', 'danger')
        else:
            flash('RUT inválido o no registrado.', 'danger')

        cursor.close()
        conn.close()

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.pop('user_id', None)  # Elimina el ID del usuario de la sesión
    session.pop('username', None)  # Elimina el username de la sesión
    session.pop('es_director', None)
    session.pop('the_big_boss', None)
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))  # Redirige a la página de login
