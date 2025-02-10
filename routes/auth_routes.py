from datetime import datetime

import psycopg2
from flask import Blueprint, render_template, redirect, url_for, session, request
from forms import LoginForm
from database import get_db_connection, get_user_by_username
from repositories.compromiso_service import CompromisoService

auth = Blueprint('auth', __name__)

compromiso_service = CompromisoService()

from functools import wraps
from flask import redirect, url_for, session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            set_alert("Por favor, inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def is_director(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'the_big_boss' not in session or not session['the_big_boss']:
            print("No es director")
            set_alert("No tienes permisos para acceder a esta página.", "danger")
            return redirect(url_for('home.home_view'))
        return f(*args, **kwargs)
    return decorated_function

def set_alert(message, alert_type='info'):
    session['alert'] = {'message': message, 'type': alert_type}

@auth.route('/login', methods=['GET', 'POST'])
def login():
    alert = session.pop('alert', None)
    if request.method == 'POST':
        rut = request.form['rut']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id_persona, u.username, u.password, p.name, p.lastname
            FROM users u
            INNER JOIN persona p ON u.id_persona = p.id
            WHERE u.username = %s
        """, (rut,))
        user = cursor.fetchone()
        print(user)

        if user:
            stored_password = user[2]
            if password == stored_password:
                session['user_id'] = user[0]
                print(user[0])
                set_alert('Bienvenido/a, {}!'.format(user[3]), 'success')
                return redirect(url_for('home.home_view'))
            else:
                set_alert('Contraseña incorrecta.', 'danger')
        else:
            set_alert('RUT inválido o no registrado.', 'danger')

        cursor.close()
        conn.close()

    return render_template('login.html', alert=alert)

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('es_director', None)
    session.pop('the_big_boss', None)
    set_alert('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))
