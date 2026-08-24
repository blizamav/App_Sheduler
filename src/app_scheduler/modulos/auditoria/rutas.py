"""Rutas read-only de auditoria."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.autorizacion import permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion


bp_auditoria = Blueprint("auditoria", __name__, url_prefix="/auditoria")


def _servicio():
    return current_app.extensions["servicio_consulta_auditoria"]


@bp_auditoria.get("/")
@permiso_requerido("AUDITORIA_VER")
def listado():
    try:
        contexto = _servicio().listar(request.args)
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
        return redirect(url_for("auditoria.listado"))
    return render_template("auditoria/listado.html", **contexto)


@bp_auditoria.get("/<int:id_auditoria>")
@permiso_requerido("AUDITORIA_DETALLE")
def detalle(id_auditoria):
    contexto = _servicio().obtener(id_auditoria)
    if contexto is None:
        flash("Registro de auditoria no encontrado.", "error")
        return redirect(url_for("auditoria.listado"))
    return render_template("auditoria/detalle.html", **contexto)
