import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_wtf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, logout_user
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from config import Config
from routes import auth, home, reunion, director_bp, reunion_routes
from repositories.reunion_service import ReunionService
from models import (
    User, Departamento, Persona, Compromiso, Reunion, Staff, Area, Origen, 
    CompromisoEliminado, CompromisosArchivados, Invitados, CompromisoModificaciones,
    ReunionCompromiso, ReunionCompromisoEliminado, ReunionCompromisoArchivado,
    PersonaCompromiso, PersonaCompromisoArchivado, PersonaCompromisoEliminado
)
from extensions import db, login_manager  # Asegúrate de importar login_manager
from routes.auth_routes import login_required, set_alert
from database import get_db_connection

# Inicializar LoginManager
login_manager = LoginManager()

@login_manager.user_loader
def load_user(username):
    return User.query.get(username)

def secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

class CustomModelView(ModelView):
    column_display_pk = True  # Mostrar la clave primaria en Flask-Admin
    can_view_details = True  # Permitir ver detalles
    column_filters = ['id']  # Agregar un filtro global por ID

class PersonaCompromisoView(CustomModelView):
    column_list = ('id_persona', 'id_compromiso', 'es_responsable_principal')
    column_labels = {
        'id_persona': 'ID Persona',
        'id_compromiso': 'ID Compromiso',
        'es_responsable_principal': 'Es Responsable Principal'
    }
    column_filters = ['id_persona', 'id_compromiso']  # Agregar filtros específicos

class ReunionCompromisoView(CustomModelView):
    column_list = ('id_reunion', 'id_compromiso')
    column_labels = {
        'id_reunion': 'ID Reunión',
        'id_compromiso': 'ID Compromiso'
    }
    column_filters = ['id_reunion', 'id_compromiso']  # Agregar filtros específicos

class UserView(CustomModelView):
    column_list = ('username', 'id_persona')
    column_labels = {
        'username': 'Username',
        'id_persona': 'ID Persona'
    }
    column_filters = ['username', 'id_persona']
    form_columns = ['username', 'password', 'id_persona']  

class DepartamentoView(CustomModelView):
    column_list = ('id', 'name', 'id_departamento_padre')
    column_labels = {
        'id': 'ID',
        'name': 'Nombre',
        'id_departamento_padre': 'ID Departamento Padre'
    }
    column_filters = ['id', 'name', 'id_departamento_padre']

class PersonaView(CustomModelView):
    column_list = ('id', 'name', 'lastname', 'rut', 'dv', 'profesion', 'correo', 'cargo', 'anexo_telefonico', 'nivel_jerarquico')
    column_labels = {
        'id': 'ID',
        'name': 'Nombre',
        'lastname': 'Apellido',
        'rut': 'RUT',
        'dv': 'DV',
        'profesion': 'Profesión',
        'correo': 'Correo',
        'cargo': 'Cargo',
        'anexo_telefonico': 'Anexo Telefónico',
        'nivel_jerarquico': 'Nivel Jerárquico'
    }
    column_filters = ['id', 'name', 'lastname', 'rut', 'dv', 'profesion', 'correo', 'cargo', 'anexo_telefonico', 'nivel_jerarquico']

class CompromisoView(CustomModelView):
    column_list = ('id', 'descripcion', 'estado', 'prioridad', 'fecha_creacion', 'avance', 'fecha_limite', 'comentario', 'comentario_direccion', 'id_departamento', 'id_area', 'id_origen')
    column_labels = {
        'id': 'ID',
        'descripcion': 'Descripción',
        'estado': 'Estado',
        'prioridad': 'Prioridad',
        'fecha_creacion': 'Fecha de Creación',
        'avance': 'Avance',
        'fecha_limite': 'Fecha Límite',
        'comentario': 'Comentario',
        'comentario_direccion': 'Comentario Dirección',
        'id_departamento': 'ID Departamento',
        'id_area': 'ID Área',
        'id_origen': 'ID Origen'
    }
    column_filters = ['id', 'descripcion', 'estado', 'prioridad', 'fecha_creacion', 'avance', 'fecha_limite', 'comentario', 'comentario_direccion', 'id_departamento', 'id_area', 'id_origen']

class ReunionView(CustomModelView):
    column_list = ('id', 'nombre', 'id_staff', 'id_area', 'id_origen', 'fecha_creacion', 'lugar', 'asistentes', 'proximas_reuniones', 'acta_pdf', 'correos', 'temas_analizado', 'tema')
    column_labels = {
        'id': 'ID',
        'nombre': 'Nombre',
        'id_staff': 'ID Staff',
        'id_area': 'ID Área',
        'id_origen': 'ID Origen',
        'fecha_creacion': 'Fecha de Creación',
        'lugar': 'Lugar',
        'asistentes': 'Asistentes',
        'proximas_reuniones': 'Próximas Reuniones',
        'acta_pdf': 'Acta PDF',
        'correos': 'Correos',
        'temas_analizado': 'Temas Analizados',
        'tema': 'Tema'
    }
    column_filters = ['id', 'nombre', 'id_staff', 'id_area', 'id_origen', 'fecha_creacion', 'lugar', 'asistentes', 'proximas_reuniones', 'acta_pdf', 'correos', 'temas_analizado', 'tema']

