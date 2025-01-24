import os
from flask import Flask, request, jsonify, render_template
from flask_wtf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager  # Import LoginManager
from config import Config
from routes import auth, home, reunion, director_bp
from repositories.reunion_service import ReunionService
from models import User  # Import User model

def secure_headers(response):  # Función para aplicar cabeceras de seguridad
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
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
    app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave secreta segura

    # Aplicar las cabeceras seguras a todas las respuestas
    app.after_request(secure_headers)

    # Registrar los Blueprints
    app.register_blueprint(auth)  # Registrar el blueprint de autenticación
    app.register_blueprint(home)
    app.register_blueprint(reunion)  # Registrar el blueprint de las reuniones
    app.register_blueprint(director_bp)  # Registrar el blueprint del director

    @app.route('/exportar_pdf', methods=['POST'])
    def exportar_pdf():
        acta_content = request.form.get('acta_content')
        return render_template('acta_pdf.html', acta_content=acta_content)

    return app

if __name__ == '__main__':
    app = create_app()  # Usar la función create_app para crear la aplicación
    app.secret_key = 'clave_super_segura'
    app.run(debug=False)
