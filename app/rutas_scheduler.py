from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_api_worker import (
    obtener_consola_api_worker,
    obtener_ejecuciones_api_worker,
    obtener_estado_api_worker,
    obtener_eventos_api_worker,
    obtener_monitor_api_worker,
)
from app.servicios.servicio_configuracion_scheduler import (
    guardar_configuracion_scheduler,
    obtener_configuracion_scheduler,
)
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_panel_scheduler import obtener_panel_scheduler
from app.servicios.servicio_scheduler_eventos import (
    limpiar_eventos_informativos_antiguos,
    listar_historial_eventos,
    obtener_limpieza_eventos,
    previsualizar_limpieza_eventos,
)


bp_scheduler = Blueprint("scheduler", __name__, url_prefix="/scheduler")
bp_worker_api = Blueprint("worker_api", __name__, url_prefix="/api/worker")


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
    if request.headers.get("X-Requested-With") == "fetch":
        return render_template("scheduler/_eventos_historial.html", **historial)
    limpieza = obtener_limpieza_eventos(request.args.get("limpieza_dias", 30))
    return render_template("scheduler/eventos.html", **historial, limpieza=limpieza)


@bp_scheduler.route("/eventos/limpiar", methods=["POST"])
@permiso_requerido("SCHEDULER_CONFIG_VER")
def limpiar_eventos():
    if not _puede_editar_scheduler():
        _registrar_bloqueo_limpieza_eventos()
        flash("No tienes permisos para limpiar eventos del programador.", "error")
        return redirect(url_for("scheduler.eventos"))

    try:
        resultado = limpiar_eventos_informativos_antiguos(
            request.form.get("dias_retencion"),
            session.get("usuario"),
            request.form.getlist("categorias"),
        )
        flash(
            f"Limpieza completada: {resultado['eliminados']} eventos anteriores a {resultado.get('fecha_limite') or 'la fecha limite'} fueron eliminados.",
            "success",
        )
    except ValueError:
        flash("Periodo de limpieza no permitido.", "error")
    except Exception as error:
        registrar_auditoria(
            "LIMPIAR_EVENTOS_PROGRAMADOR",
            "scheduler_eventos",
            descripcion="Error controlado al limpiar eventos del programador.",
            valores_despues={"error": error.__class__.__name__},
            resultado="ERROR",
            modulo="SCHEDULER",
            usuario=session.get("usuario"),
        )
        flash("No fue posible limpiar los eventos del programador.", "error")
    return redirect(url_for("scheduler.eventos"))


@bp_scheduler.route("/eventos/limpiar/previsualizar", methods=["POST"])
@permiso_requerido("SCHEDULER_CONFIG_VER")
def previsualizar_limpieza_eventos_scheduler():
    if not _puede_editar_scheduler():
        _registrar_bloqueo_limpieza_eventos()
        return jsonify({"ok": False, "mensaje": "No tienes permisos para limpiar eventos del programador."}), 403

    datos = request.get_json(silent=True) or request.form
    categorias = datos.get("categorias")
    if hasattr(datos, "getlist"):
        categorias = datos.getlist("categorias")
    try:
        resultado = previsualizar_limpieza_eventos(
            datos.get("dias_retencion"),
            categorias,
        )
        return jsonify(resultado)
    except ValueError as error:
        return jsonify({"ok": False, "mensaje": str(error)}), 400
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible previsualizar la limpieza."}), 500


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


@bp_worker_api.route("/estado")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def api_estado_worker():
    try:
        return jsonify(obtener_estado_api_worker())
    except Exception:
        return jsonify(
            {
                "worker_detectado": False,
                "estado_vida": "ERROR",
                "nombre_worker": None,
                "ultimo_heartbeat": None,
                "segundos_desde_ultimo_heartbeat": None,
                "resumen_textual": "No fue posible obtener el estado del worker.",
            }
        ), 500


@bp_worker_api.route("/consola")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def api_consola_worker():
    try:
        return jsonify(obtener_consola_api_worker(request.args.get("limit", 100)))
    except Exception:
        return jsonify(
            {
                "archivo_disponible": False,
                "lineas": [],
                "total_lineas_disponibles": 0,
                "limite_archivo": 300,
                "limite_respuesta": 100,
                "mensaje": "No fue posible leer la consola del worker.",
            }
        ), 500


@bp_worker_api.route("/monitor")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def api_monitor_worker():
    try:
        return jsonify(obtener_monitor_api_worker(limite_consola=request.args.get("limit", 100)))
    except Exception:
        return jsonify(
            {
                "estado_worker": {
                    "worker_detectado": False,
                    "estado_vida": "ERROR",
                    "resumen_textual": "No fue posible construir el monitor del worker.",
                },
                "estado_scheduler": {},
                "consola_reciente": {
                    "archivo_disponible": False,
                    "lineas": [],
                    "total_lineas_disponibles": 0,
                    "limite_archivo": 300,
                    "limite_respuesta": 100,
                    "mensaje": "No fue posible leer la consola del worker.",
                },
                "eventos_recientes": [],
                "ejecuciones_recientes": [],
                "alertas_operativas": [{"tipo": "api", "nivel": "error", "mensaje": "No fue posible construir el monitor del worker."}],
            }
        ), 500


@bp_worker_api.route("/eventos")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def api_eventos_worker():
    try:
        return jsonify({"eventos": obtener_eventos_api_worker(request.args.get("limit", 10))})
    except Exception:
        return jsonify({"eventos": [], "mensaje": "No fue posible obtener eventos recientes del worker."}), 500


@bp_worker_api.route("/ejecuciones")
@permiso_requerido("SCHEDULER_CONFIG_VER")
def api_ejecuciones_worker():
    try:
        return jsonify({"ejecuciones": obtener_ejecuciones_api_worker(request.args.get("limit", 10))})
    except Exception:
        return jsonify({"ejecuciones": [], "mensaje": "No fue posible obtener ejecuciones recientes del worker."}), 500


def _puede_editar_scheduler():
    permisos = session.get("permisos", [])
    return session.get("es_admin_env") or "*" in permisos or "SCHEDULER_CONFIG_EDITAR" in permisos


def _registrar_bloqueo_limpieza_eventos():
    registrar_log_sistema(
        "SCHEDULER_EVENTOS_LIMPIEZA_BLOQUEADA",
        "SCHEDULER",
        "Intento bloqueado de limpiar eventos del programador sin permiso.",
        usuario=session.get("usuario"),
        nivel="WARNING",
    )
    registrar_auditoria(
        "BLOQUEO_PERMISO",
        "scheduler_eventos",
        descripcion="Intento bloqueado de limpiar eventos del programador sin permiso.",
        valores_despues={"permiso_requerido": "SCHEDULER_CONFIG_EDITAR"},
        resultado="BLOQUEADO",
        modulo="SEGURIDAD",
        usuario=session.get("usuario"),
    )
