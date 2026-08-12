import hmac
import secrets
import time

from flask import current_app, session


CLAVE_CSRF_FACTORY_RESET = "csrf_factory_reset"


def generar_csrf_factory_reset(rotar=False):
    actual = session.get(CLAVE_CSRF_FACTORY_RESET) or {}
    ttl = _ttl_csrf()
    vigente = actual.get("token") and time.time() - float(actual.get("creado", 0)) <= ttl
    if rotar or not vigente:
        actual = {"token": secrets.token_urlsafe(32), "creado": time.time()}
        session[CLAVE_CSRF_FACTORY_RESET] = actual
        session.modified = True
    return actual["token"]


def validar_csrf_factory_reset(token, consumir=True):
    actual = session.get(CLAVE_CSRF_FACTORY_RESET) or {}
    esperado = str(actual.get("token") or "")
    recibido = str(token or "")
    try:
        vigente = time.time() - float(actual.get("creado", 0)) <= _ttl_csrf()
    except (TypeError, ValueError):
        vigente = False
    valido = bool(esperado and recibido and vigente and hmac.compare_digest(esperado, recibido))
    if valido and consumir:
        session.pop(CLAVE_CSRF_FACTORY_RESET, None)
        session.modified = True
    return valido


def _ttl_csrf():
    try:
        return max(60, int(current_app.config.get("FACTORY_RESET_CSRF_TTL_SEGUNDOS", 600)))
    except (TypeError, ValueError):
        return 600
