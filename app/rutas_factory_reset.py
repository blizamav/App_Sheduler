from functools import wraps

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from app.servicios.servicio_control_runtime import obtener_estado_factory_reset
from app.servicios.servicio_csrf import generar_csrf_factory_reset, validar_csrf_factory_reset
from app.servicios.servicio_factory_reset import generar_preview_factory_reset


bp_factory_reset = Blueprint("factory_reset", __name__, url_prefix="/administracion/factory-reset")


def super_admin_factory_reset_requerido(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("principal.login"))
        roles = set(session.get("roles", []))
        es_super_admin = bool(
            session.get("es_admin_env")
            or "SUPER_ADMIN" in roles
            or "SUPER_ADMIN_ENV" in roles
        )
        permisos = set(session.get("permisos", []))
        tiene_permiso = "*" in permisos or "FACTORY_RESET_EJECUTAR" in permisos
        if not es_super_admin or not tiene_permiso:
            abort(403)
        return vista(*args, **kwargs)

    return wrapper


@bp_factory_reset.get("")
@super_admin_factory_reset_requerido
def pantalla():
    return render_template(
        "administracion/factory_reset.html",
        csrf_token=generar_csrf_factory_reset(),
        lock=obtener_estado_factory_reset(),
        preview=None,
    )


@bp_factory_reset.post("/preview")
@super_admin_factory_reset_requerido
def preview():
    if not validar_csrf_factory_reset(request.form.get("csrf_token")):
        abort(403)
    resultado = generar_preview_factory_reset(session.get("usuario"))
    return render_template(
        "administracion/factory_reset.html",
        csrf_token=generar_csrf_factory_reset(rotar=True),
        lock=resultado["lock"],
        preview=resultado,
    )
