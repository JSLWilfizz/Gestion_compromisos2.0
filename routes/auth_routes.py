from flask import Blueprint, render_template, redirect, url_for, flash, session
from forms import LoginForm
from database import get_db_connection, get_user_by_username

auth = Blueprint('auth', __name__)

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

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        conn = get_db_connection()
        user = get_user_by_username(conn, form.username.data)

        if user:
            if user['password'] == form.password.data:
                session['user_id'] = user['id_persona']  # Guarda el ID del usuario en la sesión
                session['username'] = user['username']  # Guarda el username en la sesión
                return redirect(url_for('home.home_view'))
            else:
                flash('Contraseña incorrecta.', 'danger')
        else:
            flash('Usuario no encontrado.', 'danger')

    return render_template('login.html', form=form)

@auth.route('/logout')
def logout():
    session.pop('user_id', None)  # Elimina el ID del usuario de la sesión
    session.pop('username', None)  # Elimina el username de la sesión
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))  # Redirige a la página de login