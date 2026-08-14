"""Proteccion CSRF transversal para todas las escrituras HTTP."""

from __future__ import annotations

import hmac
import secrets
import time
from functools import wraps

from flask import Flask, current_app, request, session

from app_scheduler.compartido.errores import ErrorAutorizacion


CLAVE_SESION = "_csrf"
METODOS_PROTEGIDOS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def generar_token_csrf() -> str:
    actual = session.get(CLAVE_SESION) or {}
    creado = float(actual.get("creado", 0) or 0)
    ttl = int(current_app.config["CSRF_TTL_SEGUNDOS"])
    if not actual.get("token") or time.time() - creado > ttl:
        actual = {"token": secrets.token_urlsafe(32), "creado": time.time()}
        session[CLAVE_SESION] = actual
        session.modified = True
    return str(actual["token"])


def validar_token_csrf(token: str | None) -> bool:
    actual = session.get(CLAVE_SESION) or {}
    esperado = str(actual.get("token") or "")
    try:
        vigente = time.time() - float(actual.get("creado", 0)) <= int(
            current_app.config["CSRF_TTL_SEGUNDOS"]
        )
    except (TypeError, ValueError):
        vigente = False
    return bool(esperado and token and vigente and hmac.compare_digest(esperado, str(token)))


def exento_csrf(vista):
    """Exime una vista solo cuando un protocolo externo lo justifique explicitamente."""
    vista._exento_csrf = True
    return vista


def csrf_requerido(vista):
    """Marca de documentacion para endpoints que ya cubre la politica global."""

    @wraps(vista)
    def wrapper(*args, **kwargs):
        return vista(*args, **kwargs)

    return wrapper


def iniciar_csrf(app: Flask) -> None:
    @app.before_request
    def proteger_escrituras():
        if request.method not in METODOS_PROTEGIDOS:
            return None
        vista = app.view_functions.get(request.endpoint or "")
        if vista and getattr(vista, "_exento_csrf", False):
            return None
        token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not validar_token_csrf(token):
            raise ErrorAutorizacion("La solicitud expiro o no contiene un token CSRF valido.")
        return None

    app.jinja_env.globals["csrf_token"] = generar_token_csrf
