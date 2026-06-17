import time
from datetime import datetime

from app.repositorios.repositorio_configuracion_scheduler import obtener_configuracion_activa
from app.repositorios.repositorio_ejecuciones import existe_ejecucion_en_curso_tarea
from app.repositorios.repositorio_scheduler import (
    contar_ejecuciones_automaticas_en_curso,
    existe_clave_programacion,
    listar_tareas_programadas_activas,
)
from app.servicios.servicio_calendario import obtener_feriado
from app.servicios.servicio_ejecuciones import iniciar_ejecucion_automatica
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_scheduler_eventos import (
    registrar_ciclo_finalizado as registrar_evento_ciclo_finalizado,
    registrar_ciclo_iniciado as registrar_evento_ciclo_iniciado,
    registrar_error_programador,
    registrar_tarea_ejecutada,
    registrar_tarea_omitida,
)
from app.servicios.servicio_worker_heartbeat import (
    actualizar_heartbeat,
    registrar_detencion_worker,
    registrar_error_worker,
    registrar_fin_ciclo,
    registrar_inicio_ciclo,
    registrar_inicio_worker,
)
from app.servicios.servicio_programador import debe_ejecutarse_ahora


USUARIO_WORKER = "scheduler_worker"


def ejecutar_worker_continuo():
    _log_consola("Inicio worker.")
    nombre_worker = _nombre_worker_desde_configuracion()
    registrar_inicio_worker(nombre_worker)
    try:
        while True:
            intervalo = ejecutar_ciclo_worker(nombre_worker=nombre_worker)
            actualizar_heartbeat(nombre_worker, "ESPERANDO")
            time.sleep(intervalo)
    except KeyboardInterrupt:
        _log_consola("Worker detenido por interrupcion.")
        registrar_detencion_worker(nombre_worker)
        raise


def ejecutar_worker_una_vez(fecha_hora_actual=None):
    nombre_worker = _nombre_worker_desde_configuracion()
    try:
        registrar_inicio_worker(nombre_worker)
        return ejecutar_ciclo_worker(fecha_hora_actual=fecha_hora_actual, nombre_worker=nombre_worker)
    finally:
        registrar_detencion_worker(nombre_worker)


def ejecutar_ciclo_worker(fecha_hora_actual=None, nombre_worker=None):
    ahora = fecha_hora_actual or datetime.now()
    nombre_worker_actual = nombre_worker or "worker_default"
    try:
        configuracion = obtener_configuracion_activa()
        if not configuracion:
            registrar_inicio_ciclo(nombre_worker_actual)
            _registrar_estado("WORKER_CONFIG_NO_EXISTE", "No existe configuracion activa. No se ejecutan tareas.", "WARNING")
            registrar_error_programador(nombre_worker_actual, "No existe configuracion activa del programador.")
            registrar_fin_ciclo(nombre_worker_actual, "OK", 0, 0, 0)
            return 60

        intervalo = _intervalo_seguro(configuracion)
        nombre_worker_actual = nombre_worker or configuracion.get("nombre_worker_principal") or "worker_default"
        registrar_inicio_ciclo(nombre_worker_actual)
        _log_consola(f"Configuracion cargada. Worker={nombre_worker_actual}; intervalo={intervalo}s.")

        if not configuracion.get("scheduler_activo"):
            _registrar_estado("WORKER_SCHEDULER_APAGADO", "Scheduler apagado. No se evaluan tareas.")
            registrar_evento_ciclo_iniciado(nombre_worker_actual, configuracion, 0)
            registrar_tarea_omitida(None, "SCHEDULER_INACTIVO", "Ciclo omitido porque el programador esta inactivo.", nombre_worker_actual, configuracion)
            registrar_evento_ciclo_finalizado(nombre_worker_actual, configuracion, 0, 0, 0)
            registrar_fin_ciclo(nombre_worker_actual, "OK", 0, 0, 0)
            return intervalo
        if configuracion.get("modo_mantenimiento"):
            _registrar_estado("WORKER_MANTENIMIENTO", "Modo mantenimiento activo. No se inician ejecuciones.")
            registrar_evento_ciclo_iniciado(nombre_worker_actual, configuracion, 0)
            registrar_tarea_omitida(None, "MODO_MANTENIMIENTO", "Ciclo omitido porque el modo mantenimiento esta activo.", nombre_worker_actual, configuracion)
            registrar_evento_ciclo_finalizado(nombre_worker_actual, configuracion, 0, 0, 0)
            registrar_fin_ciclo(nombre_worker_actual, "OK", 0, 0, 0)
            return intervalo
        if not configuracion.get("permitir_ejecucion_automatica"):
            _registrar_estado("WORKER_AUTO_DESHABILITADA", "Ejecucion automatica deshabilitada. No se ejecutan tareas.")
            registrar_evento_ciclo_iniciado(nombre_worker_actual, configuracion, 0)
            registrar_tarea_omitida(None, "EJECUCION_AUTOMATICA_DESHABILITADA", "Ciclo omitido porque la ejecucion automatica esta deshabilitada.", nombre_worker_actual, configuracion)
            registrar_evento_ciclo_finalizado(nombre_worker_actual, configuracion, 0, 0, 0)
            registrar_fin_ciclo(nombre_worker_actual, "OK", 0, 0, 0)
            return intervalo

        resultado = _evaluar_tareas(configuracion, ahora, intervalo, nombre_worker_actual)
        registrar_fin_ciclo(
            nombre_worker_actual,
            "OK",
            resultado["evaluadas"],
            resultado["ejecutadas"],
            resultado["omitidas"],
        )
        return intervalo
    except KeyboardInterrupt:
        raise
    except Exception as error:
        _log_consola(f"Error controlado del worker: {error}")
        registrar_error_worker(nombre_worker_actual, error, incrementar_ciclo=True)
        registrar_error_programador(nombre_worker_actual, error)
        registrar_log_sistema(
            "WORKER_ERROR_CONTROLADO",
            "SCHEDULER",
            "Error controlado durante ciclo del worker.",
            usuario=USUARIO_WORKER,
            valor_nuevo=str(error),
            nivel="ERROR",
        )
        return 60


