# /routes/reunion_routes.py
import traceback

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify, current_app, send_from_directory
from .auth_routes import login_required
from repositories.reunion_service import ReunionService
from validators.reunion_validator import ReunionValidator
from werkzeug.utils import secure_filename
from forms import CreateMeetingForm
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from repositories.reunion_service import ReunionService
from .auth_routes import login_required
import logging

reunion = Blueprint('reunion', __name__)
service = ReunionService()

UPLOAD_FOLDER = 'uploads/'  # Changed from 'uploads/actas/'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'ppt', 'pptx', 'xls', 'xlsx', 'pbix'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def set_alert(message, alert_type='info'):
    session['alert'] = {'message': message, 'type': alert_type}

@reunion.route('/reunion/crear_paso1', methods=['GET', 'POST'])
@login_required
def crear_reunion_paso1():
    form = CreateMeetingForm()
    service.get_initial_form_data(form)

    session.pop('compromisos_data', None)
    session.pop('reunion_data', None)

    if request.method == 'POST' and ReunionValidator.validate_first_step(form):
        try:
            uploaded_files = request.files.getlist('acta_pdf')
            file_paths = []
            for file_item in uploaded_files:
                if file_item and allowed_file(file_item.filename):
                    ext = file_item.filename.rsplit('.', 1)[1].lower()
                    from datetime import datetime
                    now = datetime.now()
                    year = now.strftime("%Y")
                    month = now.strftime("%m")
                    day = now.strftime("%d")
                    # Build folder path: uploads/{ext}/{year}/{month}/{day}
                    target_folder = os.path.join(UPLOAD_FOLDER, ext, year, month, day)
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    filename = secure_filename(file_item.filename)
                    file_save_path = os.path.join(target_folder, filename)
                    file_item.save(file_save_path)
                    file_paths.append(file_save_path)
            acta_pdf_path = ';'.join(file_paths) if file_paths else None

            tema_values = [value.replace('\n', ';') for value in request.form.getlist('tema')]
            temas_analizados_values = [value.replace('\n', ';') for value in request.form.getlist('temas_analizado')]
            proximas_reuniones_values = [value.replace('\n', ';') for value in request.form.getlist('proximas_fechas')]

            tema_concatenado = ';'.join(tema_values)
            temas_analizados_concatenado = ';'.join(temas_analizados_values)
            proximas_reuniones_concatenado = ';'.join(proximas_reuniones_values)

            fecha_creacion = request.form.get('fecha_reunion')
            fecha_limite = request.form.get('fecha_limite')

            service.create_reunion(form, request.form, acta_pdf_path, tema_concatenado, temas_analizados_concatenado, proximas_reuniones_concatenado, fecha_creacion, fecha_limite)
            print(request.form)
            set_alert('Reunión creada con éxito.', 'success')
            return redirect(url_for('home.home_view'))

        except Exception as e:
            error_line = traceback.format_exc().splitlines()[-1]  # Última línea con detalle del error
            detailed_trace = traceback.format_exc()  # Traza completa del error

            # Mensaje de error para el usuario
            set_alert(f"Ocurrió un error al crear la reunión: {e} en {error_line}", 'danger')

            # Opcional: imprimir la traza completa en los logs o consola para depuración
            print("Detalles del error:\n", detailed_trace)
            set_alert(f"Ocurrió un error al crear la reunión: {e} en {error_line}", 'danger')

    return render_template('crear_reunion.html', form=form)

@reunion.route('/add_invitado', methods=['POST'])
def add_invitado():
    nombre = request.form.get('nombre')
    institucion = request.form.get('institucion')
    correo = request.form.get('correo')
    telefono = request.form.get('telefono')

    if not nombre or not institucion or not correo or not telefono:
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400

    try:
        logging.debug(f"Datos recibidos: nombre={nombre}, institucion={institucion}, correo={correo}, telefono={telefono}")
        invitado_id = service.add_invitado(nombre, institucion, correo, telefono)  # Call the method on the service object
        logging.debug(f"Invitado guardado con ID: {invitado_id}")
        return jsonify({'id': invitado_id, 'nombre': nombre, 'institucion': institucion, 'correo': correo, 'telefono': telefono}), 200
    except Exception as e:
        logging.error(f"Error al guardar el invitado: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reunion.route('/reunion/actas_reuniones', methods=['GET'])
@login_required
def actas_reuniones():
    return render_template('actas_reuniones.html')

@reunion.route('/reunion/ver/<int:compromiso_id>', methods=['GET'])
@login_required
def ver_reunion(compromiso_id):
    try:
        reunion_info = service.get_reunion_by_compromiso_id(compromiso_id)
        if not reunion_info:
            set_alert('No se encontró información de la reunión asociada.', 'warning')
            return redirect(url_for('home.ver_compromisos_compartidos'))
        reunion_info['origen_name'] = service.get_origen_name(reunion_info['id_origen'])
        reunion_info['area_name'] = service.get_area_name(reunion_info['id_area'])
        return render_template('ver_reunion.html', reunion=reunion_info)
    except Exception as e:
        logging.error(f"Error al obtener la información de la reunión: {str(e)}")
        set_alert('Ocurrió un error al obtener la información de la reunión.', 'danger')
        return redirect(url_for('home.ver_compromisos_compartidos'))

@reunion.route('/reunion/ver_archivos/<int:reunion_id>', methods=['GET'])
@login_required
def ver_archivos(reunion_id):
    reunion_obj = service.get_reunion_by_id(reunion_id)
    archivos = []
    if reunion_obj and reunion_obj.get('acta_pdf'):
        file_paths = reunion_obj['acta_pdf'].split(';')
        for p in file_paths:
            if p.strip():
                archivos.append(p.strip())
    return render_template('ver_archivos.html', archivos=archivos)

@reunion.route('/get_file/<path:filename>', methods=['GET'])
@login_required
def get_file(filename):
    import os
    # Normalize separators and remove any 'uploads/' prefix
    filename = filename.replace('\\', '/')
    if filename.startswith("uploads/"):
        filename = filename[len("uploads/"):]
    filename = os.path.normpath(filename)
    base_folder = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    file_path = os.path.join(base_folder, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_from_directory(base_folder, filename)

@reunion.route('/reunion/filtrar', methods=['GET', 'POST'])
@login_required
def filtrar_reuniones():
    user_id = session.get('user_id')
    if request.method == 'POST':
        search = request.form.get('search')
        fecha = request.form.get('fecha')
        origen = request.form.get('origen')
        tema = request.form.get('tema')
        lugar = request.form.get('lugar')
        referente = request.form.get('referente')

        reuniones = service.filtrar_reuniones(user_id, search, fecha, origen, tema, lugar, referente)
        return render_template('mis_reuniones.html', reuniones=reuniones)

    origenes = service.get_origenes()
    return render_template('filtrar_reuniones.html', origenes=origenes)

@reunion.route('/reunion/mis_reuniones', methods=['GET'])
@login_required
def mis_reuniones():
    user_id = session.get('user_id')
    reuniones = service.get_mis_reuniones(user_id)
    return render_template('mis_reuniones.html', reuniones=reuniones)


