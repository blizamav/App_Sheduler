import threading
from datetime import datetime
from pathlib import Path

from flask import current_app

from app.config import BASE_DIR
from app.repositorios.repositorio_ejecuciones import (
    actualizar_log_tarea_final,
    actualizar_pid_ejecucion,
    crear_ejecucion_manual,
    crear_log_tarea,
    existe_ejecucion_en_curso_tarea,
    finalizar_ejecucion,
    marcar_ejecucion_detenida,
    obtener_contexto_tarea_ejecucion,
    obtener_ejecucion,
)
from app.servicios.servicio_archivos import normalizar_segmento, resolver_ruta_segura
from app.servicios.servicio_env_scripts import cargar_env_version
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_procesos import (
    detener_proceso,
    iniciar_proceso_python,
    olvidar_proceso,
    registrar_proceso,
)


ESTADOS_FINALES = {"EXITOSA", "ERROR", "DETENIDA_MANUALMENTE", "CANCELADA"}
MAX_LOG_BYTES = 120 * 1024


def iniciar_ejecucion_manual(id_tarea, usuario):
    ok, mensaje, contexto = _validar_contexto_ejecucion(id_tarea, usuario)
    if not ok:
        registrar_log_sistema("EJECUCION_MANUAL_BLOQUEADA", "EJECUCIONES", mensaje, usuario=usuario, nivel="WARNING")
        return False, mensaje, None

    id_ejecucion = crear_ejecucion_manual(contexto, usuario)
    ruta_fisica_log, ruta_relativa_log, nombre_archivo_log = _crear_rutas_log(id_ejecucion, contexto)
    ruta_fisica_log.parent.mkdir(parents=True, exist_ok=True)
    _escribir_log(
        ruta_fisica_log,
        [
            f"Inicio ejecucion manual: {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"Tarea: {contexto['nombre_tarea']}",
            f"Script activo: {contexto['nombre_archivo']}",
            f"Version: v{contexto['numero_version']}",
            f"Ruta script: {contexto['ruta_relativa']}",
            f"Requiere .env: {'Si' if contexto.get('requiere_env') else 'No'}",
            "Contenido .env: no mostrado por seguridad.",
            "",
        ],
    )
    crear_log_tarea(id_ejecucion, contexto, ruta_fisica_log, ruta_relativa_log, nombre_archivo_log, usuario)
    registrar_log_sistema("EJECUCION_MANUAL_SOLICITADA", "EJECUCIONES", f"Ejecucion {id_ejecucion} solicitada para tarea {contexto['nombre_tarea']}.", usuario=usuario)

    app = current_app._get_current_object()
    hilo = threading.Thread(
        target=_ejecutar_en_segundo_plano,
        args=(app, id_ejecucion, contexto, ruta_fisica_log, usuario),
        daemon=True,
    )
    hilo.start()
    return True, "Ejecucion manual iniciada.", id_ejecucion


def obtener_detalle_ejecucion(id_ejecucion):
    ejecucion = obtener_ejecucion(id_ejecucion)
    if not ejecucion:
        return None
    ejecucion["log"] = leer_log_ejecucion(ejecucion)
    ejecucion["en_ejecucion"] = ejecucion.get("estado_ejecucion") == "EN_EJECUCION"
    return ejecucion


def obtener_estado_log(id_ejecucion):
    ejecucion = obtener_ejecucion(id_ejecucion)
    if not ejecucion:
        return None
    return {
        "estado": ejecucion.get("estado_ejecucion"),
        "log": leer_log_ejecucion(ejecucion),
        "fecha_hora_termino": str(ejecucion.get("fecha_hora_termino") or ""),
        "es_final": ejecucion.get("estado_ejecucion") in ESTADOS_FINALES,
    }


