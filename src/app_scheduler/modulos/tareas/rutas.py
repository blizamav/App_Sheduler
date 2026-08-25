"""Rutas web de tareas del Hito 5."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.modulos.tareas.flujo import construir_flujo, flujo_nueva_tarea


bp_tareas = Blueprint("tareas", __name__, url_prefix="/tareas")


def _servicio(): return current_app.extensions["servicio_tareas"]
def _servicio_evidencias(): return current_app.extensions["servicio_evidencias"]
def _servicio_notificaciones(): return current_app.extensions["servicio_notificaciones_tarea"]
def _servicio_scripts(): return current_app.extensions["servicio_scripts"]
def _servicio_programaciones(): return current_app.extensions["servicio_programaciones"]
def _contexto(): return ContextoAuditoria(request.remote_addr, request.user_agent.string[:500] or None, request.path, request.method)
def _entero(valor, default=None):
    try: return int(valor)
    except (TypeError, ValueError): return default
def _datos():
    return {clave: request.form.get(clave, "") for clave in
            ("nombre_tarea", "descripcion", "observacion_tecnica", "id_cliente",
             "id_categoria", "id_tipo", "estado_tarea")}


@bp_tareas.get("/")
@permiso_requerido("TAREAS_VER")
def listado():
    estado = request.args.get("estado", "").strip().upper() or None
    id_cliente = _entero(request.args.get("id_cliente"))
    try:
        resultado = _servicio().listar(
            pagina=max(1, _entero(request.args.get("pagina"), 1)),
            busqueda=request.args.get("buscar", "").strip() or None,
            estado=estado, id_cliente=id_cliente,
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error"); return redirect(url_for("tareas.listado"))
    return render_template("tareas/listado.html", resultado=resultado,
        catalogos=_servicio().catalogos(), filtros={"buscar": request.args.get("buscar", ""),
        "estado": estado or "", "id_cliente": id_cliente or ""})


@bp_tareas.route("/nueva", methods=["GET", "POST"])
@permiso_requerido("TAREAS_CREAR")
def nueva():
    datos = _datos() if request.method == "POST" else {"estado_tarea": "ACTIVA"}
    if request.method == "POST":
        try: identificador = _servicio().crear(datos, identidad_actual(), _contexto())
        except ErrorValidacion as error: flash(error.mensaje, "error")
        else:
            flash("Tarea creada correctamente.", "success")
            if request.form.get("accion") == "continuar":
                return redirect(url_for("scripts.detalle", id_tarea=identificador))
            return redirect(url_for("tareas.listado"))
    return render_template("tareas/formulario.html", modo="crear", datos=datos,
                           catalogos=_servicio().catalogos(), flujo=flujo_nueva_tarea())


@bp_tareas.route("/<int:id_tarea>/editar", methods=["GET", "POST"])
@permiso_requerido("TAREAS_EDITAR")
def editar(id_tarea):
    actual = _servicio().obtener(id_tarea)
    if actual is None:
        flash("Tarea no encontrada.", "error"); return redirect(url_for("tareas.listado"))
    datos = _datos() if request.method == "POST" else {
        "nombre_tarea": actual.nombre_tarea, "descripcion": actual.descripcion or "",
        "observacion_tecnica": actual.observacion_tecnica or "", "id_cliente": actual.id_cliente,
        "id_categoria": actual.id_categoria, "id_tipo": actual.id_tipo,
        "estado_tarea": actual.estado_tarea,
    }
    if request.method == "POST":
        try: _servicio().actualizar(id_tarea, datos, identidad_actual(), _contexto())
        except ErrorValidacion as error: flash(error.mensaje, "error")
        else:
            flash("Tarea actualizada correctamente.", "success")
            return redirect(url_for("tareas.editar", id_tarea=id_tarea))
    detalle_scripts = _servicio_scripts().detalle(id_tarea)
    evidencia = _servicio_evidencias().obtener_para_tarea(id_tarea)
    notificaciones = _servicio_notificaciones().obtener(id_tarea)
    total_programaciones = _servicio_programaciones().listar(
        pagina=1, por_pagina=1, id_tarea=id_tarea
    ).total
    flujo = list(construir_flujo(
        detalle_scripts=detalle_scripts, evidencia=evidencia,
        notificaciones=notificaciones, total_programaciones=total_programaciones,
    ))
    urls = (
        url_for("tareas.editar", id_tarea=id_tarea),
        url_for("scripts.detalle", id_tarea=id_tarea),
        url_for("tareas.editar", id_tarea=id_tarea, _anchor="evidencia"),
        url_for("tareas.editar", id_tarea=id_tarea, _anchor="notificaciones"),
        url_for("programaciones.listado", id_tarea=id_tarea),
    )
    for paso, url in zip(flujo, urls):
        paso["url"] = url
    return render_template("tareas/formulario.html", modo="editar", datos=datos,
                           actual=actual, catalogos=_servicio().catalogos(),
                           evidencia=evidencia, notificaciones=notificaciones,
                           flujo=flujo, detalle_scripts=detalle_scripts,
                           total_programaciones=total_programaciones)


@bp_tareas.post("/<int:id_tarea>/evidencia")
@permiso_requerido("TAREAS_EDITAR")
def guardar_evidencia(id_tarea):
    try:
        _servicio_evidencias().guardar(id_tarea, request.form, identidad_actual(), _contexto())
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Configuracion de evidencia actualizada.", "success")
    return redirect(url_for("tareas.editar", id_tarea=id_tarea))


@bp_tareas.post("/<int:id_tarea>/notificaciones")
@permiso_requerido("TAREAS_EDITAR")
def guardar_notificaciones(id_tarea):
    try:
        _servicio_notificaciones().guardar(
            id_tarea, request.form, identidad_actual(), _contexto()
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Configuracion de notificaciones actualizada.", "success")
    return redirect(url_for("tareas.editar", id_tarea=id_tarea))


@bp_tareas.post("/<int:id_tarea>/estado")
@permiso_requerido("TAREAS_ESTADO")
def estado(id_tarea):
    try: _servicio().cambiar_estado(id_tarea, request.form.get("estado", ""), identidad_actual(), _contexto())
    except ErrorValidacion as error: flash(error.mensaje, "error")
    else: flash("Estado de tarea actualizado.", "success")
    return redirect(url_for("tareas.listado"))
