from functools import wraps

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for

from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_mail_graph import (
    guardar_mail_graph_config,
    obtener_mail_graph_config,
)


bp_configuracion = Blueprint("configuracion", __name__, url_prefix="/configuracion")
bp_configuracion_api = Blueprint("configuracion_api", __name__, url_prefix="/api/configuracion")


def _es_super_admin_mail_graph():
    roles = session.get("roles", [])
    return bool(session.get("es_admin_env") or "SUPER_ADMIN" in roles or "SUPER_ADMIN_ENV" in roles)


def super_admin_mail_graph_requerido(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("principal.login"))
        if not _es_super_admin_mail_graph():
            registrar_log_sistema(
                "MAIL_GRAPH_ACCESO_BLOQUEADO",
                "MAIL_GRAPH",
                "Intento bloqueado de acceso a configuracion sensible Mail Graph.",
                usuario=session.get("usuario"),
                nivel="WARNING",
            )
            registrar_auditoria(
                "BLOQUEO_PERMISO",
                "configuracion_mail_graph",
                descripcion="Intento bloqueado de acceso a configuracion sensible Mail Graph.",
                valores_despues={"rol_requerido": "SUPER_ADMIN", "ruta": request.path},
                resultado="BLOQUEADO",
                modulo="SEGURIDAD",
                usuario=session.get("usuario"),
            )
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "mensaje": "No tienes permisos para acceder a Mail Automatico."}), 403
            flash("No tienes permisos para acceder a Mail Automatico.", "error")
            return abort(403)
        return vista(*args, **kwargs)

    return wrapper


@bp_configuracion.route("/mail-graph", methods=["GET", "POST"])
@super_admin_mail_graph_requerido
def mail_graph():
    if request.method == "POST":
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
@super_admin_mail_graph_requerido
def api_obtener_mail_graph():
    try:
        return jsonify({"ok": True, "config": _config_mail_graph_segura(obtener_mail_graph_config(session.get("usuario")))})
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible obtener la configuracion Mail Graph."}), 500


@bp_configuracion_api.route("/mail-graph/sensible", methods=["POST"])
@super_admin_mail_graph_requerido
def api_revelar_mail_graph_sensible():
    try:
        config = obtener_mail_graph_config(session.get("usuario"))
        return jsonify(
            {
                "ok": True,
                "config": {
                    "tenant_id": config.get("tenant_id"),
                    "client_id": config.get("client_id"),
                    "graph_scope": config.get("graph_scope"),
                },
            }
        )
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible revelar la configuracion sensible Mail Graph."}), 500


@bp_configuracion_api.route("/mail-graph", methods=["POST", "PUT"])
@super_admin_mail_graph_requerido
def api_guardar_mail_graph():
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
            "config": _config_mail_graph_segura(config),
        }
    ), estado


def _config_mail_graph_segura(config):
    seguro = dict(config or {})
    for campo in ("tenant_id", "client_id", "graph_scope"):
        if seguro.get(campo):
            seguro[campo] = "************"
    return seguro
