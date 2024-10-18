import os

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from forms import CreateMeetingForm, CompromisoForm, ActaForm
from database import get_db_connection
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename

from .auth_routes import login_required
from datetime import datetime

reunion = Blueprint('reunion', __name__)

# Define la carpeta donde se almacenarán los archivos PDF
UPLOAD_FOLDER = 'uploads/actas/'
ALLOWED_EXTENSIONS = {'pdf'}

# Asegúrate de que la carpeta de subidas exista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
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

        cursor.execute("SELECT id, name FROM area")
        form.area.choices = [(area['id'], area['name']) for area in cursor.fetchall()]

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

        cursor.execute("""
            SELECT p.id, p.name, p.lastname, d.name AS departamento, p.position
            FROM persona p
            JOIN persona_departamento pd ON p.id = pd.id_persona
            JOIN departamento d ON pd.id_departamento = d.id
        """)
        # Crear la lista con el formato "Nombre Apellido - Departamento - Cargo"
        responsables_choices = [
            (persona['id'],
             f"{persona['name']} {persona['lastname']} - {persona['departamento']} - {persona['position']}")
            for persona in cursor.fetchall()
        ]
        # Asignar los responsables al formulario de compromisos
        form.compromisos[0].responsables.choices = responsables_choices

    # Validar los campos de la reunión (primer paso)
    def validate_first_step(form):
        is_valid = True
        if not form.origen.validate(form):
            is_valid = False
        if not form.area.validate(form):
            is_valid = False

        return is_valid

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

            acta_pdf = request.files.get('acta_pdf')
            acta_pdf_filename = None

            if acta_pdf and allowed_file(acta_pdf.filename):
                # Almacenar el archivo con un nombre seguro
                acta_pdf_filename = secure_filename(acta_pdf.filename)
                acta_pdf.save(os.path.join(UPLOAD_FOLDER, acta_pdf_filename))
                path = os.path.join(UPLOAD_FOLDER, acta_pdf_filename)

            # Guardar la reunión en la base de datos
            with conn.cursor() as cursor:
                # Obtener los asistentes ingresados manualmente
                asistentes = request.form.get('asistentes')  # Capturar los asistentes ingresados manualmente
                if asistentes:
                    lista_asistentes = [asistente.strip() for asistente in asistentes.split(',')]
                    asistentes_str = ', '.join(lista_asistentes)  # Convertir la lista de asistentes en una cadena de texto

                # Usar .data para obtener los valores de los campos
                cursor.execute("""
                        INSERT INTO reunion (nombre, id_staff, id_area, id_origen, fecha_creacion, asistentes, acta_pdf)
                        VALUES (%s, %s, %s, %s, NOW(), %s,%s) RETURNING id
                    """, ("test", None, area_id, origen_id, asistentes_str, path))

                reunion_id = cursor.fetchone()[0]

            print(f'Reunión creada con ID: {reunion_id}')
            print(f'acta_pdf: {acta_pdf_filename}')
            print(f'formulario: {form.compromisos.data}')
            if form.compromisos.data:
                print(len(form.compromisos.data))
                for compromiso_form in form.compromisos:
                    nombre = compromiso_form['nombre'].data
                    prioridad = compromiso_form['prioridad'].data
                    fecha_limite = compromiso_form['fecha_limite'].data
                    id_departamento = compromiso_form['departamento'].data
                    nivel_avance = 0  # Se establece el nivel de avance en 0 por defecto
                    estado = 'Pendiente'
                    fecha_creacion = datetime.now()

                    # Guardar cada compromiso en la base de datos
                    print(f'Guardando compromiso: {nombre}')
                    with conn.cursor() as cursor:
                        cursor.execute("""
                                insert into compromiso (descripcion, prioridad, fecha_limite, id_departamento, avance, estado, fecha_creacion)
                                values (%s, %s, %s, %s, %s, %s,%s) returning id
                            """, (nombre, prioridad, fecha_limite, id_departamento, nivel_avance, estado, fecha_creacion))

                        compromiso_id = cursor.fetchone()[0]

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

