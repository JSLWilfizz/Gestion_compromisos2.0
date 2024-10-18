import os

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from forms import CreateMeetingForm, CompromisoForm, ActaForm
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

from .auth_routes import login_required
from datetime import datetime

reunion = Blueprint('reunion', __name__)


@reunion.route('/reunion/crear_paso1', methods=['GET', 'POST'])
@login_required
def crear_reunion_paso1():
    form = CreateMeetingForm()
    conn = get_db_connection()

    # Limpiar los datos previos de la sesión al comenzar el paso 1
    session.pop('compromisos_data', None)  # Eliminar los compromisos de la sesión
    session.pop('reunion_data', None)  # Eliminar los datos de la reunión de la sesión

    # Cargar los datos de la base de datos para los selects
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:

        cursor.execute("SELECT id, name FROM origen")
        form.origen.choices = [(origen['id'], origen['name']) for origen in cursor.fetchall()]
        print(f"Origen choices: {form.origen.choices}")

        cursor.execute("SELECT id, name FROM area")
        form.area.choices = [(area['id'], area['name']) for area in cursor.fetchall()]
        print(f"Area choices: {form.area.choices}")

        # Obtener asistentes con nombre completo y departamento
        cursor.execute("""
            SELECT p.id, p.name, p.lastname, d.name AS departamento
            FROM persona p
            JOIN persona_departamento pd ON p.id = pd.id_persona
            JOIN departamento d ON pd.id_departamento = d.id
        """)

        # Obtener departamentos para compromisos
        cursor.execute("SELECT id, name FROM departamento")
        departamentos_choices = [(departamento['id'], departamento['name']) for departamento in cursor.fetchall()]
        form.compromisos[0].departamento.choices = departamentos_choices
        print(f"Departamento choices: {departamentos_choices}")

        # Obtener responsables para compromisos
        cursor.execute("SELECT id, name FROM persona")
        responsables_choices = [(persona['id'], persona['name']) for persona in cursor.fetchall()]
        form.compromisos[0].responsables.choices = responsables_choices
        print(f"Responsables choices: {responsables_choices}")
        asistentes = request.form.getlist('asistentes')
        print("Asistentes seleccionados:", asistentes)  # Para verificar en los logs

    # Validar los campos de la reunión (primer paso)
    def validate_first_step(form):
        is_valid = True
        if not form.origen.validate(form):
            print("Error en el campo origen:", form.origen.errors)
            is_valid = False
        if not form.area.validate(form):
            print("Error en el campo area:", form.area.errors)
            is_valid = False
        if not form.asistentes.validate(form):
            print("Asistentes seleccionados:", form.asistentes.data)
            print("Error en el campo asistentes:", form.asistentes.errors)
            is_valid = False

        return is_valid

    print("Formulario: ", form.data)
    try:
        if request.method == 'POST' and validate_first_step(form):
            # Obtener el nuevo origen y área si existen
            new_origen = request.form.get('new_origen')
            new_area = request.form.get('new_area')

            # Si el usuario introdujo un nuevo origen, agregarlo a la base de datos
            if new_origen:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO origen (name) VALUES (%s) RETURNING id", (new_origen,))
                    origen_id = cursor.fetchone()[0]
            else:
                origen_id = form.origen.data  # Utilizar el origen seleccionado

            # Si el usuario introdujo una nueva área, agregarla a la base de datos
            if new_area:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO area (name) VALUES (%s) RETURNING id", (new_area,))
                    area_id = cursor.fetchone()[0]
            else:
                area_id = form.area.data  # Utilizar el área seleccionada

            # Guardar la reunión en la base de datos
            with conn.cursor() as cursor:
                # Obtener los asistentes ingresados manualmente
                asistentes = request.form.get('asistentes')  # Capturar los asistentes ingresados manualmente
                if asistentes:
                    lista_asistentes = [asistente.strip() for asistente in asistentes.split(',')]
                    asistentes_str = ', '.join(
                        lista_asistentes)  # Convertir la lista de asistentes en una cadena de texto

                cursor.execute("""
                        INSERT INTO reunion (nombre, id_staff, id_area, id_origen, fecha_creacion, asistentes)
                        VALUES (%s, %s, %s, %s, NOW(), %s) RETURNING id
                    """, ('Nombre de la reunión', None, area_id, origen_id, asistentes_str))

                reunion_id = cursor.fetchone()[0]
                print(f"Reunión guardada con ID: {reunion_id}")

            # Guardar los compromisos
            compromisos = request.form.getlist('compromisos')  # Captura compromisos ingresados

            print("Compromisos ingresados:", form.compromisos.data)  # Para verificar en los logs
            if form.compromisos.data:
                for compromiso_form in form.compromisos:
                    nombre = compromiso_form['nombre']
                    estado = "Pendiente"
                    prioridad = compromiso_form['prioridad']
                    fecha_limite = compromiso_form['fecha_limite']
                    id_departamento = compromiso_form['departamento']
                    nivel_avance = 0
                    responsables = compromiso_form['responsables']

                    # Guardar cada compromiso en la base de datos
                    with conn.cursor() as cursor:
                        cursor.execute("""
                                INSERT INTO compromiso (descripcion, prioridad, fecha_limite, id_departamento,nivel_avance, fecha_creacion)
                                VALUES (%s, %s, %s, %s,%s, NOW()) RETURNING id
                            """, (nombre, prioridad, fecha_limite, id_departamento, nivel_avance))

                        compromiso_id = cursor.fetchone()[0]
                        print(f"Compromiso guardado con ID: {compromiso_id}")

                        cursor.execute("""
                            INSERT INTO persona_compromiso (id_persona, id_compromiso)
                            VALUES (%s, %s) RETURNING id
                        """, (responsables, compromiso_id))
                        persona_compromiso_id = cursor.fetchone()[0]
                        print(f"Responsable guardado con ID: {persona_compromiso_id}")

                        # Asociar el compromiso a la reunión en la tabla intermedia
                        cursor.execute("""
                                INSERT INTO reunion_compromiso (id_reunion, id_compromiso)
                                VALUES (%s, %s)
                            """, (reunion_id, compromiso_id))

            conn.commit()  # Confirmar los cambios en la base de datos

            return redirect(url_for('home.home_view'))

    except Exception as e:
        print(f'Ocurrió un error: {e}')
        conn.rollback()  # Revertir los cambios si ocurre un error
        flash(f'Ocurrió un error al crear la reunión: {e}', 'danger')

    return render_template('crear_reunion_paso1.html', form=form)