def detener_ejecucion_manual(id_ejecucion, usuario, motivo=None):
    ejecucion = obtener_ejecucion(id_ejecucion)
    if not ejecucion:
        return False, "Ejecucion no encontrada."
    if ejecucion.get("estado_ejecucion") != "EN_EJECUCION":
        return False, "La ejecucion ya no esta en curso."
    if not ejecucion.get("pid_proceso"):
        return False, "La ejecucion no tiene PID registrado para detener."

    fue_forzada = detener_proceso(id_ejecucion, ejecucion.get("pid_proceso"))
    marcar_ejecucion_detenida(
        id_ejecucion,
        usuario,
        motivo or "Detencion manual solicitada desde interfaz.",
        fue_forzada,
    )
    actualizar_log_tarea_final(id_ejecucion, "DETENIDA_MANUALMENTE", None, "Ejecucion detenida manualmente.")
    _escribir_log(
        _ruta_log_desde_ejecucion(ejecucion),
        [
            "",
            f"Detencion manual solicitada por: {usuario}",
            f"Fue detencion forzada: {'Si' if fue_forzada else 'No'}",
            f"Fin ejecucion: {datetime.now():%Y-%m-%d %H:%M:%S}",
            "Estado final: DETENIDA_MANUALMENTE",
        ],
    )
    registrar_log_sistema("EJECUCION_DETENIDA_MANUALMENTE", "EJECUCIONES", f"Ejecucion {id_ejecucion} detenida manualmente.", usuario=usuario, nivel="WARNING")
    return True, "Ejecucion detenida manualmente."


def leer_log_ejecucion(ejecucion):
    ruta = _ruta_log_desde_ejecucion(ejecucion)
    if not ruta or not ruta.exists():
        return "Log aun no disponible."
    with open(ruta, "rb") as archivo:
        archivo.seek(0, 2)
        tamano = archivo.tell()
        archivo.seek(max(0, tamano - MAX_LOG_BYTES))
        contenido = archivo.read().decode("utf-8", errors="replace")
    return contenido


def _validar_contexto_ejecucion(id_tarea, usuario):
    if not usuario:
        return False, "Usuario no autenticado.", None
    contexto = obtener_contexto_tarea_ejecucion(id_tarea)
    if not contexto:
        return False, "Tarea no encontrada.", None
    if not contexto.get("activo") or contexto.get("estado_tarea") != "ACTIVA":
        return False, "No se puede ejecutar una tarea inactiva.", None
    if not contexto.get("id_script"):
        return False, "No se puede ejecutar la tarea porque no tiene script asociado.", None
    if not contexto.get("script_activo"):
        return False, "No se puede ejecutar la tarea porque el script asociado esta inactivo.", None
    if not contexto.get("id_version"):
        return False, "No se puede ejecutar la tarea porque no tiene una version activa.", None
    ruta_script = resolver_ruta_segura(Path(contexto.get("ruta_relativa") or ""))
    if not ruta_script.exists() or not ruta_script.is_file():
        return False, "No se encontro el archivo fisico del script activo.", None
    contexto["ruta_script_fisica_resuelta"] = ruta_script
    if contexto.get("requiere_env"):
        ruta_env = contexto.get("ruta_env_relativa")
        if not ruta_env:
            return False, "Esta version requiere un archivo .env, pero no tiene uno asociado o no existe fisicamente.", None
        ruta_env_fisica = resolver_ruta_segura(Path(ruta_env))
        if not ruta_env_fisica.exists() or not ruta_env_fisica.is_file():
            return False, "Esta version requiere un archivo .env, pero no tiene uno asociado o no existe fisicamente.", None
    if existe_ejecucion_en_curso_tarea(id_tarea):
        return False, "Esta tarea ya tiene una ejecucion en curso. Deten o espera que finalice antes de iniciar otra.", None
    return True, "OK", contexto


