import os


class Config:
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False# Cookie solo accesible por HTTP
    WTF_CSRF_ENABLED = False# Deshabilitar CSRF Protection