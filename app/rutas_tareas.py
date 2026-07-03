from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_notificaciones import (
    desactivar_config_notificacion_tarea,
    guardar_config_notificacion_tarea,
    obtener_config_notificacion_tarea,
)
from app.servicios.servicio_evidencias import validar_soporte_evidencia_script_por_tarea
from app.servicios.servicio_tareas import (
    actualizar_tarea_admin,
    cambiar_estado_tarea_admin,
    crear_tarea_admin,
    eliminar_tarea_admin,
    listar_tareas_admin,
    obtener_catalogos_tareas,
    obtener_tarea_admin,
)


bp_tareas = Blueprint("tareas", __name__, url_prefix="/tareas")
bp_tareas_api = Blueprint("tareas_api", __name__, url_prefix="/api/tareas")


def _filtros_request():
    filtros = {
        "estado": request.args.get("estado", "").strip(),
        "id_cliente": request.args.get("id_cliente", "").strip(),
        "id_categoria": request.args.get("id_categoria", "").strip(),
        "id_tipo": request.args.get("id_tipo", "").strip(),
        "tipo_programacion": request.args.get("tipo_programacion", "").strip(),
        "buscar": request.args.get("buscar", "").strip(),
    }
    return {clave: valor for clave, valor in filtros.items() if valor}


def _catalogos_seguros():
    try:
        return obtener_catalogos_tareas()
    except Exception:
        flash("No fue posible cargar catalogos de tareas. Verifica la conexion y migraciones pendientes.", "error")
        return {
            "clientes": [],
            "categorias": [],
            "tipos": [],
            "tipos_programacion": ("MANUAL", "DIARIA", "SEMANAL", "MENSUAL", "FECHA_ESPECIFICA"),
            "modos_ejecucion": ("UNA_VEZ", "INTERVALO"),
            "dias_semana": ("LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"),
        }


def _registro_desde_formulario():
    registro = request.form.to_dict()
    registro["dias_semana_lista"] = request.form.getlist("dias_semana")
    return registro


@bp_tareas.route("/")
@permiso_requerido("TAREAS_VER")
def listado():
    filtros = _filtros_request()
    catalogos = _catalogos_seguros()
    try:
        tareas = listar_tareas_admin(filtros)
    except Exception:
        tareas = []
        flash("No fue posible consultar tareas. Si aun no ejecutaste la migracion 008, hazlo primero en SSMS.", "error")

    return render_template(
        "tareas/listado.html",
        tareas=tareas,
        filtros=filtros,
        catalogos=catalogos,
        total_tareas=len(tareas),
    )


@bp_tareas.route("/nueva", methods=["GET", "POST"])
@permiso_requerido("TAREAS_CREAR")
def nueva():
    catalogos = _catalogos_seguros()
    registro = {"tipo_programacion": "MANUAL", "modo_ejecucion_dia": "UNA_VEZ", "activo": "1"}

    if request.method == "POST":
        registro = _registro_desde_formulario()
        try:
            ok, mensajes, id_tarea = crear_tarea_admin(request.form, session.get("usuario"))
        except Exception:
            ok, mensajes, id_tarea = False, ["No fue posible crear la tarea. Verifica conexion y migracion 008."], None
        if ok:
            flash(mensajes[0], "success")
            return redirect(url_for("tareas.editar", id_tarea=id_tarea))

        for mensaje in mensajes:
            flash(mensaje, "error")

    return render_template("tareas/formulario.html", modo="crear", registro=registro, catalogos=catalogos)


@bp_tareas.route("/<int:id_tarea>/editar", methods=["GET", "POST"])
@permiso_requerido("TAREAS_EDITAR")
def editar(id_tarea):
    catalogos = _catalogos_seguros()
    registro = obtener_tarea_admin(id_tarea)
    if not registro:
        flash("Tarea no encontrada.", "error")
        return redirect(url_for("tareas.listado"))

    if request.method == "POST":
        try:
            ok, mensajes = actualizar_tarea_admin(id_tarea, request.form, session.get("usuario"))
        except Exception:
            ok, mensajes = False, ["No fue posible actualizar la tarea. Verifica conexion y migracion 008."]
        if ok:
            flash(mensajes[0], "success")
            return redirect(url_for("tareas.listado"))

        for mensaje in mensajes:
            flash(mensaje, "info" if mensaje == "No hay cambios para guardar." else "error")
        registro.update(_registro_desde_formulario())

    return render_template("tareas/formulario.html", modo="editar", registro=registro, catalogos=catalogos)


@bp_tareas.route("/<int:id_tarea>/estado", methods=["POST"])
@permiso_requerido("TAREAS_ESTADO")
def estado(id_tarea):
    activo = request.form.get("activo") == "1"
    try:
        ok, mensaje = cambiar_estado_tarea_admin(id_tarea, activo, session.get("usuario"))
    except Exception:
        ok, mensaje = False, "No fue posible actualizar el estado de la tarea."
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("tareas.listado"))


@bp_tareas.route("/<int:id_tarea>/eliminar", methods=["POST"])
@permiso_requerido("TAREAS_ELIMINAR")
def eliminar(id_tarea):
    try:
        ok, mensaje = eliminar_tarea_admin(id_tarea, session.get("usuario"))
    except Exception:
        ok, mensaje = False, "No fue posible eliminar la tarea."
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("tareas.listado"))


@bp_tareas_api.route("/<int:id_tarea>/notificaciones", methods=["GET"])
@permiso_requerido("TAREAS_VER")
def api_obtener_notificaciones(id_tarea):
    try:
        ok, mensaje, config = obtener_config_notificacion_tarea(id_tarea)
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible obtener la configuracion de notificaciones."}), 500
    estado = 200 if ok else 404
    return jsonify({"ok": ok, "mensaje": mensaje, "config": config}), estado


@bp_tareas_api.route("/<int:id_tarea>/notificaciones", methods=["POST", "PUT"])
@permiso_requerido("TAREAS_EDITAR")
def api_guardar_notificaciones(id_tarea):
    datos = request.get_json(silent=True) or {}
    try:
        ok, mensajes, config = guardar_config_notificacion_tarea(
            id_tarea,
            datos,
            datos.get("destinatarios") or [],
            session.get("usuario"),
        )
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible guardar la configuracion de notificaciones."}), 500

    estado = 200 if ok else 400
    return jsonify(
        {
            "ok": ok,
            "mensaje": mensajes[0] if mensajes else "",
            "mensajes": mensajes,
            "config": config,
        }
    ), estado


@bp_tareas_api.route("/<int:id_tarea>/notificaciones/desactivar", methods=["POST"])
@permiso_requerido("TAREAS_EDITAR")
def api_desactivar_notificaciones(id_tarea):
    try:
        ok, mensaje = desactivar_config_notificacion_tarea(id_tarea, session.get("usuario"))
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible desactivar la configuracion de notificaciones."}), 500
    return jsonify({"ok": ok, "mensaje": mensaje}), 200 if ok else 404


@bp_tareas_api.route("/<int:id_tarea>/evidencia/validar-soporte", methods=["GET"])
@permiso_requerido("TAREAS_VER")
def api_validar_soporte_evidencia(id_tarea):
    try:
        resultado = validar_soporte_evidencia_script_por_tarea(id_tarea)
        return jsonify({"ok": True, **resultado})
    except Exception:
        return jsonify({"ok": False, "mensaje": "No fue posible validar el soporte de evidencia del script."}), 500
