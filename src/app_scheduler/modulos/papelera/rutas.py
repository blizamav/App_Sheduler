"""Rutas seguras de Papelera."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import (
    identidad_actual,
    permiso_requerido,
    sesion_requerida,
)
from app_scheduler.compartido.errores import ErrorAutorizacion, ErrorValidacion
from app_scheduler.modulos.papelera.casos_uso import PERMISOS_RETIRO


bp_papelera = Blueprint("papelera", __name__, url_prefix="/papelera")


def _servicio():
    return current_app.extensions["servicio_papelera"]


def _contexto():
    return ContextoAuditoria(
        request.remote_addr,
        request.user_agent.string[:500] or None,
        request.path,
        request.method,
    )


@bp_papelera.get("/")
@permiso_requerido("PAPELERA_VER")
def listado():
    try:
        contexto = _servicio().listar(request.args, identidad_actual())
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
        return redirect(url_for("papelera.listado"))
    return render_template("papelera/listado.html", **contexto)


@bp_papelera.post("/<entidad>/<int:id_registro>/retirar")
@sesion_requerida
def retirar(entidad, id_registro):
    actor = identidad_actual()
    permiso = PERMISOS_RETIRO.get(entidad)
    if permiso is None or not actor.tiene_permiso(permiso):
        raise ErrorAutorizacion()
    try:
        _servicio().enviar(entidad, id_registro, request.form.get("motivo"), actor, _contexto())
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Registro enviado a Papelera. Su historia permanece disponible.", "success")
    return redirect(request.referrer or url_for("papelera.listado"))


@bp_papelera.post("/<entidad>/<int:id_registro>/restaurar")
@permiso_requerido("PAPELERA_RESTAURAR")
def restaurar(entidad, id_registro):
    try:
        _servicio().restaurar(entidad, id_registro, identidad_actual(), _contexto())
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Registro restaurado como inactivo.", "success")
    return redirect(url_for("papelera.listado"))


@bp_papelera.post("/<entidad>/<int:id_registro>/eliminar-permanente")
@permiso_requerido("PAPELERA_ELIMINAR_PERMANENTE")
def eliminar_permanente(entidad, id_registro):
    try:
        _servicio().eliminar_permanente(entidad, id_registro, identidad_actual(), _contexto())
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Registro operacional eliminado permanentemente. La historia protegida se conserva.", "success")
    return redirect(url_for("papelera.listado"))
