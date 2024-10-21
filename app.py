import os

from flask import Flask
from flask_wtf import CSRFProtect

from config import Config
from flask_bcrypt import Bcrypt
from routes import auth, home, reunion  # Importar los blueprints desde routes

app = Flask(__name__)
app.config.from_object(Config)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Registrar los Blueprints
app.register_blueprint(auth) # Registrar el blueprint de autenticación
app.register_blueprint(home) # Registrar el blueprint de la página principal
app.register_blueprint(reunion) # Registrar el blueprint de las reuniones

if __name__ == '__main__':
    app.run(debug=True) # Ejecutar la aplicación en modo debug
