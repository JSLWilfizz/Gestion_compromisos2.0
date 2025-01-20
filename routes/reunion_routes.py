# /routes/reunion_routes.py
import traceback

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from .auth_routes import login_required
from repositories.reunion_service import ReunionService
from validators.reunion_validator import ReunionValidator
from werkzeug.utils import secure_filename
from forms import CreateMeetingForm
import os
from datetime import datetime

reunion = Blueprint('reunion', __name__)
service = ReunionService()

UPLOAD_FOLDER = 'uploads/actas/'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@reunion.route('/reunion/crear_paso1', methods=['GET', 'POST'])
@login_required
def crear_reunion_paso1():
    form = CreateMeetingForm()
    service.get_initial_form_data(form)

    session.pop('compromisos_data', None)
    session.pop('reunion_data', None)

    if request.method == 'POST' and ReunionValidator.validate_first_step(form):
        try:
            acta_pdf = request.files.get('acta_pdf')
            acta_pdf_path = None
            if (acta_pdf and allowed_file(acta_pdf.filename)):
                acta_pdf_filename = secure_filename(acta_pdf.filename)
                acta_pdf.save(os.path.join(UPLOAD_FOLDER, acta_pdf_filename))
                acta_pdf_path = os.path.join(UPLOAD_FOLDER, acta_pdf_filename)

            tema_values = [value.replace('\n', ';') for value in request.form.getlist('tema')]
            temas_analizados_values = [value.replace('\n', ';') for value in request.form.getlist('temas_analizado')]
            proximas_reuniones_values = [value.replace('\n', ';') for value in request.form.getlist('proximas_fechas')]

            tema_concatenado = ';'.join(tema_values)
            temas_analizados_concatenado = ';'.join(temas_analizados_values)
            proximas_reuniones_concatenado = ';'.join(proximas_reuniones_values)

            fecha_creacion = request.form.get('fecha_reunion')

            service.create_reunion(form, request.form, acta_pdf_path, tema_concatenado, temas_analizados_concatenado, proximas_reuniones_concatenado, fecha_creacion)
            print(request.form)
            return redirect(url_for('home.home_view'))

        except Exception as e:
            error_line = traceback.format_exc().splitlines()[-1]  # Última línea con detalle del error
            detailed_trace = traceback.format_exc()  # Traza completa del error

            # Mensaje de error para el usuario
            flash(f"Ocurrió un error al crear la reunión: {e} en {error_line}", 'danger')

            # Opcional: imprimir la traza completa en los logs o consola para depuración
            print("Detalles del error:\n", detailed_trace)
            flash(f'Ocurrió un error al crear la reunión: {e}', 'danger')

    return render_template('crear_reunion.html', form=form)