def _evaluar_tareas(configuracion, ahora, intervalo, nombre_worker):
    max_concurrentes = _max_concurrentes_seguro(configuracion)
    en_curso = contar_ejecuciones_automaticas_en_curso()
    if en_curso >= max_concurrentes:
        mensaje = f"Limite de concurrencia alcanzado: {en_curso}/{max_concurrentes}."
        _registrar_estado("WORKER_LIMITE_CONCURRENCIA", mensaje)
        registrar_evento_ciclo_iniciado(nombre_worker, configuracion, 0)
        registrar_tarea_omitida(None, "LIMITE_CONCURRENCIA", mensaje, nombre_worker, configuracion)
        registrar_evento_ciclo_finalizado(nombre_worker, configuracion, 0, 0, 0)
        return {"evaluadas": 0, "ejecutadas": 0, "omitidas": 0}

    tareas = listar_tareas_programadas_activas()
    _log_consola(f"Tareas evaluadas: {len(tareas)}.")
    registrar_evento_ciclo_iniciado(nombre_worker, configuracion, len(tareas))

    ejecutadas = 0
    omitidas = 0
    for tarea in tareas:
        if en_curso + ejecutadas >= max_concurrentes:
            _registrar_estado("WORKER_LIMITE_CONCURRENCIA", "Limite alcanzado durante ciclo.")
            registrar_tarea_omitida(
                tarea,
                "LIMITE_CONCURRENCIA",
                "Tarea omitida porque se alcanzo el limite de ejecuciones concurrentes durante el ciclo.",
                nombre_worker,
                configuracion,
            )
            break

        resultado = debe_ejecutarse_ahora(tarea, ahora, intervalo)
        if not resultado["debe_ejecutar"]:
            omitidas += 1
            _log_consola(f"Omitida tarea {tarea['id_tarea']}: {resultado['motivo']}")
            motivo = _motivo_omision_ventana(resultado["motivo"])
            if motivo:
                registrar_tarea_omitida(
                    tarea,
                    motivo,
                    "Tarea omitida porque la fecha/hora actual no coincide con la ventana de ejecucion.",
                    nombre_worker,
                    configuracion,
                )
            continue

        feriado = obtener_feriado(resultado["fecha_programada"].date())
        if not bool(tarea.get("ejecutar_en_feriados")) and feriado:
            omitidas += 1
            mensaje_feriado = f"Tarea omitida por feriado: {resultado['fecha_programada']:%Y-%m-%d} - {feriado['nombre']}"
            _log_consola(f"Omitida tarea {tarea['id_tarea']}: {mensaje_feriado}")
            registrar_tarea_omitida(
                tarea,
                "FERIADO",
                "Tarea omitida porque la fecha programada corresponde a feriado y la programacion no permite ejecutar en feriados.",
                nombre_worker,
                configuracion,
                fecha_programada=resultado["fecha_programada"],
                clave_programacion=resultado["clave_programacion"],
                feriado=feriado,
            )
            continue
        if bool(tarea.get("ejecutar_en_feriados")) and feriado:
            _log_consola(f"Tarea {tarea['id_tarea']} permitida en feriado por configuracion.")

        if existe_clave_programacion(resultado["clave_programacion"]):
            omitidas += 1
            _log_consola(f"Omitida tarea {tarea['id_tarea']}: clave ya ejecutada.")
            registrar_tarea_omitida(
                tarea,
                "DUPLICADO_SLOT",
                "Tarea omitida porque el slot programado ya fue ejecutado.",
                nombre_worker,
                configuracion,
                fecha_programada=resultado["fecha_programada"],
                clave_programacion=resultado["clave_programacion"],
            )
            continue

        if existe_ejecucion_en_curso_tarea(tarea["id_tarea"]):
            omitidas += 1
            _log_consola(f"Omitida tarea {tarea['id_tarea']}: ya tiene ejecucion en curso.")
            registrar_tarea_omitida(
                tarea,
                "EJECUCION_EN_CURSO",
                "Tarea omitida porque ya existe una ejecucion activa para la misma tarea.",
                nombre_worker,
                configuracion,
                fecha_programada=resultado["fecha_programada"],
                clave_programacion=resultado["clave_programacion"],
            )
            continue

        ok, mensaje, id_ejecucion = iniciar_ejecucion_automatica(
            tarea["id_tarea"],
            nombre_worker=nombre_worker,
            fecha_programada=resultado["fecha_programada"],
            clave_programacion=resultado["clave_programacion"],
        )
        if ok:
            ejecutadas += 1
            _log_consola(f"Ejecutada tarea {tarea['id_tarea']} como ejecucion {id_ejecucion}.")
            registrar_tarea_ejecutada(
                tarea,
                nombre_worker,
                configuracion,
                fecha_programada=resultado["fecha_programada"],
                clave_programacion=resultado["clave_programacion"],
                id_ejecucion=id_ejecucion,
            )
        else:
            omitidas += 1
            _log_consola(f"No se pudo ejecutar tarea {tarea['id_tarea']}: {mensaje}")
            registrar_tarea_omitida(
                tarea,
                "ERROR_VALIDACION",
                mensaje,
                nombre_worker,
                configuracion,
                fecha_programada=resultado["fecha_programada"],
                clave_programacion=resultado["clave_programacion"],
            )

    registrar_evento_ciclo_finalizado(nombre_worker, configuracion, len(tareas), ejecutadas, omitidas)
    _log_consola(f"Ciclo finalizado. Ejecutadas={ejecutadas}; omitidas={omitidas}.")
    return {"evaluadas": len(tareas), "ejecutadas": ejecutadas, "omitidas": omitidas}


