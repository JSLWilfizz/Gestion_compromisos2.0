import os
from flask import Flask, request, jsonify, render_template
from flask_wtf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager  # Import LoginManager
from config import Config
from routes import auth, home, reunion, director_bp, reunion_routes
from repositories.reunion_service import ReunionService
from models import User  # Import User model


def secure_headers(response):  # Función para aplicar cabeceras de seguridad
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Permitir que la página se cargue en un iframe si proviene del mismo origen
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar las extensiones
    bcrypt = Bcrypt(app)
    csrf = CSRFProtect(app)

    # Configuración de carpetas
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    # Agregar la ruta base para archivos estáticos subidos. 
    # Se asume que los archivos se guardan en 'uploads', por lo que sus subdirectorios se incluyen.
    app.config['STATIC_FOLDER'] = os.path.join(app.root_path, 'uploads')

    app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave secreta segura

    # Aplicar las cabeceras seguras a todas las respuestas
    app.after_request(secure_headers)

    # Registrar los Blueprints
    app.register_blueprint(auth)  # Registrar el blueprint de autenticación
    app.register_blueprint(home)
    app.register_blueprint(reunion)  # Registrar el blueprint de las reuniones
    app.register_blueprint(director_bp)  # Registrar el blueprint del director

    # Nueva ruta para servir archivos subidos en 'uploads'
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['STATIC_FOLDER'], filename)
        
    @app.route('/exportar_pdf', methods=['POST'])
    def exportar_pdf():
        acta_content = request.form.get('acta_content')
        return render_template('acta_pdf.html', acta_content=acta_content)

    return app

if __name__ == '__main__':
    app = create_app()  # Usar la función create_app para crear la aplicación
    app.secret_key = 'clave_super_segura'
    app.run(debug=False)
