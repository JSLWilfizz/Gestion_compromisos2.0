def set_alert(session, message, alert_type="info"):
    """
    Asigna una alerta en la sesión.
    alert_type puede ser "success", "danger", "warning" o "info"
    """
    session['alert'] = {"message": message, "type": alert_type}
