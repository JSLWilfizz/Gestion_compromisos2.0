import os


class Config:
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False# Cookie solo accesible por HTTP
    WTF_CSRF_ENABLED = False# Deshabilitar CSRF Protection
    SQLALCHEMY_DATABASE_URI = 'postgresql://usuariopbi:%40%40usuariopbi%40%40@10.7.196.122:5432/gestion'  # Contraseña URL-encodeada