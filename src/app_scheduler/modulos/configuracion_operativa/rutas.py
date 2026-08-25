"""Rutas administrativas de configuracion operativa."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion


bp_configuracion = Blueprint("configuracion_operativa", __name__, url_prefix="/configuracion")


@bp_configuracion.get("/")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def inicio():
    return render_template(
        "configuracion/inicio.html",
        resultado=current_app.extensions["servicio_configuracion_operativa"].obtener(),
    )


@bp_configuracion.post("/scheduler")
@permiso_requerido("SCHEDULER_CONFIG_EDITAR")
def guardar_scheduler():
    try:
        current_app.extensions["servicio_configuracion_operativa"].guardar_scheduler(
            request.form, identidad_actual(), ContextoAuditoria(
                request.remote_addr, request.user_agent.string[:500] or None,
                request.path, request.method,
            ),
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Configuracion del scheduler actualizada.", "success")
    return redirect(url_for("configuracion_operativa.inicio"))


@bp_configuracion.get("/mail-graph")
@permiso_requerido("CONFIGURACION_ADMIN")
def mail_graph():
    return render_template(
        "configuracion/mail_graph.html",
        resultado=current_app.extensions["servicio_configuracion_graph"].obtener(),
    )


@bp_configuracion.post("/mail-graph")
@permiso_requerido("CONFIGURACION_ADMIN")
def guardar_mail_graph():
    try:
        current_app.extensions["servicio_configuracion_graph"].guardar(
            request.form, identidad_actual(), ContextoAuditoria(
                request.remote_addr, request.user_agent.string[:500] or None,
                request.path, request.method,
            ),
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Configuracion Microsoft Graph actualizada.", "success")
    return redirect(url_for("configuracion_operativa.mail_graph"))
