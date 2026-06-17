from flask import Blueprint, flash, render_template, request, session

from app.seguridad import permiso_requerido
from app.servicios.servicio_configuracion_scheduler import (
    guardar_configuracion_scheduler,
    obtener_configuracion_scheduler,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_panel_scheduler import obtener_panel_scheduler


bp_scheduler = Blueprint("scheduler", __name__, url_prefix="/scheduler")


@bp_scheduler.route("/panel")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def panel():
    try:
        panel_scheduler = obtener_panel_scheduler()
    except Exception:
        panel_scheduler = None
        flash("No fue posible cargar el panel operativo del scheduler.", "error")
    return render_template("scheduler/panel.html", panel=panel_scheduler)


@bp_scheduler.route("/configuracion", methods=["GET", "POST"])
@permiso_requerido("SCHEDULER_CONFIG_VER")
def configuracion():
    if request.method == "POST":
        permiso_editar = session.get("es_admin_env") or "*" in session.get("permisos", []) or "SCHEDULER_CONFIG_EDITAR" in session.get("permisos", [])
        if not permiso_editar:
            registrar_log_sistema(
                "SCHEDULER_CONFIG_EDICION_BLOQUEADA",
                "SCHEDULER",
                "Intento bloqueado de editar configuracion del scheduler sin permiso.",
                usuario=session.get("usuario"),
                nivel="WARNING",
            )
            flash("No tienes permisos para editar la configuracion del scheduler.", "error")
        else:
            ok, mensajes, _ = guardar_configuracion_scheduler(request.form, session.get("usuario"))
            for mensaje in mensajes:
                flash(mensaje, "success" if ok else "info" if mensaje == "No hay cambios para guardar." else "error")

    configuracion_actual = obtener_configuracion_scheduler(session.get("usuario"))
    return render_template("scheduler/configuracion.html", configuracion=configuracion_actual)
