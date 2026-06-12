from flask import has_request_context, request

from app.repositorios.repositorio_logs_sistema import insertar_log_sistema


def registrar_log_sistema(
    accion,
    modulo,
    descripcion,
    usuario=None,
    valor_anterior=None,
    valor_nuevo=None,
    nivel="INFO",
):
    """Registra logs de sistema sin interrumpir el flujo si la BD falla."""
    datos = {
        "usuario": usuario,
        "accion": accion,
        "modulo": modulo,
        "descripcion": descripcion,
        "valor_anterior": valor_anterior,
        "valor_nuevo": valor_nuevo,
        "nivel": nivel,
        "ip": None,
        "user_agent": None,
    }

    if has_request_context():
        datos["ip"] = request.headers.get("X-Forwarded-For", request.remote_addr)
        datos["user_agent"] = request.headers.get("User-Agent")

    try:
        insertar_log_sistema(datos)
        return True
    except Exception:
        return False
