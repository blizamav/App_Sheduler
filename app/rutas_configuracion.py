from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_mail_graph import (
    guardar_mail_graph_config,
    obtener_mail_graph_config,
)


bp_configuracion = Blueprint("configuracion", __name__, url_prefix="/configuracion")
bp_configuracion_api = Blueprint("configuracion_api", __name__, url_prefix="/api/configuracion")


def _puede_editar_configuracion():
    permisos = session.get("permisos", [])
    return bool(session.get("es_admin_env") or "*" in permisos or "SCHEDULER_CONFIG_EDITAR" in permisos)


@bp_configuracion.route("/mail-graph", methods=["GET", "POST"])
@permiso_requerido("SCHEDULER_CONFIG_VER")
def mail_graph():
    if request.method == "POST":
        if not _puede_editar_configuracion():
            registrar_log_sistema(
                "MAIL_GRAPH_EDICION_BLOQUEADA",
                "MAIL_GRAPH",
                "Intento bloqueado de editar configuracion Mail Graph sin permiso.",
                usuario=session.get("usuario"),
                nivel="WARNING",
            )
            registrar_auditoria(
                "BLOQUEO_PERMISO",
                "configuracion_mail_graph",
                descripcion="Intento bloqueado de editar configuracion Mail Graph sin permiso.",
                valores_despues={"permiso_requerido": "SCHEDULER_CONFIG_EDITAR"},
                resultado="BLOQUEADO",
                modulo="SEGURIDAD",
                usuario=session.get("usuario"),
            )
            flash("No tienes permisos para editar Mail Automatico.", "error")
            return redirect(url_for("configuracion.mail_graph"))
        try:
            ok, mensajes, _ = guardar_mail_graph_config(request.form, session.get("usuario"))
        except Exception as error:
            registrar_auditoria(
                "EDITAR_CONFIG_MAIL_GRAPH",
                "configuracion_mail_graph",
                descripcion="Error controlado al guardar configuracion Mail Graph.",
                valores_despues={"error": error.__class__.__name__},
                resultado="ERROR",
                modulo="MAIL_GRAPH",
                usuario=session.get("usuario"),
            )
            ok, mensajes = False, ["No fue posible guardar la configuracion Mail Graph."]
        for mensaje in mensajes:
            flash(mensaje, "success" if ok else "info" if mensaje == "No hay cambios para guardar." else "error")
        return redirect(url_for("configuracion.mail_graph"))

    try:
        configuracion = obtener_mail_graph_config(session.get("usuario"))
    except Exception:
        configuracion = None
        flash("No fue posible cargar la configuracion Mail Graph. Verifica si la migracion 020 fue ejecutada.", "error")
    return render_template("configuracion/mail_graph.html", configuracion=configuracion)


@bp_configuracion_api.route("/mail-graph", methods=["GET"])
@permiso_requerido("SCHEDULER_CONFIG_VER")
def api_obtener_mail_graph():
    try:
        return jsonify({"ok": True, "config": obtener_mail_graph_config(session.get("usuario"))})
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible obtener la configuracion Mail Graph."}), 500


@bp_configuracion_api.route("/mail-graph", methods=["POST", "PUT"])
@permiso_requerido("SCHEDULER_CONFIG_VER")
def api_guardar_mail_graph():
    if not _puede_editar_configuracion():
        return jsonify({"ok": False, "mensaje": "No tienes permisos para editar Mail Automatico."}), 403
    datos = request.get_json(silent=True) or request.form or {}
    try:
        ok, mensajes, config = guardar_mail_graph_config(datos, session.get("usuario"))
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible guardar la configuracion Mail Graph."}), 500
    estado = 200 if ok else 400 if mensajes and mensajes[0] != "No hay cambios para guardar." else 200
    return jsonify(
        {
            "ok": ok,
            "mensaje": mensajes[0] if mensajes else "",
            "errores": [] if ok else mensajes,
            "config": config,
        }
    ), estado
