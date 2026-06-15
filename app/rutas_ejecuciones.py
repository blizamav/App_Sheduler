from flask import Blueprint, flash, jsonify, redirect, render_template, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_ejecuciones import (
    detener_ejecucion_manual,
    iniciar_ejecucion_manual,
    obtener_detalle_ejecucion,
    obtener_estado_log,
)


bp_ejecuciones = Blueprint("ejecuciones", __name__)


@bp_ejecuciones.route("/tareas/<int:id_tarea>/ejecutar", methods=["POST"])
@permiso_requerido("EJECUCIONES_EJECUTAR")
def ejecutar_tarea(id_tarea):
    try:
        ok, mensaje, id_ejecucion = iniciar_ejecucion_manual(id_tarea, session.get("usuario"))
    except Exception:
        ok, mensaje, id_ejecucion = False, "No fue posible iniciar la ejecucion manual.", None
    flash(mensaje, "success" if ok else "error")
    if ok:
        return redirect(url_for("ejecuciones.consola", id_ejecucion=id_ejecucion))
    return redirect(url_for("tareas.listado"))


@bp_ejecuciones.route("/ejecuciones/<int:id_ejecucion>")
@permiso_requerido("EJECUCIONES_VER")
def consola(id_ejecucion):
    ejecucion = obtener_detalle_ejecucion(id_ejecucion)
    if not ejecucion:
        flash("Ejecucion no encontrada.", "error")
        return redirect(url_for("tareas.listado"))
    return render_template("ejecuciones/consola.html", ejecucion=ejecucion)


@bp_ejecuciones.route("/ejecuciones/<int:id_ejecucion>/log")
@permiso_requerido("EJECUCIONES_LOG_VER")
def log(id_ejecucion):
    estado = obtener_estado_log(id_ejecucion)
    if not estado:
        return jsonify({"estado": "ERROR", "log": "Ejecucion no encontrada.", "es_final": True}), 404
    return jsonify(estado)


@bp_ejecuciones.route("/ejecuciones/<int:id_ejecucion>/detener", methods=["POST"])
@permiso_requerido("EJECUCIONES_DETENER")
def detener(id_ejecucion):
    try:
        ok, mensaje = detener_ejecucion_manual(id_ejecucion, session.get("usuario"))
    except Exception:
        ok, mensaje = False, "No fue posible detener la ejecucion."
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("ejecuciones.consola", id_ejecucion=id_ejecucion))
