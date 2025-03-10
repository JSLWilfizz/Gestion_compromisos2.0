from datetime import datetime, date

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField, DateTimeField, SelectField, FieldList, \
    FormField, DateField, IntegerField, TextAreaField, HiddenField
from wtforms import TextAreaField,StringField, SelectField, DateTimeField, SubmitField, FieldList, FormField, SelectMultipleField, DateField
from wtforms.validators import DataRequired, Optional, ValidationError, NumberRange, Length
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
    estado = SelectField('Estado', choices=[('Pendiente', 'Pendiente'), ('Completado', 'Completado')],default="Pendiente")  # Opcional
    prioridad = SelectField('Prioridad', choices=[('Alta', 'Alta'), ('Media', 'Media'), ('Baja', 'Baja')])  # Opcional
    fecha_limite = DateTimeField('Fecha Límite', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])  # Opcional
    fecha_creacion = DateField('Fecha Creación', default=datetime.now(),
                               format='%Y-%m-%d')  # Mantener la fecha de creación pero opcional
    departamento = SelectField('Departamento', choices=[])  # Opcional, choices cargados dinámicamente
    nivel_avance = IntegerField('Nivel de Avance',
                                validators=[NumberRange(min=0, max=100)],default=0)  # Opcional, manteniendo el rango de 0 a 100
    referentes = MultiSelectField('Referentes', choices=[])  # Opcional, choices cargados dinámicamente

class CreateCompromisoForm(FlaskForm):
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    estado = SelectField('Estado', choices=[('Pendiente', 'Pendiente'), ('Completado', 'Completado')], validators=[DataRequired()])
    prioridad = SelectField('Prioridad', choices=[('Alta', 'Alta'), ('Media', 'Media'), ('Baja', 'Baja')], validators=[DataRequired()])
    fecha_creacion = DateTimeField('Fecha de Creación', format='%Y-%m-%dT%H:%M', default=datetime.now, validators=[DataRequired()])
    fecha_limite = DateTimeField('Fecha Límite', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    comentario = TextAreaField('Comentario')
    comentario_direccion = TextAreaField('Comentario Dirección')
    id_departamento = SelectField('Departamento', choices=[], validators=[DataRequired()])
    # Asegurarnos de coercer los valores a string para consistencia
    origen = SelectField('Origen', choices=[], coerce=str, validators=[Optional()])
    area = SelectField('Área', choices=[], coerce=str, validators=[Optional()])
    referentes = MultiSelectField('Referentes', choices=[], validators=[DataRequired()])
    submit = SubmitField('Crear Compromiso')

class CreateMeetingForm(FlaskForm):
    origen = SelectField('Origen', validators=[DataRequired()], choices=[], description="Si no encuentras el origen, escríbelo en el campo de abajo")
    area = SelectField('Área', validators=[DataRequired()], choices=[], description="Si no encuentras el área, escríbela en el campo de abajo")
    asistentes = StringField('Asistentes', validators=[DataRequired()], description="Separar los nombres con comas")
    invitados = SelectMultipleField('Invitados', choices=[], coerce=int)  # Ya existente
    compromisos = FieldList(FormField(CompromisoForm), min_entries=1)  # Asegúrate de tener FieldList para compromisos
    acta_pdf = FileField('Subir Acta (PDF o Imagen)', validators=[FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'gif'], 'Solo se permiten archivos PDF o imágenes')])
    submit = SubmitField('Confirmar Reunión')
    
    def __init__(self, *args, **kwargs):
        super(CreateMeetingForm, self).__init__(*args, **kwargs)
        # Esto ya está gestionado en ReunionService.get_initial_form_data

