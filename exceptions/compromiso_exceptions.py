class CompromisoError(Exception):
    """Clase base para excepciones de compromisos"""
    pass

class ResponsablePrincipalError(CompromisoError):
    """Se lanza cuando se intenta eliminar al responsable principal de un compromiso"""
    def __init__(self, message="No se puede eliminar al responsable principal del compromiso"):
        self.message = message
        super().__init__(self.message)
