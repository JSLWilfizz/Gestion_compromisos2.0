import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'# Clave secreta de la aplicación
    SESSION_COOKIE_SECURE = True# Cookie segura
    SESSION_COOKIE_HTTPONLY = True# Cookie solo accesible por HTTP
    SESSION_COOKIE_SAMESITE = 'Lax' # Cookie con SameSite=Lax
    WTF_CSRF_ENABLED = False# Deshabilitar CSRF Protection