class InvitadosAdmin(CustomModelView):
    column_display_pk = True
    form_columns = ['id_invitado', 'nombre_completo', 'institucion', 'correo', 'telefono']
    column_list = ['id_invitado', 'nombre_completo', 'institucion', 'correo', 'telefono']
    column_labels = {
        'id_invitado': 'ID Invitado',
        'nombre_completo': 'Nombre Completo',
        'institucion': 'Institución',
        'correo': 'Correo',
        'telefono': 'Teléfono'
    }

class ProtectedAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if 'user_id' not in session:
            return False
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id_persona = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user and user[0] == '0'

    def inaccessible_callback(self, name, **kwargs):
        set_alert("No tienes permisos para acceder a esta página.", "danger")
        return redirect(url_for('home.home_view'))

class ProtectedModelView(ModelView):
    def is_accessible(self):
        if 'user_id' not in session:
            return False
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id_persona = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user and user[0] == '0'

    def inaccessible_callback(self, name, **kwargs):
        set_alert("No tienes permisos para acceder a esta página.", "danger")
        return redirect(url_for('home.home_view'))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar las extensiones
    bcrypt = Bcrypt(app)
    csrf = CSRFProtect(app)
    db.init_app(app)  # Asegúrate de inicializar db
    login_manager.init_app(app)  # Inicializar LoginManager

    # Configuración de carpetas
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['STATIC_FOLDER'] = os.path.join(app.root_path, 'static')  # Esto debería ser 'static', no 'uploads'
    
    # Asegurar que las carpetas de subida existan
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'verificadores'), exist_ok=True)

    # Configurar tamaño máximo de archivo (32MB)
    app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
    print(f"Configurado MAX_CONTENT_LENGTH a {app.config['MAX_CONTENT_LENGTH']} bytes")

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message_category = 'info'

    # Configurar Flask-Admin with custom index view
    admin = Admin(app, name='Gestion Compromisos', template_mode='bootstrap4',
                  url='/admin', index_view=ProtectedAdminIndexView())
    admin.add_view(ProtectedModelView(User, db.session, endpoint='admin/users'))
    admin.add_view(ProtectedModelView(Departamento, db.session, endpoint='admin/departamento'))
    admin.add_view(ProtectedModelView(Persona, db.session, endpoint='admin/persona'))
    admin.add_view(ProtectedModelView(Compromiso, db.session, endpoint='admin/compromiso'))
    admin.add_view(ProtectedModelView(Reunion, db.session, endpoint='admin/reunion'))
    admin.add_view(ProtectedModelView(Staff, db.session, endpoint='admin/staff'))
    admin.add_view(ProtectedModelView(Area, db.session, endpoint='admin/area'))
    admin.add_view(ProtectedModelView(Origen, db.session, endpoint='admin/origen'))
    admin.add_view(ProtectedModelView(Invitados, db.session, endpoint='admin/invitados'))
    admin.add_view(ProtectedModelView(CompromisoEliminado, db.session, endpoint='admin/compromiso_eliminado'))
    admin.add_view(ProtectedModelView(CompromisosArchivados, db.session, endpoint='admin/compromisos_archivados'))
    admin.add_view(ProtectedModelView(CompromisoModificaciones, db.session, endpoint='admin/compromiso_modificaciones'))

    # Agregar tablas intermedias con vistas personalizadas
    admin.add_view(ReunionCompromisoView(ReunionCompromiso, db.session, endpoint='admin/reunion_compromiso'))
    admin.add_view(ReunionCompromisoView(ReunionCompromisoEliminado, db.session, endpoint='admin/reunion_compromiso_eliminado'))
    admin.add_view(ReunionCompromisoView(ReunionCompromisoArchivado, db.session, endpoint='admin/reunion_compromiso_archivado'))
    admin.add_view(PersonaCompromisoView(PersonaCompromiso, db.session, endpoint='admin/persona_compromiso'))
    admin.add_view(PersonaCompromisoView(PersonaCompromisoArchivado, db.session, endpoint='admin/persona_compromiso_archivado'))
    admin.add_view(PersonaCompromisoView(PersonaCompromisoEliminado, db.session, endpoint='admin/persona_compromiso_eliminado'))

    admin.add_link(MenuLink(name='Cerrar sesión', category='', url='/admin/logout'))

    # Configuración de carpetas
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['STATIC_FOLDER'] = os.path.join(app.root_path, 'uploads')

    app.secret_key = 'tu_clave_secreta'

    app.after_request(secure_headers)

    # Registrar los Blueprints
    app.register_blueprint(auth)
    app.register_blueprint(home)
    app.register_blueprint(reunion, url_prefix='/reunion')
    app.register_blueprint(director_bp)

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        # Normalize path separators for consistency
        filename = filename.replace('\\', '/')
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        
    @app.route('/exportar_pdf', methods=['POST'])
    def exportar_pdf():
        acta_content = request.form.get('acta_content')
        return render_template('acta_pdf.html', acta_content=acta_content)

    @app.route('/admin')
    @login_required
    def admin_index():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE username = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user or user[1] != '0':
            set_alert("No tienes permisos para acceder a esta página.", "danger")
            return redirect(url_for('home.home_view'))
        return redirect(url_for('auth.login'))
    @login_required
    def admin_mis_tablas():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE username = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user or user[1] != '0':
            set_alert("No tienes permisos para acceder a esta página.", "danger")
            return redirect(url_for('home.home_view'))
        return redirect(url_for('auth.login'))

    @app.route('/admin/logout')
    def admin_logout():
        logout_user()
        session.clear()
        set_alert("Sesión de administrador cerrada correctamente.", "success")
        return redirect(url_for('auth.login'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.secret_key = 'clave_super_segura'
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode)