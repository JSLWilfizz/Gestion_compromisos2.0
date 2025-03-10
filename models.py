# filepath: /c:/Users/jsotoletelier/Documents/GitHub/Gestion_compromisos2.0/models.py
from extensions import db
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(255), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    id_persona = db.Column(db.Integer, db.ForeignKey('persona.id'))

    persona = db.relationship('Persona', backref='user')

    def get_id(self):
        return self.username

class Departamento(db.Model):
    __tablename__ = 'departamento'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    id_departamento_padre = db.Column(db.Integer, db.ForeignKey('departamento.id'))

class Persona(db.Model):
    __tablename__ = 'persona'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    lastname = db.Column(db.String(255), nullable=False)
    rut = db.Column(db.String(12), nullable=False)
    dv = db.Column(db.String(1), nullable=False)
    profesion = db.Column(db.String(255))
    correo = db.Column(db.String(255))
    cargo = db.Column(db.String(255))
    anexo_telefonico = db.Column(db.String(255))
    nivel_jerarquico = db.Column(db.String(255))

class Compromiso(db.Model):
    __tablename__ = 'compromiso'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(255), nullable=False)
    prioridad = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime)
    avance = db.Column(db.Integer)
    fecha_limite = db.Column(db.DateTime)
    comentario = db.Column(db.Text)
    comentario_direccion = db.Column(db.Text)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'))
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    id_origen = db.Column(db.Integer, db.ForeignKey('origen.id'))

    departamento = db.relationship('Departamento', backref='compromisos')
    area = db.relationship('Area', backref='compromisos')
    origen = db.relationship('Origen', backref='compromisos')

class CompromisoEliminado(db.Model):
    __tablename__ = 'compromiso_eliminado'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(255))
    prioridad = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime)
    avance = db.Column(db.Integer)
    fecha_limite = db.Column(db.DateTime)
    comentario = db.Column(db.Text)
    comentario_direccion = db.Column(db.Text)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'))
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    id_origen = db.Column(db.Integer, db.ForeignKey('origen.id'))
    fecha_eliminacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    eliminado_por = db.Column(db.Integer, db.ForeignKey('persona.id'))

    departamento = db.relationship('Departamento', backref='compromisos_eliminados')
    area = db.relationship('Area', backref='compromisos_eliminados')
    origen = db.relationship('Origen', backref='compromisos_eliminados')
    persona = db.relationship('Persona', backref='compromisos_eliminados')

class CompromisosArchivados(db.Model):
    __tablename__ = 'compromisos_archivados'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(255))
    prioridad = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime)
    avance = db.Column(db.Integer)
    fecha_limite = db.Column(db.DateTime)
    comentario = db.Column(db.Text)
    comentario_direccion = db.Column(db.Text)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'))
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    id_origen = db.Column(db.Integer, db.ForeignKey('origen.id'))
    fecha_archivado = db.Column(db.DateTime, default=db.func.current_timestamp())
    archivado_por = db.Column(db.Integer, db.ForeignKey('persona.id'))

    departamento = db.relationship('Departamento', backref='compromisos_archivados')
    area = db.relationship('Area', backref='compromisos_archivados')
    origen = db.relationship('Origen', backref='compromisos_archivados')
    persona = db.relationship('Persona', backref='compromisos_archivados')

class CompromisoModificaciones(db.Model):
    __tablename__ = 'compromiso_modificaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_compromiso = db.Column(db.Integer, db.ForeignKey('compromiso.id'))
    id_usuario = db.Column(db.Integer, db.ForeignKey('persona.id'))
    fecha_modificacion = db.Column(db.DateTime, default=db.func.current_timestamp())

    compromiso = db.relationship('Compromiso', backref='modificaciones')
    usuario = db.relationship('Persona', backref='modificaciones')

class Reunion(db.Model):
    __tablename__ = 'reunion'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255))
    id_staff = db.Column(db.Integer, db.ForeignKey('staff.id'))
    id_area = db.Column(db.Integer, db.ForeignKey('area.id'))
    id_origen = db.Column(db.Integer, db.ForeignKey('origen.id'))
    fecha_creacion = db.Column(db.DateTime)
    lugar = db.Column(db.String(255))
    asistentes = db.Column(db.Text)
    proximas_reuniones = db.Column(db.Text)
    acta_pdf = db.Column(db.String(255))
    correos = db.Column(db.Text)
    temas_analizado = db.Column(db.Text)
    tema = db.Column(db.Text)

    staff = db.relationship('Staff', backref='reuniones')
    area = db.relationship('Area', backref='reuniones')
    origen = db.relationship('Origen', backref='reuniones')
    compromisos = db.relationship('Compromiso', secondary='reunion_compromiso', backref='reuniones')

class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Area(db.Model):
    __tablename__ = 'area'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Origen(db.Model):
    __tablename__ = 'origen'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Invitados(db.Model):
    __tablename__ = 'invitados'
    id_invitado = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(255), nullable=False)
    institucion = db.Column(db.String(255), nullable=False)
    correo = db.Column(db.String(255), nullable=False, unique=True)
    telefono = db.Column(db.String(255))
    
    @hybrid_property
    def id(self):
        return self.id_invitado

# Tablas intermedias
class ReunionCompromiso(db.Model):
    __tablename__ = 'reunion_compromiso'
    id_reunion = db.Column(db.Integer, db.ForeignKey('reunion.id'), primary_key=True)
    id_compromiso = db.Column(db.Integer, db.ForeignKey('compromiso.id'), primary_key=True)

class ReunionCompromisoEliminado(db.Model):
    __tablename__ = 'reunion_compromiso_eliminado'
    id_reunion = db.Column(db.Integer, db.ForeignKey('reunion.id'), primary_key=True)
    id_compromiso = db.Column(db.Integer, db.ForeignKey('compromiso_eliminado.id'), primary_key=True)

class ReunionCompromisoArchivado(db.Model):
    __tablename__ = 'reunion_compromiso_archivado'
    id_reunion = db.Column(db.Integer, db.ForeignKey('reunion.id'), primary_key=True)
    id_compromiso = db.Column(db.Integer, db.ForeignKey('compromisos_archivados.id'), primary_key=True)

class PersonaCompromiso(db.Model):
    __tablename__ = 'persona_compromiso'
    id_persona = db.Column(db.Integer, db.ForeignKey('persona.id'), primary_key=True)
    id_compromiso = db.Column(db.Integer, db.ForeignKey('compromiso.id'), primary_key=True)
    es_responsable_principal = db.Column(db.Boolean, default=False)

class PersonaCompromisoArchivado(db.Model):
    __tablename__ = 'persona_compromiso_archivado'
    id_persona = db.Column(db.Integer, db.ForeignKey('persona.id'), primary_key=True)
    id_compromiso = db.Column(db.Integer, db.ForeignKey('compromisos_archivados.id'), primary_key=True)
    es_responsable_principal = db.Column(db.Boolean, default=False)

class PersonaCompromisoEliminado(db.Model):
    __tablename__ = 'persona_compromiso_eliminado'
    id_persona = db.Column(db.Integer, db.ForeignKey('persona.id'), primary_key=True)
    id_compromiso = db.Column(db.Integer, db.ForeignKey('compromiso_eliminado.id'), primary_key=True)
    es_responsable_principal = db.Column(db.Boolean, default=False)