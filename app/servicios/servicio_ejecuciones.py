import threading
from datetime import datetime
from pathlib import Path

from flask import current_app

from app.config import BASE_DIR
from app.repositorios.repositorio_ejecuciones import (
    actualizar_log_tarea_final,
    actualizar_pid_ejecucion,
    contar_ejecuciones_filtradas,
    crear_ejecucion_automatica,
    crear_ejecucion_manual,
    crear_log_tarea,
    existe_ejecucion_en_curso_tarea,
    finalizar_ejecucion,
    listar_ejecuciones_paginadas,
    marcar_ejecucion_detenida,
    obtener_contexto_tarea_ejecucion,
    obtener_ejecucion,
    resumir_ejecuciones_filtradas,
)
from app.servicios.servicio_archivos import normalizar_segmento, resolver_ruta_segura
from app.servicios.servicio_env_scripts import cargar_env_version
from app.servicios.servicio_evidencias import (
    DELIMITADOR_FIN,
    DELIMITADOR_INICIO,
    procesar_evidencia_ejecucion,
)
from app.servicios.servicio_logs_ejecucion import (
    escribir_linea_log,
    escribir_lineas_log,
    normalizar_linea_script,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_procesos import (
    detener_proceso,
    iniciar_proceso_python,
    terminar_proceso,
    olvidar_proceso,
    registrar_proceso,
)


ESTADOS_FINALES = {"EXITOSA", "ERROR", "DETENIDA_MANUALMENTE", "CANCELADA"}
ESTADOS_FILTRO = ("EN_EJECUCION", "EXITOSA", "ERROR", "DETENIDA_MANUALMENTE", "CANCELADA")
ORIGENES_FILTRO = ("MANUAL", "AUTOMATICA")
PER_PAGE_OPCIONES = (10, 25, 50, 100)
MAX_LOG_BYTES = 120 * 1024
MENSAJE_ERROR_MONITOR = "Ejecucion cerrada como ERROR por fallo controlado del monitor de ejecucion."
MESES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def iniciar_ejecucion_manual(id_tarea, usuario):
    ok, mensaje, contexto = _validar_contexto_ejecucion(id_tarea, usuario)
    if not ok:
        registrar_log_sistema("EJECUCION_MANUAL_BLOQUEADA", "EJECUCIONES", mensaje, usuario=usuario, nivel="WARNING")
        registrar_auditoria(
            "BLOQUEO_EJECUTAR_TAREA_NO_EJECUTABLE",
            "ejecuciones",
            id_entidad=id_tarea,
            descripcion=mensaje,
            valores_despues={"id_tarea": id_tarea, "motivo_bloqueo": mensaje},
            resultado="BLOQUEADO",
            modulo="EJECUCIONES",
            usuario=usuario,
        )
        return False, mensaje, None

    id_ejecucion = crear_ejecucion_manual(contexto, usuario)
    ruta_fisica_log, ruta_relativa_log, nombre_archivo_log = _crear_rutas_log(id_ejecucion, contexto)
    ruta_fisica_log.parent.mkdir(parents=True, exist_ok=True)
    _escribir_log(
        ruta_fisica_log,
        [
            "Inicio de ejecucion",
            "Origen: MANUAL",
            f"Tarea: {contexto['nombre_tarea']}",
            f"Script activo: {contexto['nombre_archivo']}",
            f"Version: v{contexto['numero_version']}",
            f"Ruta script: {contexto['ruta_relativa']}",
            f".env requerido: {'Si' if contexto.get('requiere_env') else 'No'}",
            "Contenido .env: no mostrado por seguridad.",
            "Salida stdout/stderr combinada: INFO por defecto.",
        ],
    )
    crear_log_tarea(id_ejecucion, contexto, ruta_fisica_log, ruta_relativa_log, nombre_archivo_log, usuario)
    registrar_log_sistema("EJECUCION_MANUAL_SOLICITADA", "EJECUCIONES", f"Ejecucion {id_ejecucion} solicitada para tarea {contexto['nombre_tarea']}.", usuario=usuario)
    registrar_auditoria(
        "EJECUTAR_MANUAL",
        "ejecuciones",
        id_entidad=id_ejecucion,
        nombre_entidad=contexto["nombre_tarea"],
        descripcion=f"Ejecucion manual {id_ejecucion} solicitada para tarea {contexto['nombre_tarea']}.",
        valores_despues={
            "id_tarea": id_tarea,
            "id_script": contexto.get("id_script"),
            "id_version": contexto.get("id_version"),
            "numero_version": contexto.get("numero_version"),
        },
        modulo="EJECUCIONES",
        usuario=usuario,
    )

    app = current_app._get_current_object()
    hilo = threading.Thread(
        target=_ejecutar_en_segundo_plano,
        args=(app, id_ejecucion, contexto, ruta_fisica_log, usuario, "MANUAL"),
        daemon=False,
    )
    hilo.start()
    return True, "Ejecucion manual iniciada.", id_ejecucion


def iniciar_ejecucion_automatica(id_tarea, nombre_worker, fecha_programada, clave_programacion):
    ok, mensaje, contexto = _validar_contexto_ejecucion(id_tarea, "scheduler_worker")
    if not ok:
        registrar_log_sistema("EJECUCION_AUTOMATICA_BLOQUEADA", "EJECUCIONES", mensaje, usuario="scheduler_worker", nivel="WARNING")
        return False, mensaje, None

    id_ejecucion = crear_ejecucion_automatica(contexto, nombre_worker, fecha_programada, clave_programacion)
    ruta_fisica_log, ruta_relativa_log, nombre_archivo_log = _crear_rutas_log(id_ejecucion, contexto)
    ruta_fisica_log.parent.mkdir(parents=True, exist_ok=True)
    _escribir_log(
        ruta_fisica_log,
        [
            "Inicio de ejecucion",
            "Origen: AUTOMATICA",
            f"Tarea: {contexto['nombre_tarea']}",
            f"Script activo: {contexto['nombre_archivo']}",
            f"Version: v{contexto['numero_version']}",
            f"Ruta script: {contexto['ruta_relativa']}",
            f"Fecha programada: {fecha_programada}",
            f"Clave programacion: {clave_programacion}",
            f"Worker: {nombre_worker}",
            f".env requerido: {'Si' if contexto.get('requiere_env') else 'No'}",
            "Contenido .env: no mostrado por seguridad.",
            "Salida stdout/stderr combinada: INFO por defecto.",
        ],
    )
    crear_log_tarea(id_ejecucion, contexto, ruta_fisica_log, ruta_relativa_log, nombre_archivo_log, "scheduler_worker")
    registrar_log_sistema(
        "EJECUCION_AUTOMATICA_SOLICITADA",
        "EJECUCIONES",
        f"Ejecucion automatica {id_ejecucion} solicitada para tarea {contexto['nombre_tarea']}.",
        usuario="scheduler_worker",
        valor_nuevo=clave_programacion,
    )

    app = current_app._get_current_object()
    hilo = threading.Thread(
        target=_ejecutar_en_segundo_plano,
        args=(app, id_ejecucion, contexto, ruta_fisica_log, "scheduler_worker", "AUTOMATICA"),
        daemon=False,
    )
    hilo.start()
    return True, "Ejecucion automatica iniciada.", id_ejecucion


def listar_ejecuciones_admin(parametros):
    filtros, page, per_page, advertencias = _normalizar_filtros_ejecuciones(parametros)
    total = contar_ejecuciones_filtradas(filtros)
    total_paginas = max(1, (total + per_page - 1) // per_page)
    if page > total_paginas:
        page = total_paginas
    ejecuciones = listar_ejecuciones_paginadas(filtros, page, per_page)
    resumen = resumir_ejecuciones_filtradas(filtros)
    return {
        "ejecuciones": ejecuciones,
        "grupos": agrupar_ejecuciones_por_fecha(ejecuciones),
        "filtros": filtros,
        "page": page,
        "per_page": per_page,
        "per_page_opciones": PER_PAGE_OPCIONES,
        "total": total,
        "total_paginas": total_paginas,
        "resumen": resumen,
        "advertencias": advertencias,
        "origenes": ORIGENES_FILTRO,
        "estados": ESTADOS_FILTRO,
    }


def agrupar_ejecuciones_por_fecha(ejecuciones):
    grupos = []
    indice_anios = {}
    for ejecucion in ejecuciones:
        fecha = ejecucion.get("fecha_hora_inicio")
        if not fecha:
            continue
        anio = fecha.year
        mes = fecha.month
        dia = fecha.day
        etiqueta_mes = f"{mes:02d} - {MESES.get(mes, str(mes))}"

        grupo_anio = indice_anios.get(anio)
        if not grupo_anio:
            grupo_anio = {"anio": anio, "meses": [], "_meses": {}}
            indice_anios[anio] = grupo_anio
            grupos.append(grupo_anio)

        grupo_mes = grupo_anio["_meses"].get(mes)
        if not grupo_mes:
            grupo_mes = {"numero": mes, "etiqueta": etiqueta_mes, "dias": [], "_dias": {}}
            grupo_anio["_meses"][mes] = grupo_mes
            grupo_anio["meses"].append(grupo_mes)

        grupo_dia = grupo_mes["_dias"].get(dia)
        if not grupo_dia:
            grupo_dia = {"dia": dia, "ejecuciones": []}
            grupo_mes["_dias"][dia] = grupo_dia
            grupo_mes["dias"].append(grupo_dia)
        grupo_dia["ejecuciones"].append(ejecucion)

    for grupo_anio in grupos:
        grupo_anio.pop("_meses", None)
        for grupo_mes in grupo_anio["meses"]:
            grupo_mes.pop("_dias", None)
    return grupos


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
    estado = ejecucion.get("estado_ejecucion")
    es_final = estado in ESTADOS_FINALES
    fecha_hora_termino = str(ejecucion.get("fecha_hora_termino") or "")
    return {
        "estado": estado,
        "estado_actual": estado,
        "estado_es_final": es_final,
        "log": leer_log_ejecucion(ejecucion),
        "fecha_hora_termino": fecha_hora_termino,
        "fecha_hora_fin": fecha_hora_termino,
        "duracion_segundos": ejecucion.get("duracion_segundos"),
        "codigo_salida": ejecucion.get("codigo_salida"),
        "mensaje_error": ejecucion.get("mensaje_error") or "",
        "en_ejecucion": estado == "EN_EJECUCION",
        "es_final": es_final,
        "detener_polling": es_final,
    }


def detener_ejecucion_manual(id_ejecucion, usuario, motivo=None):
    ejecucion = obtener_ejecucion(id_ejecucion)
    if not ejecucion:
        _auditar_detencion_bloqueada(id_ejecucion, usuario, "Ejecucion no encontrada.", None)
        return False, "Ejecucion no encontrada."
    if ejecucion.get("estado_ejecucion") != "EN_EJECUCION":
        _auditar_detencion_bloqueada(id_ejecucion, usuario, "La ejecucion ya no esta en curso.", ejecucion)
        return False, "La ejecucion ya no esta en curso."
    if not ejecucion.get("pid_proceso"):
        _auditar_detencion_bloqueada(id_ejecucion, usuario, "La ejecucion no tiene PID registrado para detener.", ejecucion)
        return False, "La ejecucion no tiene PID registrado para detener."

    fue_forzada = detener_proceso(id_ejecucion, ejecucion.get("pid_proceso"))
    marcar_ejecucion_detenida(
        id_ejecucion,
        usuario,
        motivo or "Detencion manual solicitada desde interfaz.",
        fue_forzada,
    )
    actualizar_log_tarea_final(id_ejecucion, "DETENIDA_MANUALMENTE", None, "Ejecucion detenida manualmente.")
    ruta_log = _ruta_log_desde_ejecucion(ejecucion)
    _escribir_log(
        ruta_log,
        [
            (f"Detencion manual solicitada por usuario: {usuario}", "WARN"),
            (f"Senal de detencion enviada al proceso PID {ejecucion.get('pid_proceso')}", "WARN"),
            ("Cierre forzado aplicado" if fue_forzada else "Proceso detenido correctamente", "WARN"),
            ("Fue detencion forzada: Si" if fue_forzada else "Fue detencion forzada: No", "WARN"),
            "Estado final: DETENIDA_MANUALMENTE",
            f"Fecha/hora termino: {datetime.now():%Y-%m-%d %H:%M:%S}",
        ],
    )
    registrar_log_sistema("EJECUCION_DETENIDA_MANUALMENTE", "EJECUCIONES", f"Ejecucion {id_ejecucion} detenida manualmente.", usuario=usuario, nivel="WARNING")
    registrar_auditoria(
        "DETENER_EJECUCION",
        "ejecuciones",
        id_entidad=id_ejecucion,
        nombre_entidad=ejecucion.get("nombre_tarea"),
        descripcion=f"Ejecucion {id_ejecucion} detenida manualmente.",
        valores_antes=ejecucion,
        valores_despues={"estado_ejecucion": "DETENIDA_MANUALMENTE", "fue_forzada": fue_forzada},
        modulo="EJECUCIONES",
        usuario=usuario,
    )
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
    if not bool(contexto.get("tarea_activo")):
        return False, "La tarea esta inactiva.", None
    if bool(contexto.get("tarea_eliminada_operativo")):
        return False, "La tarea fue borrada operativamente y no puede ejecutarse.", None
    if contexto.get("estado_tarea") != "ACTIVA":
        return False, "El estado de la tarea no permite ejecucion.", None
    if not contexto.get("id_script"):
        return False, "No se puede ejecutar la tarea porque no tiene script asociado.", None
    if bool(contexto.get("script_eliminado_operativo")):
        return False, "No se puede ejecutar la tarea porque el script asociado fue borrado operativamente.", None
    if not bool(contexto.get("script_activo")):
        return False, "No se puede ejecutar la tarea porque el script asociado esta inactivo.", None
    if not contexto.get("id_version_activa") or not contexto.get("id_version"):
        return False, "No se puede ejecutar la tarea porque no tiene una version activa.", None
    if bool(contexto.get("version_eliminada_operativo")):
        return False, "No se puede ejecutar la tarea porque la version activa fue borrada operativamente.", None
    if not bool(contexto.get("es_activa")) or contexto.get("estado_version") != "ACTIVA":
        return False, "No se puede ejecutar la tarea porque la version activa no esta disponible.", None
    if existe_ejecucion_en_curso_tarea(id_tarea):
        return False, "Esta tarea ya tiene una ejecucion en curso. Deten o espera que finalice antes de iniciar otra.", None
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
    return True, "OK", contexto


def _ejecutar_en_segundo_plano(app, id_ejecucion, contexto, ruta_fisica_log, usuario, origen="MANUAL"):
    with app.app_context():
        proceso = None
        monitor_fallo = False
        stdout_evidencia = []
        try:
            entorno = cargar_env_version(contexto["ruta_env_relativa"]) if contexto.get("requiere_env") else None
            if contexto.get("requiere_env"):
                _escribir_log(ruta_fisica_log, [".env cargado correctamente"])
            if entorno is None:
                import os

                entorno = os.environ.copy()
                if not contexto.get("requiere_env"):
                    _escribir_log(ruta_fisica_log, [".env no requerido"])
            proceso = iniciar_proceso_python(contexto["ruta_script_fisica_resuelta"], entorno)
            registrar_proceso(id_ejecucion, proceso)
            actualizar_pid_ejecucion(id_ejecucion, proceso.pid)
            accion_inicio = "EJECUCION_AUTOMATICA_INICIADA" if origen == "AUTOMATICA" else "EJECUCION_MANUAL_INICIADA"
            registrar_log_sistema(accion_inicio, "EJECUCIONES", f"Ejecucion {id_ejecucion} iniciada con PID {proceso.pid}.", usuario=usuario)
            _escribir_log(ruta_fisica_log, [f"PID proceso: {proceso.pid}", "Salida del proceso:"])

            if proceso.stdout:
                capturando_evidencia = False
                for linea in proceso.stdout:
                    texto_linea = str(linea).rstrip("\r\n")
                    if not capturando_evidencia and DELIMITADOR_INICIO in texto_linea:
                        stdout_evidencia.append(texto_linea)
                        capturando_evidencia = True
                        if DELIMITADOR_FIN in texto_linea:
                            capturando_evidencia = False
                    elif capturando_evidencia:
                        stdout_evidencia.append(texto_linea)
                        if DELIMITADOR_FIN in texto_linea:
                            capturando_evidencia = False
                    escribir_linea_log(ruta_fisica_log, normalizar_linea_script(linea), "INFO")
            codigo = proceso.wait()
            try:
                resultado_evidencia = procesar_evidencia_ejecucion(id_ejecucion, contexto["id_tarea"], codigo, stdout_evidencia)
                if resultado_evidencia:
                    _escribir_log(
                        ruta_fisica_log,
                        [
                            (
                                f"Evidencia stdout procesada: {resultado_evidencia.get('estado_evidencia')}",
                                "INFO" if resultado_evidencia.get("estado_evidencia") == "VALIDADA" else "WARNING",
                            )
                        ],
                    )
            except Exception as error_evidencia:
                registrar_log_sistema(
                    "EVIDENCIA_STDOUT_PROCESO_ERROR",
                    "EVIDENCIAS",
                    "Error controlado al procesar evidencia stdout.",
                    usuario=usuario,
                    valor_nuevo=error_evidencia.__class__.__name__,
                    nivel="ERROR",
                )
            if not _ejecucion_sigue_en_curso(id_ejecucion):
                return
            estado = "EXITOSA" if codigo == 0 else "ERROR"
            mensaje_error = None if codigo == 0 else f"Proceso finalizo con codigo {codigo}."
            _cerrar_ejecucion_en_curso(id_ejecucion, estado, codigo, mensaje_error)
            nivel_final = "INFO" if estado == "EXITOSA" else "ERROR"
            _escribir_log(
                ruta_fisica_log,
                [
                    (f"Codigo salida proceso: {codigo}", nivel_final),
                    (f"Estado final: {estado}", nivel_final),
                    f"Fecha/hora termino: {datetime.now():%Y-%m-%d %H:%M:%S}",
                ],
            )
            prefijo = "EJECUCION_AUTOMATICA" if origen == "AUTOMATICA" else "EJECUCION"
            registrar_log_sistema(
                f"{prefijo}_FINALIZADA_EXITOSA" if estado == "EXITOSA" else f"{prefijo}_FINALIZADA_ERROR",
                "EJECUCIONES",
                f"Ejecucion {id_ejecucion} finalizada con estado {estado}.",
                usuario=usuario,
                nivel="INFO" if estado == "EXITOSA" else "ERROR",
            )
        except Exception as error:
            if origen != "MANUAL":
                mensaje = "Error controlado al iniciar o ejecutar proceso."
                _cerrar_ejecucion_en_curso(id_ejecucion, "ERROR", None, mensaje)
                _escribir_log(ruta_fisica_log, [(mensaje, "ERROR"), (str(error), "ERROR"), ("Estado final: ERROR", "ERROR")])
                registrar_log_sistema("EJECUCION_INICIO_ERROR", "EJECUCIONES", mensaje, usuario=usuario, nivel="ERROR")
                return

            monitor_fallo = True
            if proceso and proceso.poll() is None:
                terminar_proceso(proceso)
            _cerrar_ejecucion_en_curso(id_ejecucion, "ERROR", None, MENSAJE_ERROR_MONITOR)
            _escribir_log_seguro(
                ruta_fisica_log,
                [(MENSAJE_ERROR_MONITOR, "ERROR"), (error.__class__.__name__, "ERROR"), ("Estado final: ERROR", "ERROR")],
            )
            registrar_log_sistema("EJECUCION_MONITOR_ERROR", "EJECUCIONES", MENSAJE_ERROR_MONITOR, usuario=usuario, nivel="ERROR")
            registrar_auditoria(
                "EJECUTAR_MANUAL",
                "ejecuciones",
                id_entidad=id_ejecucion,
                nombre_entidad=contexto.get("nombre_tarea"),
                descripcion=MENSAJE_ERROR_MONITOR,
                valores_antes={"id_tarea": contexto.get("id_tarea"), "id_version": contexto.get("id_version")},
                valores_despues={"estado_ejecucion": "ERROR", "error": error.__class__.__name__},
                resultado="ERROR",
                modulo="EJECUCIONES",
                usuario=usuario,
            )
        finally:
            if _ejecucion_sigue_en_curso(id_ejecucion):
                if proceso and proceso.poll() is None:
                    terminar_proceso(proceso)
                _cerrar_ejecucion_en_curso(id_ejecucion, "ERROR", None, MENSAJE_ERROR_MONITOR)
                _escribir_log_seguro(
                    ruta_fisica_log,
                    [
                        (MENSAJE_ERROR_MONITOR, "ERROR"),
                        ("El monitor finalizo sin cerrar la ejecucion.", "ERROR"),
                        ("Estado final: ERROR", "ERROR"),
                    ],
                )
                if not monitor_fallo:
                    accion_cierre = (
                        "EJECUCION_MONITOR_CIERRE_GARANTIZADO"
                        if origen == "MANUAL"
                        else "EJECUCION_AUTOMATICA_MONITOR_CIERRE_GARANTIZADO"
                    )
                    registrar_log_sistema(accion_cierre, "EJECUCIONES", MENSAJE_ERROR_MONITOR, usuario=usuario, nivel="ERROR")
            olvidar_proceso(id_ejecucion)


def _auditar_detencion_bloqueada(id_ejecucion, usuario, mensaje, ejecucion):
    registrar_auditoria(
        "BLOQUEO_DETENER_EJECUCION_FINALIZADA",
        "ejecuciones",
        id_entidad=id_ejecucion,
        nombre_entidad=ejecucion.get("nombre_tarea") if ejecucion else None,
        descripcion=mensaje,
        valores_antes={"estado_ejecucion": ejecucion.get("estado_ejecucion")} if ejecucion else None,
        valores_despues={"motivo_bloqueo": mensaje},
        resultado="BLOQUEADO",
        modulo="EJECUCIONES",
        usuario=usuario,
    )


def _ejecucion_sigue_en_curso(id_ejecucion):
    ejecucion = obtener_ejecucion(id_ejecucion)
    return bool(ejecucion and ejecucion.get("estado_ejecucion") == "EN_EJECUCION")


def _cerrar_ejecucion_en_curso(id_ejecucion, estado, codigo_salida=None, mensaje_error=None):
    if not _ejecucion_sigue_en_curso(id_ejecucion):
        return False
    finalizar_ejecucion(id_ejecucion, estado, codigo_salida, mensaje_error)
    actualizar_log_tarea_final(id_ejecucion, estado, codigo_salida, mensaje_error)
    return True


def _escribir_log_seguro(ruta_log, lineas):
    try:
        _escribir_log(ruta_log, lineas)
    except Exception:
        pass


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


def _normalizar_filtros_ejecuciones(parametros):
    advertencias = []
    filtros = {}
    page = _entero_get(parametros, "page", 1)
    per_page = _entero_get(parametros, "per_page", 25)
    if page < 1:
        page = 1
        advertencias.append("La pagina solicitada no era valida; se uso pagina 1.")
    if per_page not in PER_PAGE_OPCIONES:
        per_page = 25
        advertencias.append("El tamano de pagina no era valido; se uso 25.")

    id_ejecucion = _entero_get(parametros, "id_ejecucion", None)
    if id_ejecucion:
        if id_ejecucion > 0:
            filtros["id_ejecucion"] = id_ejecucion
        else:
            advertencias.append("El ID de ejecucion no era valido y fue ignorado.")
        return filtros, page, per_page, advertencias

    for campo in ("tarea", "usuario", "worker"):
        valor = (parametros.get(campo) or "").strip()
        if valor:
            filtros[campo] = valor[:100]

    origen = (parametros.get("origen") or "").strip().upper()
    if origen:
        if origen in ORIGENES_FILTRO:
            filtros["origen"] = origen
        else:
            advertencias.append("El origen informado no era valido y fue ignorado.")

    estado = (parametros.get("estado") or "").strip().upper()
    if estado:
        if estado in ESTADOS_FILTRO:
            filtros["estado"] = estado
        else:
            advertencias.append("El estado informado no era valido y fue ignorado.")

    anio = _entero_get(parametros, "anio", None)
    if anio:
        if 2000 <= anio <= 2100:
            filtros["anio"] = anio
        else:
            advertencias.append("El ano informado no era valido y fue ignorado.")

    mes = _entero_get(parametros, "mes", None)
    if mes:
        if 1 <= mes <= 12:
            filtros["mes"] = mes
        else:
            advertencias.append("El mes informado no era valido y fue ignorado.")

    dia = _entero_get(parametros, "dia", None)
    if dia:
        if 1 <= dia <= 31:
            filtros["dia"] = dia
        else:
            advertencias.append("El dia informado no era valido y fue ignorado.")

    for campo in ("fecha_desde", "fecha_hasta"):
        valor = (parametros.get(campo) or "").strip()
        if not valor:
            continue
        try:
            datetime.strptime(valor, "%Y-%m-%d")
            filtros[campo] = valor
        except ValueError:
            advertencias.append(f"La fecha {campo.replace('_', ' ')} no era valida y fue ignorada.")

    return filtros, page, per_page, advertencias


def _entero_get(parametros, campo, default):
    valor = parametros.get(campo)
    if valor in (None, ""):
        return default
    try:
        return int(valor)
    except (TypeError, ValueError):
        return default


def _escribir_log(ruta, lineas):
    escribir_lineas_log(ruta, lineas)
