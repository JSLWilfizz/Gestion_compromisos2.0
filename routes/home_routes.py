from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from database import get_db_connection, get_departamento_compromisos
from psycopg2.extras import RealDictCursor
from forms import CompromisoForm

home = Blueprint('home', __name__)


# Ruta principal (home)
@home.route('/home')
def home_view():
    if 'user_id' not in session:
        print("Usuario no autenticado. Redirigiendo al login.")
        return redirect(url_for('auth.login'))  # Redirige si no hay un usuario en sesión

    user_id = session.get('user_id', None)  # Recuperar el ID del usuario desde la sesión

    if not user_id:
        print("No se encontró el ID de usuario en la sesión.")
        return redirect(url_for('auth.login'))  # Redirige si el ID de usuario no está en sesión

    conn = get_db_connection()

    try:
        # Consulta para obtener la información del usuario
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT p.id, p.name, p.lastname, p.position, d.name AS departamento_name
                FROM persona p
                JOIN persona_departamento pd ON p.id = pd.id_persona
                JOIN departamento d ON pd.id_departamento = d.id
                WHERE p.id = %s
            """, (user_id,))
            user = cursor.fetchone()  # Obtener los datos del usuario desde la consulta

        # Verificar si los datos del usuario son correctos
        if user is None:
            print(f"No se encontró el usuario con ID: {user_id}")
            return redirect(url_for('auth.login'))  # Redirige si no se encontró el usuario

        print(f"Usuario logueado: {user}")

        return render_template('home.html', user=user)

    except Exception as e:
        print(f"Error al consultar los datos del usuario: {e}")
        return redirect(url_for('auth.login'))  # Redirige si ocurre algún error
    finally:
        conn.close()  # Asegurar que la conexión se cierra


# Ruta para ver compromisos del departamento
@home.route('/compromisos', methods=['GET', 'POST'])
def ver_compromisos():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    user_id = session['user_id']

    # Verificar si el usuario es director de algún departamento
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT d.id AS id_departamento, pd.es_director
            FROM persona_departamento pd
            JOIN departamento d ON pd.id_departamento = d.id
            WHERE pd.id_persona = %s
        """, (user_id,))
        departamento_info = cursor.fetchone()

    # Cargar los compromisos del departamento del usuario
    compromisos = get_departamento_compromisos(conn, user_id)

    # Procesar el comentario del director si el formulario es enviado
    if request.method == 'POST':
        if departamento_info and departamento_info[1]:  # El usuario es director
            compromiso_id = request.form.get('compromiso_id')
            comentario = request.form.get('comentario')

            # Actualizar el comentario del compromiso
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE compromiso
                    SET comentario_director = %s
                    WHERE id = %s
                """, (comentario, compromiso_id))
                conn.commit()

            flash('Comentario actualizado correctamente.', 'success')

    return render_template('compromisos.html', compromisos=compromisos, es_director=departamento_info[1])


@home.route('/edit_compromiso/<int:compromiso_id>', methods=['GET', 'POST'])
def edit_compromiso_view(compromiso_id):
    conn = get_db_connection()
    form = CompromisoForm()

    # Cargar todos los usuarios disponibles
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name, lastname FROM persona")
        personas_data = cursor.fetchall()
        form.responsables.choices = [(int(row[0]), f"{row[1]} {row[2]}") for row in personas_data]

    # Cargar todos los departamentos disponibles
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM departamento")
        departamentos_data = cursor.fetchall()
        form.departamento.choices = [(int(row[0]), row[1]) for row in departamentos_data]

    # Cargar los datos del compromiso actual
    with conn.cursor() as cursor:
        cursor.execute("""
                SELECT descripcion, estado, prioridad, fecha_limite, id_departamento, avance
                FROM compromiso WHERE id = %s
            """, (compromiso_id,))
        compromiso = cursor.fetchone()

    # Cargar los responsables actuales del compromiso
    with conn.cursor() as cursor:
        cursor.execute("""
                SELECT id_persona FROM persona_compromiso WHERE id_compromiso = %s
            """, (compromiso_id,))
        responsables_actuales = [row[0] for row in cursor.fetchall()]

    # Si no se encuentra el compromiso, mostrar un error
    if not compromiso:
        flash('El compromiso no existe', 'danger')
        return redirect(url_for('home.home_view'))

    # Pre-cargar los datos actuales del compromiso en el formulario
    if request.method == 'GET':
        form.descripcion.data = compromiso['descripcion']
        form.estado.data = compromiso['estado']
        form.prioridad.data = compromiso['prioridad']
        form.fecha_limite.data = compromiso['fecha_limite']
        form.departamento.data = compromiso['id_departamento']  # Pre-cargar el departamento actual
        form.responsables.data = responsables_actuales  # Pre-cargar los responsables actuales
        form.nivel_avance.data = compromiso['avance']  # Pre-cargar el nivel de avance

    print("Formulario validado:", form.data, form.departamento.data)

    # Procesar la actualización cuando se envía el formulario
    if form.validate_on_submit():
        try:
            # Actualizar los datos del compromiso en la base de datos
            with conn.cursor() as cursor:
                cursor.execute("""
                        UPDATE compromiso
                        SET descripcion = %s, estado = %s, prioridad = %s, 
                            fecha_limite = %s, id_departamento = %s, avance = %s
                        WHERE id = %s
                    """, (form.descripcion.data, form.estado.data,
                          form.prioridad.data, form.fecha_limite.data,
                          form.departamento.data, form.nivel_avance.data, compromiso_id))

            # Actualizar los responsables del compromiso
            with conn.cursor() as cursor:
                # Primero, eliminar todos los responsables actuales del compromiso
                cursor.execute("DELETE FROM persona_compromiso WHERE id_compromiso = %s", (compromiso_id,))

                # Luego, insertar los nuevos responsables seleccionados
                for responsable_id in form.responsables.data:
                    cursor.execute("""
                            INSERT INTO persona_compromiso (id_compromiso, id_persona)
                            VALUES (%s, %s)
                        """, (compromiso_id, responsable_id))

            conn.commit()
            flash('Compromiso actualizado con éxito', 'success')
            return redirect(url_for('home.home_view'))

        except Exception as e:
            conn.rollback()
            flash(f'Ocurrió un error al actualizar el compromiso: {e}', 'danger')

    return render_template('edit_compromiso.html', form=form, compromiso_id=compromiso_id)
