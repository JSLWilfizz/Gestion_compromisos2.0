from app import create_app

# Crea la instancia de la aplicación usando la función `create_app`
app = create_app()

if __name__ == "__main__":
    # Si ejecutas directamente este archivo, inicia la aplicación (esto no se usará en producción con Nginx)
    app.secret_key = 'clave_super_segura'
    app.run()