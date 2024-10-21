from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from database import get_db_connection, get_departamento_compromisos
from psycopg2.extras import RealDictCursor
from forms import CompromisoForm
from .auth_routes import login_required

home = Blueprint('home', __name__)

@home.route('/')
def redirect_home():
    return redirect(url_for('home.home_view'))

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
@home.route('/ver_compromisos', methods=['GET', 'POST'])
@login_required
def ver_compromisos():
    conn = get_db_connection()  # Obtener la conexión a la base de datos
    user_id = session['user_id']  # Obtener el ID del usuario logueado

    try:
        # Verificar si el usuario es director
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT pd.es_director, pd.id_departamento
                FROM persona_departamento pd
                JOIN persona p ON p.id = pd.id_persona
                WHERE p.id = %s
            """, (user_id,))
            director_info = cursor.fetchone()

        es_director = director_info['es_director']
        id_departamento = director_info['id_departamento']

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Cargar todos los responsables
            cursor.execute("""
                        SELECT p.id, p.name, p.lastname, d.name AS departamento, p.position
                        FROM persona p
                        JOIN persona_departamento pd ON p.id = pd.id_persona
                        JOIN departamento d ON pd.id_departamento = d.id
                    """)
            # Crear la lista con el formato "Nombre Apellido - Departamento - Cargo"
            todos_responsables = [
                (persona['id'],
                 f"{persona['name']} {persona['lastname']} - {persona['departamento']} - {persona['position']}")
                for persona in cursor.fetchall()
            ]

        # Si el usuario es director, ver todos los compromisos del departamento
        if es_director:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT c.id AS compromiso_id, c.descripcion, c.estado, c.avance, c.fecha_limite, c.comentario_director, 
                           ARRAY_AGG(DISTINCT p.id) AS responsables
                    FROM compromiso c
                    LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                    LEFT JOIN persona p ON pc.id_persona = p.id
                    WHERE c.id_departamento = %s
                    GROUP BY c.id
                """, (id_departamento,))
                compromisos = cursor.fetchall()
        else:
            # Si no es director, ver solo los compromisos donde el usuario es responsable
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT c.id AS compromiso_id, c.descripcion, c.estado, c.avance, c.fecha_limite, c.comentario_director, 
                       STRING_AGG(DISTINCT p.id::text, ', ') AS responsables_ids,
                       STRING_AGG(DISTINCT p.name || ' ' || p.lastname, ', ') AS responsables
                FROM compromiso c
                LEFT JOIN persona_compromiso pc ON c.id = pc.id_compromiso
                LEFT JOIN persona p ON pc.id_persona = p.id
                GROUP BY c.id
                HAVING %s = ANY(ARRAY_AGG(p.id))
                """, (user_id,))
                compromisos = cursor.fetchall()

        print(compromisos)  # Debug: mostrar compromisos cargados

        # Si se envía un formulario de actualización
        if request.method == 'POST':
            for compromiso in compromisos:
                compromiso_id = compromiso['compromiso_id']
                nuevo_estado = request.form.get(f'estado-{compromiso_id}')
                nuevo_avance = request.form.get(f'nivel_avance-{compromiso_id}')
                nuevo_comentario = request.form.get(f'comentario-{compromiso_id}')

                # Actualizar estado, avance y comentario
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE compromiso
                        SET estado = %s, avance = %s, comentario_director = %s
                        WHERE id = %s
                    """, (nuevo_estado, nuevo_avance, nuevo_comentario, compromiso_id))

                    cursor.execute("""
                        INSERT INTO compromiso_modificaciones (id_compromiso, id_usuario)
                        VALUES (%s, %s)
                    """, (compromiso_id, user_id))

                # Si es director, puede cambiar los responsables
                if es_director:
                    nuevos_responsables = request.form.getlist(f'responsables-{compromiso_id}')
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM persona_compromiso WHERE id_compromiso = %s", (compromiso_id,))
                        for responsable_id in nuevos_responsables:
                            cursor.execute("""
                                INSERT INTO persona_compromiso (id_persona, id_compromiso)
                                VALUES (%s, %s)
                            """, (responsable_id, compromiso_id))

            conn.commit()  # Confirmar cambios en la base de datos
            flash('Compromisos actualizados correctamente.', 'success')

        return render_template('compromisos.html', compromisos=compromisos, es_director=es_director, todos_responsables=todos_responsables)

    except Exception as e:
        conn.rollback()
        print(f"Error al actualizar los compromisos: {e}")
        flash('Ocurrió un error al actualizar los compromisos.', 'danger')
        return redirect(url_for('home.ver_compromisos'))

    finally:
        conn.close()  # Cerrar la conexión solo al final


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
