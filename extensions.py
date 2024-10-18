from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Inicializar las extensiones
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()