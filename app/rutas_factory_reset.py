from functools import wraps

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for

from app.servicios.servicio_control_runtime import obtener_estado_factory_reset, obtener_estado_operacion_factory_reset
from app.servicios.servicio_csrf import generar_csrf_factory_reset, validar_csrf_factory_reset
from app.servicios.servicio_factory_reset import generar_preview_factory_reset, validar_token_preview
from app.servicios.servicio_orquestador_factory_reset import (
    FRASE_CONFIRMACION_FACTORY_RESET,
    ejecutar_factory_reset,
)


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
    estado_operacion = None
    id_operacion = (request.args.get("operacion") or "").strip()
    if id_operacion:
        try:
            estado_operacion = obtener_estado_operacion_factory_reset(id_operacion)
        except ValueError:
            abort(400)
    return render_template(
        "administracion/factory_reset.html",
        csrf_token=generar_csrf_factory_reset(),
        lock=obtener_estado_factory_reset(),
        preview=None,
        estado_operacion=estado_operacion,
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


@bp_factory_reset.post("/ejecutar")
@super_admin_factory_reset_requerido
def ejecutar():
    if not validar_csrf_factory_reset(request.form.get("csrf_token")):
        abort(403)
    if request.form.get("confirmacion") != FRASE_CONFIRMACION_FACTORY_RESET:
        flash("La frase de confirmacion no coincide exactamente.", "error")
        return redirect(url_for("factory_reset.pantalla"))

    valido, mensaje, datos_preview = validar_token_preview(
        request.form.get("token_preview"),
        session.get("usuario"),
        request.form.get("resumen_hash"),
    )
    if not valido or datos_preview.get("estado_lock") != "NORMAL":
        flash(mensaje if not valido else "El preview no fue generado en estado normal.", "error")
        return redirect(url_for("factory_reset.pantalla"))

    resultado = ejecutar_factory_reset(
        datos_preview,
        session.get("usuario"),
        origen_usuario="ENV" if session.get("es_admin_env") else "BD",
    )
    if resultado["ok"]:
        session.clear()
        flash("APP Scheduler fue restablecido correctamente a su estado de fabrica.", "success")
        return redirect(url_for("principal.login"))

    flash(resultado["mensaje"], "error")
    return redirect(url_for("factory_reset.pantalla", operacion=resultado.get("id_operacion")))


@bp_factory_reset.get("/estado")
@super_admin_factory_reset_requerido
def estado():
    id_operacion = (request.args.get("operacion") or "").strip()
    if id_operacion:
        try:
            estado_operacion = obtener_estado_operacion_factory_reset(id_operacion)
        except ValueError:
            abort(400)
        if estado_operacion:
            datos = estado_operacion.get("datos") or {}
            return jsonify(
                {
                    "id_operacion": estado_operacion.get("id_operacion"),
                    "estado": datos.get("estado") or estado_operacion.get("nivel"),
                    "fase": estado_operacion.get("fase"),
                    "progreso": datos.get("progreso"),
                    "mensaje": estado_operacion.get("mensaje"),
                    "error_seguro": estado_operacion.get("mensaje") if estado_operacion.get("nivel") == "ERROR" else None,
                    "completado": bool(datos.get("completado", False)),
                    "fecha_utc": estado_operacion.get("fecha_utc"),
                }
            )
    lock = obtener_estado_factory_reset()
    return jsonify(
        {
            "id_operacion": lock.get("id_operacion"),
            "estado": lock.get("estado"),
            "fase": lock.get("fase"),
            "progreso": lock.get("progreso"),
            "mensaje": lock.get("mensaje"),
            "error_seguro": lock.get("error_seguro"),
            "completado": lock.get("completado"),
        }
    )
