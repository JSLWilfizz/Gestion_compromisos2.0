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
    alert = None
    form_data = {}  # Para almacenar los datos del formulario en caso de error

    session.pop('compromisos_data', None)
    session.pop('reunion_data', None)

    if request.method == 'POST' and ReunionValidator.validate_first_step(form):
        # Guardar los datos del formulario
        form_data = {
            'nombre_reunion': request.form.get('nombre_reunion', ''),
            'lugar': request.form.get('lugar', ''),
            'tema': request.form.get('tema', ''),
            'fecha_reunion': request.form.get('fecha_reunion', ''),
            'origen': request.form.get('origen', ''),  # Asegúrate de que este campo exista en el formulario
            'area': request.form.get('area', ''),     # Asegúrate de que este campo exista en el formulario
            'temas_analizado': request.form.get('temas_analizado', ''),
            'proximas_reuniones': request.form.get('proximas_reuniones', '')
        }
        
        # Log para depuración
        print(f"DEBUG - Datos del formulario: origen={form_data['origen']}, area={form_data['area']}")
        
        # Obtener datos de compromisos
        compromisos_data = []
        index = 1
        while True:
            nombre_key = f'compromisos-{index}-nombre'
            if nombre_key not in request.form:
                break
                
            compromiso = {
                'nombre': request.form.get(nombre_key, ''),
                'prioridad': request.form.get(f'compromisos-{index}-prioridad', ''),
                'fecha_limite': request.form.get(f'compromisos-{index}-fecha_limite', ''),
                'departamento': request.form.get(f'compromisos-{index}-departamento', ''),
                'referentes': request.form.getlist(f'compromisos-{index}-referentes')
            }
            compromisos_data.append(compromiso)
            index += 1
        
        form_data['compromisos'] = compromisos_data
        form_data['asistentes'] = request.form.getlist('asistentes[]')
        form_data['invitados'] = request.form.getlist('invitados[]')
        
        try:
            # Verificación explícita de compromisos
            compromisos_count = 0
            for key in request.form:
                if key.startswith('compromisos-') and key.endswith('-nombre'):
                    if request.form.get(key).strip():
                        compromisos_count += 1
            
            if compromisos_count == 0:
                raise ValueError("Es necesario tener al menos un compromiso por reunión")
            
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
            # Extraer proximas reuniones desde el textarea
            proximas_reuniones_text = request.form.get('proximas_reuniones', '').replace('\n', ';')
            
            tema_concatenado = ';'.join(tema_values)
            temas_analizados_concatenado = ';'.join(temas_analizados_values)
            proximas_reuniones_concatenado = proximas_reuniones_text

            # Nuevos logs para depurar
            current_app.logger.debug(f"tema_concatenado: {tema_concatenado}")
            current_app.logger.debug(f"temas_analizados_concatenado: {temas_analizados_concatenado}")
            current_app.logger.debug(f"proximas_reuniones_concatenado: {proximas_reuniones_concatenado}")

            fecha_creacion = request.form.get('fecha_reunion')
            fecha_limite = request.form.get('fecha_limite')

            service.create_reunion(form, request.form, acta_pdf_path, tema_concatenado, temas_analizados_concatenado, proximas_reuniones_concatenado, fecha_creacion, fecha_limite)
            print(request.form)
            set_alert('Reunión creada con éxito.', 'success')
            return redirect(url_for('home.home_view'))

        except ValueError as ve:
            # Para errores de validación, muestra mensaje claro
            alert = {'message': str(ve), 'type': 'danger'}
            current_app.logger.warning(f"Error de validación: {str(ve)}")
        
        except Exception as e:
            error_line = traceback.format_exc().splitlines()[-1]  # Última línea con detalle del error
            detailed_trace = traceback.format_exc()  # Traza completa del error
            
            # Mensaje de error para mostrar en la misma página, no redireccionando
            error_message = f"Ocurrió un error al crear la reunión: {e}"
            alert = {'message': error_message, 'type': 'danger'}
            
            # Imprimir la traza completa en los logs para depuración
            current_app.logger.error("Detalles del error:\n%s", detailed_trace)

    return render_template('crear_reunion.html', form=form, alert=alert, some_reunion_id_value=None, form_data=form_data)

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

@reunion.route('/get_areas_by_departamento', methods=['GET'])
@login_required
def get_areas_by_departamento():
    departamento_id = request.args.get('departamento_id', type=int)
    if not departamento_id:
        return jsonify([])
    
    areas = service.get_areas_by_departamento(departamento_id)
    return jsonify(areas)

@reunion.route('/get_origenes_by_departamento', methods=['GET'])
@login_required
def get_origenes_by_departamento():
    departamento_id = request.args.get('departamento_id', type=int)
    if not departamento_id:
        return jsonify([])
    
    origenes = service.get_origenes_by_departamento(departamento_id)
    return jsonify(origenes)