def _intervalo_seguro(configuracion):
    try:
        intervalo = int(configuracion.get("intervalo_revision_segundos") or 60)
        if 10 <= intervalo <= 3600:
            return intervalo
    except ValueError:
        pass
    _registrar_estado("WORKER_INTERVALO_INVALIDO", "Intervalo invalido. Se usa fallback 60 segundos.", "WARNING")
    return 60


def _max_concurrentes_seguro(configuracion):
    try:
        maximo = int(configuracion.get("max_ejecuciones_concurrentes") or 3)
        if 1 <= maximo <= 20:
            return maximo
    except ValueError:
        pass
    _registrar_estado("WORKER_MAX_CONCURRENCIA_INVALIDO", "Maximo concurrentes invalido. Se usa fallback 3.", "WARNING")
    return 3


def _nombre_worker_desde_configuracion():
    try:
        configuracion = obtener_configuracion_activa()
        return configuracion.get("nombre_worker_principal") or "worker_default" if configuracion else "worker_default"
    except Exception:
        return "worker_default"


def _registrar_estado(accion, mensaje, nivel="INFO", registrar_log=False):
    _log_consola(mensaje)
    if registrar_log:
        registrar_log_sistema(accion, "SCHEDULER", mensaje, usuario=USUARIO_WORKER, nivel=nivel)


def _log_consola(mensaje):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {mensaje}", flush=True)


def _motivo_omision_ventana(motivo):
    motivos_ventana = {
        "Fuera de ventana de ejecucion.",
        "No hay slot pendiente en ventana.",
        "Hora de ejecucion no configurada.",
        "Intervalo incompleto.",
        "Ventana horaria invalida.",
    }
    return "FUERA_DE_VENTANA" if motivo in motivos_ventana else None
