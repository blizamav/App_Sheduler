from app.repositorios.repositorio_configuracion_scheduler import obtener_configuracion_activa
from app.repositorios.repositorio_panel_scheduler import (
    listar_errores_scheduler_recientes,
    listar_tareas_candidatas,
    listar_ultimas_ejecuciones_automaticas,
    obtener_estado_feriados_locales,
    obtener_resumen_ejecuciones_automaticas,
)
from app.servicios.servicio_worker_heartbeat import clasificar_estado_worker, obtener_estado_worker


def obtener_panel_scheduler():
    configuracion = obtener_configuracion_activa()
    resumen_ejecuciones = obtener_resumen_ejecuciones_automaticas()
    ultimas = listar_ultimas_ejecuciones_automaticas()
    errores = listar_errores_scheduler_recientes()
    candidatas = listar_tareas_candidatas()
    feriados = obtener_estado_feriados_locales()
    nombre_worker = configuracion.get("nombre_worker_principal") if configuracion else None
    heartbeat = obtener_estado_worker(nombre_worker)
    estado_worker = clasificar_estado_worker(heartbeat, configuracion)

    return {
        "configuracion": configuracion,
        "worker": {"heartbeat": heartbeat, "estado": estado_worker},
        "resumen_ejecuciones": _normalizar_resumen(resumen_ejecuciones),
        "ultimas_ejecuciones": ultimas,
        "errores_recientes": errores,
        "tareas_candidatas": [_preparar_tarea(tarea) for tarea in candidatas],
        "feriados": _normalizar_feriados(feriados),
        "estado_operativo": _estado_operativo(configuracion, resumen_ejecuciones, errores),
    }


def _normalizar_resumen(resumen):
    resumen = resumen or {}
    return {
        "total": int(resumen.get("total") or 0),
        "en_ejecucion": int(resumen.get("en_ejecucion") or 0),
        "exitosas": int(resumen.get("exitosas") or 0),
        "errores": int(resumen.get("errores") or 0),
        "detenidas": int(resumen.get("detenidas") or 0),
    }


def _normalizar_feriados(feriados):
    feriados = feriados or {}
    return {
        "total": int(feriados.get("total") or 0),
        "activos": int(feriados.get("activos") or 0),
        "manuales_activos": int(feriados.get("manuales_activos") or 0),
        "api_nager_activos": int(feriados.get("api_nager_activos") or 0),
        "proximo": feriados.get("proximo"),
    }


def _preparar_tarea(tarea):
    tarea = dict(tarea)
    tarea["resumen_programacion"] = _resumen_programacion(tarea)
    tarea["estado_script"] = "Con script activo" if tarea.get("id_version_activa") else "Sin version activa"
    return tarea


def _resumen_programacion(tarea):
    tipo = tarea.get("tipo_programacion") or "-"
    modo = tarea.get("modo_ejecucion_dia") or "-"
    if tipo == "DIARIA":
        return f"Diaria {modo}"
    if tipo == "SEMANAL":
        return f"Semanal {tarea.get('dias_semana') or '-'}"
    if tipo == "MENSUAL":
        return f"Mensual dia {tarea.get('dia_mes') or '-'}"
    if tipo == "FECHA_ESPECIFICA":
        return f"Fecha especifica {tarea.get('fecha_especifica') or '-'}"
    return tipo


def _estado_operativo(configuracion, resumen, errores):
    if not configuracion:
        return {"texto": "Sin configuracion", "badge": "error", "detalle": "No existe configuracion activa."}
    if configuracion.get("modo_mantenimiento"):
        return {"texto": "Mantenimiento", "badge": "advertencia", "detalle": "Modo mantenimiento activo."}
    if not configuracion.get("scheduler_activo"):
        return {"texto": "Programador inactivo", "badge": "inactivo", "detalle": "El proceso programador no evaluara tareas."}
    if not configuracion.get("permitir_ejecucion_automatica"):
        return {"texto": "Automaticas bloqueadas", "badge": "advertencia", "detalle": "Programador activo sin ejecucion automatica."}
    if errores:
        return {"texto": "Activo con advertencias", "badge": "advertencia", "detalle": "Existen errores o advertencias recientes."}
    return {"texto": "Operativo", "badge": "activo", "detalle": "Configuracion habilitada para ejecuciones automaticas."}
