from datetime import date, datetime

from app.repositorios.repositorio_configuracion_scheduler import obtener_configuracion_activa
from app.repositorios.repositorio_panel_scheduler import (
    listar_ultimas_ejecuciones_automaticas,
    obtener_estado_feriados_locales,
)
from app.servicios.servicio_logging_worker import leer_buffer_worker
from app.servicios.servicio_scheduler_eventos import obtener_eventos_relevantes, obtener_resumen_inteligente_eventos
from app.servicios.servicio_worker_heartbeat import (
    clasificar_estado_worker,
    formatear_fecha_monitor,
    obtener_estado_worker,
    obtener_zona_horaria_monitor,
)


def obtener_estado_api_worker():
    configuracion = obtener_configuracion_activa()
    nombre_worker = configuracion.get("nombre_worker_principal") if configuracion else None
    heartbeat = obtener_estado_worker(nombre_worker)
    estado_worker = clasificar_estado_worker(heartbeat, configuracion)
    return {
        "worker_detectado": bool(heartbeat),
        "estado_vida": _normalizar_estado_vida(estado_worker),
        "nombre_worker": _valor(heartbeat, "nombre_worker") or nombre_worker,
        "ultimo_heartbeat": formatear_fecha_monitor(_valor(heartbeat, "fecha_ultimo_heartbeat")),
        "ultimo_heartbeat_local": formatear_fecha_monitor(_valor(heartbeat, "fecha_ultimo_heartbeat")),
        "segundos_desde_ultimo_heartbeat": estado_worker.get("segundos_desde_heartbeat"),
        "fecha_inicio": formatear_fecha_monitor(_valor(heartbeat, "fecha_inicio")),
        "ultimo_ciclo": formatear_fecha_monitor(_valor(heartbeat, "fecha_ultimo_ciclo")),
        "resultado_ultimo_ciclo": _valor(heartbeat, "resultado_ultimo_ciclo"),
        "ciclos_ejecutados": int(_valor(heartbeat, "ciclos_ejecutados") or 0),
        "tareas_evaluadas_ultimo_ciclo": int(_valor(heartbeat, "tareas_evaluadas_ultimo_ciclo") or 0),
        "tareas_ejecutadas_ultimo_ciclo": int(_valor(heartbeat, "tareas_ejecutadas_ultimo_ciclo") or 0),
        "tareas_omitidas_ultimo_ciclo": int(_valor(heartbeat, "tareas_omitidas_ultimo_ciclo") or 0),
        "ultimo_error": _valor(heartbeat, "ultimo_error"),
        "pid_proceso": _valor(heartbeat, "pid_proceso"),
        "host": _valor(heartbeat, "host"),
        "version_app": _valor(heartbeat, "version_app"),
        "zona_horaria": obtener_zona_horaria_monitor(),
        "scheduler": _estado_scheduler(configuracion),
        "resumen_textual": _resumen_textual_worker(heartbeat, estado_worker, configuracion),
    }


def obtener_monitor_api_worker(limite_consola=100):
    estado_worker = obtener_estado_api_worker()
    configuracion = obtener_configuracion_activa() or {}
    resumen_eventos = obtener_resumen_inteligente_eventos()
    eventos = _serializar_lista(obtener_eventos_relevantes(limite=10))
    ejecuciones = _serializar_lista(listar_ultimas_ejecuciones_automaticas(limite=10))
    feriados = _serializar_valor(obtener_estado_feriados_locales() or {})
    alertas = _construir_alertas_operativas(estado_worker, resumen_eventos, configuracion, feriados, eventos)

    return {
        "estado_worker": estado_worker,
        "estado_scheduler": _estado_scheduler(configuracion),
        "consola_reciente": leer_buffer_worker(limite_consola),
        "eventos_recientes": eventos,
        "resumen_eventos": _serializar_valor(resumen_eventos),
        "ejecuciones_recientes": ejecuciones,
        "feriados": feriados,
        "alertas_operativas": alertas,
    }


def obtener_consola_api_worker(limite_consola=100):
    return leer_buffer_worker(limite_consola)


def obtener_eventos_api_worker(limite=10):
    return _serializar_lista(obtener_eventos_relevantes(limite=_limite_eventos_seguro(limite)))


def obtener_ejecuciones_api_worker(limite=10):
    return _serializar_lista(listar_ultimas_ejecuciones_automaticas(limite=_limite_eventos_seguro(limite)))


def _estado_scheduler(configuracion):
    configuracion = configuracion or {}
    return {
        "scheduler_activo": bool(configuracion.get("scheduler_activo")),
        "permitir_ejecucion_automatica": bool(configuracion.get("permitir_ejecucion_automatica")),
        "modo_mantenimiento": bool(configuracion.get("modo_mantenimiento")),
        "intervalo_revision_segundos": int(configuracion.get("intervalo_revision_segundos") or 0),
        "max_ejecuciones_concurrentes": int(configuracion.get("max_ejecuciones_concurrentes") or 0),
        "nombre_worker_principal": configuracion.get("nombre_worker_principal"),
        "resumen_textual": _resumen_textual_scheduler(configuracion),
    }


def _resumen_textual_worker(heartbeat, estado_worker, configuracion):
    if not heartbeat:
        return "Worker sin senal de vida registrada."
    nombre_worker = heartbeat.get("nombre_worker") or configuracion.get("nombre_worker_principal") or "worker"
    detalle = estado_worker.get("detalle") or "Sin detalle."
    return f"{nombre_worker}: {estado_worker.get('texto') or 'Estado desconocido'}. {detalle}"


def _resumen_textual_scheduler(configuracion):
    if not configuracion:
        return "Sin configuracion activa del scheduler."
    if configuracion.get("modo_mantenimiento"):
        return "Scheduler en modo mantenimiento."
    if not configuracion.get("scheduler_activo"):
        return "Scheduler configurado como inactivo."
    if not configuracion.get("permitir_ejecucion_automatica"):
        return "Scheduler activo con ejecucion automatica deshabilitada."
    return "Scheduler operativo para ejecuciones automaticas."


def _normalizar_estado_vida(estado_worker):
    codigo = (estado_worker or {}).get("codigo")
    if codigo:
        return codigo
    badge = (estado_worker or {}).get("badge")
    equivalencias = {
        "inactivo": "DETENIDO",
        "activo": "ACTIVO",
        "advertencia": "ADVERTENCIA",
        "error": "ERROR",
        "info": "NO_DISPONIBLE",
    }
    return equivalencias.get(badge, "NO_DISPONIBLE")


def _construir_alertas_operativas(estado_worker, resumen_eventos, configuracion, feriados, eventos):
    alertas = []
    estado_vida = estado_worker.get("estado_vida")
    if estado_vida in {"ERROR", "ADVERTENCIA", "SIN_SENAL", "DETENIDO"}:
        alertas.append(
            {
                "tipo": "worker",
                "nivel": "error" if estado_vida in {"ERROR", "SIN_SENAL"} else "advertencia",
                "mensaje": estado_worker.get("resumen_textual"),
            }
        )
    if configuracion and configuracion.get("modo_mantenimiento"):
        alertas.append({"tipo": "scheduler", "nivel": "advertencia", "mensaje": "El scheduler esta en modo mantenimiento."})
    if configuracion and not configuracion.get("scheduler_activo"):
        alertas.append({"tipo": "scheduler", "nivel": "advertencia", "mensaje": "El scheduler esta desactivado en configuracion."})
    if configuracion and configuracion.get("scheduler_activo") and not configuracion.get("permitir_ejecucion_automatica"):
        alertas.append({"tipo": "scheduler", "nivel": "advertencia", "mensaje": "La ejecucion automatica esta deshabilitada."})
    if int((resumen_eventos or {}).get("errores_programador") or 0) > 0:
        alertas.append(
            {
                "tipo": "eventos",
                "nivel": "error",
                "mensaje": f"Existen {(resumen_eventos or {}).get('errores_programador')} errores recientes del programador.",
            }
        )
    evento_feriado = next((evento for evento in (eventos or []) if evento.get("motivo") == "FERIADO"), None)
    if evento_feriado:
        alertas.append(
            {
                "tipo": "feriados",
                "nivel": "advertencia",
                "mensaje": "Hay omisiones recientes por feriado registradas por el programador.",
            }
        )
    if feriados and feriados.get("proximo"):
        alertas.append(
            {
                "tipo": "feriados",
                "nivel": "info",
                "mensaje": f"Proximo feriado local: {feriados['proximo'].get('nombre')} ({feriados['proximo'].get('fecha')}).",
            }
        )
    return alertas


def _limite_eventos_seguro(valor):
    try:
        limite = int(valor or 10)
    except (TypeError, ValueError):
        return 10
    return max(1, min(20, limite))


def _serializar_lista(items):
    return [_serializar_valor(item) for item in (items or [])]


def _serializar_valor(valor):
    if isinstance(valor, dict):
        return {clave: _serializar_valor(item) for clave, item in valor.items()}
    if isinstance(valor, list):
        return [_serializar_valor(item) for item in valor]
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def _valor(diccionario, clave):
    if not diccionario:
        return None
    return diccionario.get(clave)
