"""Rutas web de reserva manual, historial y consola."""

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion


bp_ejecuciones = Blueprint("ejecuciones", __name__)


def _servicio(): return current_app.extensions["servicio_ejecuciones"]
def _contexto(): return ContextoAuditoria(request.remote_addr, request.user_agent.string[:500] or None, request.path, request.method)
def _entero(valor, default=1):
    try: return int(valor)
    except (TypeError, ValueError): return default


@bp_ejecuciones.get("/ejecuciones/")
@permiso_requerido("EJECUCIONES_VER")
def listado():
    estado = request.args.get("estado", "").strip().upper()
    origen = request.args.get("origen", "").strip().upper()
    try:
        resultado = _servicio().listar(
            pagina=max(1, _entero(request.args.get("pagina"))),
            estado=estado or None, origen=origen or None,
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error"); return redirect(url_for("ejecuciones.listado"))
    return render_template("ejecuciones/listado.html", resultado=resultado,
                           filtros={"estado": estado, "origen": origen})


@bp_ejecuciones.post("/tareas/<int:id_tarea>/ejecutar")
@permiso_requerido("EJECUCIONES_EJECUTAR")
def ejecutar_tarea(id_tarea):
    try:
        id_ejecucion = _servicio().solicitar_manual(id_tarea, identidad_actual(), _contexto())
    except ErrorValidacion as error:
        flash(error.mensaje, "error"); return redirect(url_for("tareas.listado"))
    flash("Ejecucion manual reservada. El worker la procesara respetando la capacidad configurada.", "success")
    return redirect(url_for("ejecuciones.detalle", id_ejecucion=id_ejecucion))


@bp_ejecuciones.get("/ejecuciones/<int:id_ejecucion>")
@permiso_requerido("EJECUCIONES_VER")
def detalle(id_ejecucion):
    ejecucion = _servicio().obtener(id_ejecucion)
    if ejecucion is None:
        flash("Ejecucion no encontrada.", "error"); return redirect(url_for("ejecuciones.listado"))
    return render_template("ejecuciones/detalle.html", ejecucion=ejecucion)


@bp_ejecuciones.get("/ejecuciones/<int:id_ejecucion>/log")
@permiso_requerido("EJECUCIONES_LOG_VER")
def log(id_ejecucion):
    try: return jsonify(_servicio().leer_log(id_ejecucion))
    except ErrorValidacion as error: return jsonify({"error": error.mensaje}), 404


@bp_ejecuciones.post("/ejecuciones/<int:id_ejecucion>/detener")
@permiso_requerido("EJECUCIONES_DETENER")
def detener(id_ejecucion):
    try:
        _servicio().solicitar_detencion(
            id_ejecucion, identidad_actual(), _contexto(), request.form.get("motivo"),
        )
    except ErrorValidacion as error: flash(error.mensaje, "error")
    else: flash("Detencion solicitada al worker propietario.", "success")
    return redirect(url_for("ejecuciones.detalle", id_ejecucion=id_ejecucion))
