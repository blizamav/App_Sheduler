"""Rutas de programaciones asociadas a tareas."""

import json

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.modulos.tareas.flujo import construir_flujo


bp_programaciones = Blueprint(
    "programaciones", __name__, url_prefix="/tareas/<int:id_tarea>/programaciones"
)


def _servicio():
    return current_app.extensions["servicio_programaciones"]


def _tareas():
    return current_app.extensions["servicio_tareas"]


def _flujo(id_tarea, total_programaciones):
    detalle_scripts = current_app.extensions["servicio_scripts"].detalle(id_tarea)
    evidencia = current_app.extensions["servicio_evidencias"].obtener_para_tarea(id_tarea)
    notificaciones = current_app.extensions["servicio_notificaciones_tarea"].obtener(id_tarea)
    flujo = list(construir_flujo(
        detalle_scripts=detalle_scripts,
        evidencia=evidencia,
        notificaciones=notificaciones,
        total_programaciones=total_programaciones,
        paso_actual="programacion",
    ))
    urls = (
        url_for("tareas.editar", id_tarea=id_tarea),
        url_for("scripts.detalle", id_tarea=id_tarea),
        url_for("tareas.evidencia", id_tarea=id_tarea),
        url_for("tareas.notificaciones", id_tarea=id_tarea),
        url_for("programaciones.listado", id_tarea=id_tarea),
    )
    for paso, url in zip(flujo, urls):
        paso["url"] = url
    return flujo


def _contexto():
    return ContextoAuditoria(
        request.remote_addr, request.user_agent.string[:500] or None,
        request.path, request.method,
    )


def _entero(valor, default=1):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return default


def _datos_formulario():
    return {
        "tipo_programacion": request.form.get("tipo_programacion", ""),
        "modo_ejecucion_dia": request.form.get("modo_ejecucion_dia", ""),
        "hora_inicio": request.form.get("hora_inicio", ""),
        "hora_termino": request.form.get("hora_termino", ""),
        "hora_ejecucion": request.form.get("hora_ejecucion", ""),
        "intervalo_minutos": request.form.get("intervalo_minutos", ""),
        "dias_semana": request.form.getlist("dias_semana"),
        "dia_mes": request.form.get("dia_mes", ""),
        "fecha_especifica": request.form.get("fecha_especifica", ""),
        "fechas_especificas": request.form.get("fechas_especificas", ""),
        "ejecutar_en_feriados": request.form.get("ejecutar_en_feriados") == "1",
        "zona_horaria": request.form.get("zona_horaria", ""),
        "fecha_inicio_vigencia": request.form.get("fecha_inicio_vigencia", ""),
        "fecha_fin_vigencia": request.form.get("fecha_fin_vigencia", ""),
        "activo": request.form.get("activo") == "1",
    }


def _datos_modelo(actual):
    fechas = actual.fechas_especificas or ""
    if fechas:
        try:
            fechas = ", ".join(json.loads(fechas))
        except (TypeError, ValueError, json.JSONDecodeError):
            fechas = ""
    return {
        "tipo_programacion": actual.tipo_programacion,
        "modo_ejecucion_dia": actual.modo_ejecucion_dia,
        "hora_inicio": actual.hora_inicio,
        "hora_termino": actual.hora_termino,
        "hora_ejecucion": actual.hora_ejecucion,
        "intervalo_minutos": actual.intervalo_minutos,
        "dias_semana": actual.dias_semana,
        "dia_mes": actual.dia_mes,
        "fecha_especifica": actual.fecha_especifica,
        "fechas_especificas": fechas,
        "ejecutar_en_feriados": actual.ejecutar_en_feriados,
        "zona_horaria": actual.zona_horaria,
        "fecha_inicio_vigencia": actual.fecha_inicio_vigencia,
        "fecha_fin_vigencia": actual.fecha_fin_vigencia,
        "activo": actual.activo,
    }


def _tarea_o_redireccion(id_tarea):
    tarea = _tareas().obtener(id_tarea)
    if tarea is None:
        flash("Tarea no encontrada.", "error")
        return None
    return tarea


@bp_programaciones.get("/")
@permiso_requerido("TAREAS_VER")
def listado(id_tarea):
    tarea = _tarea_o_redireccion(id_tarea)
    if tarea is None:
        return redirect(url_for("tareas.listado"))
    resultado = _servicio().listar(
        pagina=max(1, _entero(request.args.get("pagina"))), id_tarea=id_tarea,
    )
    return render_template(
        "programaciones/listado.html", tarea=tarea, resultado=resultado,
        flujo=_flujo(id_tarea, resultado.total),
    )


@bp_programaciones.route("/nueva", methods=["GET", "POST"])
@permiso_requerido("TAREAS_EDITAR")
def nueva(id_tarea):
    tarea = _tarea_o_redireccion(id_tarea)
    if tarea is None:
        return redirect(url_for("tareas.listado"))
    datos = _datos_formulario() if request.method == "POST" else {
        "tipo_programacion": "DIARIA", "modo_ejecucion_dia": "UNA_VEZ",
        "zona_horaria": current_app.config["CONFIGURACION_APLICACION"].zona_horaria,
        "activo": True, "ejecutar_en_feriados": False,
    }
    if request.method == "POST":
        try:
            _servicio().crear(id_tarea, datos, identidad_actual(), _contexto())
        except ErrorValidacion as error:
            flash(error.mensaje, "error")
        else:
            flash("Programacion creada correctamente.", "success")
            return redirect(url_for("programaciones.listado", id_tarea=id_tarea))
    return render_template(
        "programaciones/formulario.html", modo="crear", tarea=tarea, datos=datos,
        flujo=_flujo(id_tarea, _servicio().listar(pagina=1, por_pagina=1, id_tarea=id_tarea).total),
    )


@bp_programaciones.route("/<int:id_programacion>/editar", methods=["GET", "POST"])
@permiso_requerido("TAREAS_EDITAR")
def editar(id_tarea, id_programacion):
    tarea = _tarea_o_redireccion(id_tarea)
    actual = _servicio().obtener(id_programacion)
    if tarea is None or actual is None or actual.id_tarea != id_tarea:
        flash("Programacion no encontrada para la tarea.", "error")
        return redirect(url_for("programaciones.listado", id_tarea=id_tarea))
    datos = _datos_formulario() if request.method == "POST" else _datos_modelo(actual)
    if request.method == "POST":
        try:
            _servicio().actualizar(
                id_tarea, id_programacion, datos, identidad_actual(), _contexto(),
            )
        except ErrorValidacion as error:
            flash(error.mensaje, "error")
        else:
            flash("Programacion actualizada correctamente.", "success")
            return redirect(url_for("programaciones.listado", id_tarea=id_tarea))
    return render_template(
        "programaciones/formulario.html", modo="editar", tarea=tarea,
        datos=datos, actual=actual,
        flujo=_flujo(id_tarea, _servicio().listar(pagina=1, por_pagina=1, id_tarea=id_tarea).total),
    )


@bp_programaciones.post("/<int:id_programacion>/estado")
@permiso_requerido("TAREAS_ESTADO")
def estado(id_tarea, id_programacion):
    activo = request.form.get("activo") == "1"
    try:
        _servicio().cambiar_estado(
            id_tarea, id_programacion, activo, identidad_actual(), _contexto(),
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Estado de programacion actualizado.", "success")
    return redirect(url_for("programaciones.listado", id_tarea=id_tarea))
