"""Rutas administrativas del Factory Reset reconstruido."""

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for

from app_scheduler.compartido.autorizacion import (
    identidad_actual,
    limpiar_sesion,
    permiso_requerido,
)
from app_scheduler.modulos.factory_reset.contratos import (
    FRASE_CONFIRMACION,
    PERMISO_FACTORY_RESET,
)


bp_factory_reset = Blueprint(
    "factory_reset", __name__, url_prefix="/administracion/factory-reset"
)


def _servicio():
    return current_app.extensions["servicio_factory_reset"]


@bp_factory_reset.get("")
@permiso_requerido(PERMISO_FACTORY_RESET)
def pantalla():
    id_operacion = str(request.args.get("operacion") or "").strip()
    estado_operacion = _servicio().estado_operacion(id_operacion) if id_operacion else None
    return render_template(
        "factory_reset/panel.html", preview=None,
        lock=_servicio().estado_lock(), estado_operacion=estado_operacion,
        frase_confirmacion=FRASE_CONFIRMACION,
    )


@bp_factory_reset.post("/preview")
@permiso_requerido(PERMISO_FACTORY_RESET)
def preview():
    resultado = _servicio().generar_preview(identidad_actual())
    return render_template(
        "factory_reset/panel.html", preview=resultado, lock=resultado["lock"],
        estado_operacion=None, frase_confirmacion=FRASE_CONFIRMACION,
    )


@bp_factory_reset.post("/ejecutar")
@permiso_requerido(PERMISO_FACTORY_RESET)
def ejecutar():
    if request.form.get("confirmacion") != FRASE_CONFIRMACION:
        flash("La frase de confirmacion no coincide exactamente.", "error")
        return redirect(url_for("factory_reset.pantalla"))
    if request.form.get("confirmacion_consecuencias") != "1":
        flash("Debes confirmar que comprendes las consecuencias del restablecimiento.", "error")
        return redirect(url_for("factory_reset.pantalla"))
    identidad = identidad_actual()
    valido, mensaje, datos = _servicio().validar_token(
        request.form.get("token_preview"), identidad,
        request.form.get("resumen_hash"),
    )
    if not valido:
        flash(mensaje, "error")
        return redirect(url_for("factory_reset.pantalla"))
    resultado = _servicio().ejecutar(datos, identidad)
    if resultado["ok"]:
        limpiar_sesion()
        flash("APP Scheduler fue restablecido correctamente.", "success")
        return redirect(url_for("autenticacion.login"))
    flash(resultado["mensaje"], "error")
    return redirect(url_for("factory_reset.pantalla", operacion=resultado.get("id_operacion")))


@bp_factory_reset.get("/estado")
@permiso_requerido(PERMISO_FACTORY_RESET)
def estado():
    id_operacion = str(request.args.get("operacion") or "").strip()
    evento = _servicio().estado_operacion(id_operacion) if id_operacion else None
    if evento:
        datos = evento.get("datos") or {}
        return jsonify({
            "id_operacion": evento.get("id_operacion"),
            "estado": datos.get("estado") or evento.get("nivel"),
            "fase": evento.get("fase"), "progreso": datos.get("progreso"),
            "mensaje": evento.get("mensaje"),
            "error_seguro": evento.get("mensaje") if evento.get("nivel") == "ERROR" else None,
            "completado": bool(datos.get("completado", False)),
            "fecha_utc": evento.get("fecha_utc"),
        })
    lock = _servicio().estado_lock()
    return jsonify({clave: lock.get(clave) for clave in (
        "id_operacion", "estado", "fase", "progreso", "mensaje",
        "error_seguro", "completado",
    )})
