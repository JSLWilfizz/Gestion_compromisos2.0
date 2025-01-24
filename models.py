from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    id_persona = db.Column(db.Integer, db.ForeignKey('persona.id'))

    persona = db.relationship('Persona', backref='user')

class Departamento(db.Model):
    __tablename__ = 'departamento'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

class Persona(db.Model):
    __tablename__ = 'persona'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    lastname = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(150), nullable=False)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'))

    departamento = db.relationship('Departamento', backref='personas')

class Compromiso(db.Model):
    __tablename__ = 'compromiso'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(150), nullable=False)
    fecha_limite = db.Column(db.DateTime, nullable=False)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamento.id'))

    departamento = db.relationship('Departamento', backref='compromisos')

class Reunión(db.Model):
    __tablename__ = 'reunion'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False)
    id_staff = db.Column(db.Integer, db.ForeignKey('staff.id'))

    staff = db.relationship('Staff', backref='reuniones')
    compromisos = db.relationship('Compromiso', secondary='reunion_compromiso', backref='reuniones')
    asistentes = db.relationship('Persona', secondary='reunion_asistentes', backref='reuniones')

class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    nombre_staff = db.Column(db.String(150), nullable=False)

# Tabla intermedia para compromisos y reuniones
reunion_compromiso = db.Table('reunion_compromiso',
    db.Column('id_reunion', db.Integer, db.ForeignKey('reunion.id')),
    db.Column('id_compromiso', db.Integer, db.ForeignKey('compromiso.id'))
)

# Tabla intermedia para asistentes a reuniones
reunion_asistentes = db.Table('reunion_asistentes',
    db.Column('id_reunion', db.Integer, db.ForeignKey('reunion.id')),
    db.Column('id_persona', db.Integer, db.ForeignKey('persona.id'))
)
