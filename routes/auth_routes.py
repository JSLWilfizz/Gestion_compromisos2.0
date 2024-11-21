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
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to fetch user via RUT in the persona table
        cursor.execute("""
            SELECT * 
            FROM persona
            WHERE persona.rut = %s
        """, (rut,))
        user = cursor.fetchone()
        print(user)

        if user:
            # Set session or handle authenticated state
            session['user_id'] = user[0]
            flash('Bienvenido/a!', 'success')
            return redirect(url_for('home.home_view'))
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
