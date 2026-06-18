import ctypes
import os
from pathlib import Path

from app.config import BASE_DIR
from app.repositorios.repositorio_ejecuciones import (
    actualizar_log_tarea_final,
    finalizar_ejecucion,
    listar_ejecuciones_en_curso,
    obtener_ejecucion,
)
from app.servicios.servicio_logs_ejecucion import escribir_lineas_log
from app.servicios.servicio_logs_sistema import registrar_log_sistema


PROCESO_EXISTE = "EXISTE"
PROCESO_NO_EXISTE = "NO_EXISTE"
PROCESO_DESCONOCIDO = "DESCONOCIDO"
MENSAJE_HUERFANA = "Proceso no encontrado. Ejecucion marcada como ERROR por control de ejecuciones huerfanas."


def proceso_existe(pid):
    try:
        pid_normalizado = int(pid)
    except (TypeError, ValueError):
        return PROCESO_DESCONOCIDO
    if pid_normalizado <= 0:
        return PROCESO_DESCONOCIDO

    if os.name == "nt":
        return _proceso_existe_windows(pid_normalizado)
    return _proceso_existe_posix(pid_normalizado)


def detectar_ejecuciones_huerfanas():
    resultado = {"revisadas": 0, "marcadas_error": 0, "activas": 0, "desconocidas": 0, "detalles": []}
    for ejecucion in listar_ejecuciones_en_curso():
        resultado["revisadas"] += 1
        verificacion = verificar_ejecucion(ejecucion["id_ejecucion"], ejecucion=ejecucion)
        resultado["detalles"].append(verificacion)
        if verificacion["estado_control"] == "HUERFANA":
            resultado["marcadas_error"] += 1
        elif verificacion["estado_control"] == "ACTIVA":
            resultado["activas"] += 1
        elif verificacion["estado_control"] == "DESCONOCIDA":
            resultado["desconocidas"] += 1
    return resultado


def verificar_ejecucion(id_ejecucion, ejecucion=None, usuario=None):
    ejecucion = ejecucion or obtener_ejecucion(id_ejecucion)
    if not ejecucion:
        return {"ok": False, "estado_control": "NO_ENCONTRADA", "mensaje": "Ejecucion no encontrada."}

    if ejecucion.get("estado_ejecucion") != "EN_EJECUCION":
        return {
            "ok": True,
            "estado_control": "FINALIZADA",
            "mensaje": "La ejecucion ya se encuentra finalizada.",
        }

    pid = ejecucion.get("pid_proceso")
    estado_pid = proceso_existe(pid)
    if estado_pid == PROCESO_EXISTE:
        return {"ok": True, "estado_control": "ACTIVA", "mensaje": "La ejecucion sigue activa."}
    if estado_pid == PROCESO_DESCONOCIDO:
        return {
            "ok": False,
            "estado_control": "DESCONOCIDA",
            "mensaje": "No fue posible validar el proceso de la ejecucion.",
        }

    _marcar_ejecucion_huerfana(id_ejecucion, ejecucion, usuario)
    return {
        "ok": True,
        "estado_control": "HUERFANA",
        "mensaje": "La ejecucion estaba huerfana y fue marcada como ERROR.",
    }


def _proceso_existe_posix(pid):
    try:
        os.kill(pid, 0)
        return PROCESO_EXISTE
    except ProcessLookupError:
        return PROCESO_NO_EXISTE
    except PermissionError:
        return PROCESO_EXISTE
    except Exception:
        return PROCESO_DESCONOCIDO


def _proceso_existe_windows(pid):
    try:
        kernel32 = ctypes.windll.kernel32
        process_query_limited_information = 0x1000
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return PROCESO_EXISTE
        error = kernel32.GetLastError()
        if error == 87:
            return PROCESO_NO_EXISTE
        if error == 5:
            return PROCESO_EXISTE
        return PROCESO_NO_EXISTE
    except Exception:
        return PROCESO_DESCONOCIDO


def _marcar_ejecucion_huerfana(id_ejecucion, ejecucion, usuario=None):
    if not ejecucion.get("ruta_relativa_log"):
        ejecucion = obtener_ejecucion(id_ejecucion) or ejecucion
    finalizar_ejecucion(id_ejecucion, "ERROR", None, MENSAJE_HUERFANA)
    actualizar_log_tarea_final(id_ejecucion, "ERROR", None, MENSAJE_HUERFANA)
    _escribir_log_control(ejecucion)
    registrar_log_sistema(
        "EJECUCION_HUERFANA_MARCADA_ERROR",
        "EJECUCIONES",
        f"Ejecucion {id_ejecucion} marcada como ERROR por PID inexistente.",
        usuario=usuario or "control_ejecuciones",
        nivel="WARNING",
        valor_nuevo=str({"id_ejecucion": id_ejecucion, "pid_proceso": ejecucion.get("pid_proceso")}),
    )


def _escribir_log_control(ejecucion):
    ruta_relativa = ejecucion.get("ruta_relativa_log")
    if not ruta_relativa:
        return
    ruta_log = (BASE_DIR / Path(ruta_relativa)).resolve()
    escribir_lineas_log(
        ruta_log,
        [
            ("Control de ejecuciones huerfanas ejecutado.", "WARN"),
            (f"PID no encontrado: {ejecucion.get('pid_proceso')}", "WARN"),
            (MENSAJE_HUERFANA, "ERROR"),
            ("Estado final: ERROR", "ERROR"),
        ],
    )
