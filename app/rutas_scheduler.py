from flask import Blueprint, flash, render_template, request, session

from app.seguridad import permiso_requerido
from app.servicios.servicio_configuracion_scheduler import (
    guardar_configuracion_scheduler,
    obtener_configuracion_scheduler,
)
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_panel_scheduler import obtener_panel_scheduler
from app.servicios.servicio_scheduler_eventos import listar_historial_eventos


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


@bp_scheduler.route("/eventos")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def eventos():
    filtros = {
        "fecha_desde": request.args.get("fecha_desde", ""),
        "fecha_hasta": request.args.get("fecha_hasta", ""),
        "tarea": request.args.get("tarea", ""),
        "tipo_evento": request.args.get("tipo_evento", ""),
        "decision": request.args.get("decision", ""),
        "motivo": request.args.get("motivo", ""),
        "worker": request.args.get("worker", ""),
        "texto": request.args.get("texto", ""),
    }
    historial = listar_historial_eventos(
        filtros=filtros,
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 25),
    )
    return render_template("scheduler/eventos.html", **historial)


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
            registrar_auditoria(
                "BLOQUEO_PERMISO",
                "scheduler_config",
                descripcion="Intento bloqueado de editar configuracion del scheduler sin permiso.",
                valores_despues={"permiso_requerido": "SCHEDULER_CONFIG_EDITAR"},
                resultado="BLOQUEADO",
                modulo="SEGURIDAD",
                usuario=session.get("usuario"),
            )
            flash("No tienes permisos para editar la configuracion del scheduler.", "error")
        else:
            try:
                ok, mensajes, _ = guardar_configuracion_scheduler(request.form, session.get("usuario"))
            except Exception as error:
                registrar_auditoria(
                    "EDITAR_CONFIG_PROGRAMADOR",
                    "scheduler_config",
                    descripcion="Error controlado al guardar configuracion del scheduler.",
                    valores_despues={"error": error.__class__.__name__},
                    resultado="ERROR",
                    modulo="SCHEDULER",
                    usuario=session.get("usuario"),
                )
                ok, mensajes = False, ["No fue posible guardar la configuracion del scheduler."]
            for mensaje in mensajes:
                flash(mensaje, "success" if ok else "info" if mensaje == "No hay cambios para guardar." else "error")

    configuracion_actual = obtener_configuracion_scheduler(session.get("usuario"))
    return render_template("scheduler/configuracion.html", configuracion=configuracion_actual)
