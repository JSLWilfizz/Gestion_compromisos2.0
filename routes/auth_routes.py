from datetime import datetime

import psycopg2
from flask import Blueprint, render_template, redirect, url_for, session, request
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
        if 'user_id' not in session:
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

def not_funcionario_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        if user and user.get('nivel_jerarquico') == 'FUNCIONARIO/A':
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('home.home_view'))
        return f(*args, **kwargs)
    return decorated_function

def set_alert(message, alert_type='info'):
    session['alert'] = {'message': message, 'type': alert_type}
    print(f"Alert set: {session['alert']}")  # Debugging statement

@auth.route('/login', methods=['GET', 'POST'])
def login():
    alert = session.pop('alert', None)  # Clear the alert after retrieving it
    print(f"Alert retrieved at start: {alert}")  # Debugging statement
    if request.method == 'POST':
        rut = request.form['rut']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id_persona, u.username, u.password, p.name, p.lastname, p.nivel_jerarquico
            FROM users u
            INNER JOIN persona p ON u.id_persona = p.id
            WHERE u.username = %s
        """, (rut,))
        user = cursor.fetchone()
        print(f"User retrieved: {user}")  # Debugging statement

        if user:
            stored_password = user[2]
            if password == stored_password:
                session['user_id'] = user[0]
                session['nivel_jerarquico'] = user[5]  # Asegúrate de que esto se configure correctamente
                # Almacenar los datos del usuario completos en session["user"]
                session['user'] = {
                    'id': user[0],
                    'username': user[1],
                    'name': user[3],
                    'lastname': user[4],
                    'nivel_jerarquico': user[5],
                    # Agrega el departamento u otros campos necesarios si están disponibles
                }
                print(f"User ID set in session: {session['user_id']}")  # Debugging statement
                set_alert('Bienvenido/a, {}!'.format(user[3]), 'success')
                if user[1] == '0':
                    return redirect(url_for('admin.index'))
                return redirect(url_for('home.home_view'))
            else:
                set_alert('Contraseña incorrecta.', 'danger')
        else:
            set_alert('RUT inválido o no registrado.', 'danger')

        cursor.close()
        conn.close()

    alert = session.pop('alert', None)  # Retrieve the alert again after setting it
    print(f"Alert retrieved at end: {alert}")  # Debugging statement
    return render_template('login.html', alert=alert)

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('es_director', None)
    session.pop('the_big_boss', None)
    session.clear()
    set_alert('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))
