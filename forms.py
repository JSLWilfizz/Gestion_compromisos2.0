from datetime import datetime, date

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField, DateTimeField, SelectField, FieldList, \
    FormField, DateField, IntegerField
from wtforms import TextAreaField,StringField, SelectField, DateTimeField, SubmitField, FieldList, FormField, SelectMultipleField, DateField
from wtforms.validators import DataRequired, Optional, ValidationError, NumberRange
from flask_wtf.file import FileAllowed, FileField


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class ActaForm(FlaskForm):
    acta_pdf = FileField('Subir Acta (PDF)', validators=[FileAllowed(['pdf'], 'Solo se permiten archivos PDF')])
    submit = SubmitField('Subir Acta')
class MultiSelectField(SelectMultipleField):
    def process_formdata(self, valuelist):
        try:
            self.data = [int(value) for value in valuelist]
        except ValueError:
            raise ValidationError("Invalid input, not all choices are valid integers.")


class CompromisoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])  # Eliminar DataRequired() para hacerlo opcional
    estado = SelectField('Estado', choices=[('Pendiente', 'Pendiente'), ('Completado', 'Completado')])  # Opcional
    prioridad = SelectField('Prioridad', choices=[('Alta', 'Alta'), ('Media', 'Media'), ('Baja', 'Baja')])  # Opcional
    fecha_limite = DateField('Fecha Límite', format='%Y-%m-%d')  # Opcional
    fecha_creacion = DateField('Fecha Creación', default=datetime.now(),
                               format='%Y-%m-%d')  # Mantener la fecha de creación pero opcional

    departamento = SelectField('Departamento', choices=[])  # Opcional, choices cargados dinámicamente
    nivel_avance = IntegerField('Nivel de Avance',
                                validators=[NumberRange(min=0, max=100)])  # Opcional, manteniendo el rango de 0 a 100

    responsables = MultiSelectField('Responsables', choices=[])  # Opcional, choices cargados dinámicamente


class CreateMeetingForm(FlaskForm):
    origen = SelectField('Origen', validators=[DataRequired()], choices=[], description="Si no encuentras el origen, escríbelo en el campo de abajo")
    area = SelectField('Área', validators=[DataRequired()], choices=[], description="Si no encuentras el área, escríbela en el campo de abajo")
    asistentes = StringField('Asistentes', validators=[DataRequired()], description="Separar los nombres con comas")
    compromisos = FieldList(FormField(CompromisoForm), min_entries=1)  # Asegúrate de tener FieldList para compromisos
    submit = SubmitField('Confirmar Reunión')

