"""Rutas de observabilidad y logs globales."""

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.autorizacion import permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion


bp_operacion = Blueprint("operacion", __name__)


@bp_operacion.get("/operacion/estado")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def estado():
    return render_template(
        "operacion/estado.html",
        estado=current_app.extensions["servicio_observabilidad"].obtener_estado(),
    )


@bp_operacion.get("/logs/")
@permiso_requerido("LOGS_VER")
def logs():
    try:
        resultado = current_app.extensions["servicio_logs_sistema"].listar(
            pagina=max(1, _entero(request.args.get("pagina"), 1)),
            desde=request.args.get("desde"), hasta=request.args.get("hasta"),
            nivel=request.args.get("nivel"), modulo=request.args.get("modulo"),
            evento=request.args.get("evento"), busqueda=request.args.get("buscar"),
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
        return redirect(url_for("operacion.logs"))
    return render_template("operacion/logs.html", **resultado)


@bp_operacion.get("/logs/<int:id_log>")
@permiso_requerido("LOGS_VER")
def detalle_log(id_log):
    log = current_app.extensions["servicio_logs_sistema"].obtener(id_log)
    if log is None:
        abort(404)
    return render_template("operacion/detalle_log.html", log=log)


def _entero(valor, defecto):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto
