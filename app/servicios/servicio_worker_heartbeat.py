import os
import socket
from datetime import datetime

from flask import current_app

from app.repositorios.repositorio_worker_heartbeat import (
    actualizar_estado_worker,
    obtener_heartbeat_worker,
    registrar_detencion_worker_bd,
    registrar_error_worker_bd,
    registrar_fin_ciclo_worker,
    upsert_inicio_worker,
)
from app.servicios.servicio_logging_worker import registrar_log_worker
from app.servicios.servicio_logs_sistema import registrar_log_sistema


USUARIO_WORKER = "scheduler_worker"


def registrar_inicio_worker(nombre_worker):
    datos = {
        "nombre_worker": _nombre_worker_seguro(nombre_worker),
        "pid_proceso": os.getpid(),
        "host": socket.gethostname()[:150],
        "version_app": str(current_app.config.get("APP_VERSION") or "local")[:50],
    }
    try:
        upsert_inicio_worker(datos)
        registrar_log_worker(
            f"Senal de vida iniciada. worker={datos['nombre_worker']}; pid={datos['pid_proceso']}; host={datos['host']}.",
            origen="HEARTBEAT",
        )
        registrar_log_sistema(
            "WORKER_HEARTBEAT_INICIADO",
            "SCHEDULER",
            f"Senal de vida iniciada para proceso {datos['nombre_worker']}.",
            usuario=USUARIO_WORKER,
        )
    except Exception as error:
        _registrar_error_heartbeat_log("WORKER_HEARTBEAT_INICIO_ERROR", error)


def actualizar_heartbeat(nombre_worker, estado="ACTIVO"):
    try:
        actualizar_estado_worker(_nombre_worker_seguro(nombre_worker), estado)
    except Exception as error:
        _registrar_error_heartbeat_log("WORKER_HEARTBEAT_ACTUALIZAR_ERROR", error)


def registrar_inicio_ciclo(nombre_worker):
    actualizar_heartbeat(nombre_worker, "EN_CICLO")


def registrar_fin_ciclo(nombre_worker, resultado="OK", evaluadas=0, ejecutadas=0, omitidas=0, estado_final="ESPERANDO"):
    nombre = _nombre_worker_seguro(nombre_worker)
    estado_anterior = obtener_estado_worker(nombre)
    try:
        registrar_fin_ciclo_worker(
            nombre,
            resultado,
            evaluadas,
            ejecutadas,
            omitidas,
            estado_final,
        )
        if resultado == "OK" and estado_anterior and estado_anterior.get("estado") == "ERROR":
            registrar_log_sistema(
                "WORKER_RECUPERADO",
                "SCHEDULER",
                f"Proceso programador {nombre} recuperado despues de estado ERROR.",
                usuario=USUARIO_WORKER,
            )
    except Exception as error:
        _registrar_error_heartbeat_log("WORKER_HEARTBEAT_FIN_CICLO_ERROR", error)


def registrar_error_worker(nombre_worker, error, incrementar_ciclo=False):
    mensaje = _mensaje_error(error)
    try:
        registrar_error_worker_bd(_nombre_worker_seguro(nombre_worker), mensaje, incrementar_ciclo)
        registrar_log_worker(
            f"Heartbeat marco estado ERROR. worker={_nombre_worker_seguro(nombre_worker)}; detalle={mensaje}",
            origen="HEARTBEAT",
            nivel="ERROR",
        )
    except Exception as error_bd:
        _registrar_error_heartbeat_log("WORKER_HEARTBEAT_ERROR_REGISTRO_FALLO", error_bd)

    try:
        registrar_log_sistema(
            "WORKER_ERROR",
            "SCHEDULER",
            "Proceso programador registro estado ERROR.",
            usuario=USUARIO_WORKER,
            valor_nuevo=mensaje,
            nivel="ERROR",
        )
    except Exception:
        pass


def registrar_detencion_worker(nombre_worker):
    try:
        registrar_detencion_worker_bd(_nombre_worker_seguro(nombre_worker))
        registrar_log_worker(
            f"Senal de vida marcada como detenida. worker={_nombre_worker_seguro(nombre_worker)}.",
            origen="HEARTBEAT",
            nivel="WARNING",
        )
        registrar_log_sistema(
            "WORKER_DETENIDO",
            "SCHEDULER",
            f"Proceso programador {nombre_worker} detenido de forma controlada.",
            usuario=USUARIO_WORKER,
        )
    except Exception as error:
        _registrar_error_heartbeat_log("WORKER_HEARTBEAT_DETENCION_ERROR", error)


def obtener_estado_worker(nombre_worker=None):
    try:
        return obtener_heartbeat_worker(_nombre_worker_seguro(nombre_worker) if nombre_worker else None)
    except Exception:
        return None


def clasificar_estado_worker(heartbeat, configuracion_scheduler):
    if not heartbeat:
        return {
            "codigo": "NO_DISPONIBLE",
            "texto": "Proceso programador no iniciado o sin registro.",
            "badge": "info",
            "detalle": "No existe senal de vida registrada.",
            "segundos_desde_heartbeat": None,
        }

    segundos = _segundos_desde(heartbeat.get("fecha_ultimo_heartbeat"))
    intervalo = _intervalo_seguro(configuracion_scheduler)
    estado = str(heartbeat.get("estado") or "").strip().upper()

    if estado == "ERROR":
        return {
            "codigo": "ERROR",
            "texto": "Proceso programador en error.",
            "badge": "error",
            "detalle": heartbeat.get("ultimo_error") or "El proceso programador reporto error sin detalle.",
            "segundos_desde_heartbeat": segundos,
        }
    if _es_estado_detencion_explicita(estado):
        return {
            "codigo": "DETENIDO",
            "texto": "Proceso programador detenido.",
            "badge": "inactivo",
            "detalle": "El proceso programador fue detenido o finalizo su ejecucion.",
            "segundos_desde_heartbeat": segundos,
        }
    if segundos is None:
        return {
            "codigo": "NO_DISPONIBLE",
            "texto": "Proceso programador sin datos suficientes.",
            "badge": "info",
            "detalle": "El registro no tiene fecha de ultima senal.",
            "segundos_desde_heartbeat": None,
        }
    if segundos > intervalo * 5:
        return {
            "codigo": "SIN_SENAL",
            "texto": "Proceso programador sin senal reciente.",
            "badge": "error",
            "detalle": "La ultima senal supera 5 intervalos de revision.",
            "segundos_desde_heartbeat": segundos,
        }
    if segundos > intervalo * 2:
        return {
            "codigo": "ADVERTENCIA",
            "texto": "Proceso programador sin senal reciente.",
            "badge": "advertencia",
            "detalle": "La ultima senal supera 2 intervalos de revision.",
            "segundos_desde_heartbeat": segundos,
        }
    return {
        "codigo": "ACTIVO",
        "texto": "Proceso programador activo.",
        "badge": "activo",
        "detalle": "Senal de vida dentro del margen esperado.",
        "segundos_desde_heartbeat": segundos,
    }


def _nombre_worker_seguro(nombre_worker):
    return (nombre_worker or "worker_default").strip() or "worker_default"


def _mensaje_error(error):
    return str(error or error.__class__.__name__)[:2000]


def _registrar_error_heartbeat_log(accion, error):
    try:
        registrar_log_sistema(
            accion,
            "SCHEDULER",
            "No fue posible actualizar la senal de vida del proceso programador.",
            usuario=USUARIO_WORKER,
            valor_nuevo=error.__class__.__name__,
            nivel="ERROR",
        )
    except Exception:
        pass


def _intervalo_seguro(configuracion):
    try:
        intervalo = int((configuracion or {}).get("intervalo_revision_segundos") or 60)
        if intervalo > 0:
            return intervalo
    except (TypeError, ValueError):
        pass
    return 60


def _segundos_desde(fecha):
    if not fecha:
        return None
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha)
        except ValueError:
            return None
    return max(0, int((datetime.now() - fecha).total_seconds()))


def _es_estado_detencion_explicita(estado):
    if not estado:
        return False
    estados_detenidos = {
        "DETENIDO",
        "DETENIDA",
        "STOPPED",
        "FINALIZADO",
        "FINALIZADA",
        "FINALIZADO_CONTROLADO",
        "FINALIZADA_CONTROLADA",
        "INTERRUMPIDO",
        "INTERRUMPIDA",
        "DETENIDO_MANUAL",
        "DETENIDA_MANUAL",
        "DETENIDO_MANUALMENTE",
        "DETENIDA_MANUALMENTE",
    }
    return estado in estados_detenidos