def _ejecutar_en_segundo_plano(app, id_ejecucion, contexto, ruta_fisica_log, usuario):
    with app.app_context():
        try:
            entorno = cargar_env_version(contexto["ruta_env_relativa"]) if contexto.get("requiere_env") else None
            if entorno is None:
                import os

                entorno = os.environ.copy()
            proceso = iniciar_proceso_python(contexto["ruta_script_fisica_resuelta"], entorno)
            registrar_proceso(id_ejecucion, proceso)
            actualizar_pid_ejecucion(id_ejecucion, proceso.pid)
            registrar_log_sistema("EJECUCION_MANUAL_INICIADA", "EJECUCIONES", f"Ejecucion {id_ejecucion} iniciada con PID {proceso.pid}.", usuario=usuario)
            _escribir_log(ruta_fisica_log, [f"PID: {proceso.pid}", "Salida del proceso:"])

            with open(ruta_fisica_log, "a", encoding="utf-8", errors="replace") as log:
                for linea in proceso.stdout:
                    log.write(linea)
                    log.flush()
            codigo = proceso.wait()
            ejecucion = obtener_ejecucion(id_ejecucion)
            if ejecucion and ejecucion.get("estado_ejecucion") != "EN_EJECUCION":
                return
            estado = "EXITOSA" if codigo == 0 else "ERROR"
            mensaje_error = None if codigo == 0 else f"Proceso finalizo con codigo {codigo}."
            finalizar_ejecucion(id_ejecucion, estado, codigo, mensaje_error)
            actualizar_log_tarea_final(id_ejecucion, estado, codigo, mensaje_error)
            _escribir_log(
                ruta_fisica_log,
                [
                    "",
                    f"Fin ejecucion: {datetime.now():%Y-%m-%d %H:%M:%S}",
                    f"Codigo salida: {codigo}",
                    f"Estado final: {estado}",
                ],
            )
            registrar_log_sistema(
                "EJECUCION_FINALIZADA_EXITOSA" if estado == "EXITOSA" else "EJECUCION_FINALIZADA_ERROR",
                "EJECUCIONES",
                f"Ejecucion {id_ejecucion} finalizada con estado {estado}.",
                usuario=usuario,
                nivel="INFO" if estado == "EXITOSA" else "ERROR",
            )
        except Exception as error:
            mensaje = "Error controlado al iniciar o ejecutar proceso."
            finalizar_ejecucion(id_ejecucion, "ERROR", None, mensaje)
            actualizar_log_tarea_final(id_ejecucion, "ERROR", None, mensaje)
            _escribir_log(ruta_fisica_log, ["", mensaje, str(error), "Estado final: ERROR"])
            registrar_log_sistema("EJECUCION_INICIO_ERROR", "EJECUCIONES", mensaje, usuario=usuario, nivel="ERROR")
        finally:
            olvidar_proceso(id_ejecucion)


def _crear_rutas_log(id_ejecucion, contexto):
    ahora = datetime.now()
    nombre_tarea = normalizar_segmento(contexto["nombre_tarea"], mayusculas=False)
    nombre_archivo = f"ejecucion_{id_ejecucion}_{nombre_tarea}_{ahora:%Y%m%d_%H%M%S}.log"
    ruta_relativa = Path(
        current_app.config.get("RUTA_BASE_LOGS_TAREAS", "logs_tareas"),
        f"{ahora:%Y}",
        f"{ahora:%m}",
        f"{ahora:%d}",
        nombre_archivo,
    )
    ruta_fisica = (BASE_DIR / ruta_relativa).resolve()
    return ruta_fisica, ruta_relativa.as_posix(), nombre_archivo


def _ruta_log_desde_ejecucion(ejecucion):
    ruta = ejecucion.get("ruta_relativa_log")
    if not ruta:
        return None
    return (BASE_DIR / Path(ruta)).resolve()


def _escribir_log(ruta, lineas):
    if not ruta:
        return
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8", errors="replace") as archivo:
        for linea in lineas:
            archivo.write(f"{linea}\n")
